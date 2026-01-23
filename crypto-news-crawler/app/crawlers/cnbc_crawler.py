"""
CNBCCrawler: triển khai theo Template Method dựa trên BaseNewsCrawler.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from app.crawlers.base_crawler import BaseNewsCrawler

DEFAULT_CNBC_CONFIG = {
    "list_url": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "url_prefix": "https://www.cnbc.com",
    # Exclude obvious non-article paths if needed
    "feed_exclude_patterns": ["/video/"],
    "article": {
        "title_selector": "h1",
        # CNBC article body commonly renders under ArticleBody-* wrappers
        "content_selector": "div.ArticleBody-articleBody, div.ArticleBody-wrapper, article",
        # Many sites use this; BaseNewsCrawler also tries JSON-LD/time/meta fallbacks
        "date_selector_meta": "article:published_time",
        # CNBC provides author meta name="author"; keep broad fallback
        "author_selector": "meta[name='author']",
        # Prefer feed pubDate when available for better precision
        "prefer_rss_date": True,
        # Additional fallbacks for paragraphs if needed
        "content_paragraph_selectors": [
            "div.ArticleBody-articleBody p",
            "div.ArticleBody-wrapper p",
            "article p",
        ],
        "description_meta_keys": [
            ("name", "description"),
            ("property", "og:description"),
            ("name", "twitter:description"),
        ],
        "title_meta_keys": [
            ("property", "og:title"),
            ("property", "twitter:title"),
            ("name", "parsely-title"),
            ("name", "title"),
        ],
    },
}


class CNBCCrawler(BaseNewsCrawler):
    def __init__(self):
        super().__init__(
            source_code="cnbc",
            base_url="https://www.cnbc.com",
            default_config=DEFAULT_CNBC_CONFIG,
            cache_filename="cnbc_config_cache.json",
        )


if __name__ == "__main__":
    CNBCCrawler().crawl_latest_articles()
