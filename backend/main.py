import time
from crawler.crawler import get_links, rank_urls
from content_extractor import extract_content_parallel
from config import MIN_CONTENT_WORDS, TOP_N
from brochure_builder import build_brochure

INVALID_EMAILS = {"you@yourbusiness.com", "example@example.com"}

BLOCKED_TITLES = {
    "request has been blocked", "access denied",
    "forbidden", "captcha", "security check",
}

def _is_blocked(data: dict | None) -> bool:
    if not data or "title" not in data:
        return True
    title = data["title"].lower()
    return any(p in title for p in BLOCKED_TITLES)


def generate_brochure(website_url: str) -> dict:
    start_time = time.time()
    metrics: dict = {}

    company_profile = {
        "company_name":   "Unknown",
        "logo_url":       None,
        "overview_pages": [],
        "service_pages":  [],
        "product_pages":  [],
        "industry_pages": [],
        "contact_pages":  [],
        "emails":         [],
        "phones":         [],
    }

    try:
        # ── 1. Crawl ──────────────────────────────────────────────────────────
        print(f"\n=== Discovering links: {website_url} ===")
        t0 = time.time()
        links = get_links(website_url)
        metrics["crawl_time"] = round(time.time() - t0, 2)
        metrics["pages_discovered"] = len(links)

        if not links:
            raise Exception("No links discovered from the target page.")

        # ── 2. Fetch homepage for company name ────────────────────────────────
        hp_data = extract_content_parallel([website_url], max_workers=1)
        homepage = hp_data.get(website_url)

        if homepage and not _is_blocked(homepage):
            company_profile["company_name"] = homepage["company_name"]
            company_profile["logo_url"]     = homepage.get("logo_url")
        else:
            company_profile["company_name"] = "Protected Corporate Domain"

        # ── 3. Fetch top-N ranked pages in parallel ───────────────────────────
        ranked = rank_urls(links)
        top_urls = [url for _, url in ranked[:TOP_N]]

        print(f"\n=== Extracting {len(top_urls)} page(s) ===")
        t0 = time.time()
        page_data = extract_content_parallel(top_urls, max_workers=6)
        metrics["extract_time"] = round(time.time() - t0, 2)
        metrics["pages_fetched"] = len(page_data)

        # ── 4. Deduplicate ────────────────────────────────────────────────────
        from similarity_filter import remove_similar_pages
        unique_pages = remove_similar_pages(page_data)
        print(f"  After dedup: {len(unique_pages)} unique page(s)")

        # ── 5. Classify pages into sections ───────────────────────────────────
        seen_snippets: set[str] = set()

        for data in unique_pages:
            if not data or _is_blocked(data):
                continue
            word_count = len(data["content"].split())
            if word_count < MIN_CONTENT_WORDS:
                continue

            snippet = data["content"][:500]
            if snippet in seen_snippets:
                continue
            seen_snippets.add(snippet)

            url   = data["url"].lower()
            title = data.get("title", "").lower()
            heads = " ".join(data.get("headings", [])).lower()
            body  = data.get("content", "")[:2000].lower()
            ctx   = f"{url} {title} {heads} {body}"

            scores = {k: 0 for k in ("overview", "contact", "product", "service", "industry")}

            # overview
            for kw in ["about", "mission", "vision", "history", "profile",
                        "who we are", "leadership", "chairman", "board", "investor"]:
                if kw in ctx: scores["overview"] += 1
            if "about" in url or "profile" in url: scores["overview"] += 3

            # contact
            for kw in ["contact", "sales", "support", "help", "connect",
                        "location", "reach us", "get in touch", "headquarters",
                        "registered office", "office"]:
                if kw in ctx: scores["contact"] += 1
            if "contact" in url or "support" in url: scores["contact"] += 3

            # product
            for kw in ["product", "platform", "brand", "software", "hardware",
                        "device", "apps", "accessories", "download"]:
                if kw in ctx: scores["product"] += 1
            if "product" in url or "device" in url: scores["product"] += 2

            # service
            for kw in ["service", "solution", "features", "business",
                        "cloud", "enterprise", "consulting", "licensing"]:
                if kw in ctx: scores["service"] += 1
            if "service" in url or "solution" in url: scores["service"] += 2

            # industry
            for kw in ["industry", "sector", "banking", "insurance",
                        "healthcare", "manufacturing", "retail", "telecom",
                        "energy", "government", "education"]:
                if kw in ctx: scores["industry"] += 1
            if "industry" in url or "education" in url: scores["industry"] += 3

            mx = max(scores.values())
            if mx == 0:
                continue

            threshold = max(1, mx - 1)
            if scores["overview"]  >= threshold: company_profile["overview_pages"].append(data)
            if scores["contact"]   >= threshold: company_profile["contact_pages"].append(data)
            if scores["product"]   >= mx:        company_profile["product_pages"].append(data)
            if scores["service"]   >= threshold: company_profile["service_pages"].append(data)
            if scores["industry"]  >= threshold: company_profile["industry_pages"].append(data)

            # Contact info
            for e in data.get("emails", []):
                if e not in INVALID_EMAILS:
                    company_profile["emails"].append(e)
            company_profile["phones"].extend(data.get("phones", []))

        company_profile["emails"] = list(set(company_profile["emails"]))[:5]
        company_profile["phones"] = list(set(company_profile["phones"]))[:5]

        print(f"\nCompany     : {company_profile['company_name']}")
        print(f"Overview    : {len(company_profile['overview_pages'])} page(s)")
        print(f"Services    : {len(company_profile['service_pages'])} page(s)")
        print(f"Products    : {len(company_profile['product_pages'])} page(s)")
        print(f"Industry    : {len(company_profile['industry_pages'])} page(s)")

    except Exception as e:
        print(f"Pipeline error: {e}")
        raise

    # ── 6. Build brochure (compress + generate) ───────────────────────────────
    t0 = time.time()
    brochure = build_brochure(company_profile)
    metrics["generation_time"] = round(time.time() - t0, 2)

    # ── 7. Generate PDF ───────────────────────────────────────────────────────
    from pdf_generator import generate_pdf
    import base64
    brochure["pdf_data"] = base64.b64encode(generate_pdf(brochure)).decode("utf-8")

    metrics["total_time"] = round(time.time() - start_time, 2)
    print(f"\n=== Done in {metrics['total_time']}s ===")
    print(f"    crawl={metrics['crawl_time']}s  "
          f"extract={metrics['extract_time']}s  "
          f"generation={metrics['generation_time']}s")

    return brochure