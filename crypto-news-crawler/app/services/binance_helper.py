"""
Helper function để fetch giá từ Binance cho các symbols trong bài viết.

Usage trong code:
    from app.services.binance_helper import fetch_prices_for_article
    
    prices = fetch_prices_for_article(article_extra_json)
"""

import json
from typing import Dict, List, Optional
import requests


def fetch_binance_ticker_price(symbol: str) -> Optional[float]:
    """Fetch current price từ Binance API.
    
    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        
    Returns:
        Current price hoặc None nếu lỗi
    """
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return float(data.get("price", 0))
    except Exception as e:
        print(f"[Binance] Error fetching {symbol}: {e}")
    return None


def fetch_binance_klines(symbol: str, interval: str = "1h", limit: int = 24) -> List[Dict]:
    """Fetch candlestick data từ Binance API.
    
    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        interval: Kline interval (1m, 5m, 1h, 1d, ...)
        limit: Number of candles
        
    Returns:
        List of kline dicts với keys: open_time, open, high, low, close, volume
    """
    try:
        url = f"https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            klines = response.json()
            result = []
            for k in klines:
                result.append({
                    "open_time": k[0],
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                })
            return result
    except Exception as e:
        print(f"[Binance] Error fetching klines {symbol}: {e}")
    return []


def fetch_prices_for_article(extra_json: str) -> Dict[str, Optional[float]]:
    """Fetch current prices cho tất cả symbols trong bài viết.
    
    Args:
        extra_json: JSON string từ News.ExtraJson field
        
    Returns:
        Dict mapping base symbol → current price
        Example: {'BTC': 50000.0, 'ETH': 3200.0}
    """
    if not extra_json:
        return {}
    
    try:
        data = json.loads(extra_json)
        symbols = data.get("symbols", [])
        trading_pairs = data.get("trading_pairs", [])
        
        if not symbols or not trading_pairs:
            return {}
        
        prices = {}
        for base, pair in zip(symbols, trading_pairs):
            price = fetch_binance_ticker_price(pair)
            if price:
                prices[base] = price
        
        return prices
    except Exception as e:
        print(f"[Binance] Error parsing ExtraJson: {e}")
        return {}


def fetch_klines_for_article(extra_json: str, interval: str = "1h", limit: int = 24) -> Dict[str, List[Dict]]:
    """Fetch klines cho tất cả symbols trong bài viết.
    
    Args:
        extra_json: JSON string từ News.ExtraJson field
        interval: Kline interval
        limit: Number of candles
        
    Returns:
        Dict mapping base symbol → list of klines
        Example: {'BTC': [{open_time: ..., close: ...}, ...], 'ETH': [...]}
    """
    if not extra_json:
        return {}
    
    try:
        data = json.loads(extra_json)
        symbols = data.get("symbols", [])
        trading_pairs = data.get("trading_pairs", [])
        
        if not symbols or not trading_pairs:
            return {}
        
        klines_data = {}
        for base, pair in zip(symbols, trading_pairs):
            klines = fetch_binance_klines(pair, interval=interval, limit=limit)
            if klines:
                klines_data[base] = klines
        
        return klines_data
    except Exception as e:
        print(f"[Binance] Error parsing ExtraJson: {e}")
        return {}


# Example usage
if __name__ == "__main__":
    # Mock ExtraJson từ một bài viết
    mock_extra_json = json.dumps({
        "symbols": ["BTC", "ETH", "SOL"],
        "trading_pairs": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    })
    
    print("=" * 60)
    print("Fetching current prices...")
    print("=" * 60)
    
    prices = fetch_prices_for_article(mock_extra_json)
    for symbol, price in prices.items():
        print(f"{symbol:8} ${price:,.2f}")
    
    print("\n" + "=" * 60)
    print("Fetching 24h klines for BTC...")
    print("=" * 60)
    
    klines_all = fetch_klines_for_article(mock_extra_json, interval="1h", limit=5)
    if "BTC" in klines_all:
        print("\nLast 5 hours of BTC:")
        for kline in klines_all["BTC"]:
            print(f"  Close: ${kline['close']:,.2f} | High: ${kline['high']:,.2f} | Low: ${kline['low']:,.2f}")
