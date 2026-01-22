"""
Script để re-crawl một bài viết cụ thể và update symbols vào DB.

Usage:
    python recrawl_with_symbols.py <article_id>
    python recrawl_with_symbols.py --update-all --limit 100
"""

import json
import argparse
from app.core.storage import db_session, BACKEND
from app.models import News
from app.services.symbol_extractor import extract_symbols_from_article


def update_article_symbols(article_id: str):
    """Update symbols cho một bài viết cụ thể."""
    print(f"\nUpdating symbols for article: {article_id}")
    print("=" * 60)
    
    with db_session() as db:
        # SQL backend
        if BACKEND == 'sql':
            article = db.query(News).filter(News.Id == article_id).first()
            if not article:
                print(f"❌ Không tìm thấy bài viết với ID: {article_id}")
                return False
            
            # Extract symbols
            symbols = extract_symbols_from_article(
                title=article.Title or "",
                content=article.Content or "",
                max_results=10
            )
            
            print(f"📰 Title: {article.Title[:80]}...")
            print(f"🔗 URL: {article.Url}")
            print(f"💰 Symbols found: {symbols if symbols else 'None'}")
            
            if symbols:
                article.ExtraJson = json.dumps({"symbols": symbols}, ensure_ascii=False)
                db.commit()
                print("✅ Updated successfully!")
                return True
            else:
                print("⚠️  No symbols found in this article")
                return False
        
        # Mongo backend
        else:
            from bson.objectid import ObjectId
            article = db.News.find_one({"_id": ObjectId(article_id)})
            if not article:
                print(f"❌ Không tìm thấy bài viết với ID: {article_id}")
                return False
            
            # Extract symbols
            symbols = extract_symbols_from_article(
                title=article.get("Title") or "",
                content=article.get("Content") or "",
                max_results=10
            )
            
            print(f"📰 Title: {article.get('Title', '')[:80]}...")
            print(f"🔗 URL: {article.get('Url')}")
            print(f"💰 Symbols found: {symbols if symbols else 'None'}")
            
            if symbols:
                db.News.update_one(
                    {"_id": ObjectId(article_id)},
                    {"$set": {"ExtraJson": json.dumps({"symbols": symbols}, ensure_ascii=False)}}
                )
                print("✅ Updated successfully!")
                return True
            else:
                print("⚠️  No symbols found in this article")
                return False


def update_all_articles(limit: int = 100):
    """Update symbols cho tất cả bài viết chưa có ExtraJson."""
    print(f"\nUpdating symbols for all articles (limit: {limit})")
    print("=" * 60)
    
    updated = 0
    skipped = 0
    no_symbols = 0
    
    with db_session() as db:
        # SQL backend
        if BACKEND == 'sql':
            articles = db.query(News).filter(
                (News.ExtraJson.is_(None)) | (News.ExtraJson == "")
            ).limit(limit).all()
            
            print(f"Found {len(articles)} articles to process\n")
            
            for i, article in enumerate(articles, 1):
                print(f"\n[{i}/{len(articles)}] Processing: {article.Title[:60]}...")
                
                symbols = extract_symbols_from_article(
                    title=article.Title or "",
                    content=article.Content or "",
                    max_results=10
                )
                
                if symbols:
                    article.ExtraJson = json.dumps({"symbols": symbols}, ensure_ascii=False)
                    db.commit()
                    print(f"   ✅ Symbols: {', '.join(symbols)}")
                    updated += 1
                else:
                    print(f"   ⚠️  No symbols found")
                    no_symbols += 1
        
        # Mongo backend
        else:
            articles = list(db.News.find({
                "$or": [
                    {"ExtraJson": {"$exists": False}},
                    {"ExtraJson": None},
                    {"ExtraJson": ""}
                ]
            }).limit(limit))
            
            print(f"Found {len(articles)} articles to process\n")
            
            for i, article in enumerate(articles, 1):
                print(f"\n[{i}/{len(articles)}] Processing: {article.get('Title', '')[:60]}...")
                
                symbols = extract_symbols_from_article(
                    title=article.get("Title") or "",
                    content=article.get("Content") or "",
                    max_results=10
                )
                
                if symbols:
                    db.News.update_one(
                        {"_id": article["_id"]},
                        {"$set": {"ExtraJson": json.dumps({"symbols": symbols}, ensure_ascii=False)}}
                    )
                    print(f"   ✅ Symbols: {', '.join(symbols)}")
                    updated += 1
                else:
                    print(f"   ⚠️  No symbols found")
                    no_symbols += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Summary:")
    print(f"   ✅ Updated with symbols: {updated}")
    print(f"   ⚠️  No symbols found: {no_symbols}")
    print(f"   📝 Total processed: {updated + no_symbols}")
    print("=" * 60)


