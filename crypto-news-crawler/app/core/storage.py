import os
from dotenv import load_dotenv
# Ensure .env values override any existing process envs to avoid stale vars
load_dotenv(override=True)
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Iterable, Optional

BACKEND = os.getenv("DB_BACKEND", "mongo").lower()

if BACKEND == "mongo":
    # -----------------------
    # MongoDB backend
    # -----------------------
    from pymongo import MongoClient
    from pymongo.errors import DuplicateKeyError

    _MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    _MONGO_DB = os.getenv("MONGO_DB_NAME", "cryptonews")
    _mongo_client = MongoClient(_MONGO_URI)
    _mongo_db = _mongo_client[_MONGO_DB]

    # Ensure indexes (idempotent)
    _mongo_db.get_collection("News").create_index("Url", unique=True)
    _mongo_db.get_collection("NewsSources").create_index("Code", unique=True)

    @contextmanager
    def db_session():
        """Yield Mongo database handle. Connection is managed by client."""
        try:
            yield _mongo_db
        finally:
            # Keep client open for reuse; do not close per operation
            pass

    def get_enabled_sources(db) -> Iterable[dict]:
        return list(db.NewsSources.find({"Enabled": True}))

    def get_source_by_code(db, code: str) -> Optional[SimpleNamespace]:
        doc = db.NewsSources.find_one({"Code": code})
        if not doc:
            return None
        # Return a minimal object with Id for compatibility
        return SimpleNamespace(Id=str(doc.get("_id")), **doc)

    def article_exists(db, url: str) -> bool:
        return db.News.find_one({"Url": url}) is not None

    def save_article(db, source_id: str, article_data: dict) -> Optional[SimpleNamespace]:
        if not article_data.get("Url"):
            return None
        article_data["SourceId"] = source_id
        try:
            res = db.News.insert_one(article_data)
            inserted = db.News.find_one({"_id": res.inserted_id})
            return SimpleNamespace(Id=str(res.inserted_id), **inserted)
        except DuplicateKeyError:
            return None

else:
    # -----------------------
    # SQLAlchemy backend (default)
    # -----------------------
    from sqlalchemy import select

    from ..db import SessionLocal
    from ..models import News, NewsSource

    @contextmanager
    def db_session():
        """Context manager để tránh lỗi DB connection."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def get_enabled_sources(session) -> Iterable[NewsSource]:
        """Lấy tất cả source đang bật."""
        stmt = select(NewsSource).where(NewsSource.Enabled == True)
        return session.scalars(stmt).all()

    def get_source_by_code(session, code: str) -> Optional[NewsSource]:
        """Lấy source theo code (coindesk, cryptonews, ...)."""
        stmt = select(NewsSource).where(NewsSource.Code == code)
        return session.scalar(stmt)

    def article_exists(session, url: str) -> bool:
        """Kiểm tra bài viết đã tồn tại chưa."""
        stmt = select(News.Id).where(News.Url == url)
        return session.execute(stmt).first() is not None

    def save_article(session, source_id: int, article_data: dict) -> Optional[News]:
        """Lưu bài viết vào DB."""
        if not article_data.get("Url"):
            return None
        
        if article_exists(session, article_data["Url"]):
            return None

        article_data["SourceId"] = source_id
        news = News(**article_data)
        session.add(news)
        session.commit()
        session.refresh(news)
        return news
