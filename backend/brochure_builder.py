from concurrent.futures import ThreadPoolExecutor, as_completed

from compressor import compress_page
from config import COMBINE_TOP_PAGES, MAX_ITEMS_PER_SECTION, MIN_SECTION_SOURCE_WORDS
from generator import get_ai_response
from prompts import NOT_FOUND_MESSAGE


def _compress_all(pages: list[dict]) -> list[dict]:
    def _compress(page):
        if not page.get("compressed_content"):
            page["compressed_content"] = compress_page(page["content"])
        return page

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(_compress, p): p for p in pages}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"  [compressor] error: {e}")

    return pages


def _combine(pages: list[dict]) -> str:
    chunks = []
    for page in pages[:COMBINE_TOP_PAGES]:
        compressed = page.get("compressed_content") or ""
        raw = page.get("content") or ""
        headings = ", ".join(page.get("headings", [])[:8])
        raw_excerpt = " ".join(raw.split()[:220])
        evidence_parts = []
        if headings:
            evidence_parts.append(f"Headings: {headings}")
        if compressed and compressed != NOT_FOUND_MESSAGE:
            evidence_parts.append(f"Cleaned facts:\n{compressed}")
        if raw_excerpt:
            evidence_parts.append(f"Raw excerpt:\n{raw_excerpt}")
        if evidence_parts:
            chunks.append(
                f"URL: {page['url']}\nTitle: {page.get('title', '')}\n" + "\n".join(evidence_parts)
            )
    return "\n\n".join(chunks)


def _enough_evidence(pages: list[dict]) -> bool:
    words = sum(len((page.get("compressed_content") or page.get("content") or "").split()) for page in pages[:COMBINE_TOP_PAGES])
    return words >= MIN_SECTION_SOURCE_WORDS


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

    all_pages: dict[str, dict] = {}
    section_page_map = {
        "overview": profile["overview_pages"],
        "services": profile["service_pages"],
        "products": profile["product_pages"],
        "industries": profile["industry_pages"],
    }

    for pages in section_page_map.values():
        for page in pages[:COMBINE_TOP_PAGES]:
            all_pages[page["url"]] = page

    contact_pages = profile.get("contact_pages", [])
    for page in contact_pages[:COMBINE_TOP_PAGES]:
        all_pages[page["url"]] = page

    print(f"\n[brochure_builder] Compressing {len(all_pages)} unique page(s) via Gemini…")
    _compress_all(list(all_pages.values()))

    generation_inputs = {}
    for section_name, pages in section_page_map.items():
        selected_pages = pages[:COMBINE_TOP_PAGES]
        brochure["traceability"][section_name] = [page["url"] for page in selected_pages]

        if not selected_pages or not _enough_evidence(selected_pages):
            continue

        combined = _combine(selected_pages)
        if not combined.strip():
            continue

        generation_inputs[section_name] = combined

    def _generate_section(item):
        section_name, combined = item
        print(f"\n[brochure_builder] Generating '{section_name}' section…")
        return section_name, get_ai_response(section_name, combined)

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(_generate_section, item) for item in generation_inputs.items()]
        for future in as_completed(futures):
            section_name, generated = future.result()
            if section_name == "overview":
                brochure["overview"] = generated or NOT_FOUND_MESSAGE
            else:
                brochure[section_name] = _clean_list(generated if isinstance(generated, list) else [])

    brochure["traceability"]["contact"] = [page["url"] for page in contact_pages[:COMBINE_TOP_PAGES]]
    return brochure
