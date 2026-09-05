import secrets
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.config import Settings, get_settings
from app.upstox_client import UpstoxClient, get_upstox_client

from .state import auth_state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login(
    client: UpstoxClient = Depends(get_upstox_client),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    state = secrets.token_urlsafe(16)
    return RedirectResponse(client.get_login_url(state))


@router.get("/callback")
async def callback(
    code: str,
    state: str | None = None,
    client: UpstoxClient = Depends(get_upstox_client),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    try:
        token = await client.exchange_code(code)
        auth_state.set_token(token, is_mock=settings.use_mock_upstox)
    except Exception:
        logger.exception("Upstox token exchange failed")
        return RedirectResponse(f"{settings.frontend_url}/?auth_error=1")
    return RedirectResponse(f"{settings.frontend_url}/?logged_in=1")


@router.get("/status")
def status(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "logged_in": auth_state.is_logged_in,
        "is_mock": settings.use_mock_upstox,
        "logged_in_at": auth_state.logged_in_at.isoformat() if auth_state.logged_in_at else None,
    }


@router.post("/logout")
def logout() -> dict:
    auth_state.clear()
    return {"logged_in": False}
