import asyncio
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth.state import auth_state
from app.db import SessionLocal
from app.market_data.kafka import deserialize_quote, make_consumer, quote_to_tick_message
from app.snapshots.depth_store import depth_store
from app.snapshots.service import backfill_if_missing, get_snapshot, snapshot_to_dict
from app.upstox_client import get_upstox_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ws"])


@router.websocket("/ws/prices")
async def ws_prices(ws: WebSocket) -> None:
    """Each browser tab gets its own Kafka consumer group, reading the
    full market-ticks stream independently and filtering to whatever it's
    currently subscribed to — see docs/architecture.html for the shape of
    this fan-out (no shared in-process broadcaster anymore)."""
    await ws.accept()
    subscribed: set[str] = set()

    consumer = make_consumer(group_id=f"ws-{uuid.uuid4().hex}")
    await consumer.start()
    forward_task = asyncio.create_task(_forward_ticks(consumer, ws, subscribed))

    try:
        while True:
            msg = await ws.receive_json()
            if msg.get("type") != "subscribe":
                continue
            instrument_keys = list(msg.get("instrument_keys", []))
            subscribed.clear()
            subscribed.update(instrument_keys)

            db = SessionLocal()
            try:
                client = get_upstox_client()
                snapshots = []
                for key in instrument_keys:
                    snapshot = get_snapshot(db, key)
                    if snapshot is None:
                        snapshot = await backfill_if_missing(db, client, auth_state.access_token, key)
                    if snapshot is not None:
                        snapshots.append({**snapshot_to_dict(snapshot), "depth": depth_store.get(key)})
            finally:
                db.close()

            await ws.send_json({"type": "snapshot", "data": snapshots})
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("ws/prices connection error")
    finally:
        forward_task.cancel()
        await consumer.stop()


async def _forward_ticks(consumer, ws: WebSocket, subscribed: set[str]) -> None:
    try:
        async for msg in consumer:
            quote = deserialize_quote(msg.value)
            if quote.instrument_key not in subscribed:
                continue
            await ws.send_json(quote_to_tick_message(quote))
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("ws/prices tick-forward error")
