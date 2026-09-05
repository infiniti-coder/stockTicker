# backend

FastAPI backend for stockTicker. See the root `README.md` for the full
architecture; this file is just local setup notes.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # leave UPSTOX_API_KEY/SECRET blank for mock mode
```

## Mock mode vs. live mode

If `UPSTOX_API_KEY` / `UPSTOX_API_SECRET` are unset, the app runs entirely
against `app/upstox_client/mock_client.py`: 20 fixture NSE symbols, a fake
instant "login", and a synthetic feed that ticks continuously (it ignores
real market hours, so it's testable at any time of day). No Upstox account
needed. This is the default until you complete README.md §5.

Once you have real credentials, set them in `.env` and the app switches to
`real_client.py` automatically (`get_upstox_client()` in
`app/upstox_client/__init__.py` picks based on whether credentials are
present) — real OAuth, real REST quotes, real protobuf WS feed, gated on
actual NSE trading hours.

## Regenerating the protobuf stubs

`app/upstox_client/proto/MarketDataFeed_pb2.py` is a build artifact (not
committed — see `.gitignore`), generated from the checked-in
`MarketDataFeed.proto`:

```bash
python -m app.upstox_client.proto.generate
```

Re-download `MarketDataFeed.proto` from
https://assets.upstox.com/feed/market-data-feed/v3/MarketDataFeed.proto and
re-run this if Upstox revs the feed schema (watch for a `RequestMode` /
message shape mismatch as the symptom).

## Run

```bash
uvicorn app.main:app --reload
```

## Test

```bash
pytest
```
