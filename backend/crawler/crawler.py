import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

session = requests.Session()

def get_links(url):
    try:
        start = time.time()
        response = session.get(url, timeout=10)
        download_time = time.time() - start
        print(f"Downloaded: {url} in {download_time:.3f}s")
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

    links = set()
    base_domain = urlparse(url).netloc

    for a in soup.find_all("a"):
        href = a.get("href")
        if not href or href.startswith(("#", "mailto:", "javascript:")):
            continue

        full_url = urljoin(url, href)
        parsed = urlparse(full_url)

        if parsed.netloc != base_domain:
            continue
        if parsed.query or parsed.fragment:
            continue

        clean_url = (
            parsed.scheme
            + "://"
            + parsed.netloc
            + parsed.path.rstrip("/")
        )
        links.add(clean_url)

    return list(links)


def rank_urls(urls):
    keywords = {
        "about": 10, "company": 10, "contact": 9, "leadership": 8,
        "management": 8, "services": 7, "products": 7, "business": 7,
        "technology": 7, "vision": 7, "mission": 7, "sustainability": 6,
        "careers": 4
    }
    scored = []
    for url in urls:
        score = 0
        lower_url = url.lower()
        for keyword, points in keywords.items():
            if keyword in lower_url:
                score += points
        scored.append((score, url))
    scored.sort(reverse=True)
    return scored


def get_links_parallel(urls, max_workers=10):
    visited = set()
    visited_lock = Lock()
    results = {}

    def worker(url):
        with visited_lock:
            if url in visited:
                return
            visited.add(url)

        sub_links = get_links(url)

        with visited_lock:
            results[url] = sub_links

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(worker, urls)

    return results