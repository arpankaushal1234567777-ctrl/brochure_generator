import requests
from bs4 import BeautifulSoup


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

if __name__ == "__main__":
    html = download_page("https://www.ril.com")

    soup = parse_html(html)

    soup = clean_html(soup)

    text = extract_main_content(soup)

    print(text[:2000])