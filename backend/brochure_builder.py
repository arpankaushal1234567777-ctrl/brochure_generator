from generator import get_ai_response
from config import COMBINE_TOP_PAGES
from compressor import build_overview_facts


def _dedupe_pages(pages: list) -> list:
    seen: set[str] = set()
    unique = []
    for page in pages:
        url = page.get("url", "")
        if url in seen:
            continue
        seen.add(url)
        unique.append(page)
    return unique


def _section_facts(pages: list, profile: dict) -> str:
    facts = build_overview_facts(pages, profile["company_name"])
    website_url = profile.get("website_url", "")
    if website_url:
        facts = f"Website URL: {website_url}\n\n{facts}"
    return facts


def build_brochure(profile: dict) -> dict:
    brochure = {"company_name": profile["company_name"]}

    section_page_map = {
        "overview":  profile["overview_pages"],
        "offerings": profile["offerings_pages"],
        "industry":  profile["industry_pages"],
    }

    # ── Overview: Groq on pre-extracted facts ────────────────────────────────
    overview_pages = _dedupe_pages(section_page_map["overview"][:COMBINE_TOP_PAGES])
    if overview_pages:
        facts = build_overview_facts(overview_pages, profile["company_name"])
        print("\n[brochure_builder] Generating 'overview' section via Groq…")
        brochure["overview"] = get_ai_response("overview", facts)
    else:
        brochure["overview"] = ""

    # ── Offerings: Groq on facts (same pattern as overview) ─────────────────
    offerings_pages = _dedupe_pages(section_page_map["offerings"][:COMBINE_TOP_PAGES])
    if not offerings_pages:
        offerings_pages = _dedupe_pages(section_page_map["overview"][:COMBINE_TOP_PAGES])
    print(f"\n[brochure_builder] Generating offerings from {len(offerings_pages)} page(s)…")
    if offerings_pages:
        brochure["offerings"] = get_ai_response("offerings", _section_facts(offerings_pages, profile))
    else:
        brochure["offerings"] = ""

    # ── Industry: Groq on facts ─────────────────────────────────────────────
    industry_pages = _dedupe_pages(section_page_map["industry"][:COMBINE_TOP_PAGES])
    if not industry_pages:
        industry_pages = _dedupe_pages(section_page_map["overview"][:COMBINE_TOP_PAGES])
    print(f"[brochure_builder] Generating industry from {len(industry_pages)} page(s)…")
    if industry_pages:
        brochure["industry"] = get_ai_response("industry", _section_facts(industry_pages, profile))
    else:
        brochure["industry"] = ""

    brochure["contact"] = {
        "emails": profile["emails"],
        "phones": profile["phones"],
    }

    return brochure
