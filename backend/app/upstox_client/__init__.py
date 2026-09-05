from app.config import get_settings

from .base import Instrument, Quote, UpstoxClient
from .mock_client import MockUpstoxClient

__all__ = ["Instrument", "Quote", "UpstoxClient", "get_upstox_client"]


def get_upstox_client() -> UpstoxClient:
    # Always mock: the app has pivoted off the real Upstox integration (no
    # more external connection limits — see app/market_data/producer.py).
    # RealUpstoxClient stays in the repo, fully working, just unreferenced;
    # swap this back to the credential-gated branch to reconnect it.
    settings = get_settings()
    return MockUpstoxClient(redirect_uri=settings.upstox_redirect_uri)
