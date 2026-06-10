import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_links(url):
    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    links = []

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
            links.append(full_url)

    return links