"""
services/ollama_explainer.py
Dùng Ollama (local LLM) để tạo explanation
"""

import requests
from typing import Dict, Optional

OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "gemma3:1b"


def generate_explanation(
    final_prediction: str,
    final_confidence: float,
    most_important_news: Dict,
    breakdown: Dict,
    top_5_news: list,
    symbol: str,
    horizon: str
) -> Optional[str]:
    """Dùng Ollama LLM để tạo explanation CHI TIẾT"""
    
    title = most_important_news['title']
    time_ago = most_important_news['time_ago_minutes']
    time_str = f"{int(time_ago)} phút trước" if time_ago < 60 else f"{time_ago/60:.1f} giờ trước"
    
    entities = most_important_news['entities']
    keywords = most_important_news['keywords']
    
    # Top 5 context
    context = f"Có {len(top_5_news)} tin quan trọng về {symbol}:\n"
    for i, news in enumerate(top_5_news[:5], 1):
        t = news['time_ago_minutes']
        t_str = f"{int(t)}m" if t < 60 else f"{t/60:.1f}h"
        context += f"{i}. ({t_str}) {news['title'][:50]}... → {news['prediction']} ({news['confidence']:.0%})\n"
    
    # Breakdown
    breakdown_text = f"""Score tổng hợp:
- UP: {breakdown['up_score']} điểm
- DOWN: {breakdown['down_score']} điểm
→ {final_prediction} chiếm {final_confidence:.0%}"""
    
    # Tùy horizon
    if horizon == '24h':
        time_context = "24 giờ tới"
        explanation_focus = "tác động trung hạn (institutional flows, regulatory impact, market sentiment shift)"
    else:
        time_context = "1 giờ tới"
        explanation_focus = "tác động ngay lập tức (immediate reaction, trader sentiment, order book pressure)"
    
    prompt = f"""Bạn là chuyên gia phân tích crypto market. Dựa vào các tin tức sau, hãy giải thích TẠI SAO {symbol} được dự đoán sẽ {final_prediction} trong {time_context}:

TIN QUAN TRỌNG NHẤT ({time_str}):
"{title}"

THÔNG TIN:
- Entities: {', '.join(entities['cryptos'] + entities['orgs'] + entities['people'])}
- Keywords tích cực: {', '.join(keywords['positive'][:3]) if keywords['positive'] else 'không có'}
- Keywords tiêu cực: {', '.join(keywords['negative'][:3]) if keywords['negative'] else 'không có'}

BỐI CẢNH CÁC TIN KHÁC:
{context}

KẾT QUẢ TỔNG HỢP:
{breakdown_text}

YÊU CẦU:
1. Giải thích NGẮN GỌN (3-4 câu) tại sao tin này khiến {symbol} {final_prediction} trong {time_context}
2. Nhấn mạnh {explanation_focus}
3. Nhấn mạnh entities quan trọng (SEC, BlackRock, Trump, ...)
4. Đề cập đến các tin khác nếu chúng hỗ trợ hoặc mâu thuẫn
5. Trả lời bằng TIẾNG VIỆT, KHÔNG markdown

CHỈ TRẢ LỜI PHẦN GIẢI THÍCH:"""
    
    try:
        response = requests.post(
            OLLAMA_API,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 250
                }
            },
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        explanation = result.get('response', '').strip()
        explanation = explanation.replace('**', '').replace('*', '')
        explanation = ' '.join(explanation.split())
        
        return explanation
        
    except Exception as e:
        print(f"❌ Ollama error: {e}")
        return None