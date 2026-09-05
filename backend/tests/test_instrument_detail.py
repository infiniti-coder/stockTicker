from urllib.parse import parse_qs, urlparse

from app.snapshots.depth_store import depth_store
from app.upstox_client.base import DepthLevel


def test_get_instrument_returns_info_and_snapshot(client):
    search_resp = client.get("/instruments/search", params={"q": "RELIANCE"})
    instrument_key = search_resp.json()[0]["instrument_key"]

    resp = client.get(f"/instruments/{instrument_key}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["trading_symbol"] == "RELIANCE"
    assert "name" in body and "exchange" in body


def test_get_instrument_unknown_404s(client):
    resp = client.get("/instruments/NSE_EQ|DOES-NOT-EXIST")
    assert resp.status_code == 404


def test_depth_empty_until_a_live_tick_arrives(client):
    """REST backfill (what adding to the watchlist triggers) has no depth
    data — only live WS ticks do (see base.Quote) — so depth should stay
    empty even after the symbol is added and backfilled."""
    search_resp = client.get("/instruments/search", params={"q": "WIPRO"})
    instrument_key = search_resp.json()[0]["instrument_key"]

    depth_before = client.get(f"/instruments/{instrument_key}/depth")
    assert depth_before.status_code == 200
    assert depth_before.json() == {"instrument_key": instrument_key, "updated_at": None, "levels": []}

    login_resp = client.get("/auth/login", follow_redirects=False)
    qs = parse_qs(urlparse(login_resp.headers["location"]).query)
    client.get(
        "/auth/callback",
        params={"code": qs["code"][0], "state": qs["state"][0]},
        follow_redirects=False,
    )
    client.post("/watchlist", json={"instrument_key": instrument_key})

    depth_after = client.get(f"/instruments/{instrument_key}/depth")
    assert depth_after.json()["levels"] == []


def test_depth_reflects_latest_order_book(client):
    """Simulates what a live tick does: depth_store.set() is what
    upsert_snapshot calls under the hood when a Quote carries depth."""
    instrument_key = "NSE_EQ|MOCK-TEST-DEPTH"
    levels = [DepthLevel(bid_price=99.5, bid_qty=10, ask_price=100.5, ask_qty=12)]
    depth_store.set(instrument_key, levels)

    resp = client.get(f"/instruments/{instrument_key}/depth")
    assert resp.status_code == 200
    body = resp.json()
    assert body["updated_at"] is not None
    assert body["levels"] == [{"bid_price": 99.5, "bid_qty": 10, "ask_price": 100.5, "ask_qty": 12}]


def test_depth_route_not_swallowed_by_plain_instrument_route(client):
    search_resp = client.get("/instruments/search", params={"q": "ITC"})
    instrument_key = search_resp.json()[0]["instrument_key"]

    resp = client.get(f"/instruments/{instrument_key}/depth")
    assert resp.status_code == 200
    assert "levels" in resp.json()
