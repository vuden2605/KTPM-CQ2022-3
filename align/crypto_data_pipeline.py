"""
Pipeline align news-price per news article (SIMPLIFIED - REALTIME READY):
- Mỗi tin là 1 row riêng (per-article approach)
- Tính return 1h, 4h, 24h sau tin
- Tính volatility & volume 24h TRƯỚC tin (realtime-ready)
- Tính baseline return & abnormal return (cho classification)
- Luôn có BTCUSDT + symbols trong tin
- Classify label (UP/DOWN/NEUTRAL) dựa trên abnormal return
- BỎ: vol_post, vol_ratio, volume_post, volume_change, max_runup/drawdown
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
    """
    Lấy giá close của candle gần nhất trước/tại target_time
    
    Args:
        df_price: DataFrame OHLCV (index = timestamp = open_time của candle)
        target_time: Thời điểm cần lấy giá
    
    Returns:
        Giá close (float) hoặc None
    """
    if df_price.empty:
        return None
    
    # Lấy tất cả candles có open_time <= target_time
    candidates = df_price[df_price.index <= target_time]
    
    if candidates.empty:
        return None
    
    # Lấy candle gần nhất (candle cuối cùng)
    candle = candidates.iloc[-1]
    
    # Kiểm tra xem target_time có nằm trong candle không
    open_time = candle.name
    close_time = open_time + timedelta(hours=1)
    
    if open_time <= target_time < close_time:
        # Target nằm trong candle này -> OK
        return candle['close']
    else:
        # Target không nằm trong candle (có thể missing data)
        # Vẫn trả về close của candle gần nhất, nhưng cảnh báo
        time_diff = (target_time - open_time).total_seconds() / 3600
        if time_diff > 2:  # Cách quá 2h thì warn
            logger.warning(f"Target {target_time} is {time_diff:.1f}h after candle {open_time}")
        return candle['close']


def calculate_returns(
    df_price: pd.DataFrame,
    news_time: pd.Timestamp
) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], 
           Optional[float], Optional[float], Optional[float]]:
    """
    Tính return sau 1h, 4h, 24h
    
    Returns:
        (price_at_news, price_1h, price_4h, price_24h, ret_1h, ret_4h, ret_24h)
    """
    if df_price.empty:
        return None, None, None, None, None, None, None
    
    # Giá tại thời điểm tin
    price_at_news = get_price_at_time(df_price, news_time)
    if price_at_news is None:
        return None, None, None, None, None, None, None
    
    # Giá sau 1h, 4h, 24h
    price_1h = get_price_at_time(df_price, news_time + timedelta(hours=1))
    price_4h = get_price_at_time(df_price, news_time + timedelta(hours=4))
    price_24h = get_price_at_time(df_price, news_time + timedelta(hours=24))
    
    # Tính return (%)
    ret_1h = ((price_1h - price_at_news) / price_at_news * 100) if price_1h else None
    ret_4h = ((price_4h - price_at_news) / price_at_news * 100) if price_4h else None
    ret_24h = ((price_24h - price_at_news) / price_at_news * 100) if price_24h else None
    
    return price_at_news, price_1h, price_4h, price_24h, ret_1h, ret_4h, ret_24h


def calculate_volatility(df_price: pd.DataFrame, start_time: pd.Timestamp, end_time: pd.Timestamp) -> Optional[float]:
    """
    Tính volatility (standard deviation của returns) trong khoảng thời gian
    
    Returns:
        Volatility (%) hoặc None
    """
    if df_price.empty:
        return None
    
    # Lấy data trong khoảng thời gian
    period_data = df_price[(df_price.index >= start_time) & (df_price.index < end_time)]
    
    if len(period_data) < 2:
        return None
    
    # Tính returns
    returns = period_data['close'].pct_change().dropna()
    
    if len(returns) == 0:
        return None
    
    # Return standard deviation (annualized)
    volatility = returns.std() * np.sqrt(24)  # Hourly to daily
    return volatility * 100  # Convert to percentage




# ============================================
# CAUSAL ANALYSIS FUNCTIONS (MỚI)
# ============================================

def calculate_baseline_return(
    df_price: pd.DataFrame,
    news_time: pd.Timestamp,
    horizon_hours: int = 24,
    baseline_days: int = 7
) -> Optional[float]:
    """
    Tính baseline return (trung bình N ngày trước cùng khung giờ)
    
    Args:
        df_price: DataFrame giá OHLCV
        news_time: Thời điểm tin
        horizon_hours: Horizon tính return (24h)
        baseline_days: Số ngày lấy baseline (7)
    
    Returns:
        baseline_ret (%) hoặc None
    """
    if df_price.empty:
        return None
    
    rets = []
    
    for i in range(1, baseline_days + 1):
        # Thời điểm tương ứng N ngày trước
        t_baseline = news_time - timedelta(days=i)
        t_end = t_baseline + timedelta(hours=horizon_hours)
        
        # Lấy giá tại 2 mốc
        price_start = get_price_at_time(df_price, t_baseline)
        price_end = get_price_at_time(df_price, t_end)
        
        if price_start and price_end and price_start > 0:
            ret = ((price_end - price_start) / price_start) * 100
            rets.append(ret)
    
    return np.mean(rets) if len(rets) > 0 else None




def classify_label(abret: Optional[float], threshold: float = 0.2) -> str:
    """
    Phân loại label dựa trên abnormal return
    
    Args:
        abret: abnormal return (%)
        threshold: ngưỡng (0.2% mặc định)
    
    Returns:
        'UP', 'DOWN', 'NEUTRAL', hoặc 'UNKNOWN'
    """
    if abret is None:
        return 'UNKNOWN'
    
    if abret > threshold:
        return 'UP'
    elif abret < -threshold:
        return 'DOWN'
    else:
        return 'NEUTRAL'


# ============================================
# ALIGN NEWS + PRICE (PER NEWS)
# ============================================
def align_news_price_per_article(
    df_news: pd.DataFrame,
    price_data: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """
    Align mỗi tin với price metrics (ENHANCED WITH 11 NEW FEATURES)
    - Mỗi tin có nhiều rows (1 cho BTC + các symbols khác)
    - Tính baseline return & abnormal return
    - Classify label (UP/DOWN/NEUTRAL)
    - THÊM: 11 features mới (technical indicators, market context, news features)
    """
    aligned_rows = []
    
    total_news = len(df_news)
    for idx, (_, news_row) in enumerate(df_news.iterrows(), 1):
        if idx % 100 == 0:
            logger.info(f"  Processing news {idx}/{total_news}...")
        
        news_time = news_row['timestamp']
        symbols_in_news = news_row['symbols']
        
        # Normalize symbols
        if isinstance(symbols_in_news, list) and len(symbols_in_news) > 0:
            symbols_normalized = set()
            for sym in symbols_in_news:
                sym_upper = sym.upper()
                if not sym_upper.endswith('USDT'):
                    sym_upper += 'USDT'
                symbols_normalized.add(sym_upper)
        else:
            symbols_normalized = set()
        
        # Luôn thêm BTCUSDT
        symbols_to_process = {'BTCUSDT'} | symbols_normalized
        
        # Base news info
        base_info = {
            'news_id': news_row['news_id'],
            'news_timestamp': news_time,
            'title': news_row['title'],
            'sentiment_score': news_row['sentiment_score'],
            'sentiment_label': news_row['sentiment_label'],
            'breaking_score': news_row['breaking_score'],
            'is_breaking': news_row['is_breaking'],
        }
        
        # ===== NEWS FEATURES (TÍNH 1 LẦN CHO TẤT CẢ SYMBOLS) =====
        
        # 8. News count 1h trước
        news_1h_before = df_news[
            (df_news['timestamp'] >= news_time - timedelta(hours=1)) &
            (df_news['timestamp'] < news_time)
        ]
        news_count_1h = len(news_1h_before)
        
        # 9. Avg sentiment 1h trước
        if news_count_1h > 0:
            avg_sentiment_1h = news_1h_before['sentiment_score'].mean()
        else:
            avg_sentiment_1h = 0.5
        
        # 10 & 11. Entity importance & Keyword strength
        title = news_row['title']
        
        # Extract entities (simple version - không cần import nếu chưa có function)
        ENTITY_IMPORTANCE = {
            'sec': 10, 'fed': 10, 'cftc': 9,
            'blackrock': 8, 'fidelity': 8, 'grayscale': 7,
            'coinbase': 6, 'binance': 6,
            'elon musk': 8, 'musk': 8, 'trump': 7, 'powell': 7, 'gensler': 7
        }
        
        entity_importance = 0
        title_lower = title.lower()
        for entity, score in ENTITY_IMPORTANCE.items():
            if entity in title_lower:
                entity_importance += score
        entity_importance = min(entity_importance, 20)
        
        # Extract keywords
        KEYWORD_STRENGTH = {
            'approved': 5, 'approval': 5, 'etf approved': 8,
            'ban': 5, 'banned': 5, 'lawsuit': 4, 'hack': 6,
            'surge': 3, 'soar': 3, 'crash': 4, 'plunge': 4,
            'breakthrough': 5, 'adoption': 4
        }
        
        keyword_strength = 0
        for keyword, score in KEYWORD_STRENGTH.items():
            if keyword in title_lower:
                keyword_strength += score
        keyword_strength = min(keyword_strength, 20)
        
        # ===== MARKET CONTEXT (TÍNH 1 LẦN) =====
        
        # 6. Time of day (0-23 UTC)
        time_of_day = news_time.hour
        
        # 7. Day of week (0=Mon, 6=Sun)
        day_of_week = news_time.weekday()
        
        # Tạo row cho mỗi symbol
        for symbol in sorted(symbols_to_process):
            df_price = price_data.get(symbol, pd.DataFrame())
            
            if df_price.empty:
                continue
            
            # Calculate basic metrics
            price_at_news, price_1h, price_4h, price_24h, ret_1h, ret_4h, ret_24h = calculate_returns(df_price, news_time)
            
            # ===== CHỈ TÍNH VOL_PRE & VOLUME_PRE (BỎ POST) =====
            pre_start = news_time - timedelta(hours=24)
            
            # Volatility 24h TRƯỚC tin
            vol_pre = calculate_volatility(df_price, pre_start, news_time)
            
            # Volume 24h TRƯỚC tin
            pre_data = df_price[(df_price.index >= pre_start) & (df_price.index < news_time)]
            volume_pre = pre_data['volume'].sum() if not pre_data.empty else None
            
            # ===== NEW FEATURES: TECHNICAL INDICATORS =====
            
            # 1. RSI 24h
            if len(pre_data) >= 15:
                prices = pre_data['close'].values
                deltas = np.diff(prices)
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)
                
                avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else 0
                avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else 0
                
                if avg_loss == 0:
                    rsi_24h = 100.0
                else:
                    rs = avg_gain / avg_loss
                    rsi_24h = 100 - (100 / (1 + rs))
            else:
                rsi_24h = 50.0  # Neutral
            
            # 2. Price change 24h
            if len(pre_data) >= 2:
                price_start_24h = pre_data.iloc[0]['close']
                price_end_24h = pre_data.iloc[-1]['close']
                price_change_24h = (price_end_24h - price_start_24h) / price_start_24h * 100
            else:
                price_change_24h = 0.0
            
            # 3. High-Low range 24h
            if len(pre_data) >= 1:
                high_24h = pre_data['high'].max()
                low_24h = pre_data['low'].min()
                high_low_range_24h = (high_24h - low_24h) / low_24h * 100 if low_24h > 0 else 0.0
            else:
                high_low_range_24h = 0.0
            
            # 4. Volume MA ratio
            ma_start = news_time - timedelta(days=7)
            candles_7d = df_price[(df_price.index >= ma_start) & (df_price.index < news_time)]
            
            if len(candles_7d) >= 1:
                volume_ma_7d = candles_7d['volume'].mean()
                if volume_ma_7d > 0 and volume_pre is not None:
                    volume_ma_ratio = volume_pre / (volume_ma_7d * 24)  # Normalize by 24h
                else:
                    volume_ma_ratio = 1.0
            else:
                volume_ma_ratio = 1.0
            
            # 5. Market cap rank (hardcoded)
            MARKET_CAP_RANKS = {
                'BTCUSDT': 1, 'ETHUSDT': 2, 'BNBUSDT': 3, 'SOLUSDT': 4,
                'XRPUSDT': 5, 'ADAUSDT': 6, 'DOGEUSDT': 7, 'MATICUSDT': 8,
                'DOTUSDT': 9, 'LTCUSDT': 10
            }
            market_cap_rank = MARKET_CAP_RANKS.get(symbol, 50)
            
            # ===== CAUSAL METRICS (24H) =====
            baseline_ret_24h = calculate_baseline_return(
                df_price, news_time, horizon_hours=24, baseline_days=7
            )

            if ret_24h is not None and baseline_ret_24h is not None:
                abret_24h = ret_24h - baseline_ret_24h
            else:
                abret_24h = None

            label_24h = classify_label(abret_24h, threshold=0.2)

            # ===== CAUSAL METRICS (1H) =====
            baseline_ret_1h = calculate_baseline_return(
                df_price, news_time, horizon_hours=1, baseline_days=7
            )

            if ret_1h is not None and baseline_ret_1h is not None:
                abret_1h = ret_1h - baseline_ret_1h
            else:
                abret_1h = None

            label_1h = classify_label(abret_1h, threshold=0.3)
            
            # Skip nếu không có data cơ bản
            if ret_1h is None and ret_4h is None and ret_24h is None:
                continue
            
            # ===== TẠO ROW (THÊM 11 FEATURES MỚI) =====
            row = base_info.copy()
            row.update({
                'symbol': symbol,
                'price_at_news': price_at_news,
                'price_1h': price_1h,
                'price_4h': price_4h,
                'price_24h': price_24h,
                'ret_1h': ret_1h,
                'ret_4h': ret_4h,
                'ret_24h': ret_24h,
                
                # Existing features (5)
                'vol_pre_24h': vol_pre,
                'volume_pre_24h': volume_pre,
                'baseline_ret_24h': baseline_ret_24h,
                'abret_24h': abret_24h,
                'label_24h': label_24h,
                'baseline_ret_1h': baseline_ret_1h,
                'abret_1h': abret_1h,
                'label_1h': label_1h,
                'label': label_24h,
                
                # ===== NEW FEATURES (11) =====
                # Technical indicators (4)
                'rsi_24h': rsi_24h,
                'price_change_24h': price_change_24h,
                'high_low_range_24h': high_low_range_24h,
                'volume_ma_ratio': volume_ma_ratio,
                
                # Market context (3)
                'market_cap_rank': market_cap_rank,
                'time_of_day': time_of_day,
                'day_of_week': day_of_week,
                
                # News features (4)
                'news_count_1h': news_count_1h,
                'avg_sentiment_1h': avg_sentiment_1h,
                'entity_importance': entity_importance,
                'keyword_strength': keyword_strength,
            })
            
            aligned_rows.append(row)
    
    df_aligned = pd.DataFrame(aligned_rows)
    
    # Sort by news_timestamp and symbol
    df_aligned = df_aligned.sort_values(['news_timestamp', 'symbol']).reset_index(drop=True)
    
    logger.info(f"✓ Aligned {len(df_aligned)} rows from {total_news} news articles")
    logger.info(f"✓ Total columns: {len(df_aligned.columns)} (including 11 new features)")
    
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
    
    # Luôn fetch BTC
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


def get_all_symbols_from_news(df_news: pd.DataFrame) -> Set[str]:
    """Extract tất cả unique symbols từ news"""
    all_symbols = set()
    
    for symbols_list in df_news['symbols']:
        if isinstance(symbols_list, list):
            for sym in symbols_list:
                sym_upper = sym.upper()
                if not sym_upper.endswith('USDT'):
                    sym_upper += 'USDT'
                all_symbols.add(sym_upper)
    
    return all_symbols

# ============================================
# MAIN PIPELINE
# ============================================

def run_pipeline(
    start_date: str = "2025-12-19",
    end_date: str = "2026-01-22",
    save_to_mongodb: bool = True,
    save_to_csv: bool = True
):
    """
    Pipeline align news-price per article (FULL VERSION - CAUSAL READY)
    """
    
    logger.info("=" * 70)
    logger.info("NEWS-PRICE ALIGNMENT PIPELINE (PER NEWS ARTICLE - CAUSAL READY)")
    logger.info("=" * 70)
    
    try:
        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
        
        # Extend price range để có đủ data cho 24h sau tin cuối + baseline 7 ngày
        price_start_dt = start_dt - timedelta(days=8)  # Buffer 7 ngày cho baseline + 1 ngày
        price_end_dt = end_dt + timedelta(days=2)      # Buffer 24h sau
        
        start_ts = int(price_start_dt.timestamp() * 1000)
        end_ts = int(price_end_dt.timestamp() * 1000)
        
        # Step 1: Fetch news
        logger.info(f"\n[1/4] Fetching news from MongoDB...")
        df_news = fetch_news_from_mongodb(start_dt, end_dt)
        
        if df_news.empty:
            logger.error("No news data found!")
            return None
        
        logger.info(f"      ✓ {len(df_news)} news records")
        
        # Step 2: Get all unique symbols
        all_symbols = get_all_symbols_from_news(df_news)
        logger.info(f"\n[2/4] Found {len(all_symbols)} unique symbols in news: {sorted(all_symbols)}")
        
        # Step 3: Fetch prices (1h interval, always include BTCUSDT)
        logger.info(f"\n[3/4] Fetching prices (1h interval, including BTCUSDT)...")
        price_data = fetch_all_symbol_prices(all_symbols, "1h", start_ts, end_ts)
        
        if 'BTCUSDT' not in price_data:
            logger.error("Failed to fetch BTCUSDT price data!")
            return None
        
        logger.info(f"      ✓ Fetched price data for {len(price_data)} symbols")
        
        # Step 4: Align news + price (WITH CAUSAL METRICS)
        logger.info(f"\n[4/4] Aligning news with price metrics (including causal features)...")
        df_aligned = align_news_price_per_article(df_news, price_data)
        
        if df_aligned.empty:
            logger.error("No aligned data!")
            return None
        
        logger.info(f"\n✅ Total aligned: {len(df_aligned)} rows from {len(df_news)} news")
        
        # Save results
        if save_to_csv:
            csv_filename = f"aligned_news_price_per_article_{start_date}_to_{end_date}.csv"
            df_aligned.to_csv(csv_filename, index=False)
            logger.info(f"✓ CSV saved: {csv_filename}")
        
        if save_to_mongodb:
            try:
                client = get_mongodb_connection()
                db = client[MONGO_DB_NAME]
                collection = db["Aligned_News_Price_Per_Article"]
                
                records = df_aligned.to_dict('records')
                
                # Convert numpy types
                for record in records:
                    for key, value in record.items():
                        if isinstance(value, np.integer):
                            record[key] = int(value)
                        elif isinstance(value, np.floating):
                            record[key] = float(value) if not np.isnan(value) else None
                        elif pd.isna(value):
                            record[key] = None
                        elif isinstance(value, pd.Timestamp):
                            record[key] = value.to_pydatetime()
                
                # Add metadata
                for record in records:
                    record['created_at'] = datetime.now()
                
                # Clear old data
                collection.delete_many({
                    "news_timestamp": {"$gte": start_dt, "$lte": end_dt}
                })
                
                if records:
                    collection.insert_many(records)
                    logger.info(f"✓ MongoDB saved: {len(records)} records")
                
                client.close()
                
            except Exception as e:
                logger.error(f"✗ MongoDB save failed: {e}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 ALIGNED DATASET SUMMARY (CAUSAL READY)")
        print("=" * 70)
        print(f"Date range: {df_aligned['news_timestamp'].min()} to {df_aligned['news_timestamp'].max()}")
        print(f"Total news articles: {df_aligned['news_id'].nunique()}")
        print(f"Total rows: {len(df_aligned)}")
        
        # Count by symbol
        print(f"\nRows per symbol:")
        for symbol in sorted(df_aligned['symbol'].unique()):
            count = len(df_aligned[df_aligned['symbol'] == symbol])
            avg_ret_24h = df_aligned[df_aligned['symbol'] == symbol]['ret_24h'].mean()
            avg_abret_24h = df_aligned[df_aligned['symbol'] == symbol]['abret_24h'].mean()
            print(f"  {symbol}: {count} rows (avg ret_24h: {avg_ret_24h:.3f}%, avg abret_24h: {avg_abret_24h:.3f}%)")
        
        # Label distribution
        # Label distribution
        print(f"\nLabel distribution (24H):")
        print(df_aligned['label_24h'].value_counts())

        print(f"\nLabel distribution (1H):")
        print(df_aligned['label_1h'].value_counts())
        
        print(f"\nColumns ({len(df_aligned.columns)}):")
        print(list(df_aligned.columns))
        
        print(f"\nSample data (first 3 rows):")
        print(df_aligned.head(3).to_string())
        print("=" * 70 + "\n")
        
        return df_aligned
        
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============================================
# USAGE
# ============================================

if __name__ == "__main__":
    
    print("\n" + "🚀 " * 20)
    print("NEWS-PRICE ALIGNMENT PIPELINE (REALTIME-READY)")
    print("Features: vol_pre, volume_pre, baseline_ret, abnormal_ret, label")
    print("🚀 " * 20 + "\n")
    df_result = run_pipeline(
        start_date="2025-12-01",
        end_date="2026-01-22",
        save_to_mongodb=True,
        save_to_csv=True
    )
    
    print("\n" + "=" * 70)
    print("🎉 DONE!")
    print("=" * 70)
    if df_result is not None:
        print(f"✅ Total rows: {len(df_result)}")
        print(f"✅ Columns: {len(df_result.columns)}")
        print(f"✅ Features include: vol_pre_24h, volume_pre_24h, baseline_ret_24h, abret_24h, label_24h, label_1h")
    else:
        print("❌ Pipeline failed")
    print("=" * 70 + "\n")