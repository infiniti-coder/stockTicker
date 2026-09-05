from app.snapshots.service import get_snapshot, snapshot_to_dict, upsert_snapshot
from app.upstox_client.base import Quote


def test_upsert_then_get(db_session):
    quote = Quote(
        instrument_key="NSE_EQ|TEST",
        ltp=100.5,
        bid=100.4,
        ask=100.6,
        bid_qty=10,
        ask_qty=12,
        close=99.0,
        is_live=True,
    )
    upsert_snapshot(db_session, quote)

    row = get_snapshot(db_session, "NSE_EQ|TEST")
    assert row is not None
    assert row.ltp == 100.5
    assert row.is_live is True

    as_dict = snapshot_to_dict(row)
    assert as_dict["instrument_key"] == "NSE_EQ|TEST"
    assert "ts" in as_dict


def test_upsert_overwrites_existing_row(db_session):
    key = "NSE_EQ|TEST2"
    upsert_snapshot(db_session, Quote(key, 10, 9.9, 10.1, 1, 1, 10, is_live=False))
    upsert_snapshot(db_session, Quote(key, 20, 19.9, 20.1, 2, 2, 10, is_live=True))

    row = get_snapshot(db_session, key)
    assert row.ltp == 20
    assert row.is_live is True
