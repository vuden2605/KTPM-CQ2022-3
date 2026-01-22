from datetime import datetime
import os
import sys

# Ensure repo root is on sys.path when running directly
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.crawlers.coindesk_crawler import CoindeskCrawler
from app.crawlers.cointelegraph_crawler import CointelegraphCrawler
from app.crawlers.decrypt import DecryptCrawler
from app.core.normalizer import normalize_article


def check(crawler, name: str, limit: int = 3):
    cfg = crawler.get_config()
    urls = crawler.get_urls(cfg)[:limit]
    print(f"=== {name} - {len(urls)} urls ===")
    for u in urls:
        data = crawler.extract_article(u, cfg)
        pub = data.get("published_at")
        print(name, "URL:", u)
        print(name, "published_at(raw):", pub, type(pub))
        if isinstance(pub, datetime):
            print(name, "raw time:", pub.strftime("%Y-%m-%d %H:%M:%S%z"))
        # Also show normalized PublishedAt
        norm = normalize_article(data, crawler.source_code, u)
        n_pub = norm.get("PublishedAt")
        print(name, "PublishedAt(normalized UTC naive):", n_pub, type(n_pub))
        if isinstance(n_pub, datetime):
            print(name, "normalized time:", n_pub.strftime("%Y-%m-%d %H:%M:%S"))
        print("-" * 60)


def main():
    crawlers = [
        ("coindesk", CoindeskCrawler()),
        ("cointelegraph", CointelegraphCrawler()),
        ("decrypt", DecryptCrawler()),
    ]
    for name, c in crawlers:
        check(c, name)


if __name__ == "__main__":
    main()
