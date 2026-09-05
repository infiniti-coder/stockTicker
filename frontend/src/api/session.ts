const STORAGE_KEY = "stockticker_session_id";

/**
 * One id per browser profile (localStorage), sent as X-Session-Id on every
 * API call so the backend can scope the watchlist per browser instead of
 * sharing one global list (app/session.py). Two windows of the *same*
 * browser profile share localStorage and so share a watchlist — open an
 * incognito window, or a different browser, to see an independent one.
 */
export function getSessionId(): string {
  let id = localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}
