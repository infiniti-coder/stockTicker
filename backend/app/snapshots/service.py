from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import LastSnapshot
from app.upstox_client.base import Quote

from .depth_store import depth_store


def upsert_snapshot(db: Session, quote: Quote) -> LastSnapshot:
    row = db.get(LastSnapshot, quote.instrument_key)
    now = datetime.now(timezone.utc)
    if row is None:
        row = LastSnapshot(instrument_key=quote.instrument_key)
        db.add(row)
    row.ltp = quote.ltp
    row.bid = quote.bid
    row.ask = quote.ask
    row.bid_qty = quote.bid_qty
    row.ask_qty = quote.ask_qty
    row.close = quote.close
    row.ts = now
    row.is_live = quote.is_live
    db.commit()
    db.refresh(row)
    if quote.depth:
        depth_store.set(quote.instrument_key, quote.depth)
    return row


def get_snapshot(db: Session, instrument_key: str) -> LastSnapshot | None:
    return db.get(LastSnapshot, instrument_key)


async def backfill_if_missing(db: Session, client, access_token: str | None, instrument_key: str) -> LastSnapshot | None:
    """Called when a symbol is added to the watchlist (or the app starts)
    and has no snapshot yet — fetches Upstox's Quote/LTP REST API once,
    which works even when the market is closed, unlike the WS feed
    (README §3, "Backfill on cold start / new symbol").
    """
    existing = get_snapshot(db, instrument_key)
    if existing is not None:
        return existing
    if access_token is None:
        return None
    quotes = await client.get_ltp_quotes(access_token, [instrument_key])
    quote = quotes.get(instrument_key)
    if quote is None:
        return None
    return upsert_snapshot(db, quote)


def snapshot_to_dict(row: LastSnapshot) -> dict:
    return {
        "instrument_key": row.instrument_key,
        "ltp": row.ltp,
        "bid": row.bid,
        "ask": row.ask,
        "bid_qty": row.bid_qty,
        "ask_qty": row.ask_qty,
        "close": row.close,
        "ts": row.ts.isoformat(),
        "is_live": row.is_live,
    }
