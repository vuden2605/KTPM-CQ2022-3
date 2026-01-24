"""
Configuration file for Crypto AI Pipeline
Aligned with: align_pipeline.py, train_model_1h.py, train_model_24h.py, ai-service
"""

# ============================================
# MONGODB CONFIGURATION
# ============================================

MONGODB_CONFIG = {
    # MongoDB Atlas URI (FULL)
    "uri": "mongodb+srv://nguyenvanvu060104:cryptonews123456@cluster0.mz66r.mongodb.net/cryptonews?retryWrites=true&w=majority&appName=Cluster0&authSource=admin",
    
    # Or use separate fields
    "username": "nguyenvanvu060104",
    "password": "cryptonews123456",
    "cluster": "cluster0.mz66r.mongodb.net",
    "database": "cryptonews",
    "app_name": "Cluster0",
    
    # Collections
    "news_collection": "News",
    "aligned_collection": "Aligned_News_Price_Per_Article",
    "training_collection": "AI_Training_Data",
    
    # Connection settings
    "timeout_ms": 5000,
    "retry_writes": True
}

# ============================================
# BINANCE CONFIGURATION
# ============================================

BINANCE_CONFIG = {
    "base_url": "https://api.binance.com",
    "requests_per_minute": 1200,
    "sleep_between_requests": 0.1,
    "max_retries": 5,
    "backoff_factor": 1,
    "timeout": 30
}

# ============================================
# DATA COLLECTION SETTINGS
# ============================================

DATA_CONFIG = {
    "default_symbol": "BTCUSDT",
    "default_interval": "1h",
    "default_start_date": "2025-12-01",  # ← FIXED
    "default_end_date": "2026-01-22",
    
    "symbols": [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
        "XRPUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT", "AVAXUSDT"
    ],
    
    "intervals": ["1h", "24h"]  # ← Only 1h and 24h (match with models)
}

# ============================================
# FEATURE ENGINEERING SETTINGS
# ============================================

FEATURE_CONFIG = {
    # Basic features (existing - 7 features)
    "basic_features": [
        'sentiment_score',
        'breaking_score',
        'vol_pre_24h',
        'volume_pre_24h',
        'baseline_ret_1h',  # or baseline_ret_24h
        'is_breaking_int',
        'sentiment_extreme'
    ],
    
    # NEW FEATURES (11 features)
    "new_features": {
        # Technical indicators (4)
        "rsi_period": 14,
        "price_change_window": 24,
        "high_low_range_window": 24,
        "volume_ma_days": 7,
        
        # Market context (3)
        "market_cap_ranks": {
            'BTCUSDT': 1, 'ETHUSDT': 2, 'BNBUSDT': 3, 'SOLUSDT': 4,
            'XRPUSDT': 5, 'ADAUSDT': 6, 'DOGEUSDT': 7, 'MATICUSDT': 8,
            'DOTUSDT': 9, 'LTCUSDT': 10, 'AVAXUSDT': 11
        },
        
        # News features (4)
        "news_count_window": 1,
        "avg_sentiment_window": 1,
        
        "entity_importance_map": {
            'sec': 10, 'fed': 10, 'cftc': 9,
            'blackrock': 8, 'fidelity': 8, 'grayscale': 7,
            'coinbase': 6, 'binance': 6,
            'elon musk': 8, 'trump': 7, 'powell': 7, 'gensler': 7
        },
        
        "keyword_strength_map": {
            'approved': 5, 'approval': 5, 'etf approved': 8,
            'ban': 5, 'banned': 5, 'lawsuit': 4, 'hack': 6,
            'surge': 3, 'soar': 3, 'crash': 4, 'plunge': 4,
            'breakthrough': 5, 'adoption': 4
        }
    },
    
    # Prediction horizons
    "prediction_horizons": [1, 24],
    
    # Classification thresholds (abnormal return based)
    "classification_thresholds": {
        "1h": 0.3,
        "24h": 0.2
    },
    
    # Baseline return settings
    "baseline_days": 7,  # Use 7 days before for baseline
}

# ============================================
# DATA QUALITY SETTINGS
# ============================================

QUALITY_CONFIG = {
    "min_samples": 100,
    "max_missing_pct": 0.5,
    "min_class_ratio": 0.1,
    "sentiment_score_range": (0, 1),  # ← FIXED (0-1, not -1 to 1)
    "price_return_clip": (-0.5, 0.5),
    "drop_missing_targets": True
}

# ============================================
# OUTPUT SETTINGS
# ============================================

OUTPUT_CONFIG = {
    "save_to_csv": True,
    "save_to_mongodb": True,
    "save_to_parquet": False,
    
    "output_dir": "./analysis",  # ← Match folder structure
    "csv_compression": None,
    
    "filename_template": "aligned_news_price_per_article_{start_date}_to_{end_date}",
    
    "mongodb_batch_size": 1000
}

# ============================================
# LOGGING SETTINGS
# ============================================

LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "save_to_file": True,
    "log_file": "pipeline.log",
    "log_rotation": True,
    "max_log_size_mb": 10
}

# ============================================
# MODEL TRAINING SETTINGS
# ============================================

MODEL_CONFIG = {
    # Models to train
    "models": {
        "random_forest": {
            "n_estimators": 200,
            "max_depth": 10,
            "min_samples_split": 10,
            "min_samples_leaf": 5,
            "class_weight": "balanced"
        },
        
        "gradient_boosting": {
            "n_estimators": 100,
            "max_depth": 5,
            "learning_rate": 0.1
        },
        
        "xgboost": {
            "n_estimators": 200,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8
        }
    },
    
    # Train/val/test split
    "test_size": 0.15,
    "val_size": 0.176,  # ~15% of train+val
    
    # Model save path
    "model_dir": "./analysis/models",
    
    # Feature importance threshold
    "feature_importance_threshold": 0.01
}

# ============================================
# AI SERVICE SETTINGS
# ============================================

AI_SERVICE_CONFIG = {
    # Service config
    "host": "0.0.0.0",
    "port": 8003,
    
    # CORS
    "allowed_origins": ["*"],
    
    # Ollama (LLM explanation)
    "ollama": {
        "enabled": True,
        "api_url": "http://localhost:11434/api/generate",
        "model": "llama3.2:3b",
        "temperature": 0.3,
        "max_tokens": 250
    },
    
    # Prediction settings
    "default_hours": 1,  # Fetch news from last N hours
    "max_news_analyze": 100,  # Max news to analyze per request
}

# ============================================
# PRESETS
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
        "start_date": "2025-12-01",
        "end_date": "2026-01-22",
        "save_to_mongodb": True,
        "save_to_csv": True
    },
    
    "multi_symbol": {
        "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        "interval": "1h",
        "start_date": "2025-12-01",
        "end_date": "2026-01-22"
    },
    
    "multi_timeframe": {
        "symbol": "BTCUSDT",
        "intervals": ["1h", "24h"],
        "start_date": "2025-12-01",
        "end_date": "2026-01-22"
    }
}