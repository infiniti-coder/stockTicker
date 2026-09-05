from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WatchlistItem(Base):
    """One browser's watchlist row. Scoped by session_id (a client-generated
    id the frontend stores in localStorage — see app/session.py) so
    multiple browsers each see their own list, not a single shared one."""

    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("session_id", "instrument_key", name="uq_watchlist_session_instrument"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    instrument_key: Mapped[str] = mapped_column(String, index=True)
    trading_symbol: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    exchange: Mapped[str] = mapped_column(String, default="NSE_EQ")
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class LastSnapshot(Base):
    """Last-known price for an instrument, upserted on every tick.

    Kept even when the market is closed / the app restarts, so the
    watchlist never renders a blank row (see README §3, "Data availability").
    """

    __tablename__ = "last_snapshots"

    instrument_key: Mapped[str] = mapped_column(String, primary_key=True)
    ltp: Mapped[float] = mapped_column(Float, default=0.0)
    bid: Mapped[float] = mapped_column(Float, default=0.0)
    ask: Mapped[float] = mapped_column(Float, default=0.0)
    bid_qty: Mapped[int] = mapped_column(Integer, default=0)
    ask_qty: Mapped[int] = mapped_column(Integer, default=0)
    close: Mapped[float] = mapped_column(Float, default=0.0)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    is_live: Mapped[bool] = mapped_column(Boolean, default=False)


class ChatMessage(Base):
    """One turn of the "Ask Claude" panel, scoped by session_id exactly
    like WatchlistItem — same browser -> same history on the next visit,
    no real login involved (see app/session.py)."""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(String)
    sources: Mapped[list] = mapped_column(JSON, default=list)  # [{"title": ..., "url": ...}, ...]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
