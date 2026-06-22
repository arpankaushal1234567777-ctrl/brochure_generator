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
    positive = {
        "about": 40, "company": 34, "history": 28, "profile": 28, "story": 20, "leadership": 18,
        "business": 30, "businesses": 36, "what-we-do": 36, "operations": 28, "segments": 30,
        "services": 34, "solutions": 34, "offerings": 30, "capabilities": 28, "digital": 20,
        "products": 36, "product": 34, "portfolio": 34, "brands": 34, "brand": 28,
        "industries": 34, "industry": 34, "sectors": 30, "sector": 26, "markets": 24,
        "contact": 40, "sales": 32, "support": 30, "help": 26, "connect": 26, "office": 26, "location": 26
    }

    negative = {
        "index": -80, "blog": -90, "news": -60, "release": -50, "media": -30,
        "privacy": -100, "terms": -100, "store": -120, "gift-card": -150, "career": -80, "jobs": -80
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
