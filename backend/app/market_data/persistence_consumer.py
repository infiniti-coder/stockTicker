import asyncio
import logging

from aiokafka import AIOKafkaConsumer

from app.db import SessionLocal
from app.snapshots.service import upsert_snapshot

from .kafka import deserialize_quote

logger = logging.getLogger(__name__)

PERSISTENCE_GROUP_ID = "backend-persistence"


class PersistenceConsumer:
    """The one backend-owned Kafka consumer: keeps SQLite's last-known
    snapshot (and the in-memory depth store) warm for every instrument, so
    REST reads and a freshly-connected browser's initial snapshot are
    correct even before that browser's own tick has arrived."""

    def __init__(self, consumer: AIOKafkaConsumer) -> None:
        self._consumer = consumer
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None
        await self._consumer.stop()

    async def _run(self) -> None:
        await self._consumer.start()
        try:
            async for msg in self._consumer:
                quote = deserialize_quote(msg.value)
                db = SessionLocal()
                try:
                    upsert_snapshot(db, quote)
                finally:
                    db.close()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("PersistenceConsumer loop error")
