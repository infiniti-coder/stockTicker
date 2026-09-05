# stockTicker

A personal market dashboard: a live-updating watchlist backed by a mock
Kafka tick feed, a real-data market-overview treemap (yfinance), an
"Ask Claude" research chat, and a multi-step autonomous stock screener
agent — all in one React + FastAPI app.

> ⚠️ **Personal/portfolio project, not financial advice.** Live prices are
> synthetic (see §2). Market-overview, chat, and screener data comes from
> Yahoo Finance and the public web. Nothing in this app recommends buying
> or selling anything, and nothing here should be treated as investment
> advice.

---

## 1. What this is

- **Watchlist with live prices** — search instruments, add them to a
  per-browser watchlist, and see prices update in real time over
  WebSocket. Every browser tab is a fully independent subscriber (see §2)
  and its own watchlist (see §3) — nothing is shared across tabs/devices.
- **Market overview** — a treemap of real equities (India or worldwide),
  sized by market cap and colored by return over a selectable period,
  filterable by sector or by a few curated themes (AI, Green Energy,
  Oil). Click any tile to see that stock's full price history from
  inception as a line chart.
- **Ask Claude** — a chat panel, persistent per browser, for grounded
  questions about specific stocks or how they compare (price moves,
  fundamentals, sector context). Every answer cites up to 5 trusted
  sources and never gives buy/sell advice.
- **Screener agent** — a dedicated page where you describe open-ended
  criteria in plain English and an autonomous agent decides its own
  research depth: it screens the full universe, shortlists against your
  criteria, digs deeper into up to 6 candidates, and returns a ranked
  shortlist of up to 5 — see §5.

## 2. Live prices: mock feed over Kafka, one consumer per browser

There's no live broker connection. A backend-side `MockTickProducer`
generates synthetic ticks for a fixed instrument universe and publishes
them to a `market-ticks` topic on Kafka (Redpanda locally). From there:

- A **`backend-persistence`** consumer group persists every tick to
  SQLite (`last_snapshots`), so a price is always available even before
  any browser connects, or after a restart.
- **Each `/ws/prices` WebSocket connection creates its own Kafka consumer
  group** (`ws-<uuid>`), independently reading the entire tick stream and
  filtering client-side to whatever that browser has subscribed to. Two
  browser tabs on the same watchlist genuinely get two independent
  feeds — there's no shared in-process broadcaster fanning out to
  clients. This only works because there's no real upstream broker
  connection limit to conserve, unlike a real feed provider — see the
  detailed diagram in `docs/kafka-architecture.html`.

The app previously integrated with the real Upstox Market Data Feed
(protobuf WebSocket, OAuth login, real NSE entitlements). That
integration is retained in the codebase (`app/upstox_client/real_client.py`,
the `/auth/*` OAuth routes) but is currently unreferenced —
`get_upstox_client()` always returns the mock client. Swapping back is a
one-line change if real market data is wanted again.

## 3. Per-browser identity: session id, not login

There's no user database or real authentication. On first load, the
frontend generates a UUID (`crypto.randomUUID()`), stores it in
`localStorage`, and sends it as an `X-Session-Id` header on every
request. The backend uses that id to scope:

- the **watchlist** (`watchlist_items.session_id`) — each browser only
  ever sees rows it created;
- the **chat history** (`chat_messages.session_id`) — the Ask Claude
  panel picks up where you left off on the same browser, with no login.

Clearing `localStorage` (or opening a different browser) starts a fresh,
empty session.

## 4. Market overview: real data, real sectors

