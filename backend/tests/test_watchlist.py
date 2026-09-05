from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app.main import app


def _mock_login(client):
    """Drive the mock OAuth flow to completion, without following redirects
    to hosts httpx can't reach in-process."""
    login_resp = client.get("/auth/login", follow_redirects=False)
    assert login_resp.status_code in (302, 307)
    location = login_resp.headers["location"]
    parsed = urlparse(location)
    qs = parse_qs(parsed.query)

    callback_resp = client.get(
        "/auth/callback",
        params={"code": qs["code"][0], "state": qs["state"][0]},
        follow_redirects=False,
    )
    assert callback_resp.status_code in (302, 307)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["mock"] is True


def test_instrument_search_finds_mock_fixture(client):
    resp = client.get("/instruments/search", params={"q": "TCS"})
    assert resp.status_code == 200
    symbols = [row["trading_symbol"] for row in resp.json()]
    assert "TCS" in symbols


def test_add_list_remove_watchlist(client):
    _mock_login(client)

    search_resp = client.get("/instruments/search", params={"q": "INFY"})
    instrument_key = search_resp.json()[0]["instrument_key"]

    add_resp = client.post("/watchlist", json={"instrument_key": instrument_key})
    assert add_resp.status_code == 200
    added = add_resp.json()
    assert added["instrument_key"] == instrument_key
    assert added["snapshot"] is not None  # backfilled via mock LTP quote

    list_resp = client.get("/watchlist")
    assert any(row["instrument_key"] == instrument_key for row in list_resp.json())

    delete_resp = client.delete(f"/watchlist/{instrument_key}")
    assert delete_resp.status_code == 200

    list_resp_after = client.get("/watchlist")
    assert not any(row["instrument_key"] == instrument_key for row in list_resp_after.json())


def test_add_unknown_instrument_404s(client):
    resp = client.post("/watchlist", json={"instrument_key": "NSE_EQ|DOES-NOT-EXIST"})
    assert resp.status_code == 404


def test_remove_missing_item_404s(client):
    resp = client.delete("/watchlist/NSE_EQ|NEVER-ADDED")
    assert resp.status_code == 404


def test_missing_session_header_400s(client):
    resp = client.get("/watchlist", headers={"X-Session-Id": ""})
    assert resp.status_code == 400


def test_watchlist_is_scoped_per_session(client):
    """Two browsers (two X-Session-Id values) must not see each other's
    watchlist — this is the whole point of session scoping (app/session.py)."""
    _mock_login(client)

    search_resp = client.get("/instruments/search", params={"q": "TCS"})
    instrument_key = search_resp.json()[0]["instrument_key"]

    client.post("/watchlist", json={"instrument_key": instrument_key})
    assert any(row["instrument_key"] == instrument_key for row in client.get("/watchlist").json())

    with TestClient(app, headers={"X-Session-Id": "a-different-browser"}) as other_client:
        other_list = other_client.get("/watchlist").json()
        assert not any(row["instrument_key"] == instrument_key for row in other_list)
