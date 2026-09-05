import os
import tempfile

_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"
os.environ["UPSTOX_API_KEY"] = ""
os.environ["UPSTOX_API_SECRET"] = ""
os.environ["SESSION_SECRET"] = "test-secret"
os.environ["KAFKA_ENABLED"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import SessionLocal, init_db  # noqa: E402
from app.main import app  # noqa: E402

init_db()


@pytest.fixture
def client():
    with TestClient(app, headers={"X-Session-Id": "test-session"}) as c:
        yield c


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