def show_article_detail(article_id: str):
    """Hiển thị chi tiết bài viết để check symbols."""
    with db_session() as db:
        # SQL backend
        if BACKEND == 'sql':
            article = db.query(News).filter(News.Id == article_id).first()
            if not article:
                print(f"❌ Không tìm thấy bài viết với ID: {article_id}")
                return
            
            print("\n" + "=" * 60)
            print("📰 ARTICLE DETAILS")
            print("=" * 60)
            print(f"ID: {article.Id}")
            print(f"Title: {article.Title}")
            print(f"URL: {article.Url}")
            print(f"Published: {article.PublishedAt}")
            print(f"Sentiment: {article.SentimentLabel} ({article.SentimentScore:.2f})")
            
            if article.ExtraJson:
                try:
                    data = json.loads(article.ExtraJson)
                    symbols = data.get("symbols", [])
                    print(f"💰 Symbols: {', '.join(symbols) if symbols else 'None'}")
                except:
                    print(f"ExtraJson: {article.ExtraJson}")
            else:
                print("💰 Symbols: Not extracted yet")
            
            print(f"\nContent preview:")
            print(f"{article.Content[:500]}...")
        
        # Mongo backend
        else:
            from bson.objectid import ObjectId
            article = db.News.find_one({"_id": ObjectId(article_id)})
            if not article:
                print(f"❌ Không tìm thấy bài viết với ID: {article_id}")
                return
            
            print("\n" + "=" * 60)
            print("📰 ARTICLE DETAILS")
            print("=" * 60)
            print(f"ID: {article['_id']}")
            print(f"Title: {article.get('Title')}")
            print(f"URL: {article.get('Url')}")
            print(f"Published: {article.get('PublishedAt')}")
            print(f"Sentiment: {article.get('SentimentLabel')} ({article.get('SentimentScore', 0):.2f})")
            
            if article.get('ExtraJson'):
                try:
                    data = json.loads(article['ExtraJson'])
                    symbols = data.get("symbols", [])
                    print(f"💰 Symbols: {', '.join(symbols) if symbols else 'None'}")
                except:
                    print(f"ExtraJson: {article.get('ExtraJson')}")
            else:
                print("💰 Symbols: Not extracted yet")
            
            print(f"\nContent preview:")
            print(f"{article.get('Content', '')[:500]}...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-crawl và update symbols cho bài viết")
    parser.add_argument("article_id", nargs="?", help="ID của bài viết cần update")
    parser.add_argument("--update-all", action="store_true", help="Update tất cả bài viết")
    parser.add_argument("--limit", type=int, default=100, help="Số lượng bài viết tối đa khi update all")
    parser.add_argument("--show", action="store_true", help="Hiển thị chi tiết bài viết")
    
    args = parser.parse_args()
    
    if args.update_all:
        update_all_articles(args.limit)
    elif args.article_id:
        if args.show:
            show_article_detail(args.article_id)
        else:
            update_article_symbols(args.article_id)
    else:
        parser.print_help()
        print("\n💡 Ví dụ:")
        print("   python recrawl_with_symbols.py 69708a96e04d403664dcf309")
        print("   python recrawl_with_symbols.py 69708a96e04d403664dcf309 --show")
        print("   python recrawl_with_symbols.py --update-all --limit 50")
