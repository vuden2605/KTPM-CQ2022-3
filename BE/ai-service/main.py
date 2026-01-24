"""
main.py
FastAPI service - AI Prediction với FULL LOGIC
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import os

from services.news_fetcher import fetch_all_news
from services.feature_calculator import calculate_features_realtime
from services.predictor import predict
from services.entity_extractor import extract_entities, extract_keywords
from services.importance_calculator import calculate_importance
from services.aggregator import aggregate_predictions
from services.ollama_explainer import generate_explanation

# ============================================
# APP INITIALIZATION
# ============================================

app = FastAPI(
    title="Crypto News AI Prediction Service v3.0",
    description="Dự đoán UP/DOWN/NEUTRAL dựa trên TẤT CẢ tin tức + LLM explanation",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("\n" + "=" * 70)
print("🚀 AI PREDICTION SERVICE V3.0 - FULL REWRITE")
print("=" * 70)
print(f"Allowed origins: {ALLOWED_ORIGINS}")
print("=" * 70 + "\n")

# ============================================
# SCHEMAS
# ============================================

class PredictRequest(BaseModel):
    symbol: str = "BTCUSDT"
    horizon: str = "1h"  # "1h" hoặc "24h"
    hours: int = 1  # Lấy tin trong N giờ gần đây


class NewsInfo(BaseModel):
    news_id: str
    title: str
    time_ago_minutes: float
    prediction: str
    confidence: float
    importance: float
    entities: Dict[str, List[str]]
    keywords: Dict[str, List[str]]
    is_breaking: bool
    sentiment_score: float


class PredictResponse(BaseModel):
    symbol: str
    horizon: str
    final_prediction: str
    final_confidence: float
    total_news_analyzed: int
    most_important_news: NewsInfo
    explanation: str
    breakdown: Dict
    top_5_news: List[NewsInfo]
    timestamp: datetime


# ============================================
# MAIN PREDICTION ENDPOINT
# ============================================

@app.post("/api/predict", response_model=PredictResponse)
async def predict_endpoint(request: PredictRequest):
    """
    Dự đoán UP/DOWN/NEUTRAL dựa trên TẤT CẢ tin tức
    
    FLOW:
    1. Fetch TẤT CẢ tin liên quan (không limit)
    2. Predict TỪNG tin (features + model)
    3. Aggregate predictions (confidence-weighted voting)
    4. Tìm tin quan trọng nhất
    5. Generate explanation (Ollama LLM)
    6. Return result
    
    Example Request:
    {
      "symbol": "BTCUSDT",
      "horizon": "1h",
      "hours": 1
    }
    
    Example Request (24h):
    {
      "symbol": "BTCUSDT",
      "horizon": "24h",
      "hours": 24
    }
    """
    
    # Validate
    if request.horizon not in ["1h", "24h"]:
        raise HTTPException(
            status_code=400,
            detail="horizon must be '1h' or '24h'"
        )
    
    if request.hours < 1 or request.hours > 48:
        raise HTTPException(
            status_code=400,
            detail="hours must be between 1 and 48"
        )
    
    try:
        print(f"\n{'='*70}")
        print(f"📊 PREDICTING {request.symbol} ({request.horizon})")
        print(f"{'='*70}\n")
        
        # ============================================
        # STEP 1: FETCH TẤT CẢ TIN
        # ============================================
        print(f"[1/6] Fetching ALL news for {request.symbol} in last {request.hours}h...")
        
        news_list = fetch_all_news(request.symbol, request.hours)
        
        if not news_list:
            raise HTTPException(
                status_code=404,
                detail=f"No news found for {request.symbol} in the last {request.hours} hour(s)"
            )
        
        print(f"      ✓ Found {len(news_list)} news articles\n")
        
        # ============================================
        # STEP 2: PREDICT TỪNG TIN
        # ============================================
        print(f"[2/6] Predicting each news article...")
        
        analyzed_news = []
        
        for i, news in enumerate(news_list, 1):
            if i % 10 == 0 or i == len(news_list):
                print(f"      Processing {i}/{len(news_list)}...")
            
            # Extract entities & keywords
            title = news['title']
            entities = extract_entities(title)
            keywords = extract_keywords(title)
            
            # Calculate features (REALTIME - với horizon)
            features = calculate_features_realtime(news, request.symbol, request.horizon)
            
            # Predict
            prediction_result = predict(features, request.horizon)
            
            if not prediction_result:
                continue
            
            # Calculate importance
            time_ago = (datetime.utcnow() - news['timestamp']).total_seconds() / 60
            importance = calculate_importance(
                news, entities, keywords, prediction_result, time_ago
            )
            
            analyzed_news.append({
                'news_id': news['news_id'],
                'title': title,
                'timestamp': news['timestamp'].isoformat(),
                'time_ago_minutes': time_ago,
                'prediction': prediction_result['prediction'],
                'confidence': prediction_result['confidence'],
                'probabilities': prediction_result['probabilities'],
                'entities': entities,
                'keywords': keywords,
                'importance': importance,
                'is_breaking': news.get('is_breaking', False),
                'sentiment_score': news.get('sentiment_score', 0.5)
            })
        
        if not analyzed_news:
            raise HTTPException(
                status_code=500,
                detail="Failed to analyze any news (all predictions failed)"
            )
        
        print(f"      ✓ Successfully analyzed {len(analyzed_news)} news\n")
        
        # ============================================
        # STEP 3: AGGREGATE PREDICTIONS
        # ============================================
        print(f"[3/6] Aggregating predictions (confidence-weighted voting)...")
        
        aggregation_result = aggregate_predictions(analyzed_news)
        
        if not aggregation_result:
            raise HTTPException(
                status_code=500,
                detail="Failed to aggregate predictions"
            )
        
        final_prediction = aggregation_result['final_prediction']
        final_confidence = aggregation_result['final_confidence']
        breakdown = aggregation_result['breakdown']
        
        print(f"      ✓ Final prediction: {final_prediction} ({final_confidence:.1%})")
        print(f"      Breakdown: UP={breakdown['up_score']:.1f}, DOWN={breakdown['down_score']:.1f}")
        
        # ============================================
        # STEP 4: TÌM TIN QUAN TRỌNG NHẤT
        # ============================================
        print(f"[4/6] Finding most important news...")
        
        analyzed_news_sorted = sorted(analyzed_news, key=lambda x: x['importance'], reverse=True)
        most_important = analyzed_news_sorted[0]
        top_5 = analyzed_news_sorted[:5]
        
        print(f"      ✓ Most important: \"{most_important['title'][:60]}...\" (importance={most_important['importance']:.1f})\n")
        
        # ============================================
        # STEP 5: GENERATE EXPLANATION (OLLAMA)
        # ============================================
        print(f"[5/6] Generating explanation (Ollama LLM)...")
        
        explanation = generate_explanation(
            final_prediction=final_prediction,
            final_confidence=final_confidence,
            most_important_news=most_important,
            breakdown=breakdown,
            top_5_news=top_5,
            symbol=request.symbol,
            horizon=request.horizon
        )
        
        if not explanation:
            # Fallback to simple explanation
            time_ago = most_important['time_ago_minutes']
            time_str = f"{int(time_ago)} phút trước" if time_ago < 60 else f"{time_ago/60:.1f} giờ trước"
            
            explanation = f"""Dựa trên {len(analyzed_news)} tin trong {request.hours}h gần đây, {request.symbol} được dự đoán {final_prediction} với confidence {final_confidence:.0%}. 

