import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


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
                links.add(full_url)

    return list(links)