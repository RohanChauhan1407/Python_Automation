import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

visited = set()
emails_found = set()
session = requests.Session()

def scrape_page(url, base_domain):
    if url in visited:
        return
    visited.add(url)

    try:
        response = session.get(url, timeout=10)
    except requests.RequestException:
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract and store emails
    emails = set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", soup.get_text()))
    emails_found.update(emails)

    links = []
    for link_tag in soup.find_all("a", href=True):
        link = urljoin(url, link_tag["href"])
        parsed_link = urlparse(link)
        if parsed_link.scheme in ["http", "https"] and base_domain in parsed_link.netloc:
            if link not in visited:
                links.append(link)
    return links

def crawl(start_url, max_workers=10):
    base_domain = urlparse(start_url).netloc.split(":")[0]
    to_visit = [start_url]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while to_visit:
            futures = {executor.submit(scrape_page, url, base_domain): url for url in to_visit}
            to_visit = []
            for future in as_completed(futures):
                links = future.result()
                if links:
                    to_visit.extend(links)

if __name__ == "__main__":
    start_url = input("Enter the starting URL: ").strip()
    print(f"🌐 Crawling {start_url} and subdomains...\n")

    crawl(start_url, max_workers=20)  # You can adjust max_workers for speed

    print("\n✅ Done! Total emails found:", len(emails_found))
    for email in sorted(emails_found):
        print(email)
