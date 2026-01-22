"""
app/api/main_api.py

FastAPI application for serving news, prices, analysis, and user management.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from pathlib import Path
from bson import ObjectId

from app.core.storage import db_session
from app.core.storage import BACKEND as STORAGE_BACKEND
from app.services.sentiment_analyzer import analyze_news_sentiment, batch_analyze_sentiment
# TODO: from app.services.binance_service import get_binance_service
# TODO: from app.services.ai_service import get_ai_service

app = FastAPI(
    title="CryptoNews API",
    description="Crypto news aggregation, price tracking, and AI analysis",
    version="1.0.0"
)

# Setup static files
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Create directories if they don't exist
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ============ Schemas ============

class NewsItemSchema(BaseModel):
    id: str
    source: str
    title: str
    content: str
    published_at: Optional[datetime]
    url: str
    language: str
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    
    class Config:
        from_attributes = True


class NewsSourceSchema(BaseModel):
    id: int
    name: str
    base_url: str
    enabled: bool


class PriceSchema(BaseModel):
    symbol: str
    price: float
    change_24h: float
    volume_24h: float


class AnalysisResultSchema(BaseModel):
    symbol: str
    sentiment_score: float
    recent_news_count: int
    price_impact_prediction: str
    summary: Optional[str]


# ============ Endpoints ============

@app.get("/")
def read_root():
    """Serve the main HTML page"""
    return FileResponse(str(TEMPLATES_DIR / "index.html"), media_type="text/html")


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ============ News Endpoints ============

@app.get("/api/news", response_model=List[NewsItemSchema])
def get_news(
    source: Optional[str] = None,
    sentiment: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
):
    """Fetch latest news articles with sentiment analysis from database.
    
    Query params:
    - source: Filter by source name (coindesk, cointelegraph, decrypt, reuters, ...)
    - sentiment: Filter by sentiment (positive, negative, neutral)
    - search: Search in title, content, summary
    - limit: Max results (default 10)
    - offset: Pagination offset (default 0)
    """
    # MongoDB path
    if STORAGE_BACKEND == "mongo":
        try:
            with db_session() as db:
                filt = {}
                # Filter by source code (match News.SourceId via NewsSources.Code)
                if source:
                    src_docs = list(db.NewsSources.find({"Code": {"$regex": source, "$options": "i"}}))
                    if src_docs:
                        src_ids = [str(s["_id"]) for s in src_docs]
                        filt["SourceId"] = {"$in": src_ids}
                    else:
                        return []
                # Filter by sentiment
                if sentiment:
                    filt["SentimentLabel"] = {"$regex": sentiment, "$options": "i"}
                # Search
                if search:
                    regex = {"$regex": search, "$options": "i"}
                    filt["$or"] = [{"Title": regex}, {"Content": regex}, {"Summary": regex}]

                cursor = db.News.find(filt).sort("PublishedAt", -1).skip(offset).limit(limit)
                articles = list(cursor)

                # Build source map to avoid N lookups
                source_ids = list({a.get("SourceId") for a in articles if a.get("SourceId")})
                src_map = {}
                if source_ids:
                    obj_ids = []
                    for i in source_ids:
                        try:
                            obj_ids.append(ObjectId(i))
                        except Exception:
                            # Skip non-ObjectId strings
                            pass
                    if obj_ids:
                        src_docs = list(db.NewsSources.find({"_id": {"$in": obj_ids}}))
                        src_map = {str(s["_id"]): s for s in src_docs}

                news_list = []
                for a in articles:
                    src_doc = src_map.get(a.get("SourceId"))
                    source_name = (src_doc or {}).get("Code", "unknown")
                    sentiment_score = a.get("SentimentScore")
                    sentiment_label = a.get("SentimentLabel")

                    # If sentiment missing, compute without updating DB (to keep read-only)
                    if sentiment_label is None:
                        sres = analyze_news_sentiment(
                            title=a.get("Title") or "",
                            content=a.get("Content") or "",
                            summary=a.get("Summary") or ""
                        )
                        sentiment_score = sres["score"]
                        sentiment_label = sres["label"]

                    news_list.append({
                        "id": str(a.get("_id")),
                        "source": source_name,
                        "title": a.get("Title") or "",
                        "content": a.get("Content") or "",
                        "summary": a.get("Summary") or "",
                        "published_at": a.get("PublishedAt"),
                        "url": a.get("Url"),
                        "language": a.get("Language") or "en",
                        "author": a.get("Author") or "",
                        "sentiment_score": sentiment_score or 0.5,
                        "sentiment_label": sentiment_label or "neutral",
                    })
                return news_list
        except Exception as e:
            print(f"Error fetching news (mongo): {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")

    # SQLAlchemy path (legacy)
    from app.db import SessionLocal
    from app.models import News, NewsSource
    db = SessionLocal()
    try:
        query = db.query(News).order_by(News.PublishedAt.desc())
        if source:
            query = query.join(NewsSource).filter(NewsSource.Code.ilike(f"%{source}%"))
        if sentiment:
            query = query.filter(News.SentimentLabel.ilike(f"%{sentiment}%"))
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (News.Title.ilike(search_term)) |
                (News.Content.ilike(search_term)) |
                (News.Summary.ilike(search_term))
            )
        articles = query.offset(offset).limit(limit).all()
        news_list = []
        for article in articles:
            source_name = article.source_ref.Code if article.source_ref else "unknown"
            if not article.SentimentLabel:
                sentiment_res = analyze_news_sentiment(
                    title=article.Title or "",
                    content=article.Content or "",
                    summary=article.Summary or ""
                )
                article.SentimentScore = sentiment_res["score"]
                article.SentimentLabel = sentiment_res["label"]
                article.SentimentModel = "VADER"
                db.commit()
            news_list.append({
                "id": article.Id,
                "source": source_name,
                "title": article.Title or "",
                "content": article.Content or "",
                "summary": article.Summary or "",
                "published_at": article.PublishedAt,
                "url": article.Url,
                "language": article.Language,
                "author": article.Author or "",
                "sentiment_score": article.SentimentScore or 0.5,
                "sentiment_label": article.SentimentLabel or "neutral",
            })
        return news_list
    except Exception as e:
        print(f"Error fetching news (sql): {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")
    finally:
        db.close()


@app.get("/api/news/count")
def get_news_count(
    source: Optional[str] = None,
    sentiment: Optional[str] = None,
    search: Optional[str] = None
):
    """Get total count of news articles with filters."""
    if STORAGE_BACKEND == "mongo":
        try:
            with db_session() as db:
                filt = {}
                if source:
                    src_docs = list(db.NewsSources.find({"Code": {"$regex": source, "$options": "i"}}))
                    if src_docs:
                        src_ids = [str(s["_id"]) for s in src_docs]
                        filt["SourceId"] = {"$in": src_ids}
                    else:
                        return {"total": 0}
                if sentiment:
                    filt["SentimentLabel"] = {"$regex": sentiment, "$options": "i"}
                if search:
                    regex = {"$regex": search, "$options": "i"}
                    filt["$or"] = [{"Title": regex}, {"Content": regex}, {"Summary": regex}]
                total = db.News.count_documents(filt)
                return {"total": total}
        except Exception as e:
            print(f"Error counting news (mongo): {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error counting news: {str(e)}")

    from app.db import SessionLocal
    from app.models import News, NewsSource
    db = SessionLocal()
    try:
        query = db.query(News)
        if source:
            query = query.join(NewsSource).filter(NewsSource.Code.ilike(f"%{source}%"))
        if sentiment:
            query = query.filter(News.SentimentLabel.ilike(f"%{sentiment}%"))
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (News.Title.ilike(search_term)) |
                (News.Content.ilike(search_term)) |
                (News.Summary.ilike(search_term))
            )
        total = query.count()
        return {"total": total}
    except Exception as e:
        print(f"Error counting news (sql): {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error counting news: {str(e)}")
    finally:
        db.close()


@app.get("/api/news/{news_id}", response_model=NewsItemSchema)
def get_news_detail(news_id: str):
    """Fetch a single news article by ID."""
    # TODO: Implement
    pass


@app.get("/api/news/search")
def search_news(q: str, limit: int = 20):
    """Full-text search in news content and titles."""
    # TODO: Implement with SQL LIKE or FTS
    pass


@app.get("/api/sources", response_model=List[NewsSourceSchema])
def get_sources():
    """Get list of configured news sources."""
    # TODO: Implement
    pass


# ============ Price Endpoints ============

@app.get("/api/prices/{symbol}", response_model=PriceSchema)
def get_price(symbol: str):
    """Get current price for a symbol (BTC, ETH, DOGE, ...).
    
    symbol: Crypto symbol (case-insensitive)
    """
    # TODO: Implement Binance API call
    # binance = get_binance_service()
    # price = binance.get_ticker_price(symbol.upper() + "USDT")
    pass


@app.get("/api/prices/{symbol}/history")
def get_price_history(
    symbol: str,
    interval: str = "1h",
    limit: int = 100,
):
    """Get historical candles for a symbol.
    
    Args:
    - symbol: Crypto symbol
    - interval: Candle interval (1m, 5m, 1h, 1d, ...)
    - limit: Number of candles
    """
    # TODO: Implement
    pass


# ============ Analysis Endpoints ============

@app.get("/api/analysis/{symbol}", response_model=AnalysisResultSchema)
def get_analysis(symbol: str):
    """Get AI analysis for a crypto symbol.
    
    Includes: sentiment from recent news, price impact prediction, etc.
    """
    # TODO: Implement
    # 1. Fetch recent news for symbol
    # 2. Run sentiment analysis on each
    # 3. Call AI service for impact prediction
    # 4. Fetch current price and 24h changes
    # 5. Return aggregated result
    pass


# ============ Health & Admin ============

@app.post("/api/admin/crawl")
def trigger_crawl():
    """Manually trigger a crawler run (admin only)."""
    # TODO: Add auth check
    # TODO: from app.crawler_runner import run_all_sources
    # run_all_sources()
    return {"message": "Crawl triggered"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
