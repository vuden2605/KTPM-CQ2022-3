"""
Initialize MongoDB database and seed NewsSources for the CryptoNews crawler.

Env vars:
- MONGO_URI (default: mongodb://localhost:27017)
- MONGO_DB_NAME (default: cryptonews)
"""

import os
from dotenv import load_dotenv
from pathlib import Path
DOTENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=DOTENV_PATH, override=True)
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "cryptonews")

SOURCES = [
    {
        "Name": "Decrypt",
        "Code": "decrypt",
        "BaseUrl": "https://decrypt.co",
        "ListUrl": "https://decrypt.co/feed",
        "Enabled": True,
        "Config": {"type": "rss", "frequency": "daily"},
    },
    {
        "Name": "Reuters Crypto",
        "Code": "reuters",
        "BaseUrl": "https://www.reuters.com",
        "ListUrl": "https://www.reuters.com/finance/cryptocurrency/rss",
        "Enabled": True,
        "Config": {"type": "rss", "frequency": "hourly"},
    },
    {
        "Name": "Cointelegraph",
        "Code": "cointelegraph",
        "BaseUrl": "https://cointelegraph.com",
        "ListUrl": "https://cointelegraph.com/rss",
        "Enabled": True,
        "Config": {"type": "rss", "frequency": "hourly"},
    },
    {
        "Name": "Coindesk",
        "Code": "coindesk",
        "BaseUrl": "https://www.coindesk.com",
        "ListUrl": "https://www.coindesk.com/arc/outboundfeeds/rss",
        "Enabled": True,
        "Config": {"type": "rss", "frequency": "weekly"},
    },
    {
        "Name": "CNBC",
        "Code": "cnbc",
        "BaseUrl": "https://www.cnbc.com",
        "ListUrl": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
        "Enabled": True,
        "Config": {"type": "rss", "frequency": "hourly"},
    },
     {
        "Name": "TradingView News",
        "Code": "tradingviewnews",
        "BaseUrl": "https://www.tradingview.com",
        "ListUrl": "https://www.tradingview.com/news/",
        "Enabled": True,
        "Config": {"type": "rss", "frequency": "daily"},
    }
]


def main():
    print("Connecting to:", MONGO_URI.replace(os.getenv("MONGO_URI"), os.getenv("MONGO_URI", "").replace(os.getenv("MONGO_URI"), "")))
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Ensure indexes
    try:
        db.get_collection("News").create_index("Url", unique=True)
        db.get_collection("NewsSources").create_index("Code", unique=True)
    except Exception as e:
        print("Failed to create indexes:", e)
        print("Hints: check credentials (URL-encoded password), IP whitelist, and DB_NAME")
        raise

    # Seed sources (upsert-like behavior)
    for s in SOURCES:
        existing = db.NewsSources.find_one({"Code": s["Code"]})
        if existing:
            # Update basic fields in case they changed
            db.NewsSources.update_one({"_id": existing["_id"]}, {"$set": s})
            print(f"Updated source: {s['Code']}")
        else:
            try:
                db.NewsSources.insert_one(s)
                print(f"Inserted source: {s['Code']}")
            except DuplicateKeyError:
                print(f"Source already exists: {s['Code']}")

    print(f"MongoDB init complete at {MONGO_URI}/{DB_NAME}")


if __name__ == "__main__":
    main()
