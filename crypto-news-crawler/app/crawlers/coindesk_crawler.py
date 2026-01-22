"""
CoindeskCrawler: triển khai theo Template Method dựa trên BaseNewsCrawler.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from app.crawlers.base_crawler import BaseNewsCrawler

DEFAULT_COINDESK_CONFIG = {
    "list_url": "https://www.coindesk.com/arc/outboundfeeds/rss",
    "url_prefix": "https://www.coindesk.com",
    "article": {
        "title_selector": "h1",
        "content_selector": "div.article-paragraphs, div.at-text",
        "date_selector_meta": "article:published_time",
        "author_selector": "meta[name='authors']",
    },
}


class CoindeskCrawler(BaseNewsCrawler):
    def __init__(self):
        super().__init__(
            source_code="coindesk",
            base_url="https://www.coindesk.com",
            default_config=DEFAULT_COINDESK_CONFIG,
            cache_filename="coindesk_config_cache.json",
        )


if __name__ == "__main__":
    CoindeskCrawler().crawl_latest_articles()
