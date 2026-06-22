import re
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from bs4 import BeautifulSoup
from curl_cffi import requests
from urllib.parse import urljoin

session = requests.Session(impersonate="chrome")
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
})

def extract_logo(soup, url):

    logo_selectors = [
        'img[alt*="logo" i]',
        'img[src*="logo" i]',
        'header img'
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
    for tag in soup(["header", "nav", "footer", "script", "style", "noscript"]):
        tag.decompose()
    return soup

def extract_headings(soup):
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = tag.get_text(strip=True)
        if text:
            headings.append(text)
    return headings


def extract_meta_description(soup):
    tag = soup.find("meta", attrs={"name": "description"})
    if tag and tag.get("content"):
        return tag["content"].strip()
    tag = soup.find("meta", attrs={"property": "og:description"})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return ""


def extract_list_items(soup, limit=20):
    items = []
    seen = set()
    for li in soup.find_all("li"):
        text = li.get_text(separator=" ", strip=True)
        if len(text) < 4 or len(text) > 120:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(text)
        if len(items) >= limit:
            break
    return items


def extract_lead_paragraph(soup):
    for tag in soup.find_all("p"):
        text = tag.get_text(separator=" ", strip=True)
        if len(text.split()) >= 12:
            return text[:400]
    return ""

def extract_emails(text):
    return re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)

def extract_phones(text):

    pattern = r'''
    (?:
        \+\d{1,3}[\s\-]?
    )?
    (?:
        \d{2,5}[\s\-]?
    )?
    \d{3,5}[\s\-]?\d{3,5}[\s\-]?\d{0,5}
    '''

    matches = re.findall(pattern, text, re.VERBOSE)

    phones = []

    for phone in matches:

        phone = phone.strip()

        digits = re.sub(r'\D', '', phone)

        if len(digits) < 10:
            continue

        if len(digits) > 15:
            continue

        if digits.startswith(("19", "20")) and len(digits) <= 12:
            continue

        groups = re.findall(r"\d+", phone)
        if len(groups) >= 2 and all(len(g) == 4 and 1900 <= int(g) <= 2035 for g in groups):
            continue

        phones.append(phone)

    return sorted(list(set(phones)))

def extract_main_content(soup):
    main = soup.find("main")
    if main:
        return main.get_text(separator=" ", strip=True)
    return soup.get_text(separator=" ", strip=True)

from config import MAX_CONTENT_WORDS

def truncate_text(text, max_words=MAX_CONTENT_WORDS):
    words = text.split()
    return " ".join(words[:max_words])

def chunk_text(text, chunk_size=2000):

    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks


def extract_content_from_url(url):
    try:
        html = download_page(url)
        soup = parse_html(html)

        company_name = extract_company_name(soup, url)
        logo_url = extract_logo(soup, url)

        title = ""
        if soup.title:
            title = soup.title.get_text(strip=True)

        meta_description = extract_meta_description(soup)

        soup = clean_html(soup)
        content = extract_main_content(soup)
        content = truncate_text(content)
        headings = extract_headings(soup)
        list_items = extract_list_items(soup)
        lead_paragraph = extract_lead_paragraph(soup)
        emails = extract_emails(content)
        phones = extract_phones(content)

        return {
            "url": url,
            "title": title,
            "meta_description": meta_description,
            "headings": headings,
            "list_items": list_items,
            "lead_paragraph": lead_paragraph,
            "content": content,
            "emails": emails,
            "phones": phones,
            "company_name": company_name,
            "logo_url": logo_url
        }
    except Exception as e:
        print(f"Failed to extract {url}: {e}")
        return None
    

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