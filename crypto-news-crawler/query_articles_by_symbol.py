"""
Script mẫu để query bài viết theo symbols đã trích xuất.

Usage:
    python query_articles_by_symbol.py BTC
    python query_articles_by_symbol.py ETH --limit 5
"""

import json
import argparse
from datetime import datetime
from app.core.storage import db_session, BACKEND
from app.models import News


def query_articles_by_symbol(symbol: str, limit: int = 10):
    """Query các bài viết có nhắc đến symbol cụ thể.
    
    Args:
        symbol: Crypto symbol (e.g., BTC, ETH, SOL)
        limit: Số lượng bài viết tối đa
    """
    symbol = symbol.upper()
    print(f"\n{'=' * 60}")
    print(f"Tìm bài viết nhắc đến: {symbol}")
    print(f"{'=' * 60}\n")
    
    with db_session() as db:
        # SQL backend
        if BACKEND == 'sql':
            articles = db.query(News).filter(
                News.ExtraJson.isnot(None)
            ).order_by(News.CollectedAt.desc()).limit(limit * 3).all()
        # Mongo backend
        else:
            articles = list(db.News.find(
                {"ExtraJson": {"$ne": None}}
            ).sort("CollectedAt", -1).limit(limit * 3))
        
        found = []
        for article in articles:
            extra_json = article.ExtraJson if hasattr(article, 'ExtraJson') else article.get('ExtraJson')
            if not extra_json:
                continue
            
            try:
                data = json.loads(extra_json)
                symbols = data.get("symbols", [])
                if symbol in symbols:
                    found.append((article, symbols))
                    if len(found) >= limit:
                        break
            except Exception:
                continue
        
        if not found:
            print(f"Không tìm thấy bài viết nào nhắc đến {symbol}")
            return
        
        print(f"Tìm thấy {len(found)} bài viết:\n")
        
        for i, (article, symbols) in enumerate(found, 1):
            if hasattr(article, 'Title'):
                title = article.Title
                url = article.Url
                published = article.PublishedAt
                collected = article.CollectedAt
                sentiment = article.SentimentLabel
                score = article.SentimentScore
            else:
                title = article.get('Title')
                url = article.get('Url')
                published = article.get('PublishedAt')
                collected = article.get('CollectedAt')
                sentiment = article.get('SentimentLabel')
                score = article.get('SentimentScore')
            
            print(f"{i}. {title}")
            print(f"   URL: {url}")
            print(f"   Published: {published}")
            print(f"   Symbols: {', '.join(symbols)}")
            if sentiment:
                print(f"   Sentiment: {sentiment.upper()} ({score:.2f})")
            print()


def list_all_symbols():
    """Liệt kê tất cả symbols đã được trích xuất từ các bài viết."""
    print(f"\n{'=' * 60}")
    print("Tất cả symbols được tìm thấy trong database")
    print(f"{'=' * 60}\n")
    
    all_symbols = set()
    symbol_counts = {}
    
    with db_session() as db:
        # SQL backend
        if BACKEND == 'sql':
            articles = db.query(News).filter(
                News.ExtraJson.isnot(None)
            ).all()
        # Mongo backend
        else:
            articles = list(db.News.find(
                {"ExtraJson": {"$ne": None}}
            ))
        
        for article in articles:
            extra_json = article.ExtraJson if hasattr(article, 'ExtraJson') else article.get('ExtraJson')
            if not extra_json:
                continue
            
            try:
                data = json.loads(extra_json)
                symbols = data.get("symbols", [])
                for sym in symbols:
                    all_symbols.add(sym)
                    symbol_counts[sym] = symbol_counts.get(sym, 0) + 1
            except Exception:
                continue
    
    if not all_symbols:
        print("Chưa có bài viết nào với symbols được trích xuất.")
        return
    
    # Sắp xếp theo số lần xuất hiện
    sorted_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)
    
    print(f"Tổng số symbols: {len(all_symbols)}\n")
    print(f"{'Symbol':<10} {'Số bài viết':<15}")
    print("-" * 30)
    for sym, count in sorted_symbols:
        print(f"{sym:<10} {count:<15}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query bài viết theo crypto symbol")
    parser.add_argument("symbol", nargs="?", help="Crypto symbol (e.g., BTC, ETH)")
    parser.add_argument("--limit", type=int, default=10, help="Số lượng bài viết tối đa")
    parser.add_argument("--list", action="store_true", help="Liệt kê tất cả symbols")
    
    args = parser.parse_args()
    
    if args.list:
        list_all_symbols()
    elif args.symbol:
        query_articles_by_symbol(args.symbol, args.limit)
    else:
        parser.print_help()
