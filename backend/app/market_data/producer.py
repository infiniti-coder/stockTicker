import asyncio
import logging

from aiokafka import AIOKafkaProducer

from app.upstox_client.fixtures import MOCK_INSTRUMENTS
from app.upstox_client.mock_client import MockUpstoxClient

from .kafka import MARKET_TICKS_TOPIC, serialize_quote

logger = logging.getLogger(__name__)

TICK_INTERVAL_SECONDS = 1.5


class MockTickProducer:
    """Ticks every mock instrument onto Kafka, independent of any
    watchlist, market hours, or login state — the mock feed is meant to
    look "live" at any time of day (README, "Mock mode vs. live mode")."""

    def __init__(self, producer: AIOKafkaProducer, client: MockUpstoxClient) -> None:
        self._producer = producer
        self._client = client
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None
        await self._producer.stop()

    async def _run(self) -> None:
        await self._producer.start()
        try:
            while True:
                await asyncio.sleep(TICK_INTERVAL_SECONDS)
                for instrument in MOCK_INSTRUMENTS:
                    quote = self._client.make_quote(instrument.instrument_key, is_live=True, walk=True)
                    await self._producer.send(
                        MARKET_TICKS_TOPIC,
                        key=quote.instrument_key.encode("utf-8"),
                        value=serialize_quote(quote),
                    )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("MockTickProducer loop error")
