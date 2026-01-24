"""
services/feature_calculator.py
Tính features REALTIME cho 1 tin (chỉ dùng data TRƯỚC tin)
Hỗ trợ cả 1h và 24h
"""

from datetime import timedelta
from typing import Dict
import numpy as np

from utils.binance_client import get_klines

"""
services/feature_calculator.py
Tính features REALTIME (18 features mới)
"""

from datetime import timedelta
from typing import Dict
import numpy as np

from utils.binance_client import get_klines


def calculate_rsi(prices, period=14):
    """Tính RSI từ list prices"""
    if len(prices) < period + 1:
        return 50.0
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_features_realtime(news: Dict, symbol: str, horizon: str = '1h') -> Dict:
    """
    Tính TẤT CẢ 18 features REALTIME
    """
    from services.entity_extractor import extract_entities, extract_keywords
    
    news_time = news['timestamp']
    
    # ===== VOL_PRE & VOLUME_PRE (24h TRƯỚC tin) =====
    pre_start = news_time - timedelta(hours=24)
    candles = get_klines(symbol, pre_start, news_time, interval='1h')
    
    # Volatility 24h TRƯỚC tin
    if len(candles) > 1:
        returns = [
            (candles[i]['close'] - candles[i-1]['close']) / candles[i-1]['close']
            for i in range(1, len(candles))
        ]
        vol_pre_24h = float(np.std(returns) * np.sqrt(24) * 100)
    else:
        vol_pre_24h = 1.0
    
    # Volume 24h TRƯỚC tin
    volume_pre_24h = float(sum(c['volume'] for c in candles)) if candles else 0.0
    
    # ===== TECHNICAL INDICATORS =====
    
    # 1. RSI
    if len(candles) >= 15:
        prices = [c['close'] for c in candles]
        rsi_24h = calculate_rsi(prices, period=14)
    else:
        rsi_24h = 50.0
    
    # 2. Price change 24h
    if len(candles) >= 2:
        price_change_24h = (candles[-1]['close'] - candles[0]['close']) / candles[0]['close'] * 100
    else:
        price_change_24h = 0.0
    
    # 3. High-Low range
    if len(candles) >= 1:
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        high_low_range_24h = (max(highs) - min(lows)) / min(lows) * 100
    else:
        high_low_range_24h = 0.0
    
    # 4. Volume MA ratio
    ma_start = news_time - timedelta(days=7)
    candles_7d = get_klines(symbol, ma_start, news_time, interval='1h')
    
    if len(candles_7d) >= 1:
        volume_ma_7d = np.mean([c['volume'] for c in candles_7d])
        volume_ma_ratio = volume_pre_24h / volume_ma_7d if volume_ma_7d > 0 else 1.0
    else:
        volume_ma_ratio = 1.0
    
    # ===== MARKET CONTEXT =====
    
    MARKET_CAP_RANKS = {
        'BTCUSDT': 1, 'ETHUSDT': 2, 'BNBUSDT': 3, 'SOLUSDT': 4,
        'XRPUSDT': 5, 'ADAUSDT': 6, 'DOGEUSDT': 7, 'MATICUSDT': 8
    }
    market_cap_rank = MARKET_CAP_RANKS.get(symbol, 50)
    time_of_day = news_time.hour
    day_of_week = news_time.weekday()
    
    # ===== NEWS FEATURES =====
    
    # NOTE: news_count_1h, avg_sentiment_1h cần query MongoDB
    # Đơn giản hóa: set default (hoặc implement query nếu cần)
    news_count_1h = 0  # TODO: Query MongoDB nếu cần chính xác
    avg_sentiment_1h = 0.5
    
    # Entity & keyword importance
    title = news.get('title', '')
    entities = extract_entities(title)
    keywords = extract_keywords(title)
    
    ENTITY_IMPORTANCE = {
        'sec': 10, 'fed': 10, 'cftc': 9,
        'blackrock': 8, 'fidelity': 8, 'grayscale': 7,
        'coinbase': 6, 'binance': 6,
        'elon_musk': 8, 'trump': 7, 'powell': 7
    }
    
    entity_importance = 0
    for entity in entities['orgs'] + entities['people']:
        entity_importance += ENTITY_IMPORTANCE.get(entity, 0)
    entity_importance = min(entity_importance, 20)
    
    KEYWORD_STRENGTH = {
        'approved': 5, 'approval': 5, 'etf approved': 8,
        'ban': 5, 'banned': 5, 'lawsuit': 4, 'hack': 6,
        'surge': 3, 'soar': 3, 'crash': 4, 'plunge': 4
    }
    
    keyword_strength = 0
    for kw in keywords['positive'] + keywords['negative']:
        keyword_strength += KEYWORD_STRENGTH.get(kw, 1)
    keyword_strength = min(keyword_strength, 20)
    
    # ===== BASELINE RETURN =====
    
    if horizon == '1h':
        t_baseline = news_time - timedelta(days=1)
        t_end = t_baseline + timedelta(hours=1)
        candles_baseline = get_klines(symbol, t_baseline, t_end, interval='1h')
        
        if len(candles_baseline) >= 1:
            baseline_ret_1h = (candles_baseline[0]['close'] - candles_baseline[0]['open']) / candles_baseline[0]['open'] * 100
        else:
            baseline_ret_1h = 0.0
        
        features = {
            'sentiment_score': news.get('sentiment_score', 0.5),
            'breaking_score': news.get('breaking_score', 0),
            'vol_pre_24h': vol_pre_24h,
            'volume_pre_24h': volume_pre_24h,
            'baseline_ret_1h': baseline_ret_1h,
            
            # Technical
            'rsi_24h': rsi_24h,
            'price_change_24h': price_change_24h,
            'high_low_range_24h': high_low_range_24h,
            'volume_ma_ratio': volume_ma_ratio,
            
            # Market context
            'market_cap_rank': market_cap_rank,
            'time_of_day': time_of_day,
            'day_of_week': day_of_week,
            
            # News
            'news_count_1h': news_count_1h,
            'avg_sentiment_1h': avg_sentiment_1h,
            'entity_importance': entity_importance,
            'keyword_strength': keyword_strength,
            
            # Derived
            'is_breaking_int': 1 if news.get('is_breaking') else 0,
            'sentiment_extreme': abs(news.get('sentiment_score', 0.5) - 0.5)
        }
    
    else:  # 24h
        t_baseline = news_time - timedelta(days=1)
        t_end = t_baseline + timedelta(hours=24)
        candles_baseline = get_klines(symbol, t_baseline, t_end, interval='1h')
        
        if len(candles_baseline) >= 2:
            baseline_ret_24h = (candles_baseline[-1]['close'] - candles_baseline[0]['close']) / candles_baseline[0]['close'] * 100
        else:
            baseline_ret_24h = 0.0
        
        features = {
            'sentiment_score': news.get('sentiment_score', 0.5),
            'breaking_score': news.get('breaking_score', 0),
            'vol_pre_24h': vol_pre_24h,
            'volume_pre_24h': volume_pre_24h,
            'baseline_ret_24h': baseline_ret_24h,
            
            # Technical
            'rsi_24h': rsi_24h,
            'price_change_24h': price_change_24h,
            'high_low_range_24h': high_low_range_24h,
            'volume_ma_ratio': volume_ma_ratio,
            
            # Market context
            'market_cap_rank': market_cap_rank,
            'time_of_day': time_of_day,
            'day_of_week': day_of_week,
            
            # News
            'news_count_1h': news_count_1h,
            'avg_sentiment_1h': avg_sentiment_1h,
            'entity_importance': entity_importance,
            'keyword_strength': keyword_strength,
            
            # Derived
            'is_breaking_int': 1 if news.get('is_breaking') else 0,
            'sentiment_extreme': abs(news.get('sentiment_score', 0.5) - 0.5)
        }
    
    return features