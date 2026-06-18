import time
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from bs4 import BeautifulSoup
from curl_cffi import requests

session = requests.Session(impersonate="chrome")
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
})

def get_links(url):
    try:
        start = time.time()
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

    links = set()
    base_domain = urlparse(url).netloc

    for a in soup.find_all("a"):
        href = a.get("href")
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue

        full_url = urljoin(url, href)
        parsed = urlparse(full_url)

        # Restrict within corporate base domain to prevent crawler leakages
        if parsed.netloc != base_domain:
            continue
        if parsed.query or parsed.fragment:
            continue

        clean_url = parsed.scheme + "://" + parsed.netloc + parsed.path.rstrip("/")
        links.add(clean_url)

    return list(links)

def rank_urls(urls):
    # Balanced weights spanning multi-sector entities (Tech, Manufacturing, Retail, Telecom)
    positive = {
        "about": 30, "company": 30, "history": 25, "profile": 25, "story": 20, "leadership": 20, "chairman": 20,
        "services": 30, "solutions": 30, "licensing": 25, "features": 20, "digital": 20,
        "products": 30, "platform": 30, "brands": 30, "software": 25, "hardware": 25, "devices": 25,
        "contact": 35, "sales": 35, "support": 30, "help": 30, "connect": 30, "investor": 25, "office": 25,
        "business": 25, "enterprise": 25, "industry": 25, "industries": 25, "petrochemicals": 25, "retail": 25
    }

    negative = {
        "index": -100, "blog": -100, "news": -100, "release": -100, "media": -50,
        "privacy": -100, "terms": -100, "store": -150, "gift-card": -150, "career": -80, "jobs": -80
    }

    scored = []
    for url in urls:
        lower_url = url.lower()
        score = 0
        for keyword, value in positive.items():
            if keyword in lower_url:
                score += value
        for keyword, value in negative.items():
            if keyword in lower_url:
                score += value
        scored.append((score, url))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored

def get_links_parallel(urls, max_workers=5):
    visited = set()
    lock = Lock()
    results = {}

    def worker(url):
        with lock:
            if url in visited:
                return
            visited.add(url)
        results[url] = get_links(url)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(worker, urls)

    return results 