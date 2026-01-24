"""
services/aggregator.py
AGGREGATE TẤT CẢ PREDICTIONS → FINAL PREDICTION
PHƯƠNG PHÁP: CONFIDENCE-WEIGHTED VOTING
"""

from typing import List, Dict

# services/aggregator.py

def aggregate_predictions(analyzed_news: List[Dict]) -> Dict:
    """
    Aggregate predictions → BINARY (UP/DOWN only)
    
    STRATEGY: NEUTRAL được chia đều cho UP và DOWN
    """
    
    up_score = 0.0
    down_score = 0.0
    neutral_score = 0.0
    
    contributing_news = {
        'UP': [],
        'DOWN': [],
        'NEUTRAL': []
    }
    
    for news in analyzed_news:
        prediction = news['prediction']
        confidence = news['confidence']
        importance = news['importance']
        
        weight = confidence * (importance / 100.0)
        
        if prediction == 'UP':
            up_score += weight
            contributing_news['UP'].append({...})
        elif prediction == 'DOWN':
            down_score += weight
            contributing_news['DOWN'].append({...})
        else:  # NEUTRAL
            # ===== CHIA NEUTRAL CHO UP VÀ DOWN =====
            neutral_score += weight
            contributing_news['NEUTRAL'].append({...})
    
    # ===== DISTRIBUTE NEUTRAL =====
    # Option 1: Chia đều (50-50)
    up_score += neutral_score * 0.5
    down_score += neutral_score * 0.5
    
    # Option 2: Chia theo tỷ lệ hiện tại (proportional)
    # if up_score + down_score > 0:
    #     ratio = up_score / (up_score + down_score)
    #     up_score += neutral_score * ratio
    #     down_score += neutral_score * (1 - ratio)
    
    total_score = up_score + down_score
    
    if total_score == 0:
        return {
            'final_prediction': 'UP',  # Default
            'final_confidence': 0.5,
            'breakdown': {...}
        }
    
    # ===== BINARY DECISION: UP vs DOWN =====
    if up_score > down_score:
        final_prediction = 'UP'
        final_confidence = up_score / total_score
    else:
        final_prediction = 'DOWN'
        final_confidence = down_score / total_score
    
    return {
        'final_prediction': final_prediction,
        'final_confidence': final_confidence,
        'breakdown': {
            'up_score': round(up_score, 2),
            'down_score': round(down_score, 2),
            'neutral_score_distributed': round(neutral_score, 2),  # Đã chia
            'total': round(total_score, 2)
        },
        'contributing_news': contributing_news
    }