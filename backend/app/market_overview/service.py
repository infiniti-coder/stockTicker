import logging
from concurrent.futures import ThreadPoolExecutor

import yfinance as yf

from .themes import classify

logger = logging.getLogger(__name__)

INFO_FETCH_WORKERS = 20

# Trading-day offsets from the latest close for each period except 5y,
# which just uses the earliest close in the fetched 5y window (so a
# recently-listed stock with less history still gets a best-effort figure
# instead of nothing).
PERIOD_TRADING_DAYS = {
    "1d": 1,
    "1w": 5,
    "1m": 21,
    "6m": 126,
    "1y": 252,
}


def _compute_returns(close: "list[float]") -> dict[str, float | None]:
    if not close:
        return {p: None for p in (*PERIOD_TRADING_DAYS, "5y")}
    latest = close[-1]
    returns: dict[str, float | None] = {}
    for period, offset in PERIOD_TRADING_DAYS.items():
        if len(close) > offset and close[-1 - offset]:
            past = close[-1 - offset]
            returns[period] = (latest - past) / past * 100
        else:
            returns[period] = None
    first = close[0]
    returns["5y"] = (latest - first) / first * 100 if first else None
    return returns


def _fetch_info(symbol: str) -> dict:
    try:
        info = yf.Ticker(symbol).info
    except Exception:
        logger.exception("Failed to fetch info for %s", symbol)
        return {}
    return info or {}


def fetch_region_overview(tickers: list[str], extra_info_fields: tuple[str, ...] = ()) -> list[dict]:
    """Synchronous, network-bound — call via asyncio.to_thread from the
    router so it never blocks the event loop the Kafka consumers run on.

    extra_info_fields: optional raw yfinance `.info` keys (already fetched
    for sector/industry/market_cap below, at no extra network cost) to
    include under a "fundamentals" key per stock. Omitted by default so the
    treemap's response shape is unchanged; app/chat/tools.py passes a
    curated list so the chat/screener agents can ground claims like
    "improving margins" in real numbers instead of only web-search prose."""
    history = yf.download(tickers, period="5y", interval="1d", group_by="ticker", progress=False, threads=True)

    with ThreadPoolExecutor(max_workers=INFO_FETCH_WORKERS) as pool:
        infos = dict(zip(tickers, pool.map(_fetch_info, tickers)))

    results: list[dict] = []
    for symbol in tickers:
        info = infos.get(symbol, {})
        market_cap = info.get("marketCap")
        if market_cap is None:
            continue  # unusable without a size for the treemap

        try:
            close = history[symbol]["Close"].dropna().tolist()
        except (KeyError, TypeError):
            close = []

        sector = info.get("sector")
        industry = info.get("industry")
        stock = {
            "symbol": symbol,
            "name": info.get("longName") or info.get("shortName") or symbol,
            "market_cap": market_cap,
            "sector": sector,
            "industry": industry,
            "theme": classify(sector, industry),
            "returns": _compute_returns(close),
        }
        if extra_info_fields:
            stock["fundamentals"] = {field: info.get(field) for field in extra_info_fields}
        results.append(stock)
    return results


def fetch_full_history(symbol: str) -> list[dict]:
    """Daily closes from inception (yfinance's earliest available bar) to
    today. Synchronous/network-bound — call via asyncio.to_thread."""
    df = yf.download(symbol, period="max", interval="1d", progress=False)
    if df.empty:
        return []

    close = df["Close"]
    if hasattr(close, "columns"):  # single-ticker download still nests a Ticker column level
        close = close[symbol]
    close = close.dropna()

    return [{"date": ts.strftime("%Y-%m-%d"), "close": float(v)} for ts, v in close.items()]
