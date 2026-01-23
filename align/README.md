# 🚀 Crypto Data Pipeline - News Sentiment + Price Analysis

Pipeline để kết hợp dữ liệu News Sentiment từ MongoDB với Price Data từ Binance để training AI model dự đoán giá cryptocurrency.

---

## ✨ Các cải tiến so với version cũ

### 🔧 Bugs đã fix:
1. ✅ **MongoDB URI** - Thêm authentication đúng format
2. ✅ **aggregate_news()** - Xóa duplicate `agg_dict`, fix logic
3. ✅ **Division by zero** - Safe division cho tất cả ratios
4. ✅ **Empty DataFrame handling** - Xử lý trường hợp không có news
5. ✅ **Data type conversion** - Convert numpy types cho MongoDB
6. ✅ **Error handling** - Try-catch cho tất cả critical operations

### 🎯 Tính năng mới:
1. 🔄 **Retry logic** - Auto retry khi Binance API fail
2. 📊 **Data validation** - Check quality trước khi save
3. 📝 **Logging system** - Track toàn bộ quá trình
4. 🧹 **Data cleaning** - Remove duplicates, outliers
5. 📈 **More features** - RSI, momentum, interaction features
6. 🎓 **Multi-class target** - Thêm 4-class classification
7. 🔍 **Better aggregation** - Sentiment momentum, volume ratios

---

## 📋 Requirements

```bash
pip install pandas numpy pymongo requests urllib3
```

**Dependencies:**
- pandas >= 1.3.0
- numpy >= 1.21.0
- pymongo >= 4.0.0
- requests >= 2.26.0

---

## ⚙️ Setup

### 1. Cấu hình MongoDB

Mở file `crypto_data_pipeline.py` và thay đổi:

```python
# Line 31-32
MONGO_USERNAME = "YOUR_USERNAME"  # ← Thay username thực tế
MONGO_PASSWORD = "YOUR_PASSWORD"  # ← Thay password thực tế
```

### 2. Kiểm tra MongoDB Collections

Đảm bảo MongoDB có:
- Database: `cryptonews`
- Collection: `News` (chứa news data)
- Collection: `AI_Training_Data` (sẽ được tạo tự động)

### 3. Schema MongoDB News Collection

```json
{
  "PublishedAt": ISODate("2026-01-22T10:00:00Z"),
  "SentimentScore": 0.75,
  "SentimentLabel": "positive",
  "Title": "Bitcoin reaches new high",
  "Url": "https://...",
  "ExtraJson": {
    "isBreaking": true,
    "breakingScore": 8.5
  }
}
```

---

## 🎯 Usage

### Basic Usage

```python
from crypto_data_pipeline import run_pipeline

# Run với config mặc định
df = run_pipeline(
    symbol="BTCUSDT",
    interval="1h",
    start_date="2026-01-01",
    end_date="2026-01-22",
    save_to_mongodb=True,
    save_to_csv=True
)
```

### Advanced Usage

```python
# Multi-timeframe analysis
timeframes = ["1h", "4h", "1d"]

for tf in timeframes:
    df = run_pipeline(
        symbol="BTCUSDT",
        interval=tf,
        start_date="2025-01-01",
        end_date="2026-01-22",
        save_to_mongodb=True,
        save_to_csv=True
    )
    print(f"Completed {tf} timeframe: {len(df)} samples")
```

### Multiple Symbols

```python
symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

for symbol in symbols:
    df = run_pipeline(
        symbol=symbol,
        interval="1h",
        start_date="2026-01-01",
        end_date="2026-01-22"
    )
```

---

## 📊 Output Features

### Price Features (15 features)
- `open`, `high`, `low`, `close`, `volume`
- Returns: `price_return_1h`, `price_return_3h`, `price_return_6h`, `price_return_24h`
- Moving averages: `price_ma_6h`, `price_ma_24h`, `price_ma_168h`
- Volatility: `price_volatility_6h`, `price_volatility_24h`
- Volume ratios: `volume_ratio_6h`, `volume_ratio_24h`
- Indicators: `rsi_14`, `high_low_spread`, `price_position`

### Sentiment Features (20+ features)
- Raw: `sentiment_score_mean`, `sentiment_score_std`, `sentiment_score_min`, `sentiment_score_max`
- Counts: `positive_count`, `negative_count`, `neutral_count`, `sentiment_score_count`
- Ratios: `positive_ratio`, `negative_ratio`, `neutral_ratio`
- Moving averages: `sentiment_ma_3h`, `sentiment_ma_6h`, `sentiment_ma_24h`
- Changes: `sentiment_change_1h`, `sentiment_change_3h`, `sentiment_change_6h`
- Momentum: `sentiment_momentum_3h`
- Lags: `sentiment_lag_1h`, `sentiment_lag_2h`, `sentiment_lag_3h`, `sentiment_lag_6h`
- Breaking news: `is_breaking_sum`, `breaking_score_mean`
- Interactions: `sentiment_x_volume`, `sentiment_x_volatility`

### Target Variables (12 targets)
- **Prices**: `target_price_1h`, `target_price_3h`, `target_price_6h`, `target_price_24h`
- **Returns**: `target_return_1h`, `target_return_3h`, `target_return_6h`, `target_return_24h`
- **Binary**: `target_direction_1h`, `target_direction_3h`, `target_direction_6h`, `target_direction_24h`
  - 0 = DOWN
  - 1 = UP
