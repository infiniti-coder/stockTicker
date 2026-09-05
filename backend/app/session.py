from fastapi import Header, HTTPException


def get_session_id(x_session_id: str = Header(..., alias="X-Session-Id")) -> str:
    """Identifies which browser is calling, so per-browser data (currently
    just the watchlist) can be scoped instead of shared globally. The
    frontend generates one UUID per browser profile and stores it in
    localStorage (see frontend/src/api/session.ts) — this app has no real
    user accounts (README §9, "Single user"), so this is a scoping key,
    not an auth credential."""
    session_id = x_session_id.strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="X-Session-Id header is required")
    return session_id
