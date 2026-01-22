import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.crawlers.cointelegraph_crawler import CointelegraphCrawler


def main():
    # Optional: allow rendered fetch to give AI better samples
    os.environ.setdefault("AI_HTML_SAMPLE_LIMIT", "20000")
    c = CointelegraphCrawler()
    cfg = c.get_config()  # This will generate and save cache if missing
    print("Regenerated config for cointelegraph:")
    print(cfg)


if __name__ == "__main__":
    main()
