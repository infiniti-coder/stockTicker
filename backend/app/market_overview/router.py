import asyncio
from typing import Literal

from fastapi import APIRouter, HTTPException

from . import universe
from .service import fetch_full_history, fetch_region_overview

router = APIRouter(prefix="/market-overview", tags=["market-overview"])

REGIONS: dict[str, list[str]] = {"india": universe.INDIA, "world": universe.WORLD}
ALL_SYMBOLS: set[str] = {*universe.INDIA, *universe.WORLD}


@router.get("")
async def get_market_overview(region: Literal["india", "world"]) -> dict:
    tickers = REGIONS.get(region)
    if tickers is None:
        raise HTTPException(status_code=400, detail="region must be 'india' or 'world'")

    stocks = await asyncio.to_thread(fetch_region_overview, tickers)
    return {"region": region, "stocks": stocks}


@router.get("/history")
async def get_market_overview_history(symbol: str) -> dict:
    # Restricted to the known universe rather than any string, so this
    # endpoint can't be used as an open proxy for arbitrary yfinance queries.
    if symbol not in ALL_SYMBOLS:
        raise HTTPException(status_code=404, detail="Unknown symbol")

    points = await asyncio.to_thread(fetch_full_history, symbol)
    return {"symbol": symbol, "points": points}
