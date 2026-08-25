# stockTicker

A personal, production-grade dashboard that shows **live bid/ask prices** for a
watchlist of NSE equities, backed by your own Upstox demat account — and
still shows meaningful (last-known) prices when the market is closed instead
of going blank.

> ⚠️ **Personal-use tool, not financial advice.** This app displays market
> data from your authenticated Upstox account for informational purposes. It
> does not place orders. Market data is subject to Upstox's terms of use and
> exchange data policies.

---

## 1. What this is

- Search NSE equities and build a **watchlist**.
- See **live LTP, bid, ask, bid/ask quantity** (market depth) for every symbol
  in the watchlist, streamed over WebSocket during market hours.
- **Always shows a price** — pre-market, after-hours, weekends, and
  exchange holidays all fall back to the last known traded price instead of
  an empty/blank row (clearly labeled as "closed" data, never silently
  passed off as live).
- Auth against **your own Upstox account** via OAuth2 — you click "Login with
  Upstox" once a day (Upstox access tokens are valid for a single trading day
  and don't support silent refresh).

## 2. Why Upstox instead of yfinance

`yfinance` scrapes an unofficial Yahoo endpoint: no streaming, delayed data
on many symbols, and bid/ask fields are frequently stale or empty. Upstox, by
contrast, gives an **authenticated, real-time Market Data Feed** (WebSocket,
protobuf-encoded) with genuine top-of-book bid/ask, because you're pulling
data through your own broker account with actual exchange entitlements.

Trade-off: this ties the app to one broker and one user (you), and requires
a daily login instead of a "just works, no account" setup.

---

## 3. Architecture

```
┌──────────────────┐        OAuth2 login/callback        ┌──────────────────────┐
│                   │ ───────────────────────────────────▶│                      │
│  React + TS SPA   │                                      │   FastAPI backend    │
│  (frontend)       │◀──────────── REST (search, ─────────│   (single process)   │
│                   │              watchlist CRUD)         │                      │
│                   │                                      │  ┌────────────────┐  │
│                   │◀════ WebSocket (live prices) ═══════▶│  │ Upstox WS client│──┼──▶ Upstox Market
└──────────────────┘        /ws/prices                     │  │ (one connection)│  │    Data Feed (wss)
                                                              │  └────────────────┘  │
                                                              │  SQLite (watchlist,  │
                                                              │  cached instrument   │
                                                              │  master, last-known  │
                                                              │  price snapshots)    │
                                                              └──────────────────────┘
```

Key design point: the backend holds **one** authenticated WebSocket
connection to Upstox and **fans out** updates to however many browser tabs/
clients are connected, filtered to what each client has subscribed to. This
respects Upstox's connection limits and keeps the frontend simple (plain JSON
over WebSocket, no protobuf in the browser).

### Data flow

1. User clicks **Login with Upstox** → backend redirects to Upstox's OAuth
   authorization dialog.
2. User authenticates with Upstox (credentials + TOTP) and grants consent.
3. Upstox redirects back to the backend's callback URL with an auth `code`.
4. Backend exchanges the `code` for an **access token** (valid until ~3:30am
   IST the next day) and holds it server-side for the session.
5. Backend calls Upstox's feed-authorize endpoint to get a signed WebSocket
   URL, connects, and subscribes in **`full`** mode (LTP + market depth) for
   every instrument currently on the watchlist.
6. Upstox pushes protobuf-encoded ticks; backend decodes them and re-emits a
   small JSON payload (`{instrument_key, ltp, bid, ask, bid_qty, ask_qty, ts}`)
   to every connected frontend client subscribed to that instrument.
7. Frontend updates the relevant watchlist row in place — no full reload.

### Data availability: live vs last-known

Upstox's feed only ticks during NSE trading hours (09:15–15:30 IST,
weekdays, excluding exchange holidays). Outside that window there is
nothing to stream — but the UI should never just go blank. Design:

- **Persist every tick.** Every price update the backend receives is
  upserted into a `last_snapshot` table in SQLite (`instrument_key`, `ltp`,
  `bid`, `ask`, `bid_qty`, `ask_qty`, `close`, `ts`, `is_live`). This
  survives backend restarts, not just in-memory state.
- **Snapshot-first API.** Adding a symbol to the watchlist, or opening the
  app, immediately returns whatever is in `last_snapshot` (via REST and as
  the first WebSocket message) — even before/without a live feed connection.
  No row is ever empty once a symbol has been quoted at least once.
- **Backfill on cold start / new symbol.** If a symbol has no snapshot yet
  (freshly added, backend never fetched it), the backend calls Upstox's
  REST **Quote/LTP API** once — this endpoint returns the previous close and
  last traded price even when the market is closed, unlike the WS feed.