`app/market_overview/` pulls real quotes via `yfinance` for a curated
India/worldwide equity universe (`universe.py`): market cap, sector,
industry, and return over the selected period, batched with
`yf.download(..., group_by="ticker")` plus a threaded `.info` fetch per
ticker for fundamentals. The treemap sizes tiles by market cap and colors
them red/green by return; filters include every real sector present in
the fetched data plus three curated cross-sector themes
(`app/market_overview/themes.py`: AI, Green Energy, Oil — approximated
from sector/industry strings, not a real thematic classifier). Clicking a
tile fetches that symbol's full history via `yf.download(symbol,
period="max")` and renders it as a line chart.

<img width="1347" height="916" alt="image" src="https://github.com/user-attachments/assets/7e5a6a30-3854-47c5-b140-bec9e88c735c" />


## 5. Ask Claude & the screener agent

Both features call Claude (`claude-opus-5` via the Anthropic SDK's
`tool_runner`) with two tools: `get_stock_data` (reuses the same
yfinance-backed market-overview data, plus per-stock fundamentals like
margins/PE/ROE) and `web_search` (server-side web search, ranked and
capped to the 5 most trusted financial-publisher domains — see
`app/chat/sourcing.py`). Both share one `HARD_RULES` prompt constant:
never recommend buying or selling, never claim to predict or prove
future prices, ground every claim in a named tool result, and end with a
non-advice disclaimer. Answers stream to the frontend over SSE.

They differ in shape, not mechanism:

| | Ask Claude (`/chat`) | Screener (`/screener`) |
|---|---|---|
| Input | One question at a time | Open-ended free-text criteria + region |
| Process | Bounded: a couple of tool calls, then answer | Model-driven: screen the full universe → shortlist → deep-dive up to 6 candidates → rank up to 5, deciding its own step count |
| Output | 2 paragraphs by default (more on request) | A ranked shortlist with a rationale per stock |
| Persistence | Saved per session, chat history reloads | Stateless — one run, no history |
| Safety cap | — | `max_iterations=15` on the tool runner, hard stop against a runaway loop |

Both require `ANTHROPIC_API_KEY`; without it, those two features fail
gracefully (the rest of the app works fine either way).

---

## 6. Architecture

```
┌───────────────────┐   REST: search, watchlist, market-overview,   ┌───────────────────────────┐
│  React + TS SPA    │   chat, screener  (X-Session-Id header)      │      FastAPI backend       │
│  (frontend)        │──────────────────────────────────────────────▶                            │
│                     │                                              │  market_overview/ (yfinance)│
│                     │◀════ WebSocket /ws/prices (live ticks) ═════▶│  chat/, screener/ (Claude)  │
└───────────────────┘   one Kafka consumer group per connection      │  watchlist/, ws_gateway/    │
                                                                       └─────────────┬──────────────┘
                                                                                     │
                                                          ┌──────────────────────────┼───────────────────────┐
                                                          │                          │                       │
                                                ┌─────────▼─────────┐   ┌────────────▼───────────┐  ┌────────▼────────┐
                                                │ MockTickProducer   │   │ Kafka / Redpanda topic  │  │ SQLite           │
                                                │ (synthetic ticks)  │──▶│ "market-ticks"          │  │ watchlist_items  │
                                                └────────────────────┘   └────────────┬────────────┘  │ last_snapshots   │
                                                                                       │               │ chat_messages    │
                                                                          ┌────────────▼────────────┐  └──────────────────┘
                                                                          │ backend-persistence      │
                                                                          │ consumer → last_snapshots│
                                                                          └──────────────────────────┘
