"""Deterministic page structuring — offerings AI fallback is triggered in brochure_builder."""

import re

OFFERING_KEYWORDS = (
    "product", "service", "solution", "platform", "software", "hardware",
    "feature", "cloud", "enterprise", "consulting", "licensing", "api",
    "module", "tool", "suite", "application", "app",
)

INDUSTRY_KEYWORDS = (
    "industry", "sector", "banking", "insurance", "healthcare",
    "manufacturing", "retail", "telecom", "energy", "government",
    "education", "finance", "logistics", "automotive", "pharma",
)


def structure_page(page: dict) -> str:
    """Format extracted page fields into a facts block for the overview LLM."""
    lines = []
    if page.get("title"):
        lines.append(f"Title: {page['title']}")
    if page.get("meta_description"):
        lines.append(f"Description: {page['meta_description']}")
    for h in page.get("headings", [])[:6]:
        lines.append(f"Heading: {h}")
    if page.get("lead_paragraph"):
        lines.append(f"Lead: {page['lead_paragraph']}")
    return "\n".join(lines)


def _normalize_item(text: str) -> str:
    return " ".join(text.split()).strip()


def _is_valid_item(text: str, min_len: int = 4, max_len: int = 120) -> bool:
    if not text or len(text) < min_len or len(text) > max_len:
        return False
    words = text.split()
    if len(words) == 1 and len(words[0]) < 8:
        return False
    if len(words) > 18:
        return False
    lower = text.lower()
    skip = (
        "click here", "read more", "learn more", "sign up", "log in",
        "cookie", "privacy policy", "terms of", "all rights",
        "follow ", "join the", "where can i", "how do i", "how to ",
        "designed for", "experience the", "start using", "meet surface",
        "less plastic", "for business", "support center", "free office",
    )
    if any(s in lower for s in skip):
        return False
    if text.endswith("?") or lower.startswith(("how ", "what ", "where ", "when ", "why ")):
        return False
    if re.match(r"^\d+\.\s", text):
        return False
    return True


def _matches_keywords(text: str, keywords: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def _sentences_from_content(text: str, keywords: tuple[str, ...]) -> list[str]:
    items: list[str] = []
    for raw in re.split(r"[.!?]+", text):
        sentence = _normalize_item(raw)
        if len(sentence) < 20 or len(sentence) > 200:
            continue
        if not _matches_keywords(sentence, keywords):
            continue
        if not _is_valid_item(sentence, min_len=20, max_len=200):
            continue
        items.append(sentence)
    return items


def _collect_items(pages: list, keywords: tuple[str, ...], *, strict: bool) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []

    for page in pages:
        candidates = (
            [page.get("title", ""), page.get("meta_description", "")]
            + list(page.get("headings", []))
            + list(page.get("list_items", []))
        )
        if not strict:
            candidates.extend(_sentences_from_content(page.get("content", ""), keywords))
        for raw in candidates:
            text = _normalize_item(raw)
            if not _is_valid_item(text):
                continue
            if strict and not _matches_keywords(text, keywords):
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            items.append(text)

    return items


def extract_bullets(pages: list, section: str) -> str:
    """Build a deduplicated bullet list from page headings and list items."""
    if not pages:
        return ""

    if section == "offerings":
        keywords = OFFERING_KEYWORDS
    elif section == "industry":
        keywords = INDUSTRY_KEYWORDS
    else:
        return ""

    # Keyword-matched items only — non-strict pass pulled in nav/FAQ noise.
    items = _collect_items(pages, keywords, strict=True)

    if not items:
        return ""

    return "\n".join(f"- {item}" for item in items[:12])


def build_overview_facts(pages: list, company_name: str) -> str:
    """Assemble a facts-only block for the overview Groq call."""
    lines = [f"Company: {company_name}"]
    for page in pages:
        block = structure_page(page)
        if block.strip():
            lines.append(block)
    return "\n\n".join(lines)
