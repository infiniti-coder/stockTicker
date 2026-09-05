from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import WatchlistItem


def list_watchlist(db: Session, session_id: str) -> list[WatchlistItem]:
    return list(
        db.scalars(
            select(WatchlistItem).where(WatchlistItem.session_id == session_id).order_by(WatchlistItem.added_at)
        )
    )


def add_to_watchlist(
    db: Session, *, session_id: str, instrument_key: str, trading_symbol: str, name: str
) -> WatchlistItem:
    existing = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.session_id == session_id, WatchlistItem.instrument_key == instrument_key
        )
    )
    if existing is not None:
        return existing
    item = WatchlistItem(session_id=session_id, instrument_key=instrument_key, trading_symbol=trading_symbol, name=name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_watchlist(db: Session, session_id: str, instrument_key: str) -> bool:
    item = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.session_id == session_id, WatchlistItem.instrument_key == instrument_key
        )
    )
    if item is None:
        return False
    db.delete(item)
    db.commit()
    return True
