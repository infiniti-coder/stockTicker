import gzip
import json
import logging
import uuid
from collections.abc import AsyncIterator
from datetime import date, datetime

import httpx
import websockets

from .base import DepthLevel, Instrument, Quote
from .proto import MarketDataFeed_pb2 as pb

logger = logging.getLogger(__name__)

API_BASE = "https://api.upstox.com"
AUTH_DIALOG_URL = f"{API_BASE}/v2/login/authorization/dialog"
TOKEN_URL = f"{API_BASE}/v2/login/authorization/token"
LTP_URL = f"{API_BASE}/v3/market-quote/ltp"
FEED_AUTHORIZE_URL = f"{API_BASE}/v3/feed/market-data-feed/authorize"
HOLIDAYS_URL = f"{API_BASE}/v2/market/holidays"
INSTRUMENTS_URL = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"

MAX_DEPTH_LEVELS = 10

# 2026-08-28: "full_d30" (up to 30 depth levels) requires an entitlement this
# app doesn't have — Upstox accepts the subscription but then sends nothing
# for it at all (no data, no error frame), which looked like a dead feed.
# "full" (5 depth levels) works with default Market Data Feed V3 access.
FEED_MODE = "full"


class RealUpstoxClient:
    """Talks to the real Upstox OAuth2 + REST + protobuf WebSocket feed.

    Endpoints and the .proto schema were pulled from the official Upstox
    developer docs (see comments below and proto/MarketDataFeed.proto) as of
    2026-08-25. Upstox has changed these before (see README §5) — if calls
    start failing, diff against https://upstox.com/developer/api-documentation/
    before assuming this code is wrong.
    """

    def __init__(self, api_key: str, api_secret: str, redirect_uri: str) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._redirect_uri = redirect_uri

    def get_login_url(self, state: str) -> str:
        params = httpx.QueryParams(
            {
                "response_type": "code",
                "client_id": self._api_key,
                "redirect_uri": self._redirect_uri,
                "state": state,
            }
        )
        return f"{AUTH_DIALOG_URL}?{params}"

    async def exchange_code(self, code: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                TOKEN_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
                data={
                    "code": code,
                    "client_id": self._api_key,
                    "client_secret": self._api_secret,
                    "redirect_uri": self._redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            resp.raise_for_status()
            return resp.json()["access_token"]

    async def get_instruments(self) -> list[Instrument]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(INSTRUMENTS_URL, timeout=60)
            resp.raise_for_status()
            raw = gzip.decompress(resp.content)
            records = json.loads(raw)

        instruments: list[Instrument] = []
        for rec in records:
            # Equity segment only for the MVP watchlist (README §9).
            if rec.get("segment") != "NSE_EQ" and rec.get("instrument_type") != "EQ":
                continue
            instruments.append(
                Instrument(
                    instrument_key=rec["instrument_key"],
                    trading_symbol=rec.get("trading_symbol", ""),
                    name=rec.get("name", rec.get("trading_symbol", "")),
                    exchange="NSE_EQ",
                )
            )
        return instruments

    async def get_ltp_quotes(self, access_token: str, instrument_keys: list[str]) -> dict[str, Quote]:
        if not instrument_keys:
            return {}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                LTP_URL,
                params={"instrument_key": ",".join(instrument_keys)},
                headers=self._auth_headers(access_token),
            )
            resp.raise_for_status()
            payload = resp.json()["data"]

        quotes: dict[str, Quote] = {}
        for entry in payload.values():
            key = entry["instrument_token"]
            ltp = float(entry.get("last_price", 0.0))
            quotes[key] = Quote(
                instrument_key=key,
                ltp=ltp,
                # The LTP endpoint doesn't return live bid/ask depth (that's
                # WS-feed-only); use ltp as a same-price fallback so a
                # freshly-added symbol still renders sane values pre-feed.
                bid=ltp,
                ask=ltp,
                bid_qty=0,
                ask_qty=0,
                close=ltp,
                is_live=False,
                # No order-book depth over REST — only the live WS feed has
                # it (see base.Quote).
            )
        return quotes

    async def get_holidays(self) -> list[date]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(HOLIDAYS_URL)
            resp.raise_for_status()
            payload = resp.json()["data"]
        return [datetime.strptime(item["date"], "%Y-%m-%d").date() for item in payload]

    async def open_feed(self, access_token: str, instrument_keys: list[str]) -> AsyncIterator[Quote]:
        if not instrument_keys:
            return
        ws_url = await self._get_feed_ws_url(access_token)
        async with websockets.connect(ws_url) as ws:
            subscribe_msg = json.dumps(
                {
                    "guid": str(uuid.uuid4()),
                    "method": "sub",
                    "data": {"mode": FEED_MODE, "instrumentKeys": instrument_keys},
                }
            ).encode("utf-8")
            await ws.send(subscribe_msg)

            async for raw in ws:
                if isinstance(raw, str):
                    # Upstox sends subscription errors (e.g. a mode the app
                    # isn't entitled to) as a text frame with no other signal
                    # — surface it instead of dropping it silently.
                    logger.warning("feed text frame (possible error from Upstox): %s", raw)
                    continue
                feed_response = pb.FeedResponse()
                feed_response.ParseFromString(raw)
                for key, feed in feed_response.feeds.items():
                    quote = _feed_to_quote(key, feed)
                    if quote is not None:
                        yield quote

    async def _get_feed_ws_url(self, access_token: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.get(FEED_AUTHORIZE_URL, headers=self._auth_headers(access_token))
            resp.raise_for_status()
            return resp.json()["data"]["authorized_redirect_uri"]

    def _auth_headers(self, access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}


def _feed_to_quote(instrument_key: str, feed: "pb.Feed") -> Quote | None:
    which = feed.WhichOneof("FeedUnion")
    if which == "ltpc":
        ltpc = feed.ltpc
        return Quote(
            instrument_key=instrument_key,
            ltp=ltpc.ltp,
            bid=ltpc.ltp,
            ask=ltpc.ltp,
            bid_qty=0,
            ask_qty=0,
            close=ltpc.cp,
            is_live=True,
        )
    if which == "fullFeed":
        full = feed.fullFeed
        market = full.marketFF if full.WhichOneof("FullFeedUnion") == "marketFF" else None
        if market is None:
            return None
        levels = market.marketLevel.bidAskQuote[:MAX_DEPTH_LEVELS]
        top = levels[0] if levels else None
        return Quote(
            instrument_key=instrument_key,
            ltp=market.ltpc.ltp,
            bid=top.bidP if top else market.ltpc.ltp,
            ask=top.askP if top else market.ltpc.ltp,
            bid_qty=int(top.bidQ) if top else 0,
            ask_qty=int(top.askQ) if top else 0,
            close=market.ltpc.cp,
            is_live=True,
            depth=[
                DepthLevel(bid_price=lvl.bidP, bid_qty=int(lvl.bidQ), ask_price=lvl.askP, ask_qty=int(lvl.askQ))
                for lvl in levels
            ],
        )
    return None
