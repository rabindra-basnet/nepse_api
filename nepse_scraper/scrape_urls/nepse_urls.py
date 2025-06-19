import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib3
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

visited = set()
failed_urls = {}
base_url = "https://www.nepalstock.com"
parsed_base = urlparse(base_url)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
}

def is_internal_link(url):
    parsed = urlparse(url)
    return parsed.netloc == "" or parsed.netloc == parsed_base.netloc

def normalize_url(href):
    full_url = urljoin(base_url, href)
    return full_url.split('#')[0].rstrip('/')

def crawl(url, depth=0, max_depth=3, session=None):
    if url in visited or depth > max_depth:
        return

    print(f"🔍 Visiting: {url}")
    visited.add(url)

    try:
        res = session.get(url, headers=headers, timeout=15, verify=False)
        if res.status_code != 200:
            print(f"⚠️ Skipping {url}: Status {res.status_code}")
            failed_urls[url] = {'status': res.status_code, 'headers': dict(res.headers)}
            return
        if "text/html" not in res.headers.get("Content-Type", ""):
            print(f"⚠️ Skipping {url}: Non-HTML content")
            failed_urls[url] = {'status': res.status_code, 'headers': dict(res.headers)}
            return

        soup = BeautifulSoup(res.text, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = normalize_url(href)
            if is_internal_link(full_url):
                crawl(full_url, depth + 1, max_depth, session)
        time.sleep(1)  # Increased delay to avoid rate-limiting
    except Exception as e:
        print(f"⚠️ Error visiting {url}: {e}")
        failed_urls[url] = {'error': str(e)}

def main():
    # Set up session with retries
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    crawl(base_url, session=session)

    # Save and print results
    print("\n✅ Found Routes:")
    with open("crawled_urls.txt", "w") as f:
        for url in sorted(visited):
            print(url)
            f.write(url + "\n")

    if failed_urls:
        print("\n❌ Failed URLs:")
        with open("failed_urls.txt", "w") as f:
            for url, info in sorted(failed_urls.items()):
                print(f"{url}: {info}")
                f.write(f"{url}: {info}\n")

if __name__ == "__main__":
    main()