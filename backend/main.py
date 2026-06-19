import time
import json
from crawler.crawler import get_links, rank_urls
from content_extractor import extract_content_parallel
from config import MIN_CONTENT_WORDS, TOP_N
from brochure_builder import build_brochure

metrics = {
    "crawl_time": 0,
    "extract_time": 0,
    "generation_time": 0,
    "total_time": 0,
    "pages_discovered": 0,
    "pages_processed": 0,
    "emails_found": 0,
    "phones_found": 0
}

def is_blocked_page(data):
    if not data or "title" not in data:
        return True
    title = data["title"].lower()
    blocked_patterns = [
        "request has been blocked", "access denied",
        "forbidden", "captcha", "security check"
    ]
    return any(p in title for p in blocked_patterns)


def generate_brochure(website_url: str) -> dict:
    start_time = time.time()

    company_profile = {
        "company_name": "Unknown / Blocked",
        "overview_pages": [],
        "service_pages": [],
        "product_pages": [],
        "industry_pages": [],
        "contact_pages": [],
        "emails": [],
        "phones": []
    }

    INVALID_EMAILS = ["you@yourbusiness.com", "example@example.com"]

    try:
        print(f"\n--- Discovering Links for: {website_url} ---")

        crawl_start = time.time()
        links = get_links(website_url)
        metrics["crawl_time"] = round(time.time() - crawl_start, 2)
        metrics["pages_discovered"] = len(links)

        if not links:
            raise Exception("No links discovered from the target page.")

        homepage_data = extract_content_parallel([website_url], max_workers=1)
        homepage = homepage_data.get(website_url)

        if homepage and not is_blocked_page(homepage):
            company_profile["company_name"] = homepage["company_name"]
        else:
            company_profile["company_name"] = "Protected Corporate Domain"

            company_profile["logo_url"] = homepage.get("logo_url")

        ranked_links = rank_urls(links)
        top_urls = [url for score, url in ranked_links[:TOP_N]]

        print("\n--- Extracting Content ---\n")

        extract_start = time.time()

        page_data = extract_content_parallel(top_urls,max_workers=5)

        metrics["extract_time"] = round(time.time() - extract_start,2)

        seen_snippets = set()

        for url, data in page_data.items():
            if not data or is_blocked_page(data):
                continue
            if len(data["content"].split()) < MIN_CONTENT_WORDS:
                continue

            from compressor import compress_page

            data["compressed_content"] = compress_page(data["content"])

            snippet = data["content"][:500]
            if snippet in seen_snippets:
                continue
            seen_snippets.add(snippet)

            lower_url = url.lower()
            page_ctx = (
            lower_url + " " +
            data.get("title", "").lower() + " " +
            " ".join(data.get("headings", [])).lower() + " " +
            data.get("compressed_content", "").lower())

            scores = {"overview": 0, "contact": 0, "product": 0, "service": 0, "industry": 0}

            overview_kw = ["about", "mission", "vision", "history", "profile", "chairperson",
                           "chairman", "who we are", "leadership team", "board of directors", "investor"]
            for kw in overview_kw:
                if kw in page_ctx:
                    scores["overview"] += 1
            if "about" in lower_url or "profile" in lower_url:
                scores["overview"] += 3

            contact_kw = ["contact", "sales", "support", "help", "connect", "investor-contacts",
                          "location", "reach us", "get in touch", "headquarters", "registered office",
                          "sitemap", "office-locations"]
            for kw in contact_kw:
                if kw in page_ctx:
                    scores["contact"] += 1
            if "contact" in lower_url or "support" in lower_url:
                scores["contact"] += 3

            product_kw = ["product", "platform", "brand", "software", "hardware", "device",
                          "surface", "windows", "office", "xbox", "apps", "download", "accessories"]
            for kw in product_kw:
                if kw in page_ctx:
                    scores["product"] += 1
            if "product" in lower_url or "device" in lower_url:
                scores["product"] += 2

            service_kw = ["service", "solution", "licensing", "features", "business",
                          "cloud", "azure", "enterprise", "consulting"]
            for kw in service_kw:
                if kw in page_ctx:
                    scores["service"] += 1
            if "services" in lower_url or "solutions" in lower_url or "licensing" in lower_url:
                scores["service"] += 2

            industry_kw = ["industry", "industries", "sector", "sectors", "public services",
                           "banking", "insurance", "healthcare", "manufacturing", "retail",
                           "telecom", "energy", "utilities", "government"]
            for kw in industry_kw:
                if kw in page_ctx:
                    scores["industry"] += 1
            if "education" in lower_url or "industry" in lower_url or "case-study" in lower_url:
                scores["industry"] += 3

            max_score = max(scores.values())

            if max_score > 0:
                if scores["overview"] >= max_score - 1 and scores["overview"] > 0:
                    company_profile["overview_pages"].append(data)
                if scores["contact"] >= max_score - 1 and scores["contact"] > 0:
                    company_profile["contact_pages"].append(data)
                if scores["product"] >= max_score and scores["product"] > 0:
                    company_profile["product_pages"].append(data)
                if scores["service"] >= max_score - 1 and scores["service"] > 0:
                    company_profile["service_pages"].append(data)
                if scores["industry"] >= max_score - 1 and scores["industry"] > 0:
                    company_profile["industry_pages"].append(data)

            company_profile["emails"].extend(
                e for e in data["emails"] if e not in INVALID_EMAILS
            )
            company_profile["phones"].extend(data["phones"])

        company_profile["emails"] = list(set(company_profile["emails"]))[:5]
        company_profile["phones"] = list(set(company_profile["phones"]))[:5]

        print(f"\nCompany: {company_profile['company_name']}")
        print(f"Overview Pages:  {len(company_profile['overview_pages'])}")
        print(f"Service Pages:   {len(company_profile['service_pages'])}")
        print(f"Product Pages:   {len(company_profile['product_pages'])}")
        print(f"Industry Pages:  {len(company_profile['industry_pages'])}")
        print(f"Runtime: {time.time() - start_time:.2f}s")

    except Exception as e:
        print(f"Pipeline crashed: {e}")
        raise

    generation_start = time.time()

    brochure = build_brochure(company_profile)

    from pdf_generator import generate_pdf
    import base64

    pdf_bytes = generate_pdf(brochure)

    brochure["pdf_data"] = base64.b64encode(
    pdf_bytes).decode("utf-8")

    metrics["generation_time"] = round(time.time() - generation_start,2)


    metrics["pages_processed"] = len(page_data)
    metrics["emails_found"] = len(company_profile["emails"])
    metrics["phones_found"] = len(company_profile["phones"])

    metrics["total_time"] = round(time.time() - start_time,2)

    #brochure["metrics"] = metrics

    #with open("brochure.json", "w") as f:
     #json.dump(brochure, f, indent=4)

    return brochure
