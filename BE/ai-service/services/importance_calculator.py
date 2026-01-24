"""
services/importance_calculator.py
Tính importance score cho 1 tin (để rank)
"""

from typing import Dict


def calculate_importance(
    news: Dict, 
    entities: Dict, 
    keywords: Dict, 
    prediction_result: Dict,
    time_ago_minutes: float
) -> float:
    """
    Tính importance score (0-100)
    
    CÔNG THỨC:
      importance = confidence_weight (30%) 
                 + breaking_weight (30%)
                 + entity_weight (25%)
                 + keyword_weight (15%)
                 - time_decay_penalty
    """
    score = 0
    
    # === FACTOR 1: CONFIDENCE (30 points) ===
    confidence = prediction_result['confidence']
    score += confidence * 30
    
    # === FACTOR 2: BREAKING NEWS (30 points) ===
    if news.get('is_breaking'):
        score += 30
    elif news.get('breaking_score', 0) > 0.5:
        score += news['breaking_score'] * 20
    
    # === FACTOR 3: IMPORTANT ENTITIES (25 points) ===
    if 'sec' in entities['orgs'] or 'fed' in entities['orgs']:
        score += 25
    elif any(org in entities['orgs'] for org in ['blackrock', 'fidelity', 'grayscale']):
        score += 20
    elif any(org in entities['orgs'] for org in ['coinbase', 'microstrategy', 'tesla']):
        score += 15
    
    if 'elon_musk' in entities['people'] or 'trump' in entities['people']:
        score += 10
    elif 'gensler' in entities['people'] or 'powell' in entities['people']:
        score += 5
    
    # === FACTOR 4: STRONG KEYWORDS (15 points) ===
    strong_positive = ['approved', 'approval', 'etf approved', 'breakthrough', 'adoption']
    strong_negative = ['ban', 'banned', 'lawsuit', 'hack', 'crash', 'fraud']
    
    if any(kw in keywords['positive'] for kw in strong_positive):
        score += 15
    elif any(kw in keywords['negative'] for kw in strong_negative):
        score += 15
    elif len(keywords['positive']) > 0 or len(keywords['negative']) > 0:
        score += 5
    
    # === TIME DECAY PENALTY ===
    if time_ago_minutes > 30:
        penalty = min((time_ago_minutes - 30) / 60 * 5, 10)
        score -= penalty
    
    return max(0, min(score, 100))