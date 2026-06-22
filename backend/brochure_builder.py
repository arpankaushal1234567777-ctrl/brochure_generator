from concurrent.futures import ThreadPoolExecutor, as_completed
from generator import get_ai_response
from config import COMBINE_TOP_PAGES


def _compress_all(pages: list) -> list:
    from compressor import compress_page

    def _compress(page):
        if not page.get("compressed_content"):
            page["compressed_content"] = compress_page(page["content"])
        return page

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(_compress, p): p for p in pages}
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  [compressor] error: {e}")

    return pages


def _combine(pages: list) -> str:
   
    return "\n\n".join(
        p["compressed_content"]
        for p in pages[:COMBINE_TOP_PAGES]
        if p.get("compressed_content")
    )


def build_brochure(profile: dict) -> dict:
    brochure = {"company_name": profile["company_name"]}

    
    all_pages: dict[str, dict] = {}   
    section_page_map = {
        "overview":  profile["overview_pages"],
        "services":  profile["service_pages"],
        "products":  profile["product_pages"],
        "industry":  profile["industry_pages"],
    }
    for pages in section_page_map.values():
        for p in pages[:COMBINE_TOP_PAGES]:
            all_pages[p["url"]] = p

   
    print(f"\n[brochure_builder] Compressing {len(all_pages)} unique page(s) via Gemini…")
    _compress_all(list(all_pages.values()))

    
    for section_name, pages in section_page_map.items():
        if not pages:
            brochure[section_name] = ""
            continue

        combined = _combine(pages)
        if not combined.strip():
            brochure[section_name] = ""
            continue

        print(f"\n[brochure_builder] Generating '{section_name}' section…")
        brochure[section_name] = get_ai_response(section_name, combined)

    brochure["contact"] = {
        "emails": profile["emails"],
        "phones": profile["phones"],
    }

    return brochure