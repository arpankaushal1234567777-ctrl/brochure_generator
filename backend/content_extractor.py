import re
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from curl_cffi import requests

from config import MAX_CONTENT_WORDS

session = requests.Session(impersonate="chrome")
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
})

NOISE_PATTERNS = (
    "cookie",
    "privacy policy",
    "terms of use",
    "all rights reserved",
    "subscribe",
    "sign in",
    "log in",
    "follow us",
    "share this",
    "javascript",
)


def extract_logo(soup, url):
    logo_selectors = [
        'img[alt*="logo" i]',
        'img[src*="logo" i]',
        "header img",
    ]
    for selector in logo_selectors:
        logo = soup.select_one(selector)
        if logo and logo.get("src"):
            return urljoin(url, logo["src"])
    return None


def download_page(url):
    response = session.get(url, timeout=10)
    response.raise_for_status()
    return response.text


def parse_html(html):
    return BeautifulSoup(html, "html.parser")


def clean_html(soup):
    for tag in soup(["header", "nav", "footer", "script", "style", "noscript", "svg"]):
        tag.decompose()
    return soup


def extract_headings(soup):
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = " ".join(tag.get_text(" ", strip=True).split())
        if text:
            headings.append(text)
    return headings


def extract_emails(text):
    return sorted(set(re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)))


def extract_phones(text):
    pattern = r"""
    (?:
        \+\d{1,3}[\s\-]?
    )?
    (?:
        \d{2,5}[\s\-]?
    )?
    \d{3,5}[\s\-]?\d{3,5}[\s\-]?\d{0,5}
    """
    matches = re.findall(pattern, text, re.VERBOSE)
    phones = []
    for phone in matches:
        phone = phone.strip()
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 10 or len(digits) > 15:
            continue
        if digits.startswith(("19", "20")) and len(digits) <= 12:
            continue
        phones.append(phone)
    return sorted(set(phones))


def _normalize_line(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _is_noise(line: str) -> bool:
    lowered = line.lower()
    if len(line.split()) < 4:
        return True
    return any(pattern in lowered for pattern in NOISE_PATTERNS)


def extract_main_content(soup):
    root = soup.find("main") or soup.find("article") or soup.body or soup
    blocks = []
    for tag in root.find_all(["h1", "h2", "h3", "p", "li"]):
        text = _normalize_line(tag.get_text(" ", strip=True))
        if not text or _is_noise(text):
            continue
        blocks.append(text)

    if not blocks:
        text = _normalize_line(root.get_text(" ", strip=True))
        return text

    unique_blocks = []
    seen = set()
    for block in blocks:
        key = block.lower()
        if key in seen:
            continue
        seen.add(key)
        unique_blocks.append(block)

    return "\n".join(unique_blocks)


def truncate_text(text, max_words=MAX_CONTENT_WORDS):
    words = text.split()
    return " ".join(words[:max_words])


def extract_company_name(soup, url):
    if soup.title:
        title = soup.title.get_text(strip=True)
        company_name = (
            title.split("–")[0]
            .split("|")[0]
            .split("-")[0]
            .split(":")[0]
            .strip()
        )
        if len(company_name) > 3:
            return company_name

    h1 = soup.find("h1")
    if h1:
        text = h1.get_text(strip=True)
        if len(text) > 3:
            return text

    return url.split("//")[-1].split("/")[0]


def extract_content_from_url(url):
    try:
        html = download_page(url)
        soup = parse_html(html)

        company_name = extract_company_name(soup, url)
        logo_url = extract_logo(soup, url)
        title = soup.title.get_text(strip=True) if soup.title else ""

        soup = clean_html(soup)
        content = truncate_text(extract_main_content(soup))
        headings = extract_headings(soup)
        emails = extract_emails(content)
        phones = extract_phones(content)

        return {
            "url": url,
            "title": title,
            "headings": headings,
            "content": content,
            "emails": emails,
            "phones": phones,
            "company_name": company_name,
            "logo_url": logo_url,
            "word_count": len(content.split()),
        }
    except Exception as e:
        print(f"Failed to extract {url}: {e}")
        return None


def extract_content_parallel(urls, max_workers=5):
    results = {}
    results_lock = Lock()

    def worker(url):
        start = time.time()
        data = extract_content_from_url(url)
        duration = time.time() - start
        print(f"Extracted {url} in {duration:.2f}s")
        with results_lock:
            results[url] = data

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(worker, urls)

    return results
