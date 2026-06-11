import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


BUSINESS_KEYWORDS = [
    "about",
    "company",
    "team",
    "leadership",
    "management",
    "services",
    "products",
    "solutions",
    "business",
    "contact",
    "careers",
    "investors",
    "news",
    "media",
    "sustainability"
]


def get_links(url):
    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    links = set()

    base_domain = urlparse(url).netloc

    for a in soup.find_all("a"):
        href = a.get("href")

        if href:

            if href.startswith("#"):
                continue

            if href.startswith("javascript:"):
                continue

            if href.startswith("mailto:"):
                continue

            full_url = urljoin(url, href)

            link_domain = urlparse(full_url).netloc

            if link_domain == base_domain:

                is_business_link = False

                for keyword in BUSINESS_KEYWORDS:
                    if keyword in full_url.lower():
                        is_business_link = True
                        break

                if is_business_link:
                    links.add(full_url)

    return list(links)


def crawl(url, visited):
    
    if url in visited:
        return

    visited.add(url)

    print("Visiting:", url)

    links = get_links(url)

    for link in links:
        crawl(link, visited)