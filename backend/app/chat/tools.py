import asyncio
import json

from anthropic import beta_async_tool

from app.market_overview import universe
from app.market_overview.service import fetch_full_history, fetch_region_overview

REGIONS: dict[str, list[str]] = {"india": universe.INDIA, "world": universe.WORLD}
HISTORY_YEAR_STRIDE = 252  # ~1 trading year, keeps the summary light on context

# Already sitting in the same yfinance .info dict fetch_region_overview
# fetches for sector/industry/market_cap — free to include, and lets the
# chat/screener agents ground "improving margins"-style claims in real
# numbers instead of only whatever a web search happens to surface.
FUNDAMENTAL_FIELDS = ("profitMargins", "revenueGrowth", "trailingPE", "returnOnEquity", "earningsGrowth")


def _summarize_history(points: list[dict]) -> dict:
    if not points:
        return {}
    yearly = points[::HISTORY_YEAR_STRIDE]
    if yearly[-1] is not points[-1]:
        yearly = [*yearly, points[-1]]
    first, last = points[0], points[-1]
    change_pct = (last["close"] - first["close"]) / first["close"] * 100 if first["close"] else None
    return {
        "from": first["date"],
        "to": last["date"],
        "latest_close": last["close"],
        "change_pct_since_inception": change_pct,
        "yearly_closes": yearly,
    }


@beta_async_tool
async def get_stock_data(region: str, symbol: str | None = None) -> str:
    """Real market data from stockTicker's own live feed — the same numbers
    shown in the app's market-overview treemap. Always prefer this over
    guessing a number.

    Args:
        region: "india" or "world" — which stock universe to query. Returns
            market cap, sector, theme, period returns (1d/1w/1m/6m/1y/5y),
            and fundamentals (profit margin, revenue growth, trailing P/E,
            ROE, earnings growth) for every stock in that universe.
        symbol: optional exact ticker (e.g. "RELIANCE.NS", "AAPL") already
            present in that region's universe — also returns a price-history
            summary (yearly closes + overall change since inception) for
            that one stock.
    """
    tickers = REGIONS.get(region)
    if tickers is None:
        return json.dumps({"error": "region must be 'india' or 'world'"})

    stocks = await asyncio.to_thread(fetch_region_overview, tickers, FUNDAMENTAL_FIELDS)
    result: dict = {"region": region, "stocks": stocks}

    if symbol:
        if symbol not in tickers:
            result["history_error"] = f"{symbol} is not in the {region} universe"
        else:
            points = await asyncio.to_thread(fetch_full_history, symbol)
            result["history_summary"] = _summarize_history(points)

    return json.dumps(result, default=str)
