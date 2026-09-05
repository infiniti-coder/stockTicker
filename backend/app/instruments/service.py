import logging

from app.upstox_client.base import Instrument, UpstoxClient

logger = logging.getLogger(__name__)


class InstrumentCache:
    """In-memory NSE equity instrument master, loaded once at startup.

    ~2000 NSE-equity rows (or 20 in mock mode) comfortably fits in memory;
    no need for a DB-backed search index at this scale (README §7 keeps this
    separate from the watchlist DB table on purpose — one is a reference
    list, the other is user data).
    """

    def __init__(self) -> None:
        self._instruments: list[Instrument] = []

    async def load(self, client: UpstoxClient) -> None:
        try:
            self._instruments = await client.get_instruments()
            logger.info("Loaded %d instruments", len(self._instruments))
        except Exception:
            logger.exception("Failed to load instrument master")
            self._instruments = []

    def search(self, query: str, limit: int = 20) -> list[Instrument]:
        q = query.strip().upper()
        if not q:
            return []
        results = [
            inst
            for inst in self._instruments
            if q in inst.trading_symbol.upper() or q in inst.name.upper()
        ]
        results.sort(key=lambda inst: (not inst.trading_symbol.upper().startswith(q), inst.trading_symbol))
        return results[:limit]

    def get(self, instrument_key: str) -> Instrument | None:
        for inst in self._instruments:
            if inst.instrument_key == instrument_key:
                return inst
        return None


instrument_cache = InstrumentCache()