Tin quan trọng nhất ({time_str}): "{most_important['title']}"

Score tổng hợp: UP={breakdown['up_score']:.1f}, DOWN={breakdown['down_score']:.1f}"""
        
        print(f"      ✓ Explanation generated\n")
        
        # ============================================
        # STEP 6: BUILD RESPONSE
        # ============================================
        print(f"[6/6] Building response...\n")
        
        response = PredictResponse(
            symbol=request.symbol,
            horizon=request.horizon,
            final_prediction=final_prediction,
            final_confidence=final_confidence,
            total_news_analyzed=len(analyzed_news),
            most_important_news=NewsInfo(**most_important),
            explanation=explanation,
            breakdown=breakdown,
            top_5_news=[NewsInfo(**news) for news in top_5],
            timestamp=datetime.utcnow()
        )
        
        print(f"{'='*70}")
        print(f"✅ PREDICTION COMPLETED")
        print(f"   Symbol: {request.symbol}")
        print(f"   Horizon: {request.horizon}")
        print(f"   Prediction: {final_prediction} ({final_confidence:.1%})")
        print(f"   News analyzed: {len(analyzed_news)}")
        print(f"{'='*70}\n")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================

@app.get("/")
def root():
    """Root endpoint - service info"""
    return {
        "service": "AI Prediction Service v3.0",
        "status": "running",
        "description": "Phân tích TẤT CẢ tin tức + Aggregate predictions + LLM explanation",
        "features": [
            "✅ Fetch ALL news (không limit)",
            "✅ Predict từng tin với ML model",
            "✅ Confidence-weighted voting",
            "✅ Importance ranking",
            "✅ LLM explanation (Ollama)",
            "✅ Hỗ trợ 1h & 24h horizon"
        ],
        "models": [
            "model_1h.pkl (accuracy ~65-70%)",
            "model_24h.pkl (accuracy ~78-83%)"
        ],
        "endpoints": [
            "GET / - Service info",
            "GET /health - Health check",
            "POST /api/predict - Main prediction endpoint",
            "GET /docs - API documentation"
        ]
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    from services.predictor import models
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "models_loaded": {
            "1h": models.get('1h') is not None,
            "24h": models.get('24h') is not None
        }
    }


# ============================================
# STARTUP/SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    print("\n✅ AI Service v3.0 started successfully!")
    print(f"📡 Listening on port {os.getenv('PORT', 8003)}")
    print(f"📚 API docs: http://localhost:{os.getenv('PORT', 8003)}/docs")
    print(f"🔍 Health check: http://localhost:{os.getenv('PORT', 8003)}/health\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    print("\n🛑 AI Service shutting down...")


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8003))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )