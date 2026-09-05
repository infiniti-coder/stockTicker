import logging
import time
from datetime import date, datetime, time as dtime
from zoneinfo import ZoneInfo

from app.upstox_client.base import UpstoxClient

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
MARKET_OPEN = dtime(9, 15)
MARKET_CLOSE = dtime(15, 30)

HOLIDAY_REFRESH_SECONDS = 6 * 60 * 60  # holiday list rarely changes intraday


class MarketStatus:
    """Weekday + NSE holiday-calendar check for whether the feed should be
    ticking right now (README §3, "Market-hours awareness"). Holidays are
    refreshed periodically from Upstox rather than hardcoded, per README §9.
    """

    def __init__(self, client: UpstoxClient) -> None:
        self._client = client
        self._holidays: set[date] = set()
        self._holidays_fetched_at: float = 0.0

    async def refresh_holidays_if_stale(self) -> None:
        if time.monotonic() - self._holidays_fetched_at < HOLIDAY_REFRESH_SECONDS:
            return
        try:
            holidays = await self._client.get_holidays()
            self._holidays = set(holidays)
            self._holidays_fetched_at = time.monotonic()
        except Exception:
            logger.exception("Failed to refresh holiday calendar; keeping previous list")

    def is_open(self, now: datetime | None = None) -> bool:
        now = (now or datetime.now(IST)).astimezone(IST)
        if now.weekday() >= 5:  # Sat/Sun
            return False
        if now.date() in self._holidays:
            return False
        return MARKET_OPEN <= now.time() <= MARKET_CLOSE