```

See `docs/kafka-architecture.html` for a more detailed view of the tick
pipeline and per-browser fan-out. (`docs/architecture.html` predates this
pivot and describes the old real-Upstox-only design — kept for history,
not current.)

## 7. Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Backend framework | **FastAPI** (Python, async) | native WebSocket support, auto OpenAPI docs |
| Live tick pipeline | **Kafka** (aiokafka) on **Redpanda** | one mock producer, one persistence consumer group, one consumer group per browser WebSocket |
| Market data | **yfinance** | market-overview treemap, per-stock fundamentals, full price history |
| AI | **Anthropic Claude API** (`claude-opus-5`), `tool_runner`, server-side web search | powers Ask Claude + the screener agent, streamed via SSE |
| Persistence | **SQLite** (SQLAlchemy) | watchlist, last-known price snapshots, chat history — all session-scoped |
| Frontend | **React + TypeScript**, Vite | |
| Frontend state | **React Query** (REST) + a WebSocket hook for live price state | |
| Identity | Client-generated `X-Session-Id` (localStorage UUID) | no real login; a legacy Upstox OAuth flow exists but runs against the mock client |
| Deployment | Docker Compose (Redpanda + backend + frontend) | |

## 8. Project structure

```
stockTicker/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, router + lifespan wiring
│   │   ├── auth/                   # legacy OAuth login/callback (runs against the mock client)
│   │   ├── upstox_client/          # mock client (active) + real client (retained, unreferenced)
│   │   ├── instruments/            # instrument search/cache
│   │   ├── watchlist/              # session-scoped watchlist CRUD
│   │   ├── market_status/          # trading-hours/holiday checks
│   │   ├── market_data/            # Kafka topic, producer, persistence consumer
│   │   ├── ws_gateway/             # /ws/prices — per-connection Kafka consumer group
│   │   ├── snapshots/              # last-known price persistence + REST backfill
│   │   ├── market_overview/        # yfinance-backed treemap + per-stock history
│   │   ├── chat/                   # "Ask Claude" — prompts, tools, sourcing, streaming service
│   │   ├── screener/               # multi-step screener agent
│   │   └── session.py              # X-Session-Id dependency
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/             # WatchlistTable, SymbolSearch, MarketOverviewTreemap,
│   │   │                           # StockHistoryChart, ChatPanel, StreamedAnswer, ...
│   │   ├── hooks/                  # useLivePrices, useWatchlist, useMarketOverview,
│   │   │                           # useStockHistory, useChatHistory
│   │   ├── api/                    # REST/SSE client, session id
│   │   └── pages/                  # Dashboard, MarketStockDetailPage, ScreenerPage, ...
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml               # Redpanda + backend + frontend
├── docs/                            # archify-generated architecture diagrams
├── CLAUDE.md
└── README.md
```

## 9. Environment variables

Backend (`backend/.env`, see `backend/.env.example`):

```
KAFKA_BOOTSTRAP_SERVERS=localhost:19092   # Redpanda's host-exposed listener
KAFKA_ENABLED=true                        # false skips the tick producer/consumers (used by tests)
ANTHROPIC_API_KEY=                        # required for Ask Claude + the screener; rest of app works without it
DATABASE_URL=sqlite:///./data/app.db
SESSION_SECRET=change-me-to-a-random-string

# Unused (real Upstox integration retained but not wired up):
UPSTOX_API_KEY=
UPSTOX_API_SECRET=
UPSTOX_REDIRECT_URI=http://localhost:8000/auth/callback
```

Frontend (`frontend/.env`, see `frontend/.env.example`):

```
VITE_API_BASE=http://localhost:8000
```

## 10. Local development

```bash
# 1. start Redpanda (needed for live prices; skip if you set KAFKA_ENABLED=false)
docker compose up redpanda

# 2. backend
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # add ANTHROPIC_API_KEY if you want Ask Claude / the screener
uvicorn app.main:app --reload

# 3. frontend
cd frontend
npm install
npm run dev
```

Then open the frontend — the watchlist, market overview, chat, and
screener all work immediately with no login required.

Or run everything via Docker Compose:

```bash
docker compose up
```

## 11. Known limitations

- **Prices are synthetic** — `/ws/prices` streams a mock feed, not a real
  exchange feed. The real Upstox integration is retained in the codebase
  but currently unreferenced (see §2).
- **`yfinance` data drift** — a hand-maintained equity universe
  (`app/market_overview/universe.py`) occasionally includes a delisted or
  renamed symbol; it's silently skipped rather than erroring.
- **Ask Claude / screener require `ANTHROPIC_API_KEY`** — without it,
  those two endpoints return an error; the rest of the app is unaffected.
- **No real authentication** — per-browser identity is a `localStorage`
  UUID, not a login. Clearing site data or switching browsers starts a
  fresh, empty watchlist and chat history.
- **Theme tagging is approximate** — AI/Green Energy/Oil filters are
  derived from Yahoo's sector/industry strings, not a real thematic
  classification (see §4).

## 12. Roadmap ideas (not committed yet)

- Wire the real Upstox client back in as an opt-in live-data mode.
- Persist screener runs so past shortlists can be revisited.
- Alerting (price crosses threshold) via the existing Kafka pipeline.

---

## 13. Status

Fully running end-to-end: mock live prices over Kafka/Redpanda with
per-browser consumer groups, a session-scoped watchlist, a real-data
market-overview treemap, per-stock history charts, an "Ask Claude" chat
panel, and a multi-step screener agent — all covered by a passing test
suite (`cd backend && pytest`). See `backend/README.md` for backend-only
setup notes.
