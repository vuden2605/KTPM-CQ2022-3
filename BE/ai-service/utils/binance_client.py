"""
utils/binance_client.py
Lấy giá từ Binance API (OHLCV candles)
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional

BINANCE_API = "https://api.binance.com/api/v3"


def get_klines(
    symbol: str, 
    start_time: datetime, 
    end_time: datetime, 
    interval: str = '1h'
) -> List[Dict]:
    """
    Lấy OHLCV candles từ Binance
    
    Args:
        symbol: BTCUSDT, ETHUSDT, ...
        start_time: Start datetime
        end_time: End datetime
        interval: 1h, 4h, 1d, ...
    
    Returns:
        List of candles [{'timestamp', 'open', 'high', 'low', 'close', 'volume'}, ...]
    """
    url = f"{BINANCE_API}/klines"
    
    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': int(start_time.timestamp() * 1000),
        'endTime': int(end_time.timestamp() * 1000),
        'limit': 1000
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Error fetching {symbol} from Binance: {e}")
        return []
    
    candles = []
    for k in data:
        candles.append({
            'timestamp': datetime.fromtimestamp(k[0] / 1000),
            'open': float(k[1]),
            'high': float(k[2]),
            'low': float(k[3]),
            'close': float(k[4]),
            'volume': float(k[5])
        })
    
    return candles


def get_current_price(symbol: str) -> Optional[float]:
    """
    Lấy giá hiện tại
    
    Args:
        symbol: BTCUSDT, ETHUSDT, ...
    
    Returns:
        Current price (float) hoặc None
    """
    url = f"{BINANCE_API}/ticker/price"
    
    try:
        response = requests.get(url, params={'symbol': symbol}, timeout=5)
        response.raise_for_status()
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"❌ Error fetching price for {symbol}: {e}")
        return None