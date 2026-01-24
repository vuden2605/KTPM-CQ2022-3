"""
services/news_fetcher.py
Fetch TẤT CẢ tin liên quan đến 1 symbol trong N giờ gần đây
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import List, Dict
import os
import json

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://nguyenvanvu060104:cryptonews123456@cluster0.mz66r.mongodb.net/cryptonews?retryWrites=true&w=majority&appName=Cluster0&authSource=admin"
)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "cryptonews")


def fetch_all_news(symbol: str, hours: int = 1) -> List[Dict]:
    """
    Lấy TẤT CẢ tin liên quan đến symbol trong N giờ gần đây
    
    Args:
        symbol: BTCUSDT, ETHUSDT, ...
        hours: Số giờ lấy tin (default: 1)
    
    Returns:
        List of news dicts (KHÔNG LIMIT)
    """
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[MONGO_DB_NAME]
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    symbol_short = symbol.replace('USDT', '').upper()  # BTCUSDT → BTC
    
    try:
        # Query MongoDB (KHÔNG LIMIT - lấy hết)
        cursor = db.News.find({
            'PublishedAt': {'$gte': cutoff}
        }).sort('PublishedAt', -1)
        
        news_list = []
        
        for doc in cursor:
            # Parse ExtraJson
            extra_json = doc.get('ExtraJson', '{}')
            try:
                extra = json.loads(extra_json) if isinstance(extra_json, str) else extra_json
            except:
                extra = {}
            
            symbols = extra.get('symbols', [])
            trading_pairs = extra.get('trading_pairs', [])
            
            # Check if symbol matches
            if any(symbol_short in str(s).upper() for s in symbols + trading_pairs):
                news_list.append({
                    'news_id': str(doc['_id']),
                    'timestamp': doc['PublishedAt'],
                    'title': doc.get('Title', ''),
                    'sentiment_score': float(doc.get('SentimentScore', 0.5)),
                    'sentiment_label': doc.get('SentimentLabel', 'neutral'),
                    'is_breaking': extra.get('isBreaking', False),
                    'breaking_score': float(extra.get('breakingScore', 0))
                })
        
        client.close()
        
        print(f"✓ Fetched {len(news_list)} news for {symbol} in last {hours}h")
        return news_list
    
    except Exception as e:
        print(f"❌ Error fetching news: {e}")
        client.close()
        return []