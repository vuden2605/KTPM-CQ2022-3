"""
CointelegraphCrawler: triển khai theo Template Method dựa trên BaseNewsCrawler.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from app.crawlers.base_crawler import BaseNewsCrawler

DEFAULT_COINTELEGRAPH_CONFIG = {
    "list_url": "https://cointelegraph.com/rss",
    "url_prefix": "https://cointelegraph.com",
    "article": {
        "title_selector": "h1.post__title, h1",
        "content_selector": "div.post-content, div.post__content, article.post",
        "date_selector_meta": "article:published_time",
        "author_selector": "a[href*='/author/'], a[href*='/authors/'], meta[name='author']"
    },
}


class CointelegraphCrawler(BaseNewsCrawler):
    def __init__(self):
        super().__init__(
            source_code="cointelegraph",
            base_url="https://cointelegraph.com",
            default_config=DEFAULT_COINTELEGRAPH_CONFIG,
            cache_filename="cointelegraph_config_cache.json",
        )


if __name__ == "__main__":
    CointelegraphCrawler().crawl_latest_articles()
