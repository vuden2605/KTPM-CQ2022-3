"""
Run all news crawlers in one go.

Usage examples:
- Default (run all enabled sources sequentially):
    python -m app.scripts.run_all_crawlers

- Specify sources explicitly (coindesk, cointelegraph, decrypt):
    python -m app.scripts.run_all_crawlers --sources coindesk cointelegraph decrypt

- Run continuously every minute (graceful Ctrl+C to stop):
    python -m app.scripts.run_all_crawlers --watch --interval 60

- Limit to N cycles while watching (useful for testing):
    python -m app.scripts.run_all_crawlers --watch --interval 60 --max-runs 2

Environment flags:
- SKIP_AI_CONFIG=1       # skip AI config generation, use defaults/cache
- ENABLE_RENDERED_FETCH=1 # enable Playwright-rendered HTML (slower)
- OLLAMA_URL, OLLAMA_MODEL # configure local Ollama if using AI config
Env-based scheduling:
- CRAWL_WATCH=1            # enable continuous watch mode
- CRAWL_INTERVAL_SECONDS=60 # interval between runs when watching
"""

import argparse
import os
import time
from dotenv import load_dotenv

from app.crawlers.coindesk_crawler import CoindeskCrawler
from app.crawlers.cointelegraph_crawler import CointelegraphCrawler
from app.crawlers.decrypt import DecryptCrawler
from app.crawlers.cnbc_crawler import CNBCCrawler

AVAILABLE = {
    "coindesk": CoindeskCrawler,
    "cointelegraph": CointelegraphCrawler,
    "decrypt": DecryptCrawler,
    "cnbc": CNBCCrawler,
}


def run_source(code: str) -> None:
    cls = AVAILABLE.get(code)
    if not cls:
        print(f"Unknown source: {code}")
        return
    print(f"\n=== Running crawler: {code} ===")
    try:
        crawler = cls()
        crawler.crawl_latest_articles()
    except Exception as e:
        print(f"[Runner] Crawler '{code}' failed: {e}")


def main():
    # Load .env so env vars like CRAWL_INTERVAL_SECONDS are available
    try:
        load_dotenv()
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Run multiple crawlers")
    parser.add_argument(
        "--sources",
        nargs="*",
        help="List of sources to run (default: all)",
        default=list(AVAILABLE.keys()),
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run continuously at the given interval (default: 60s)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Interval in seconds between runs when using --watch (CLI > env)",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=0,
        help="Maximum number of cycles to run when watching (0 = unlimited)",
    )
    args = parser.parse_args()

    # Print env overview for visibility
    print("Env overview:")
    print("  SKIP_AI_CONFIG:", os.getenv("SKIP_AI_CONFIG", ""))
    print("  ENABLE_RENDERED_FETCH:", os.getenv("ENABLE_RENDERED_FETCH", ""))
    print("  OLLAMA_URL:", os.getenv("OLLAMA_URL", ""))
    print("  OLLAMA_MODEL:", os.getenv("OLLAMA_MODEL", ""))

    # Allow env to toggle watch mode
    env_watch = os.getenv("CRAWL_WATCH", "0") == "1"
    if args.watch or env_watch:
        # Precedence: CLI --interval > env CRAWL_INTERVAL_SECONDS > 60
        interval_env = os.getenv("CRAWL_INTERVAL_SECONDS")
        interval = (
            int(args.interval) if args.interval is not None else
            int(interval_env) if interval_env and interval_env.isdigit() else
            60
        )
        interval = max(1, interval)
        max_runs = int(args.max_runs or 0)
        run_count = 0
        print(f"\nWatching: running every {interval} seconds; max_runs={max_runs or '∞'}")
        try:
            while True:
                start_ts = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n=== Cycle start: {start_ts} ===")
                for src in args.sources:
                    run_source(src)
                run_count += 1
                if max_runs and run_count >= max_runs:
                    print("Reached max runs; exiting watch loop.")
                    break
                print(f"Sleeping {interval}s until next cycle...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nInterrupted by user (Ctrl+C). Exiting.")
    else:
        for src in args.sources:
            run_source(src)


if __name__ == "__main__":
    main()
