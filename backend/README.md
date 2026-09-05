# backend

FastAPI backend for stockTicker. See the root `README.md` for the full
architecture; this file is local setup notes.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env
```

Fill in `ANTHROPIC_API_KEY` if you want the "Ask Claude" chat panel or
the screener agent to work — everything else runs without it. Leave
`UPSTOX_API_KEY`/`UPSTOX_API_SECRET` blank; they're unused (see below).

## Live prices need Kafka

`/ws/prices` and the watchlist's live updates depend on a Kafka broker.
Locally that's Redpanda, started from the repo root:

```bash
docker compose up redpanda
```

`KAFKA_BOOTSTRAP_SERVERS` in `.env` should point at Redpanda's
host-exposed `OUTSIDE` listener (`localhost:19092` by default — see
`docker-compose.yml`). If you don't need live prices (e.g. running the
test suite), set `KAFKA_ENABLED=false` in `.env` to skip starting the
tick producer and consumers entirely; `backend/tests/conftest.py` does
exactly this.

On startup with Kafka enabled, the app runs:

- `MockTickProducer` — publishes synthetic ticks for the mock instrument
  universe to the `market-ticks` topic.
- `PersistenceConsumer` (group `backend-persistence`) — persists every
  tick to `last_snapshots` in SQLite.

Each `/ws/prices` WebSocket connection then opens its **own** Kafka
consumer group (`ws-<uuid>`) in `app/ws_gateway/router.py`, independently
reading the full stream and filtering to whatever that browser has
subscribed to.

## Mock market data (always on)

`get_upstox_client()` (`app/upstox_client/__init__.py`) always returns
`mock_client.py`: a fixed set of synthetic NSE instruments and (via
`MockTickProducer`) a continuously ticking feed that ignores real market
hours, so it's testable at any time of day. No Upstox account or
credentials are needed for anything in this app.

`real_client.py` (real Upstox OAuth + REST + protobuf WebSocket feed) is
still in the repo and fully implemented, just unreferenced — swap the
branch in `get_upstox_client()` to reconnect it. If you do, regenerate
the protobuf stubs it depends on:

```bash
python -m app.upstox_client.proto.generate
```

`app/upstox_client/proto/MarketDataFeed_pb2.py` is a build artifact (not
committed — see `.gitignore`), generated from the checked-in
`MarketDataFeed.proto`. Re-download it from
https://assets.upstox.com/feed/market-data-feed/v3/MarketDataFeed.proto
if Upstox revs the feed schema. Note this is unused by the current
mock-only pipeline, which sends plain JSON over Kafka
(`app/market_data/kafka.py`) — it only matters if `real_client.py` is
reconnected.

## Market overview, chat, and screener

- `app/market_overview/` fetches real quotes/fundamentals via `yfinance`
  for the treemap and per-stock history endpoints — no API key needed.
- `app/chat/` and `app/screener/` call the Anthropic API
  (`claude-opus-5`, `tool_runner`, server-side web search) and require
  `ANTHROPIC_API_KEY` in `.env`. Without it, `POST /chat/messages` and
  `POST /screener/run` return errors; nothing else in the backend is
  affected.

Every request to the watchlist and chat endpoints expects an
`X-Session-Id` header (see `app/session.py`) — the frontend sets this
automatically from a `localStorage` UUID. Tests use a fixed
`X-Session-Id: test-session` header (`backend/tests/conftest.py`).

## Run

```bash
uvicorn app.main:app --reload
```

## Test

```bash
pytest
```

`KAFKA_ENABLED=false` is set for the test environment, so tests don't
require a running Kafka broker.
