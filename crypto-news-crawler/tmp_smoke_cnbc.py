import sys
sys.path.append('c:/Users/ADMIN/Desktop/workspace/Learn/KTPM(T6)/KTPM-CQ2022-3/crypto-news-crawler')
from app.crawlers.cnbc_crawler import CNBCCrawler
c = CNBCCrawler()
cfg = c.get_config()
urls = c.get_urls(cfg)
print('CNBC URLs:', len(urls))
print('Sample:', (urls or [])[:5])
