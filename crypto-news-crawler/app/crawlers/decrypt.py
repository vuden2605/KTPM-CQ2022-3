"""
DecryptCrawler: triển khai theo Template Method dựa trên BaseNewsCrawler.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from app.crawlers.base_crawler import BaseNewsCrawler
try:
    import feedparser
except Exception:
    feedparser = None

DEFAULT_DECRYPT_CONFIG = {
    "list_url": "https://decrypt.co/feed",
    "url_prefix": "https://decrypt.co",
    "feed_exclude_patterns": ["/videos/"],
    "article": {
        "title_selector": "h1",
        "content_selector": "article, .article-body, div.article-body",
        "date_selector_meta": "article:published_time",
        "author_selector": "meta[name='author']",
        "prefer_rss_date": True
    },
}


class DecryptCrawler(BaseNewsCrawler):
    def __init__(self):
        super().__init__(
            source_code="decrypt",
            base_url="https://decrypt.co",
            default_config=DEFAULT_DECRYPT_CONFIG,
            cache_filename="decrypt_config_cache.json",
        )


if __name__ == "__main__":
    DecryptCrawler().crawl_latest_articles()
