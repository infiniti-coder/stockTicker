import json
import logging
from collections.abc import AsyncIterator
from urllib.parse import urlparse

from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.models import ChatMessage

from .prompts import SYSTEM_PROMPT
from .tools import get_stock_data

logger = logging.getLogger(__name__)

MODEL = "claude-opus-5"
MAX_HISTORY_MESSAGES = 40  # cap how much prior conversation gets resent each turn
MAX_SOURCES = 5  # shown under a reply, most-trusted first
SOURCE_POOL_LIMIT = 25  # collect up to this many candidates before ranking, so trust-ranking has real choices
WEB_SEARCH_TOOL = {"type": "web_search_20260318", "name": "web_search"}

# Established financial publishers, exchanges, and data providers — preferred
# over forums/blogs/community chart posts when picking which sources to show.
# Not exhaustive; anything not on this list is still shown, just after these.
TRUSTED_SOURCE_DOMAINS = (
    "reuters.com",
    "bloomberg.com",
    "wsj.com",
    "ft.com",
    "cnbc.com",
    "business-standard.com",
    "economictimes.indiatimes.com",
    "livemint.com",
    "moneycontrol.com",
    "nseindia.com",
    "bseindia.com",
    "finance.yahoo.com",
    "marketwatch.com",
    "forbes.com",
    "ndtv.com",
    "thehindu.com",
    "financialexpress.com",
    "hindustantimes.com",
    "theweek.in",
    "businesstoday.in",
)


def _is_trusted_domain(url: str) -> bool:
    host = urlparse(url).netloc.removeprefix("www.")
    return any(host == d or host.endswith(f".{d}") for d in TRUSTED_SOURCE_DOMAINS)


def _rank_sources(sources: list[dict]) -> list[dict]:
    """Most-trusted first (see TRUSTED_SOURCE_DOMAINS), preserving each
    tier's original search-result order, then take the top MAX_SOURCES."""
    trusted = [s for s in sources if _is_trusted_domain(s["url"])]
    other = [s for s in sources if not _is_trusted_domain(s["url"])]
    return (trusted + other)[:MAX_SOURCES]


def list_messages(db: Session, session_id: str) -> list[ChatMessage]:
    return list(
        db.scalars(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at))
    )


def _persist(db: Session, session_id: str, role: str, content: str, sources: list[dict] | None = None) -> ChatMessage:
    row = ChatMessage(session_id=session_id, role=role, content=content, sources=sources or [])
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


async def stream_chat_reply(session_id: str, user_text: str) -> AsyncIterator[tuple[str, str]]:
    """Yields ("delta", text) chunks as the reply streams in, then exactly
    one final ("sources", json_array) event. Persists the user message
    immediately and the finished assistant reply (with sources) at the end,
    scoped by session_id like every other per-browser table in this app.

    Opens its own DB session rather than taking one via FastAPI's
    Depends(get_db): that dependency is torn down as soon as the endpoint
    function returns the StreamingResponse object, which happens before
    this generator actually runs — a session handed in from there would
    already be closed by the time we tried to use it."""
    db = SessionLocal()
    try:
        _persist(db, session_id, "user", user_text)

        history = list_messages(db, session_id)[-MAX_HISTORY_MESSAGES:]
        messages = [{"role": m.role, "content": m.content} for m in history]

        settings = get_settings()
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)

        runner = client.beta.messages.tool_runner(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[get_stock_data, WEB_SEARCH_TOOL],
            messages=messages,
            stream=True,
        )

        text_parts: list[str] = []
        sources: list[dict] = []
        seen_urls: set[str] = set()

        try:
            async for message_stream in runner:
                async for text in message_stream.text_stream:
                    text_parts.append(text)
                    yield "delta", text
                final = await message_stream.get_final_message()
                for block in final.content:
                    if len(sources) >= SOURCE_POOL_LIMIT:
                        break
                    if block.type == "web_search_tool_result" and isinstance(block.content, list):
                        for result in block.content:
                            if len(sources) >= SOURCE_POOL_LIMIT:
                                break
                            if result.url not in seen_urls:
                                seen_urls.add(result.url)
                                sources.append({"title": result.title, "url": result.url})
        except Exception:
            logger.exception("Chat reply generation failed")
            error_text = "\n\n(Something went wrong generating the rest of this reply.)"
            text_parts.append(error_text)
            yield "delta", error_text

        full_text = "".join(text_parts)
        top_sources = _rank_sources(sources)
        _persist(db, session_id, "assistant", full_text, top_sources)
        yield "sources", json.dumps(top_sources)
    finally:
        db.close()
