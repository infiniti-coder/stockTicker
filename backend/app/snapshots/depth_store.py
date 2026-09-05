from datetime import datetime, timezone

from app.upstox_client.base import DepthLevel


class DepthStore:
    """Latest order-book depth per instrument — overwritten on every tick,
    not a history. An in-memory-only, live-only concept: unlike LTP (see
    LastSnapshot), a stale order book from a past session is misleading
    rather than useful, so nothing here is persisted or served as
    last-known (README §3's last-known fallback applies to price, not
    depth). Empty whenever the market's closed or the app just restarted.
    """

    def __init__(self) -> None:
        self._depth: dict[str, list[DepthLevel]] = {}
        self._updated_at: dict[str, datetime] = {}

    def set(self, instrument_key: str, levels: list[DepthLevel]) -> None:
        self._depth[instrument_key] = levels
        self._updated_at[instrument_key] = datetime.now(timezone.utc)

    def get(self, instrument_key: str) -> list[dict]:
        return [
            {"bid_price": lvl.bid_price, "bid_qty": lvl.bid_qty, "ask_price": lvl.ask_price, "ask_qty": lvl.ask_qty}
            for lvl in self._depth.get(instrument_key, [])
        ]

    def updated_at(self, instrument_key: str) -> str | None:
        ts = self._updated_at.get(instrument_key)
        return ts.isoformat() if ts else None


depth_store = DepthStore()
