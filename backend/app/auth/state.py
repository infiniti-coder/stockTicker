from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class AuthState:
    """Server-held Upstox session for this single-user app (README §4: 'no
    user database'). The access token never goes to the browser; the
    frontend only ever sees `logged_in`/`is_mock` via /auth/status.
    """

    access_token: str | None = None
    logged_in_at: datetime | None = None
    is_mock: bool = False

    @property
    def is_logged_in(self) -> bool:
        return self.access_token is not None

    def set_token(self, token: str, *, is_mock: bool) -> None:
        self.access_token = token
        self.logged_in_at = datetime.now(timezone.utc)
        self.is_mock = is_mock

    def clear(self) -> None:
        self.access_token = None
        self.logged_in_at = None


# Single-process, single-user: one global auth state is intentional here,
# not a workaround. See README §9, "Single user".
auth_state = AuthState()
