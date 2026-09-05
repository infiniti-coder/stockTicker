"""Approximate AI / Green Energy / Oil tagging from Yahoo's sector+industry
strings (e.g. "Technology" / "Semiconductors", "Energy" / "Oil & Gas E&P").

This is a coarse sector-based approximation, not a real thematic
classifier — no free data source screens by theme reliably. "AI" in
particular ends up meaning "large tech/semiconductor company"; that
imprecision is an accepted trade-off, not a bug.

Matching is case-insensitive substring matching on the industry string
(falling back to sector) since Yahoo's punctuation (em-dash vs hyphen)
isn't consistent across listings.
"""

OIL_INDUSTRY_HINTS = ("oil & gas", "oil and gas", "petroleum")
GREEN_ENERGY_INDUSTRY_HINTS = ("solar", "renewable", "wind power", "clean energy")
AI_INDUSTRY_HINTS = (
    "semiconductor",
    "software",
    "information technology services",
    "computer hardware",
    "consumer electronics",
    "internet content",
)

THEMES = ("AI", "Green Energy", "Oil")


def classify(sector: str | None, industry: str | None) -> str | None:
    text = f"{industry or ''} {sector or ''}".lower()
    if any(hint in text for hint in OIL_INDUSTRY_HINTS):
        return "Oil"
    if any(hint in text for hint in GREEN_ENERGY_INDUSTRY_HINTS):
        return "Green Energy"
    if (sector or "").lower() == "technology" and any(hint in text for hint in AI_INDUSTRY_HINTS):
        return "AI"
    return None
