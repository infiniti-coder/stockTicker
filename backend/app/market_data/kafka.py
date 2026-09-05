import json
from dataclasses import asdict
from datetime import datetime, timezone

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.config import get_settings
from app.upstox_client.base import DepthLevel, Quote

MARKET_TICKS_TOPIC = "market-ticks"


def make_producer() -> AIOKafkaProducer:
    settings = get_settings()
    return AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)


def make_consumer(*, group_id: str) -> AIOKafkaConsumer:
    settings = get_settings()
    return AIOKafkaConsumer(
        MARKET_TICKS_TOPIC,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=group_id,
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )


def serialize_quote(quote: Quote) -> bytes:
    return json.dumps(asdict(quote)).encode("utf-8")


def deserialize_quote(raw: bytes) -> Quote:
    data = json.loads(raw)
    depth = [DepthLevel(**level) for level in data.pop("depth", [])]
    return Quote(**data, depth=depth)


def quote_to_tick_message(quote: Quote) -> dict:
    """Same field shape as app.snapshots.service.snapshot_to_dict, for the
    frontend's shared Snapshot type — built from a live Quote instead of a
    DB row, so `ts` is generated at forward time."""
    return {
        "type": "tick",
        "instrument_key": quote.instrument_key,
        "ltp": quote.ltp,
        "bid": quote.bid,
        "ask": quote.ask,
        "bid_qty": quote.bid_qty,
        "ask_qty": quote.ask_qty,
        "close": quote.close,
        "ts": datetime.now(timezone.utc).isoformat(),
        "is_live": quote.is_live,
        "depth": [asdict(level) for level in quote.depth],
    }
