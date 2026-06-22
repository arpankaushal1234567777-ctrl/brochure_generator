from compressor import compress_page
from config import COMBINE_TOP_PAGES, MAX_ITEMS_PER_SECTION, MIN_SECTION_SOURCE_WORDS
from generator import generate_brochure_sections
from prompts import NOT_FOUND_MESSAGE


def _clean_list(values):
    seen = set()
    cleaned = []
    for value in values[:MAX_ITEMS_PER_SECTION]:
        item = " ".join(str(value).split()).strip()
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
    return cleaned


def _enough_evidence(pages: list[dict]) -> bool:
    words = sum(len((page.get("content") or "").split()) for page in pages[:COMBINE_TOP_PAGES])
    return words >= MIN_SECTION_SOURCE_WORDS


def _section_evidence(label: str, pages: list[dict]) -> str:
    blocks = []
    for page in pages[:COMBINE_TOP_PAGES]:
        content = compress_page(page.get("content", ""))
        headings = ", ".join(page.get("headings", [])[:6])
        if not content:
            continue
        block = [f"Section: {label}", f"URL: {page['url']}"]
        if page.get("title"):
            block.append(f"Title: {page['title']}")
        if headings:
            block.append(f"Headings: {headings}")
        block.append(f"Evidence:\n{content}")
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def build_brochure(profile: dict, template_key: str) -> dict:
    brochure = {
        "company_name": profile["company_name"],
        "overview": NOT_FOUND_MESSAGE,
        "services": [],
        "products": [],
        "industries": [],
        "contact": {
            "emails": _clean_list(profile.get("emails", [])),
            "phones": _clean_list(profile.get("phones", [])),
        },
        "template_used": template_key,
        "traceability": {
            "overview": [],
            "services": [],
            "products": [],
            "industries": [],
            "contact": [],
        },
    }

    section_page_map = {
        "overview": profile["overview_pages"],
        "services": profile["service_pages"],
        "products": profile["product_pages"],
        "industries": profile["industry_pages"],
    }

    evidence_blocks = []
    for section_name, pages in section_page_map.items():
        selected_pages = pages[:COMBINE_TOP_PAGES]
        brochure["traceability"][section_name] = [page["url"] for page in selected_pages]
        if not selected_pages or not _enough_evidence(selected_pages):
            continue
        combined = _section_evidence(section_name, selected_pages)
        if combined.strip():
            evidence_blocks.append(combined)

    brochure["traceability"]["contact"] = [page["url"] for page in profile.get("contact_pages", [])[:COMBINE_TOP_PAGES]]

    if evidence_blocks:
        print("\n[brochure_builder] Generating all brochure sections in one Groq call…")
        generated = generate_brochure_sections("\n\n".join(evidence_blocks))
        brochure["overview"] = generated.get("overview") or NOT_FOUND_MESSAGE
        brochure["services"] = _clean_list(generated.get("services", []))
        brochure["products"] = _clean_list(generated.get("products", []))
        brochure["industries"] = _clean_list(generated.get("industries", []))

    return brochure
