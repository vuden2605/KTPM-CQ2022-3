"""
Debug script to inspect Coindesk HTML and find author selector.
"""
import httpx
from bs4 import BeautifulSoup

url = "https://www.coindesk.com/markets/2025/12/24/gold-knocks-on-a-door-that-s-been-shut-for-50-years-as-bitcoin-tests-a-defining-support"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

print(f"Fetching: {url}\n")
html = httpx.get(url, headers=headers, timeout=20.0).text
soup = BeautifulSoup(html, "lxml")

# Search for author-related patterns
print("=" * 60)
print("SEARCHING FOR AUTHOR/BYLINE PATTERNS")
print("=" * 60)

patterns = [
    ("a[rel='author']", "Links with rel=author"),
    (".byline", "byline class"),
    (".byline__name", "byline__name"),
    (".author", "author class"),
    (".author-name", "author-name class"),
    ("[itemprop='author']", "itemprop=author"),
    ("meta[name='author']", "meta author"),
    ("meta[property='article:author']", "meta article:author"),
    ("span[class*='author']", "span with author in class"),
    ("span[class*='byline']", "span with byline in class"),
    (".article__byline", "article__byline"),
    (".article__author", "article__author"),
    ("*[class*='contributor']", "contributor class"),
    ("*[class*='writer']", "writer class"),
    ("*[class*='journalist']", "journalist class"),
]

for selector, description in patterns:
    elements = soup.select(selector)
    if elements:
        print(f"\n✓ {description}: {selector}")
        for i, elem in enumerate(elements[:2]):  # Show first 2
            text = elem.get_text(strip=True)[:100]
            print(f"  [{i}] {text}")

# Also print all meta tags to see what's available
print("\n" + "=" * 60)
print("ALL META TAGS (for reference)")
print("=" * 60)
for meta in soup.find_all("meta"):
    name_or_prop = meta.get("name") or meta.get("property")
    content = meta.get("content", "")[:80]
    if name_or_prop:
        print(f"{name_or_prop}: {content}")

# Look for any text near "by" or "written"
print("\n" + "=" * 60)
print("SEARCHING FOR TEXT PATTERNS")
print("=" * 60)
for elem in soup.find_all(text=True):
    text = elem.strip()
    if ("by " in text.lower() or text.lower().startswith("written by")) and 5 < len(text) < 100:
        parent = elem.parent
        print(f"Text: '{text}'")
        print(f"Parent tag: <{parent.name} class='{parent.get('class')}'>")
        print()
