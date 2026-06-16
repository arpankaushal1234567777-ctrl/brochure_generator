import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

def download_page(url):
    response = requests.get(url)
    return response.text


def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup

def clean_html(soup):
    for tag in soup(["header", "nav", "footer", "script", "style"]):
        tag.decompose()

    return soup

def extract_main_content(soup):
    main = soup.find("main")

    if main:
        return main.get_text()

    return soup.get_text()

def truncate_text(text, max_words=2000):
    words = text.split()

    if len(words) <= max_words:
        return text

    return " ".join(words[:max_words])

def extract_content_parallel(urls, max_workers=10):
    results = {}
    results_lock = Lock()

    import time

    def worker(url):
        start = time.time()

        text = extract_content_from_url(url)

        duration = time.time() - start

        print(
            f"Extracted {url} in {duration:.2f}s"
        )

        with results_lock:
            results[url] = text

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(worker, urls)

    return results

def extract_content_from_url(url):
    try:
        html = download_page(url)
        soup = parse_html(html)
        soup = clean_html(soup)
        text = extract_main_content(soup)
        text = truncate_text(text, max_words=2000)

        return text
    

    except Exception as e:
        print(f"Failed to extract {url}: {e}")
        return ""