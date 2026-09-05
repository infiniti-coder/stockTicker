import json
import logging
from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic

from app.chat.sourcing import WEB_SEARCH_TOOL, collect_sources, rank_sources
from app.chat.tools import get_stock_data
from app.config import get_settings

from .prompts import SCREENER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

MODEL = "claude-opus-5"
MAX_TOKENS = 8000  # more room than chat: multi-step reasoning + a longer final list
MAX_ITERATIONS = 15  # hard stop against a runaway tool loop


async def stream_screener_run(region: str, criteria: str) -> AsyncIterator[tuple[str, str]]:
    """Same SSE-shaped ("delta", text) / ("sources", json) yields as
    chat.service.stream_chat_reply, but stateless — one-shot, not tied to
    a session's history or persisted anywhere."""
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    runner = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        max_iterations=MAX_ITERATIONS,
        system=SCREENER_SYSTEM_PROMPT,
        tools=[get_stock_data, WEB_SEARCH_TOOL],
        messages=[{"role": "user", "content": f"Region: {region}\nCriteria: {criteria}"}],
        stream=True,
    )

    sources: list[dict] = []
    seen_urls: set[str] = set()

    try:
        async for message_stream in runner:
            async for text in message_stream.text_stream:
                yield "delta", text
            final = await message_stream.get_final_message()
            collect_sources(final, sources, seen_urls)
    except Exception:
        logger.exception("Screener run failed")
        yield "delta", "\n\n(Something went wrong running this screen.)"

    yield "sources", json.dumps(rank_sources(sources))
