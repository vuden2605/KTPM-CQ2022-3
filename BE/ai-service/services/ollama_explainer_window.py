"""
services/ollama_explainer_window.py
Generate explanation với LLM (Ollama) - WINDOW-BASED
Dùng TẤT CẢ tin (không cần rank tin quan trọng nhất)
"""

import requests
from typing import List, Dict
from datetime import datetime

# Ollama config
import os

OLLAMA_API = os.getenv("OLLAMA_API", "http://ollama:11434/api/generate")  # ← SỬA: ollama thay vì localhost
MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")  # ← SỬA: gemma3:1b

def generate_explanation_window(
    final_prediction: str,
    final_confidence: float,
    all_news: List[Dict],
    symbol: str,
    horizon: str
) -> str:
    """
    Generate explanation với LLM (Ollama) - WINDOW-BASED
    
    Args:
        final_prediction: 'UP' hoặc 'DOWN'
        final_confidence: 0.0 - 1.0
        all_news: List TẤT CẢ tin (10-100 tin)
        symbol: 'BTCUSDT'
        horizon: '1h' hoặc '24h'
    
    Returns:
        Explanation text (tiếng Việt)
    """
    
    # Build context từ TẤT CẢ tin (hoặc top 15 nếu quá nhiều)
    news_context = f"Có {len(all_news)} tin về {symbol} trong {horizon} gần đây:\n\n"
    
    # Limit to top 15 news (sorted by breaking_score hoặc timestamp)
    news_sorted = sorted(
        all_news,
        key=lambda x: (x.get('breaking_score', 0), x.get('timestamp', datetime.min)),
        reverse=True
    )
    
    top_news = news_sorted[:15]
    
    for i, news in enumerate(top_news, 1):
        # Calculate time ago
        news_time = news.get('timestamp', datetime.utcnow())
        if isinstance(news_time, str):
            try:
                news_time = datetime.fromisoformat(news_time.replace('Z', '+00:00'))
            except:
                news_time = datetime.utcnow()
        
        time_ago = (datetime.utcnow() - news_time).total_seconds() / 60
        time_str = f"{int(time_ago)}m" if time_ago < 60 else f"{time_ago/60:.1f}h"
        
        # Format
        news_context += f"{i}. ({time_str}) {news.get('title', 'N/A')}\n"
        news_context += f"   Sentiment: {news.get('sentiment_score', 0.5):.2f}"
        
        if news.get('is_breaking'):
            news_context += " [BREAKING]"
        
        news_context += "\n\n"
    
    if len(all_news) > 15:
        news_context += f"... và {len(all_news) - 15} tin khác\n\n"
    
    # Build prompt
    prompt = f"""Bạn là chuyên gia phân tích crypto market.

DỰ ĐOÁN: {symbol} sẽ {final_prediction} trong {horizon} tới (confidence: {final_confidence:.0%})

TIN TỨC ({len(all_news)} tin trong {horizon} gần đây):
{news_context}

YÊU CẦU:
Giải thích TẠI SAO {symbol} được dự đoán {final_prediction} dựa trên các tin trên:
- Phân tích 3-4 tin quan trọng nhất (breaking, entities, keywords)
- Nhấn mạnh entities quan trọng (SEC, BlackRock, Fed, ...)
- Giải thích keywords tích cực/tiêu cực (approved, ban, surge, crash, ...)
- Giải thích tác động lên thị trường
- Trả lời bằng TIẾNG VIỆT, 4-6 câu, dễ hiểu

CHỈ TRẢ LỜI PHẦN GIẢI THÍCH, KHÔNG CẦN CHÀO HỎI:"""
    
    try:
        # Call Ollama API
        response = requests.post(
            OLLAMA_API,
            json={
                "model": MODEL,
                "prompt": prompt,
                "temperature": 0.3,
                "stream": False
            },
            timeout=90
        )
        
        response.raise_for_status()
        result = response.json()
        
        explanation = result.get('response', '').strip()
        
        # Fallback nếu empty
        if not explanation:
            explanation = f"{symbol} được dự đoán {final_prediction} dựa trên {len(all_news)} tin gần đây với confidence {final_confidence:.0%}."
        
        return explanation
        
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        
        # Fallback explanation
        return f"{symbol} được dự đoán {final_prediction} trong {horizon} tới (confidence: {final_confidence:.0%}) dựa trên {len(all_news)} tin tức gần đây."