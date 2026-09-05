import asyncio
import random
from collections.abc import AsyncIterator
from datetime import date

from .base import DepthLevel, Instrument, Quote
from .fixtures import MOCK_BASE_PRICE, MOCK_INSTRUMENTS

MOCK_ACCESS_TOKEN = "mock-access-token"
DEPTH_LEVELS = 10


class MockUpstoxClient:
    """Synthetic stand-in for RealUpstoxClient.

    Lets the whole app (search, watchlist, snapshots, live WS fan-out) run
    without an Upstox developer account. `open_feed` ticks continuously
    (it doesn't gate on real market hours) so the "live" experience is
    testable at any time of day.
    """

    def __init__(self, redirect_uri: str = "http://localhost:8000/auth/callback") -> None:
        self._prices = dict(MOCK_BASE_PRICE)
        self._redirect_uri = redirect_uri

    def get_login_url(self, state: str) -> str:
        # No real consent screen to send the browser to — go straight to our
        # own callback with a fake code, as if the user had just approved.
        return f"{self._redirect_uri}?code=mock-auth-code&state={state}"

    async def exchange_code(self, code: str) -> str:
        return MOCK_ACCESS_TOKEN

    async def get_instruments(self) -> list[Instrument]:
        return list(MOCK_INSTRUMENTS)

    async def get_ltp_quotes(self, access_token: str, instrument_keys: list[str]) -> dict[str, Quote]:
        return {key: self.make_quote(key, is_live=False) for key in instrument_keys}

    async def get_holidays(self) -> list[date]:
        return []

    async def open_feed(self, access_token: str, instrument_keys: list[str]) -> AsyncIterator[Quote]:
        # Superseded by app.market_data.producer.MockTickProducer, which
        # ticks every instrument (not just a subscribed subset) onto Kafka.
        # Left in place for UpstoxClient Protocol conformance.
        try:
            while True:
                await asyncio.sleep(1.5)
                for key in instrument_keys:
                    if key not in self._prices:
                        continue
                    yield self.make_quote(key, is_live=True, walk=True)
        except asyncio.CancelledError:
            return

    def make_quote(self, key: str, *, is_live: bool, walk: bool = False) -> Quote:
        base = self._prices.get(key)
        if base is None:
            base = 100.0
        if walk:
            base = max(1.0, base * (1 + random.uniform(-0.0015, 0.0015)))
            self._prices[key] = base
        spread = max(0.05, base * 0.0005)
        tick = max(0.05, round(base * 0.0005, 2))

        # Real order-book depth only exists on live WS ticks (see base.Quote);
        # REST backfill (is_live=False / walk=False) gets no depth, matching
        # the real client's REST-vs-feed split.
        depth = _make_depth_levels(base, tick) if is_live and walk else []

        return Quote(
            instrument_key=key,
            ltp=round(base, 2),
            bid=round(base - spread, 2),
            ask=round(base + spread, 2),
            bid_qty=random.randint(1, 500),
            ask_qty=random.randint(1, 500),
            close=round(MOCK_BASE_PRICE.get(key, base), 2),
            is_live=is_live,
            depth=depth,
        )


def _make_depth_levels(base: float, tick: float) -> list[DepthLevel]:
    levels = []
    for i in range(1, DEPTH_LEVELS + 1):
        levels.append(
            DepthLevel(
                bid_price=round(base - i * tick, 2),
                bid_qty=random.randint(1, 500),
                ask_price=round(base + i * tick, 2),
                ask_qty=random.randint(1, 500),
            )
        )
    return levels
