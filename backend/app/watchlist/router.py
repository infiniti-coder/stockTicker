from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.state import auth_state
from app.db import get_db
from app.instruments.service import instrument_cache
from app.session import get_session_id
from app.snapshots.service import backfill_if_missing, get_snapshot, snapshot_to_dict
from app.upstox_client import UpstoxClient, get_upstox_client

from . import service

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class AddWatchlistItem(BaseModel):
    instrument_key: str


@router.get("")
async def get_watchlist(db: Session = Depends(get_db), session_id: str = Depends(get_session_id)) -> list[dict]:
    items = service.list_watchlist(db, session_id)
    result = []
    for item in items:
        snapshot = get_snapshot(db, item.instrument_key)
        result.append(
            {
                "instrument_key": item.instrument_key,
                "trading_symbol": item.trading_symbol,
                "name": item.name,
                "snapshot": snapshot_to_dict(snapshot) if snapshot else None,
            }
        )
    return result


@router.post("")
async def add_watchlist_item(
    body: AddWatchlistItem,
    db: Session = Depends(get_db),
    client: UpstoxClient = Depends(get_upstox_client),
    session_id: str = Depends(get_session_id),
) -> dict:
    instrument = instrument_cache.get(body.instrument_key)
    if instrument is None:
        raise HTTPException(status_code=404, detail="Unknown instrument_key")

    item = service.add_to_watchlist(
        db,
        session_id=session_id,
        instrument_key=instrument.instrument_key,
        trading_symbol=instrument.trading_symbol,
        name=instrument.name,
    )
    await backfill_if_missing(db, client, auth_state.access_token, item.instrument_key)
    snapshot = get_snapshot(db, item.instrument_key)
    return {
        "instrument_key": item.instrument_key,
        "trading_symbol": item.trading_symbol,
        "name": item.name,
        "snapshot": snapshot_to_dict(snapshot) if snapshot else None,
    }


@router.delete("/{instrument_key:path}")
def remove_watchlist_item(
    instrument_key: str, db: Session = Depends(get_db), session_id: str = Depends(get_session_id)
) -> dict:
    removed = service.remove_from_watchlist(db, session_id, instrument_key)
    if not removed:
        raise HTTPException(status_code=404, detail="Not in watchlist")
    return {"removed": instrument_key}
