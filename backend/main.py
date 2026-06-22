import base64
import time

from brochure_builder import build_brochure
from config import AVAILABLE_TEMPLATES, DEFAULT_TEMPLATE, MIN_CONTENT_WORDS, TOP_N
from content_extractor import extract_content_parallel
from crawler.crawler import get_links, rank_urls
from pdf_generator import generate_pdf
from prompts import NOT_FOUND_MESSAGE

INVALID_EMAILS = {"you@yourbusiness.com", "example@example.com"}
GENERIC_EMAIL_HINTS = ("info@", "contact@", "support@", "help@", "sales@", "media@", "press@", "ir@", "investor@", "care@", "corpcomm@")

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
    preferred = []
    others = []
    for value in values:
        item = value.strip()
        if not item or item in INVALID_EMAILS:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        target = preferred if any(hint in key for hint in GENERIC_EMAIL_HINTS) else others
        target.append(item)
    return (preferred + others)[:limit]


def _normalize_phones(values: list[str], limit: int = 5) -> list[str]:
    seen = set()
    cleaned = []
    for value in values:
        item = value.strip()
        if not item:
            continue
        digits = "".join(ch for ch in item if ch.isdigit())
        if len(digits) < 10:
            continue
        if digits in seen:
            continue
        seen.add(digits)
        cleaned.append(item)
        if len(cleaned) == limit:
            break
    return cleaned


def _valid_template(template_key: str | None) -> str:
    if template_key in AVAILABLE_TEMPLATES:
        return template_key
    return DEFAULT_TEMPLATE


def _push_candidate(bucket: dict[str, list[tuple[int, dict]]], section: str, score: int, page: dict) -> None:
    if score <= 0:
        return
    bucket[section].append((score, page))


def _select_pages(scored_pages: list[tuple[int, dict]], limit: int) -> list[dict]:
    selected = []
    seen = set()
    for score, page in sorted(scored_pages, key=lambda item: item[0], reverse=True):
        url = page["url"]
        if url in seen:
            continue
        seen.add(url)
        selected.append(page | {"section_score": score})
        if len(selected) == limit:
            break
    return selected


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
        if website_url not in top_urls:
            top_urls.insert(0, website_url)
        top_urls = list(dict.fromkeys(top_urls))

        print(f"\n=== Extracting {len(top_urls)} page(s) ===")
        page_data = extract_content_parallel(top_urls, max_workers=6)
        if homepage:
            page_data[website_url] = homepage

        from similarity_filter import remove_similar_pages

        unique_pages = remove_similar_pages(page_data)
        print(f"  After dedup: {len(unique_pages)} unique page(s)")

        section_candidates = {
            "overview": [],
            "contact": [],
            "products": [],
            "services": [],
            "industries": [],
        }
        contact_emails = []
        contact_phones = []
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
            heading_blob = " ".join(data.get("headings", [])[:8]).lower()

            for kw in ["about", "mission", "vision", "history", "profile", "who we are", "leadership", "board", "business overview", "overview"]:
                if kw in ctx:
                    scores["overview"] += 1
            if url.rstrip("/") == website_url.rstrip("/").lower():
                scores["overview"] += 4
            if "about" in url or "profile" in url or "company" in url:
                scores["overview"] += 3

            for kw in ["contact", "sales", "support", "help", "location", "reach us", "get in touch", "office", "registered office"]:
                if kw in ctx:
                    scores["contact"] += 1
            if data.get("emails") or data.get("phones"):
                scores["contact"] += 4
            if "contact" in url or "support" in url:
                scores["contact"] += 3

            for kw in ["product", "products", "platform", "brand", "brands", "software", "hardware", "device", "portfolio", "consumer", "retail products"]:
                if kw in ctx:
                    scores["products"] += 1
            if "product" in url or "brand" in url or "portfolio" in url:
                scores["products"] += 2

            for kw in ["service", "services", "solution", "solutions", "consulting", "offering", "offerings", "capability", "capabilities", "what we do"]:
                if kw in ctx:
                    scores["services"] += 1
            if "service" in url or "solution" in url:
                scores["services"] += 2

            for kw in ["industry", "industries", "sector", "sectors", "markets", "applications", "banking", "healthcare", "manufacturing", "retail", "telecom", "energy", "education"]:
                if kw in ctx:
                    scores["industries"] += 1
            if "industry" in url or "sector" in url:
                scores["industries"] += 3
            if any(keyword in heading_blob for keyword in ["products", "brands", "portfolio"]):
                scores["products"] += 3
            if any(keyword in heading_blob for keyword in ["services", "solutions", "offerings", "capabilities"]):
                scores["services"] += 3
            if any(keyword in heading_blob for keyword in ["industries", "sectors", "markets", "applications"]):
                scores["industries"] += 3
            if any(keyword in heading_blob for keyword in ["contact", "office", "location"]):
                scores["contact"] += 3
            if any(keyword in heading_blob for keyword in ["about", "overview", "company", "businesses"]):
                scores["overview"] += 3

            _push_candidate(section_candidates, "overview", scores["overview"], data)
            _push_candidate(section_candidates, "contact", scores["contact"], data)
            _push_candidate(section_candidates, "products", scores["products"], data)
            _push_candidate(section_candidates, "services", scores["services"], data)
            _push_candidate(section_candidates, "industries", scores["industries"], data)

            if scores["contact"] > 0:
                contact_emails.extend(data.get("emails", []))
                contact_phones.extend(data.get("phones", []))

        company_profile["emails"] = _normalize_contact(contact_emails)
        company_profile["phones"] = _normalize_phones(contact_phones)
        company_profile["overview_pages"] = _select_pages(section_candidates["overview"], TOP_N)
        company_profile["contact_pages"] = _select_pages(section_candidates["contact"], TOP_N)
        company_profile["product_pages"] = _select_pages(section_candidates["products"], TOP_N)
        company_profile["service_pages"] = _select_pages(section_candidates["services"], TOP_N)
        company_profile["industry_pages"] = _select_pages(section_candidates["industries"], TOP_N)

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
