"""Web-search source collection, shared by app/chat/service.py and
app/screener/service.py — both run a tool_runner loop with the same
web_search tool and need the same "which sources do we show" policy."""

from urllib.parse import urlparse

WEB_SEARCH_TOOL = {"type": "web_search_20260318", "name": "web_search"}

MAX_SOURCES = 5  # shown under a reply, most-trusted first
SOURCE_POOL_LIMIT = 25  # collect up to this many candidates before ranking, so trust-ranking has real choices

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


def is_trusted_domain(url: str) -> bool:
    host = urlparse(url).netloc.removeprefix("www.")
    return any(host == d or host.endswith(f".{d}") for d in TRUSTED_SOURCE_DOMAINS)


def rank_sources(sources: list[dict]) -> list[dict]:
    """Most-trusted first (see TRUSTED_SOURCE_DOMAINS), preserving each
    tier's original search-result order, then take the top MAX_SOURCES."""
    trusted = [s for s in sources if is_trusted_domain(s["url"])]
    other = [s for s in sources if not is_trusted_domain(s["url"])]
    return (trusted + other)[:MAX_SOURCES]


def collect_sources(final_message, sources: list[dict], seen_urls: set[str]) -> None:
    """Mutates sources/seen_urls in place with any new web_search_result
    entries found in one tool_runner turn's final message, up to
    SOURCE_POOL_LIMIT total. Call once per turn while iterating a runner."""
    for block in final_message.content:
        if len(sources) >= SOURCE_POOL_LIMIT:
            break
        if block.type == "web_search_tool_result" and isinstance(block.content, list):
            for result in block.content:
                if len(sources) >= SOURCE_POOL_LIMIT:
                    break
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    sources.append({"title": result.title, "url": result.url})