- **Market-hours awareness.** A small `market_status` util (weekday +
  NSE holiday calendar, refreshed periodically from Upstox's holiday
  endpoint) determines whether the WS feed *should* be ticking right now.
  The backend only opens the Upstox WS connection during trading hours (no
  point holding an idle connection all night) and reconnects automatically
  at the next session open.
- **Explicit staleness in the UI.** Every price row carries `is_live` and
  `ts`. The frontend shows a small badge — "Live" (green, updating) vs
  "Market closed · as of last close / HH:MM" (grey) — so last-known data is
  never mistaken for a live quote.

---

## 4. Tech stack

| Layer            | Choice                          | Notes |
|-------------------|----------------------------------|-------|
| Backend framework | **FastAPI** (Python, async)     | native WebSocket support, auto OpenAPI docs |
| Upstream feed     | **Upstox Market Data Feed v3**  | protobuf over WebSocket, requires compiled `.proto` stubs |
| Realtime transport (backend ⇄ browser) | **WebSocket** | one connection per client, JSON messages |
| Persistence       | **SQLite** (via SQLAlchemy)     | watchlist + cached instrument master; upgrade path to Postgres if ever multi-user |
| Frontend          | **React + TypeScript**          | Vite for dev/build |
| Frontend state    | React Query (REST) + a small store (Zustand/Context) for live price state | |
| Auth              | **Upstox OAuth2**, server-held access token | no user database — single-user tool |
| Deployment        | Docker Compose (backend + frontend, or backend serving built frontend) | see §8 |

---

## 5. Upstox app setup (one-time, manual)

Since you don't yet have API credentials, do this before writing code:

1. Go to <https://developer.upstox.com> and log in with your Upstox account.
2. Create a new app:
   - **App name**: anything, e.g. `trading-engine-dev`
   - **Redirect URI**: `http://localhost:8000/auth/callback` (must match
     exactly what the backend uses — add a second one for production later)
3. Note the **API Key (Client ID)** and **API Secret** issued.
4. Read the current rate limits and WebSocket connection limits in the
   [Upstox API docs](https://upstox.com/developer/api-documentation) — these
   change occasionally and affect how aggressively we can subscribe/poll.
5. Download the Market Data Feed `.proto` definition from Upstox's docs and
   compile it with `protoc` into Python stubs (checked into
   `backend/app/upstox_client/proto/` as a build step, not committed as
   generated code).

## 6. Environment variables

```
UPSTOX_API_KEY=...
UPSTOX_API_SECRET=...
UPSTOX_REDIRECT_URI=http://localhost:8000/auth/callback
SESSION_SECRET=...          # for signing the backend session cookie
DATABASE_URL=sqlite:///./data/app.db
```

---

## 7. Project structure (planned)

```
stockTicker/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, router wiring
│   │   ├── auth/                   # OAuth login/callback, token storage
│   │   ├── upstox_client/          # REST client + WS market feed client, proto stubs
│   │   ├── instruments/            # instrument master download/cache/search
│   │   ├── watchlist/              # CRUD for watchlist symbols (SQLite)
│   │   ├── market_status/          # trading-hours + holiday-calendar checks
│   │   ├── snapshots/              # last-known price persistence + REST backfill
│   │   └── ws_gateway/             # browser-facing /ws/prices, fan-out logic
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/             # WatchlistTable, SymbolSearch, PriceCell, LoginButton
│   │   ├── hooks/                  # useLivePrices (WebSocket), useWatchlist (REST)
│   │   └── pages/
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── CLAUDE.md
└── README.md
```

---

## 8. Local development (once scaffolded)

```bash
# backend
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

Then open the frontend, click **Login with Upstox**, complete the OAuth
consent, and add symbols to your watchlist.

---

## 9. Known limitations

- **Daily re-login required** — Upstox access tokens expire once a day; no
  silent refresh, so the app will prompt you to log in again each trading
  day (or when a token-expired error is detected).
- **Single user** — this is built around one Upstox account. Multi-user
  support would require per-user token storage and a real auth layer.
- **NSE equity only** for the MVP — F&O/BSE support is a possible future
  extension, not in scope initially.
- **Market hours** — live depth only updates during NSE trading hours; outside
  that window the app intentionally falls back to last-known data (see
  §3, "Data availability: live vs last-known") rather than a live feed.
- **Holiday calendar freshness** — the exchange holiday list is fetched
  periodically, not hardcoded forever; if it goes stale, the app may briefly
  attempt to open a WS connection on a holiday and simply get no ticks (falls
  back to last-known automatically, no user-facing error).

## 10. Roadmap ideas (not committed yet)

- Persist historical ticks for simple intraday charting.
- Alerting (price crosses threshold) via the existing WS pipeline.
- Multi-account support if this ever needs to serve more than one user.

---

## 11. Status

Planning stage — no code yet. This README reflects the architecture agreed
on so far. Next step: scaffold `backend/` and `frontend/` per §7.
