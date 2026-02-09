"""
Pipeline align news-price WINDOW-BASED (REALTIME READY):
- Mỗi WINDOW (1h) → 1 row (aggregate TẤT CẢ tin trong window)
- Predict trực tiếp cho ĐỒNG (UP/DOWN) - KHÔNG CẦN aggregate
- Tính return 1h, 24h sau window
- Tính volatility & volume 24h TRƯỚC window (realtime-ready)
- Tính baseline return & abnormal return (cho classification)
- Features: aggregate từ TẤT CẢ tin trong window + price features
"""

import pandas as pd
import numpy as np
from pymongo import MongoClient
from datetime import datetime, timedelta
import requests
from typing import List, Dict, Tuple, Set, Optional
import time
import logging
import json

# ============================================
# LOGGING SETUP
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# MONGODB CONFIGURATION
# ============================================

MONGO_URI = "mongodb+srv://nguyenvanvu060104:cryptonews123456@cluster0.mz66r.mongodb.net/cryptonews?retryWrites=true&w=majority&appName=Cluster0&authSource=admin"
MONGO_DB_NAME = "cryptonews"

def get_mongodb_connection():
    """Get MongoDB connection"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        logger.info("✓ MongoDB connected")
        return client
    except Exception as e:
        logger.error(f"✗ MongoDB connection failed: {e}")
        raise

# ============================================
# BINANCE API
# ============================================

def fetch_binance_klines(symbol: str, interval: str, start_time: int, end_time: int) -> List[List]:
    """Lấy dữ liệu OHLCV từ Binance"""
    url = "https://api.binance.com/api/v3/klines"
    
    all_klines = []
    current_start = start_time
    
    while current_start < end_time:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current_start,
            "endTime": end_time,
            "limit": 1000
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            klines = response.json()
            
            if not klines:
                break
            
            all_klines.extend(klines)
            current_start = klines[-1][0] + 1
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            time.sleep(2)
            continue
    
    logger.info(f"✓ Fetched {len(all_klines)} klines for {symbol}")
    return all_klines


def klines_to_dataframe(klines: List[List], symbol: str) -> pd.DataFrame:
    """Convert Binance klines to DataFrame"""
    if not klines:
        return pd.DataFrame()
    
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df['symbol'] = symbol
    df = df.drop_duplicates(subset=['timestamp'])
    df = df.set_index('timestamp')
    df = df.sort_index()
    
    return df


def parse_extra_json(x):
    """Parse ExtraJson field"""
    if isinstance(x, str):
        try:
            return json.loads(x)
        except:
            return {}
    return x or {}

# ============================================
# MONGODB NEWS
# ============================================

def fetch_news_from_mongodb(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Fetch news từ MongoDB"""
    client = get_mongodb_connection()
    db = client[MONGO_DB_NAME]
    news_collection = db["News"]

    try:
        pipeline = [
            {
                "$match": {
                    "PublishedAt": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            },
            {
                "$project": {
                    "news_id": "$_id",
                    "timestamp": "$PublishedAt",
                    "sentiment_score": "$SentimentScore",
                    "sentiment_label": "$SentimentLabel",
                    "extraJson": "$ExtraJson",
                    "title": "$Title",
                    "url": "$Url"
                }
            }
        ]

        news_data = list(news_collection.aggregate(pipeline))
        if not news_data:
            return pd.DataFrame()

        df = pd.DataFrame(news_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['news_id'] = df['news_id'].astype(str)

        # Parse extraJson
        df['extraJson'] = df['extraJson'].apply(parse_extra_json)

        # Extract fields
        df['is_breaking'] = df['extraJson'].apply(
            lambda x: x.get('isBreaking', False)
        )
        df['breaking_score'] = df['extraJson'].apply(
            lambda x: x.get('breakingScore', 0)
        )
        df['symbols'] = df['extraJson'].apply(
            lambda x: x.get('symbols', [])
        )

        # Clean data
        df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')
        df['breaking_score'] = pd.to_numeric(df['breaking_score'], errors='coerce').fillna(0)
        df['is_breaking'] = df['is_breaking'].astype(bool)

        logger.info(f"✓ Fetched {len(df)} news records")
        return df

    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return pd.DataFrame()
    finally:
        client.close()

# ============================================
# PRICE ANALYSIS FUNCTIONS
# ============================================

def get_price_at_time(df_price: pd.DataFrame, target_time: pd.Timestamp) -> Optional[float]:
    """Lấy giá close của candle gần nhất trước/tại target_time"""
    if df_price.empty:
        return None
    
    candidates = df_price[df_price.index <= target_time]
    
    if candidates.empty:
        return None
    
    candle = candidates.iloc[-1]
    open_time = candle.name
    close_time = open_time + timedelta(hours=1)
    
    if open_time <= target_time < close_time:
        return candle['close']
    else:
        time_diff = (target_time - open_time).total_seconds() / 3600
        if time_diff > 2:
            logger.warning(f"Target {target_time} is {time_diff:.1f}h after candle {open_time}")
        return candle['close']


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


def calculate_baseline_return(
    df_price: pd.DataFrame,
    window_start: pd.Timestamp,
    horizon_hours: int = 24,
    baseline_days: int = 7
) -> Optional[float]:
    """Tính baseline return"""
    if df_price.empty:
        return None
    
    rets = []
    
    for i in range(1, baseline_days + 1):
        t_baseline = window_start - timedelta(days=i)
        t_end = t_baseline + timedelta(hours=horizon_hours)
        
        price_start = get_price_at_time(df_price, t_baseline)
        price_end = get_price_at_time(df_price, t_end)
        
        if price_start and price_end and price_start > 0:
            ret = ((price_end - price_start) / price_start) * 100
            rets.append(ret)
    
    return np.mean(rets) if len(rets) > 0 else None


def classify_label(abret: Optional[float], threshold: float = 0.0) -> str:
    """
    Phân loại label BINARY (UP/DOWN only)
    
    Args:
        abret: abnormal return (%)
        threshold: ngưỡng (0.0 = bất kỳ biến động nào)
    
    Returns:
        'UP' nếu abret >= 0, 'DOWN' nếu abret < 0
    """
    if abret is None:
        return 'UNKNOWN'
    
    # BINARY: chỉ UP hoặc DOWN (không có NEUTRAL)
    if abret >= threshold:
        return 'UP'
    else:
        return 'DOWN'

# ============================================
# ALIGN NEWS + PRICE (WINDOW-BASED)
# ============================================

def align_news_price_window(
    df_news: pd.DataFrame,
    price_data: Dict[str, pd.DataFrame],
    window_hours: int = 1
) -> pd.DataFrame:
    """
    Align theo TIME WINDOW
    
    Mỗi window (1h) → 1 row → aggregate TẤT CẢ tin trong window
    """
    aligned_rows = []
    
    # Get time range
    start_time = df_news['timestamp'].min()
    end_time = df_news['timestamp'].max()
    
    # Create windows
    current_time = start_time.floor('H')  # Round to hour
    window_count = 0
    
    while current_time <= end_time:
        window_start = current_time
        window_end = current_time + timedelta(hours=window_hours)
        
        window_count += 1
        if window_count % 100 == 0:
            logger.info(f"  Processing window {window_count}...")
        
        # Lặp qua từng symbol
        for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']:
            df_price = price_data.get(symbol, pd.DataFrame())
            if df_price.empty:
                continue
            
            # ===== FILTER TIN TRONG WINDOW =====
            news_in_window = df_news[
                (df_news['timestamp'] >= window_start) &
                (df_news['timestamp'] < window_end)
            ]
            
            # Filter theo symbol
            symbol_short = symbol.replace('USDT', '').upper()
            news_filtered = []
            for _, news_row in news_in_window.iterrows():
                symbols_list = news_row['symbols']
                if isinstance(symbols_list, list):
                    if any(symbol_short in str(s).upper() for s in symbols_list):
                        news_filtered.append(news_row)
            
            news_count = len(news_filtered)
            
            # ===== AGGREGATE NEWS FEATURES =====
            if news_count == 0:
                avg_sentiment = 0.5
                max_sentiment = 0.5
                min_sentiment = 0.5
                sentiment_std = 0.0
                breaking_count = 0
                avg_breaking_score = 0.0
                has_sec = 0
                has_fed = 0
                has_blackrock = 0
                has_major_entity = 0
                positive_keyword_count = 0
                negative_keyword_count = 0
            else:
                # Sentiment features
                sentiments = [n['sentiment_score'] for n in news_filtered]
                avg_sentiment = float(np.mean(sentiments))
                max_sentiment = float(np.max(sentiments))
                min_sentiment = float(np.min(sentiments))
                sentiment_std = float(np.std(sentiments))
                
                # Breaking features
                breaking_count = sum(1 for n in news_filtered if n.get('is_breaking'))
                breaking_scores = [n.get('breaking_score', 0) for n in news_filtered]
                avg_breaking_score = float(np.mean(breaking_scores))
                
                # Entity & keyword features
                ENTITY_IMPORTANCE = {
                    'sec': 1, 'fed': 1, 'cftc': 1,
                    'blackrock': 1, 'fidelity': 1, 'grayscale': 1
                }
                
                POSITIVE_KEYWORDS = ['approved', 'approval', 'etf', 'surge', 'soar', 'bullish', 'adoption']
                NEGATIVE_KEYWORDS = ['ban', 'banned', 'lawsuit', 'hack', 'crash', 'plunge', 'bearish']
                
                has_sec = 0
                has_fed = 0
                has_blackrock = 0
                positive_keyword_count = 0
                negative_keyword_count = 0
                
                for n in news_filtered:
                    title_lower = n['title'].lower()
                    
                    if 'sec' in title_lower:
                        has_sec = 1
                    if 'fed' in title_lower:
                        has_fed = 1
                    if 'blackrock' in title_lower:
                        has_blackrock = 1
                    
                    for kw in POSITIVE_KEYWORDS:
                        if kw in title_lower:
                            positive_keyword_count += 1
                    
                    for kw in NEGATIVE_KEYWORDS:
                        if kw in title_lower:
                            negative_keyword_count += 1
                
                has_major_entity = max(has_sec, has_fed, has_blackrock)
            
            # ===== PRICE FEATURES =====
            pre_start = window_start - timedelta(hours=24)
            pre_data = df_price[
                (df_price.index >= pre_start) &
                (df_price.index < window_start)
            ]
            
            # Volatility
            if len(pre_data) > 1:
                returns = pre_data['close'].pct_change().dropna()
                vol_pre_24h = float(returns.std() * np.sqrt(24) * 100) if len(returns) > 0 else 1.0
            else:
                vol_pre_24h = 1.0
            
            # Volume
            volume_pre_24h = float(pre_data['volume'].sum()) if not pre_data.empty else 0.0
            
            # RSI
            if len(pre_data) >= 15:
                rsi_24h = calculate_rsi(pre_data['close'].values)
            else:
                rsi_24h = 50.0
            
            # Price change
            if len(pre_data) >= 2:
                price_change_24h = float((pre_data.iloc[-1]['close'] - pre_data.iloc[0]['close']) / pre_data.iloc[0]['close'] * 100)
            else:
                price_change_24h = 0.0
            
            # High-Low range
            if len(pre_data) >= 1:
                high_low_range_24h = float((pre_data['high'].max() - pre_data['low'].min()) / pre_data['low'].min() * 100) if pre_data['low'].min() > 0 else 0.0
            else:
                high_low_range_24h = 0.0
            
            # Volume MA ratio
            ma_start = window_start - timedelta(days=7)
            candles_7d = df_price[(df_price.index >= ma_start) & (df_price.index < window_start)]
            
            if len(candles_7d) >= 1:
                volume_ma_7d = candles_7d['volume'].mean()
                volume_ma_ratio = float(volume_pre_24h / (volume_ma_7d * 24)) if volume_ma_7d > 0 else 1.0
            else:
                volume_ma_ratio = 1.0
            
            # Market cap rank
            MARKET_CAP_RANKS = {
                'BTCUSDT': 1, 'ETHUSDT': 2, 'BNBUSDT': 3, 'SOLUSDT': 4,
                'XRPUSDT': 5, 'ADAUSDT': 6, 'DOGEUSDT': 7
            }
            market_cap_rank = MARKET_CAP_RANKS.get(symbol, 50)
            
            # ===== FUTURE RETURN (TARGET) =====
            price_at_window = get_price_at_time(df_price, window_start)
            price_1h = get_price_at_time(df_price, window_start + timedelta(hours=1))
            price_24h = get_price_at_time(df_price, window_start + timedelta(hours=24))
            
            ret_1h = ((price_1h - price_at_window) / price_at_window * 100) if (price_at_window and price_1h) else None
            ret_24h = ((price_24h - price_at_window) / price_at_window * 100) if (price_at_window and price_24h) else None
            
            # Baseline & abnormal return
            baseline_ret_1h = calculate_baseline_return(df_price, window_start, 1, 7)
            baseline_ret_24h = calculate_baseline_return(df_price, window_start, 24, 7)
            
            abret_1h = (ret_1h - baseline_ret_1h) if (ret_1h is not None and baseline_ret_1h is not None) else None
            abret_24h = (ret_24h - baseline_ret_24h) if (ret_24h is not None and baseline_ret_24h is not None) else None
            
            label_1h = classify_label(abret_1h, threshold=0.3)
            label_24h = classify_label(abret_24h, threshold=0.2)
            
            # Skip if no label
            if label_24h == 'UNKNOWN':
                continue
            
            # ===== CREATE ROW =====
            row = {
                'window_start': window_start,
                'window_end': window_end,
                'symbol': symbol,
                
                # NEWS (13 features)
                'news_count': news_count,
                'avg_sentiment': avg_sentiment,
                'max_sentiment': max_sentiment,
                'min_sentiment': min_sentiment,
                'sentiment_std': sentiment_std,
                'breaking_count': breaking_count,
                'avg_breaking_score': avg_breaking_score,
                'has_sec': has_sec,
                'has_fed': has_fed,
                'has_blackrock': has_blackrock,
                'has_major_entity': has_major_entity,
                'positive_keyword_count': positive_keyword_count,
                'negative_keyword_count': negative_keyword_count,
                
                # PRICE (6 features)
                'vol_pre_24h': vol_pre_24h,
                'volume_pre_24h': volume_pre_24h,
                'rsi_24h': rsi_24h,
                'price_change_24h': price_change_24h,
                'high_low_range_24h': high_low_range_24h,
                'volume_ma_ratio': volume_ma_ratio,
                
                # CONTEXT (3 features)
                'market_cap_rank': market_cap_rank,
                'time_of_day': window_start.hour,
                'day_of_week': window_start.weekday(),
                
                # TARGET
                'price_at_window': price_at_window,
                'price_1h': price_1h,
                'price_24h': price_24h,
                'ret_1h': ret_1h,
                'ret_24h': ret_24h,
                'baseline_ret_1h': baseline_ret_1h,
                'baseline_ret_24h': baseline_ret_24h,
                'abret_1h': abret_1h,
                'abret_24h': abret_24h,
                'label_1h': label_1h,
                'label_24h': label_24h,
            }
            
            aligned_rows.append(row)
        
        # Next window
        current_time = window_end
    
    df_aligned = pd.DataFrame(aligned_rows)
    
    logger.info(f"✓ Created {len(df_aligned)} windows from {len(df_news)} news")
    logger.info(f"  Average {len(df_news) / len(df_aligned):.1f} news per window" if len(df_aligned) > 0 else "  No windows created")
    
    return df_aligned


# ============================================
# FETCH MULTI-SYMBOL PRICES
# ============================================

def fetch_all_symbol_prices(
    symbols: Set[str],
    interval: str,
    start_ts: int,
    end_ts: int
) -> Dict[str, pd.DataFrame]:
    """Fetch price data cho tất cả symbols"""
    price_data = {}
    
    symbols_to_fetch = {'BTCUSDT'} | symbols
    
    for symbol in sorted(symbols_to_fetch):
        logger.info(f"Fetching price for {symbol}...")
        klines = fetch_binance_klines(symbol, interval, start_ts, end_ts)
        
        if klines:
            df = klines_to_dataframe(klines, symbol)
            price_data[symbol] = df
        else:
            logger.warning(f"  ⚠ No price data for {symbol}")
    
    return price_data


# ============================================
# MAIN PIPELINE
# ============================================

def run_pipeline(
    start_date: str = "2025-12-01",
    end_date: str = "2026-02-02",
    window_hours: int = 1,
    save_to_mongodb: bool = True,
    save_to_csv: bool = True
):
    """Pipeline align news-price WINDOW-BASED"""
    
    logger.info("=" * 70)
    logger.info("NEWS-PRICE ALIGNMENT PIPELINE (WINDOW-BASED)")
    logger.info("=" * 70)
    
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
        
        price_start_dt = start_dt - timedelta(days=8)
        price_end_dt = end_dt + timedelta(days=2)
        
        start_ts = int(price_start_dt.timestamp() * 1000)
        end_ts = int(price_end_dt.timestamp() * 1000)
        
        # Fetch news
        logger.info(f"\n[1/3] Fetching news from MongoDB...")
        df_news = fetch_news_from_mongodb(start_dt, end_dt)
        
        if df_news.empty:
            logger.error("No news data found!")
            return None
        
        logger.info(f"      ✓ {len(df_news)} news records")
        
        # Fetch prices
        logger.info(f"\n[2/3] Fetching prices (1h interval)...")
        all_symbols = {'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT'}
        price_data = fetch_all_symbol_prices(all_symbols, "1h", start_ts, end_ts)
        
        if 'BTCUSDT' not in price_data:
            logger.error("Failed to fetch BTCUSDT!")
            return None
        
        logger.info(f"      ✓ Fetched price for {len(price_data)} symbols")
        
        # Align
        logger.info(f"\n[3/3] Aligning (window={window_hours}h)...")
        df_aligned = align_news_price_window(df_news, price_data, window_hours)
        
        if df_aligned.empty:
            logger.error("No aligned data!")
            return None
        
        logger.info(f"\n✅ Total: {len(df_aligned)} windows")
        
        # Save
        if save_to_csv:
            csv_filename = f"aligned_news_price_window_{window_hours}h_{start_date}_to_{end_date}.csv"
            df_aligned.to_csv(csv_filename, index=False)
            logger.info(f"✓ CSV saved: {csv_filename}")
        
        if save_to_mongodb:
            try:
                client = get_mongodb_connection()
                db = client[MONGO_DB_NAME]
                collection = db["Aligned_News_Price_Window"]
                
                records = df_aligned.to_dict('records')
                
                for record in records:
                    for key, value in record.items():
                        if isinstance(value, (np.integer, np.int64)):
                            record[key] = int(value)
                        elif isinstance(value, (np.floating, np.float64)):
                            record[key] = float(value) if not np.isnan(value) else None
                        elif pd.isna(value):
                            record[key] = None
                        elif isinstance(value, pd.Timestamp):
                            record[key] = value.to_pydatetime()
                
                for record in records:
                    record['created_at'] = datetime.now()
                
                collection.delete_many({
                    "window_start": {"$gte": start_dt, "$lte": end_dt}
                })
                
                if records:
                    collection.insert_many(records)
                    logger.info(f"✓ MongoDB saved: {len(records)} records")
                
                client.close()
                
            except Exception as e:
                logger.error(f"✗ MongoDB save failed: {e}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 WINDOW-BASED DATASET SUMMARY")
        print("=" * 70)
        print(f"Window size: {window_hours}h")
        print(f"Total windows: {len(df_aligned)}")
        print(f"Date range: {df_aligned['window_start'].min()} to {df_aligned['window_end'].max()}")
        
        print(f"\nWindows per symbol:")
        for symbol in sorted(df_aligned['symbol'].unique()):
            count = len(df_aligned[df_aligned['symbol'] == symbol])
            print(f"  {symbol}: {count}")
        
        print(f"\nLabel distribution (24h):")
        print(df_aligned['label_24h'].value_counts())
        
        print(f"\nLabel distribution (1h):")
        print(df_aligned['label_1h'].value_counts())
        
        print(f"\nFeatures ({len(df_aligned.columns)} columns):")
        print(list(df_aligned.columns))
        
        print("=" * 70 + "\n")
        
        return df_aligned
        
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "🚀 " * 20)
    print("WINDOW-BASED ALIGNMENT PIPELINE")
    print("🚀 " * 20 + "\n")
    
    df_result = run_pipeline(
        start_date="2025-12-01",
        end_date="2026-06-02",
        window_hours=1,
        save_to_mongodb=True,
        save_to_csv=True
    )
    
    print("\n" + "=" * 70)
    print("🎉 DONE!")
    print("=" * 70)
    if df_result is not None:
        print(f"✅ Total windows: {len(df_result)}")
        print(f"✅ Features: 22 (13 news + 6 price + 3 context)")
    else:
        print("❌ Failed")
    print("=" * 70 + "\n")