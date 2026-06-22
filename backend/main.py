import base64
import time

from brochure_builder import build_brochure
from config import AVAILABLE_TEMPLATES, DEFAULT_TEMPLATE, MIN_CONTENT_WORDS, TOP_N
from content_extractor import extract_content_parallel
from crawler.crawler import get_links, rank_urls
from pdf_generator import generate_pdf
from prompts import NOT_FOUND_MESSAGE

INVALID_EMAILS = {"you@yourbusiness.com", "example@example.com"}

BLOCKED_TITLES = {
    "request has been blocked",
    "access denied",
    "forbidden",
    "captcha",
    "security check",
}


def _is_blocked(data: dict | None) -> bool:
    if not data or "title" not in data:
        return True
    title = data["title"].lower()
    return any(pattern in title for pattern in BLOCKED_TITLES)


def _normalize_contact(values: list[str], limit: int = 5) -> list[str]:
    seen = set()
    cleaned = []
    for value in values:
        item = value.strip()
        if not item or item in INVALID_EMAILS:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
        if len(cleaned) == limit:
            break
    return cleaned


def _valid_template(template_key: str | None) -> str:
    if template_key in AVAILABLE_TEMPLATES:
        return template_key
    return DEFAULT_TEMPLATE


def generate_brochure(website_url: str, template_key: str | None = None) -> dict:
    start_time = time.time()
    template_key = _valid_template(template_key)

    company_profile = {
        "company_name": "Unknown",
        "logo_url": None,
        "overview_pages": [],
        "service_pages": [],
        "product_pages": [],
        "industry_pages": [],
        "contact_pages": [],
        "emails": [],
        "phones": [],
    }

    try:
        print(f"\n=== Discovering links: {website_url} ===")
        links = get_links(website_url)
        if not links:
            raise Exception("No links discovered from the target page.")

        homepage_data = extract_content_parallel([website_url], max_workers=1)
        homepage = homepage_data.get(website_url)

        if homepage and not _is_blocked(homepage):
            company_profile["company_name"] = homepage["company_name"]
            company_profile["logo_url"] = homepage.get("logo_url")
        else:
            company_profile["company_name"] = "Protected Corporate Domain"

        ranked = rank_urls(links)
        top_urls = [url for _, url in ranked[:TOP_N]]

        print(f"\n=== Extracting {len(top_urls)} page(s) ===")
        page_data = extract_content_parallel(top_urls, max_workers=6)

        from similarity_filter import remove_similar_pages

        unique_pages = remove_similar_pages(page_data)
        print(f"  After dedup: {len(unique_pages)} unique page(s)")

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

            url = data["url"].lower()
            title = data.get("title", "").lower()
            heads = " ".join(data.get("headings", [])).lower()
            body = data.get("content", "")[:2000].lower()
            ctx = f"{url} {title} {heads} {body}"

            scores = {k: 0 for k in ("overview", "contact", "products", "services", "industries")}

            for kw in ["about", "mission", "vision", "history", "profile", "who we are", "leadership", "board"]:
                if kw in ctx:
                    scores["overview"] += 1
            if "about" in url or "profile" in url:
                scores["overview"] += 3

            for kw in ["contact", "sales", "support", "help", "location", "reach us", "get in touch", "office"]:
                if kw in ctx:
                    scores["contact"] += 1
            if "contact" in url or "support" in url:
                scores["contact"] += 3

            for kw in ["product", "platform", "brand", "software", "hardware", "device", "portfolio"]:
                if kw in ctx:
                    scores["products"] += 1
            if "product" in url or "brand" in url:
                scores["products"] += 2

            for kw in ["service", "solution", "consulting", "offering", "capability"]:
                if kw in ctx:
                    scores["services"] += 1
            if "service" in url or "solution" in url:
                scores["services"] += 2

            for kw in ["industry", "sector", "banking", "healthcare", "manufacturing", "retail", "telecom", "energy", "education"]:
                if kw in ctx:
                    scores["industries"] += 1
            if "industry" in url or "sector" in url:
                scores["industries"] += 3

            max_score = max(scores.values())
            if max_score == 0:
                continue

            threshold = max(1, max_score - 1)
            if scores["overview"] >= threshold:
                company_profile["overview_pages"].append(data)
            if scores["contact"] >= threshold:
                company_profile["contact_pages"].append(data)
            if scores["products"] >= max_score:
                company_profile["product_pages"].append(data)
            if scores["services"] >= threshold:
                company_profile["service_pages"].append(data)
            if scores["industries"] >= threshold:
                company_profile["industry_pages"].append(data)

            company_profile["emails"].extend(data.get("emails", []))
            company_profile["phones"].extend(data.get("phones", []))

        company_profile["emails"] = _normalize_contact(company_profile["emails"])
        company_profile["phones"] = _normalize_contact(company_profile["phones"])

    except Exception as e:
        print(f"Pipeline error: {e}")
        raise

    brochure = build_brochure(company_profile, template_key)
    brochure["contact"]["emails"] = brochure["contact"]["emails"] or [NOT_FOUND_MESSAGE]
    brochure["contact"]["phones"] = brochure["contact"]["phones"] or [NOT_FOUND_MESSAGE]

    brochure["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    pdf_bytes = generate_pdf(brochure)
    brochure["pdf_data"] = base64.b64encode(pdf_bytes).decode("utf-8")
    brochure["pdf_available"] = True
    brochure["generation_time"] = round(time.time() - start_time, 2)

    print(f"\n=== Done in {brochure['generation_time']}s ===")
    return brochure
