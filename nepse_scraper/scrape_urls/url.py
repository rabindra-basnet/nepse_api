# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin, urlparse
# import certifi
# import time
# import urllib3


# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# visited = set()
# base_url = "https://www.nepalstock.com"
# parsed_base = urlparse(base_url)

# headers = {
#     'Host': 'www.nepalstock.com',
#     'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
#     'Accept': 'application/json, text/plain, */*',
#     'Accept-Language': 'en-US,en;q=0.5',
#     'Accept-Encoding': 'gzip, deflate, br',
#     'Connection': 'keep-alive',
#     'Referer': 'https://www.nepalstock.com/',
#     'Pragma': 'no-cache',
#     'Cache-Control': 'no-cache',
#     'TE': 'Trailers',
# }

# def is_internal_link(url):
#     parsed = urlparse(url)
#     return parsed.netloc == "" or parsed.netloc == parsed_base.netloc

# def normalize_url(href):
#     full_url = urljoin(base_url, href)
#     return full_url.split('#')[0].rstrip('/')

# def crawl(url, depth=0, max_depth=3):
#     if url in visited or depth > max_depth:
#         return
#     print(f"🔍 Visiting: {url}")
#     visited.add(url)

#     try:
#         res = requests.get(url, headers=headers, timeout=10, verify=False)
#         if res.status_code != 200 or "text/html" not in res.headers.get("Content-Type", ""):
#             return

#         soup = BeautifulSoup(res.text, "html.parser")
#         for link in soup.find_all("a", href=True):
#             href = link["href"]
#             full_url = normalize_url(href)
#             if is_internal_link(full_url):
#                 crawl(full_url, depth + 1, max_depth)
#         time.sleep(0.5)
#     except Exception as e:
#         print(f"⚠️ Error visiting {url}: {e}")

# if __name__ == "__main__":
#     crawl(base_url)

#     print("\n✅ Found Routes:")
#     for url in sorted(visited):
#         print(url)

from bs4 import BeautifulSoup
import httplib2 

class Extractor():
    
    def get_links(self, url):

        http = httplib2.Http()
        response, content = http.request(url)

        links=[]

        for link in BeautifulSoup(content).find_all('a', href=True):
            links.append(link['href'])
        
        return links

url = 'https://pyshark.com/'

myextractor = Extractor()

links = myextractor.get_links(url)