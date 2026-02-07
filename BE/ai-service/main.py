"""
main.py
AI Service API - WINDOW-BASED APPROACH
Predict UP/DOWN cho crypto symbol dựa trên news aggregation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import uvicorn

# Import services
from services.news_fetcher import fetch_all_news
from services.feature_calculator_window import calculate_window_features
from services.predictor import predict
from services.ollama_explainer_window import generate_explanation_window


# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title="Crypto AI Service (Window-based)",
    version="4.0.0",
    description="Predict crypto price movement (UP/DOWN) using window-based news aggregation"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class PredictRequest(BaseModel):
    symbol: str = "BTCUSDT"
    horizon: str = "24h"  # '1h' or '24h'
    hours: int = 1  # Fetch news trong bao nhiêu giờ gần đây


class NewsInfo(BaseModel):
    news_id: str
    timestamp: str
    title: str
    sentiment_score: float
    is_breaking: bool
    content: Optional[str] = ""  # New field for content
    author: Optional[str] = "Unknown" # New field for author


class PredictResponse(BaseModel):
    symbol: str
    horizon: str
    final_prediction: str  # 'UP' or 'DOWN'
    final_confidence: float
    total_news_analyzed: int
    explanation: str
    top_news: List[NewsInfo]
    timestamp: str


class NewsListResponse(BaseModel):
    symbol: str
    hours: int
    total_news: int
    news_list: List[NewsInfo]
    timestamp: str


# ============================================
# HEALTH CHECK
# ============================================

@app.get("/")
async def root():
    return {
        "service": "Crypto AI Service (Window-based)",
        "version": "4.0.0",
        "status": "running",
        "approach": "window-based",
        "endpoints": {
            "predict": "/api/predict",
            "news": "/api/news",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================
# NEWS ENDPOINT
# ============================================

@app.get("/api/news", response_model=NewsListResponse)
def get_news_endpoint(symbol: str = "BTCUSDT", hours: int = 1):
    """
    Lấy danh sách tin tức trong x giờ gần đây
    
    Args:
        symbol: Symbol của crypto (BTCUSDT, ETHUSDT, ...)
        hours: Số giờ lấy tin tức gần đây (default: 1)
    
    Returns:
        NewsListResponse với danh sách tin tức
    """
    try:
        # Validate hours
        if hours < 1:
            raise HTTPException(
                status_code=400,
                detail="hours phải lớn hơn 0"
            )
        
        if hours > 168:  # 1 tuần
            raise HTTPException(
                status_code=400,
                detail="hours không được vượt quá 168 (1 tuần)"
            )
        
        # Fetch news
        print(f"\n[GET NEWS] Fetching news for {symbol} ({hours}h)...")
        news_list = fetch_all_news(symbol, hours)
        
        if not news_list:
            # Nếu không có tin, vẫn trả về response với empty list
            return NewsListResponse(
                symbol=symbol,
                hours=hours,
                total_news=0,
                news_list=[],
                timestamp=datetime.utcnow().isoformat()
            )
        
        # Convert to NewsInfo format
        news_info_list = []
        for news in news_list:
            ts = news.get('timestamp', datetime.utcnow())
            if isinstance(ts, datetime):
                 # Assume UTC if naive, append Z
                 ts_str = ts.isoformat()
                 if not ts.tzinfo and not ts_str.endswith('Z'):
                     ts_str += 'Z'
            else:
                 ts_str = str(news.get('timestamp', ''))

            news_info_list.append(NewsInfo(
                news_id=str(news.get('news_id', '')),
                timestamp=ts_str,
                title=news.get('title', ''),
                sentiment_score=news.get('sentiment_score', 0.5),
                is_breaking=news.get('is_breaking', False),
                content=news.get('content', ''),  # Add content
                author=news.get('author', 'Unknown')
            ))
        
        print(f"✓ Fetched {len(news_info_list)} news for {symbol}")
        
        return NewsListResponse(
            symbol=symbol,
            hours=hours,
            total_news=len(news_info_list),
            news_list=news_info_list,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ Error fetching news: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# ============================================
# MAIN PREDICT ENDPOINT
# ============================================

@app.post("/api/predict", response_model=PredictResponse)
def predict_endpoint(request: PredictRequest):
    """
    Predict crypto price movement (UP/DOWN) - WINDOW-BASED
    
    Flow:
    1. Fetch TẤT CẢ tin trong {hours}h gần đây
    2. Aggregate features từ TẤT CẢ tin → 1 feature set
    3. Predict 1 LẦN → Final prediction (UP/DOWN)
    4. LLM explain với TẤT CẢ tin
    """
    
    try:
        # ===== STEP 1: FETCH ALL NEWS =====
        print(f"\n[STEP 1] Fetching news for {request.symbol} ({request.hours}h)...")
        
        news_list = fetch_all_news(request.symbol, request.hours)
        
        if not news_list or len(news_list) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No news found for {request.symbol} in the last {request.hours}h"
            )
        
        print(f"✓ Fetched {len(news_list)} news")
        
        # ===== STEP 2: AGGREGATE FEATURES FROM ALL NEWS =====
        print(f"\n[STEP 2] Calculating window features from {len(news_list)} news...")
        
        features = calculate_window_features(
            news_list=news_list,
            symbol=request.symbol,
            horizon=request.horizon
        )
        
        print(f"✓ Features calculated: {len(features)} features")
        print(f"  news_count: {features.get('news_count', 0)}")
        print(f"  avg_sentiment: {features.get('avg_sentiment', 0):.2f}")
        print(f"  breaking_count: {features.get('breaking_count', 0)}")
        
        # ===== STEP 3: PREDICT (1 LẦN - CHO ĐỒNG) =====
        print(f"\n[STEP 3] Predicting for {request.symbol} ({request.horizon})...")
        
        prediction_result = predict(features, request.horizon)
        
        final_prediction = prediction_result['prediction']  # 'UP' or 'DOWN'
        final_confidence = prediction_result['confidence']
        
        print(f"✓ Prediction: {final_prediction} ({final_confidence:.2%})")
        
        # ===== STEP 4: GENERATE EXPLANATION (LLM) =====
        print(f"\n[STEP 4] Generating explanation with LLM...")
        
        explanation = generate_explanation_window(
            final_prediction=final_prediction,
            final_confidence=final_confidence,
            all_news=news_list,
            symbol=request.symbol,
            horizon=request.horizon
        )
        
        print(f"✓ Explanation generated ({len(explanation)} chars)")
        
        # ===== STEP 5: PREPARE TOP NEWS FOR RESPONSE =====
        # Sort by breaking_score + timestamp
        news_sorted = sorted(
            news_list,
            key=lambda x: (x.get('breaking_score', 0), x.get('timestamp', datetime.min)),
            reverse=True
        )
        
        top_news = news_sorted[:10]  # Top 10 tin
        
        top_news_info = []
        for news in top_news:
            ts = news.get('timestamp', datetime.utcnow())
            if isinstance(ts, datetime):
                 ts_str = ts.isoformat()
                 if not ts.tzinfo and not ts_str.endswith('Z'):
                     ts_str += 'Z'
            else:
                 ts_str = str(news.get('timestamp', ''))

            top_news_info.append(NewsInfo(
                news_id=str(news.get('news_id', '')),
                timestamp=ts_str,
                title=news.get('title', ''),
                sentiment_score=news.get('sentiment_score', 0.5),
                is_breaking=news.get('is_breaking', False),
                content=news.get('content', ''),  # Add content
                author=news.get('author', 'Unknown')
            ))
        
        # ===== STEP 6: RETURN RESPONSE =====
        response = PredictResponse(
            symbol=request.symbol,
            horizon=request.horizon,
            final_prediction=final_prediction,
            final_confidence=final_confidence,
            total_news_analyzed=len(news_list),
            explanation=explanation,
            top_news=top_news_info,
            timestamp=datetime.utcnow().isoformat()
        )
        
        print(f"\n✅ Prediction completed successfully!")
        print(f"   Symbol: {request.symbol}")
        print(f"   Prediction: {final_prediction} ({final_confidence:.0%})")
        print(f"   News analyzed: {len(news_list)}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 CRYPTO AI SERVICE (WINDOW-BASED) STARTING...")
    print("=" * 70)
    print(f"Approach: Window-based (aggregate news)")
    print(f"Models: model_window_1h.pkl, model_window_24h.pkl")
    print(f"LLM: Ollama (llama3.2:3b)")
    print("=" * 70)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )