import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.chat.router import router as chat_router
from app.config import get_settings
from app.db import init_db
from app.instruments.router import router as instruments_router
from app.instruments.service import instrument_cache
from app.market_data.kafka import make_consumer, make_producer
from app.market_data.persistence_consumer import PERSISTENCE_GROUP_ID, PersistenceConsumer
from app.market_data.producer import MockTickProducer
from app.market_overview.router import router as market_overview_router
from app.upstox_client import get_upstox_client
from app.watchlist.router import router as watchlist_router
from app.ws_gateway.router import router as ws_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()

    client = get_upstox_client()
    await instrument_cache.load(client)

    producer = None
    persistence = None
    if settings.kafka_enabled:
        producer = MockTickProducer(make_producer(), client)
        producer.start()
        persistence = PersistenceConsumer(make_consumer(group_id=PERSISTENCE_GROUP_ID))
        persistence.start()

    logger.info("stockTicker backend started in MOCK mode (Kafka %s)", "enabled" if settings.kafka_enabled else "disabled")

    yield

    if producer is not None:
        await producer.stop()
    if persistence is not None:
        await persistence.stop()


app = FastAPI(title="stockTicker", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(instruments_router)
app.include_router(watchlist_router)
app.include_router(ws_router)
app.include_router(market_overview_router)
app.include_router(chat_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mock": settings.use_mock_upstox, "kafka_enabled": settings.kafka_enabled}