- **Multi-class**: `target_class_1h`, `target_class_3h`, `target_class_6h`
  - 0 = Strong Down (< -2%)
  - 1 = Down (0% to -2%)
  - 2 = Neutral/Small Up (0% to +2%)
  - 3 = Strong Up (> +2%)

---

## 📁 Output Files

### CSV File
```
training_data_BTCUSDT_1h_2026-01-01_to_2026-01-22.csv
```

Chứa toàn bộ features và targets, sẵn sàng cho training.

### MongoDB Collection
```
Database: cryptonews
Collection: AI_Training_Data
```

Mỗi document chứa:
- Tất cả features
- Metadata (symbol, interval, dates)
- Timestamp index

---

## 🔍 Data Quality Checks

Pipeline tự động validate:
1. ✅ Sufficient data (>100 samples)
2. ✅ Target distribution (không all 1 class)
3. ✅ Missing values (<50% per column)
4. ✅ No extreme outliers in sentiment scores
5. ✅ Price data continuity

---

## 🎓 Example: Training an AI Model

```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Load data
df = pd.read_csv("training_data_BTCUSDT_1h_2026-01-01_to_2026-01-22.csv")

# Select features
feature_cols = [col for col in df.columns if not col.startswith('target_')]
feature_cols = [col for col in feature_cols if col not in ['timestamp', 'symbol', 'interval']]

X = df[feature_cols].fillna(0)
y = df['target_direction_1h']

# Remove rows with missing targets
mask = ~y.isna()
X, y = X[mask], y[mask]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# Feature importance
importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 10 Most Important Features:")
print(importance.head(10))
```

---

## 🐛 Troubleshooting

### Issue 1: MongoDB Connection Failed
```
✗ MongoDB connection failed: ServerSelectionTimeoutError
```
**Solution:**
- Check username/password
- Verify MongoDB cluster URL
- Check IP whitelist in MongoDB Atlas

### Issue 2: No News Data
```
⚠ No news found between ... and ...
```
**Solution:**
- Check `PublishedAt` field exists
- Verify date range has data
- Pipeline will continue with price data only

### Issue 3: Binance Rate Limit
```
HTTP Error: 429 Too Many Requests
```
**Solution:**
- Đã có retry logic tự động
- Increase sleep time in line 121
- Use smaller date ranges

### Issue 4: Empty Dataset
```
Insufficient data: only 50 samples
```
**Solution:**
- Increase date range
- Check if Binance has data for that symbol/interval
- Verify interval format: "1h", "4h", "1d" (lowercase)

---

## 📈 Performance Tips

### 1. Large Date Ranges
Cho date range > 1 năm, split thành chunks:
```python
from datetime import datetime, timedelta

start = datetime(2024, 1, 1)
end = datetime(2026, 1, 22)
chunk_size = timedelta(days=90)  # 3 months

current = start
all_dfs = []

while current < end:
    chunk_end = min(current + chunk_size, end)
    
    df = run_pipeline(
        symbol="BTCUSDT",
        interval="1h",
        start_date=current.strftime("%Y-%m-%d"),
        end_date=chunk_end.strftime("%Y-%m-%d"),
        save_to_mongodb=False,
        save_to_csv=False
    )
    
    if df is not None:
        all_dfs.append(df)
    
    current = chunk_end

# Combine all chunks
final_df = pd.concat(all_dfs)
final_df.to_csv("complete_dataset.csv")
```

### 2. Memory Optimization
Cho dataset cực lớn:
```python
# Use chunks
chunksize = 10000
for chunk in pd.read_csv("large_file.csv", chunksize=chunksize):
    # Process chunk
    pass
```

---

## 📝 Changelog

### Version 2.0 (Current)
- ✅ Fixed all critical bugs
- ✅ Added retry logic
- ✅ Improved error handling
- ✅ Added data validation
- ✅ More features (RSI, momentum, etc.)
- ✅ Multi-class targets
- ✅ Better logging
- ✅ MongoDB type conversion

### Version 1.0 (Original)
- Basic pipeline
- Price + sentiment features
- Binary classification only

---

## 🤝 Contributing

Nếu bạn tìm thấy bugs hoặc có suggestions:
1. Test thoroughly
2. Document changes
3. Add error handling
4. Update README

---

## 📞 Support

Nếu gặp vấn đề:
1. Check logs carefully
2. Verify MongoDB connection
3. Test with small date range first
4. Check Binance API status

---

## ⚠️ Important Notes

1. **API Rate Limits**: Binance có rate limit 1200 requests/minute. Pipeline đã optimize.
2. **Data Freshness**: Binance data có delay ~1 second.
3. **News Coverage**: Kết quả phụ thuộc vào quality và coverage của news data.
4. **Backfill**: Binance chỉ có historical data từ 2017.
5. **MongoDB Size**: Check disk space khi save large datasets.

---

## 📜 License

Free to use. Modify as needed for your projects.

---

## 🎯 Next Steps

After generating training data:
1. 🧹 **Data Cleaning**: Remove outliers, handle missing values
2. 🔧 **Feature Engineering**: Create more domain-specific features
3. 🤖 **Model Selection**: Try different algorithms (XGBoost, LSTM, Transformer)
4. 📊 **Backtesting**: Validate on out-of-sample data
5. 🚀 **Deployment**: Real-time prediction pipeline

**Good luck with your AI model! 🚀📈**
