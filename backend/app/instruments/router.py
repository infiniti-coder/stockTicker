from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.snapshots.depth_store import depth_store
from app.snapshots.service import get_snapshot, snapshot_to_dict

from .service import instrument_cache

router = APIRouter(prefix="/instruments", tags=["instruments"])


@router.get("/search")
def search(q: str = Query(..., min_length=1)) -> list[dict]:
    return [
        {
            "instrument_key": inst.instrument_key,
            "trading_symbol": inst.trading_symbol,
            "name": inst.name,
            "exchange": inst.exchange,
        }
        for inst in instrument_cache.search(q)
    ]


# Registered before the plain {instrument_key} route below: both use the
# :path converter (instrument keys contain "|"), and Starlette matches in
# registration order, so the more specific "/depth" suffix route must come
# first or it'd never be reached — the plain route's ".*" would swallow it.
@router.get("/{instrument_key:path}/depth")
def get_instrument_depth(instrument_key: str) -> dict:
    # No last-known fallback here on purpose (unlike get_snapshot elsewhere)
    # — a stale order book is misleading, not useful (see depth_store.py).
    # Empty levels + updated_at=None means "no live depth right now",
    # which is simply true outside market hours.
    return {
        "instrument_key": instrument_key,
        "updated_at": depth_store.updated_at(instrument_key),
        "levels": depth_store.get(instrument_key),
    }


@router.get("/{instrument_key:path}")
def get_instrument(instrument_key: str, db: Session = Depends(get_db)) -> dict:
    instrument = instrument_cache.get(instrument_key)
    if instrument is None:
        raise HTTPException(status_code=404, detail="Unknown instrument_key")
    snapshot = get_snapshot(db, instrument_key)
    return {
        "instrument_key": instrument.instrument_key,
        "trading_symbol": instrument.trading_symbol,
        "name": instrument.name,
        "exchange": instrument.exchange,
        "snapshot": snapshot_to_dict(snapshot) if snapshot else None,
    }
