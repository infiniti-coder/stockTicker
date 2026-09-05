from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.market_status.service import MarketStatus

IST = ZoneInfo("Asia/Kolkata")


class _NoHolidaysClient:
    async def get_holidays(self):
        return []


def test_open_on_weekday_during_trading_hours():
    ms = MarketStatus(_NoHolidaysClient())
    monday_1030 = datetime(2026, 8, 24, 10, 30, tzinfo=IST)  # a Monday
    assert ms.is_open(monday_1030) is True


def test_closed_before_market_open():
    ms = MarketStatus(_NoHolidaysClient())
    monday_0900 = datetime(2026, 8, 24, 9, 0, tzinfo=IST)
    assert ms.is_open(monday_0900) is False


def test_closed_after_market_close():
    ms = MarketStatus(_NoHolidaysClient())
    monday_1600 = datetime(2026, 8, 24, 16, 0, tzinfo=IST)
    assert ms.is_open(monday_1600) is False


def test_closed_on_weekend():
    ms = MarketStatus(_NoHolidaysClient())
    saturday_1100 = datetime(2026, 8, 22, 11, 0, tzinfo=IST)
    assert ms.is_open(saturday_1100) is False


def test_closed_on_holiday():
    ms = MarketStatus(_NoHolidaysClient())
    ms._holidays = {date(2026, 8, 24)}
    monday_1030 = datetime(2026, 8, 24, 10, 30, tzinfo=IST)
    assert ms.is_open(monday_1030) is False
