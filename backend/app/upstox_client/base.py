from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Instrument:
    instrument_key: str
    trading_symbol: str
    name: str
    exchange: str = "NSE_EQ"


@dataclass(frozen=True, slots=True)
class DepthLevel:
    bid_price: float
    bid_qty: int
    ask_price: float
    ask_qty: int


@dataclass(frozen=True, slots=True)
class Quote:
    instrument_key: str
    ltp: float
    bid: float
    ask: float
    bid_qty: int
    ask_qty: int
    close: float
    is_live: bool
    # Multi-level order book (up to 10 levels), only populated on ticks from
    # the live WS feed — REST LTP backfill has no depth data, and a stale
    # order book from a past session is misleading rather than useful (unlike
    # a stale *price*, which is a legitimate last-known value — see
    # snapshots/service.py). Empty outside market hours.
    depth: list[DepthLevel] = field(default_factory=list)


class UpstoxClient(Protocol):
    """Everything the rest of the backend needs from Upstox.

    Implemented by RealUpstoxClient (OAuth2 + REST + protobuf WS feed against
    the real broker API) and MockUpstoxClient (synthetic data, no account
    needed). Every other module (auth, watchlist, snapshots, ws_gateway)
    codes against this interface, not against either implementation, so
    swapping mock <-> real is a one-line change in get_upstox_client().
    """

    def get_login_url(self, state: str) -> str:
        """URL to send the browser to for the Upstox OAuth consent screen."""
        ...

    async def exchange_code(self, code: str) -> str:
        """Exchange an OAuth `code` for an access token."""
        ...

    async def get_instruments(self) -> list[Instrument]:
        """NSE equity instrument master, for search/autocomplete."""
        ...

    async def get_ltp_quotes(self, access_token: str, instrument_keys: list[str]) -> dict[str, Quote]:
        """REST snapshot (works even when the market is closed) — used to
        backfill a symbol the first time it's added, before any tick has
        arrived over the WS feed."""
        ...

    async def get_holidays(self) -> list[date]:
        """NSE exchange holiday calendar for the current year."""
        ...

    def open_feed(self, access_token: str, instrument_keys: list[str]) -> AsyncIterator[Quote]:
        """Open the live market-data feed and yield ticks as they arrive.

        Not called anywhere in the app anymore — app/market_data/producer.py
        drives the mock feed onto Kafka instead. Kept for Protocol
        conformance with RealUpstoxClient, which still implements it.
        """
        ...
