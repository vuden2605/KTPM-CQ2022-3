"""
Configuration file for Crypto Data Pipeline
Copy this file and modify for your needs
"""

# ============================================
# MONGODB CONFIGURATION
# ============================================

MONGODB_CONFIG = {
    # MongoDB Atlas credentials
    "username": "YOUR_USERNAME",  # ← Change this
    "password": "YOUR_PASSWORD",  # ← Change this
    "cluster": "cluster0.mz66r.mongodb.net",
    "database": "cryptonews",
    
    # Collections
    "news_collection": "News",
    "training_collection": "AI_Training_Data",
    
    # Connection settings
    "timeout_ms": 5000,
    "retry_writes": True
}

# ============================================
# BINANCE CONFIGURATION
# ============================================

BINANCE_CONFIG = {
    # API endpoint
    "base_url": "https://api.binance.com",
    
    # Rate limiting
    "requests_per_minute": 1200,
    "sleep_between_requests": 0.1,  # seconds
    
    # Retry settings
    "max_retries": 5,
    "backoff_factor": 1,  # exponential backoff multiplier
    
    # Request timeout
    "timeout": 30  # seconds
}

# ============================================
# DATA COLLECTION SETTINGS
# ============================================

DATA_CONFIG = {
    # Default symbol and interval
    "default_symbol": "BTCUSDT",
    "default_interval": "1h",  # 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
    
    # Date range
    "default_start_date": "2026-01-01",
    "default_end_date": "2026-01-22",
    
    # Multiple symbols for batch processing
    "symbols": [
        "BTCUSDT",   # Bitcoin
        "ETHUSDT",   # Ethereum
        "BNBUSDT",   # Binance Coin
        "ADAUSDT",   # Cardano
        "SOLUSDT",   # Solana
        "XRPUSDT",   # Ripple
        "DOGEUSDT",  # Dogecoin
        "DOTUSDT",   # Polkadot
        "MATICUSDT", # Polygon
        "AVAXUSDT"   # Avalanche
    ],
    
    # Multiple timeframes
    "intervals": ["1h", "4h", "1d"]
}

# ============================================
# FEATURE ENGINEERING SETTINGS
# ============================================

FEATURE_CONFIG = {
    # Price feature windows (in periods)
    "price_windows": {
        "short": [3, 6],      # Short-term: 3h, 6h
        "medium": [12, 24],   # Medium-term: 12h, 24h (1 day)
        "long": [168]         # Long-term: 168h (1 week)
    },
    
    # Sentiment feature windows
    "sentiment_windows": {
        "short": [3, 6],
        "medium": [12, 24],
        "long": [72, 168]  # 3 days, 1 week
    },
    
    # Technical indicators
    "indicators": {
        "rsi_period": 14,
        "ma_periods": [6, 24, 168],  # 6h, 1d, 1w
        "volatility_periods": [6, 24]
    },
    
    # Target prediction horizons (hours ahead)
    "prediction_horizons": [1, 3, 6, 24],
    
    # Classification thresholds
    "price_change_thresholds": {
        "strong_down": -0.02,  # -2%
        "strong_up": 0.02      # +2%
    }
}

# ============================================
# DATA QUALITY SETTINGS
# ============================================

QUALITY_CONFIG = {
    # Minimum samples required
    "min_samples": 100,
    
    # Maximum missing percentage per column
    "max_missing_pct": 0.5,  # 50%
    
    # Target class balance
    "min_class_ratio": 0.1,  # At least 10% for minority class
    
    # Outlier detection
    "sentiment_score_range": (-1, 1),
    "price_return_clip": (-0.5, 0.5),  # Clip returns at ±50%
    
    # Remove rows with missing targets
    "drop_missing_targets": True
}

# ============================================
# OUTPUT SETTINGS
# ============================================

OUTPUT_CONFIG = {
    # Save options
    "save_to_csv": True,
    "save_to_mongodb": True,
    "save_to_parquet": False,  # More efficient for large datasets
    
    # Output directory
    "output_dir": "./training_data",
    
    # CSV options
    "csv_compression": None,  # None, 'gzip', 'bz2', 'zip', 'xz'
    
    # File naming
    "filename_template": "training_data_{symbol}_{interval}_{start_date}_to_{end_date}",
    
    # MongoDB batch insert size
    "mongodb_batch_size": 1000
}

# ============================================
# LOGGING SETTINGS
# ============================================

LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    
    # Save logs to file
    "save_to_file": True,
    "log_file": "pipeline.log",
    "log_rotation": True,
    "max_log_size_mb": 10
}

# ============================================
# ADVANCED SETTINGS
# ============================================

ADVANCED_CONFIG = {
    # Parallel processing
    "enable_multiprocessing": False,
    "num_workers": 4,
    
    # Memory management
    "chunk_size": 10000,  # Process data in chunks
    "low_memory_mode": False,
    
    # Caching
    "cache_binance_data": True,
    "cache_dir": "./cache",
    "cache_expiry_hours": 24,
    
    # Feature selection
    "auto_feature_selection": False,
    "feature_importance_threshold": 0.01,
    
    # Data validation
    "strict_validation": True,
    "auto_fix_issues": True
}

# ============================================
# EXPERIMENTAL FEATURES
# ============================================

EXPERIMENTAL_CONFIG = {
    # Technical indicators
    "enable_advanced_indicators": False,
    "indicators_list": [
        "MACD", "Bollinger Bands", "Stochastic", "ATR"
    ],
    
    # Sentiment analysis
    "enable_sentiment_nlp": False,
    "sentiment_model": "distilbert-base-uncased",
    
    # Time-based features
    "enable_temporal_features": True,
    "temporal_features": [
        "hour_of_day",
        "day_of_week",
        "is_weekend",
        "is_us_trading_hours"
    ],
    
    # External data sources
    "enable_external_data": False,
    "external_sources": [
        "google_trends",
        "twitter_sentiment",
        "reddit_sentiment"
    ]
}

# ============================================
# PRESET CONFIGURATIONS
# ============================================

PRESETS = {
    "quick_test": {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "start_date": "2026-01-20",
        "end_date": "2026-01-22",
        "save_to_mongodb": False,
        "save_to_csv": True
    },
    
    "full_training": {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "start_date": "2025-01-01",
        "end_date": "2026-01-22",
        "save_to_mongodb": True,
        "save_to_csv": True
    },
    
    "multi_symbol": {
        "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        "interval": "1h",
        "start_date": "2026-01-01",
        "end_date": "2026-01-22"
    },
    
    "multi_timeframe": {
        "symbol": "BTCUSDT",
        "intervals": ["1h", "4h", "1d"],
        "start_date": "2026-01-01",
        "end_date": "2026-01-22"
    }
}

# ============================================
# USAGE EXAMPLES
# ============================================

"""
# Example 1: Quick test
from crypto_data_pipeline import run_pipeline
from config import PRESETS

df = run_pipeline(**PRESETS["quick_test"])

# Example 2: Custom configuration
df = run_pipeline(
    symbol="ETHUSDT",
    interval="4h",
    start_date="2025-06-01",
    end_date="2026-01-22",
    save_to_mongodb=True,
    save_to_csv=True
)

# Example 3: Batch processing multiple symbols
from config import DATA_CONFIG

for symbol in DATA_CONFIG["symbols"]:
    df = run_pipeline(
        symbol=symbol,
        interval="1h",
        start_date="2026-01-01",
        end_date="2026-01-22"
    )
    print(f"Completed {symbol}: {len(df)} samples")
"""
