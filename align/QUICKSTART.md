# 🚀 QUICK START GUIDE

## Bắt đầu trong 5 phút

### 📦 Bước 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### ⚙️ Bước 2: Cấu hình MongoDB
Mở file `crypto_data_pipeline.py` và sửa dòng 31-32:
```python
MONGO_USERNAME = "your_username_here"  # ← Thay đổi
MONGO_PASSWORD = "your_password_here"  # ← Thay đổi
```

### ✅ Bước 3: Test Setup
```bash
python test_setup.py
```

Nếu tất cả test pass → Bạn đã sẵn sàng!

### 🎯 Bước 4: Chạy Pipeline

#### Option A: Quick Test (2 days data)
```python
python -c "
from crypto_data_pipeline import run_pipeline

df = run_pipeline(
    symbol='BTCUSDT',
    interval='1h',
    start_date='2026-01-20',
    end_date='2026-01-22',
    save_to_mongodb=False,
    save_to_csv=True
)
print(f'Done! Generated {len(df)} samples')
"
```

#### Option B: Full Run (3 weeks data)
```python
python -c "
from crypto_data_pipeline import run_pipeline

df = run_pipeline(
    symbol='BTCUSDT',
    interval='1h',
    start_date='2026-01-01',
    end_date='2026-01-22',
    save_to_mongodb=True,
    save_to_csv=True
)
"
```

#### Option C: Custom Script
Create `run.py`:
```python
from crypto_data_pipeline import run_pipeline

# Customize these
CONFIG = {
    "symbol": "BTCUSDT",
    "interval": "1h",
    "start_date": "2026-01-01",
    "end_date": "2026-01-22",
    "save_to_mongodb": True,
    "save_to_csv": True
}

df = run_pipeline(**CONFIG)
print(f"✅ Done! {len(df)} samples created")
```

Then run:
```bash
python run.py
```

---

## 📊 Expected Output

### Console Output:
```
======================================================================
STARTING CRYPTO DATA PIPELINE
======================================================================

[1/6] Fetching BTCUSDT price data from Binance...
      ✓ Fetched 528 price records

[2/6] Connecting to MongoDB...
      ✓ MongoDB connection successful

[3/6] Fetching news from MongoDB...
      ✓ Fetched 1,234 news records

[4/6] Aggregating news by 1H...
      ✓ Aggregated to 528 time windows

[5/6] Creating features...
      ✓ Created dataset with 504 samples
      ✓ Total features: 68

[6/6] Saving results...
      ✓ Saved to CSV: training_data_BTCUSDT_1h_2026-01-01_to_2026-01-22.csv
      ✓ Saved to MongoDB: 504 records

======================================================================
PIPELINE COMPLETED SUCCESSFULLY ✓
======================================================================
```

### Files Created:
- `training_data_BTCUSDT_1h_2026-01-01_to_2026-01-22.csv`
- MongoDB collection: `cryptonews.AI_Training_Data`

---

## 🎓 What's Next?

### 1. Train a Simple Model
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Load data
df = pd.read_csv("training_data_BTCUSDT_1h_2026-01-01_to_2026-01-22.csv")

# Prepare features
feature_cols = [col for col in df.columns 
                if not col.startswith('target_') 
                and col not in ['timestamp', 'symbol', 'interval']]

X = df[feature_cols].fillna(0)
y = df['target_direction_1h'].dropna()

# Align X and y
X = X.loc[y.index]

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Evaluate
accuracy = model.score(X_test, y_test)
print(f"Accuracy: {accuracy:.2%}")
```

### 2. Analyze Features
```python
import pandas as pd

df = pd.read_csv("training_data_BTCUSDT_1h_2026-01-01_to_2026-01-22.csv")

# Check correlations
target_corr = df.corr()['target_return_1h'].sort_values(ascending=False)
print("Top 10 correlated features:")
print(target_corr.head(11))  # 11 because target_return_1h is #1
```

### 3. Visualize Data
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("training_data_BTCUSDT_1h_2026-01-01_to_2026-01-22.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')

# Plot price and sentiment
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 8), sharex=True)

ax1.plot(df.index, df['close'], label='BTC Price')
ax1.set_ylabel('Price (USD)')
ax1.legend()
ax1.grid(True)

ax2.plot(df.index, df['sentiment_score_mean'], label='Sentiment', color='orange')
ax2.set_ylabel('Sentiment Score')
ax2.set_xlabel('Date')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.savefig('price_vs_sentiment.png')
plt.show()
```

---

## ⚠️ Troubleshooting

### Issue: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Issue: "MongoDB connection failed"
1. Check username/password in `crypto_data_pipeline.py`
2. Verify internet connection
3. Check MongoDB Atlas IP whitelist (add 0.0.0.0/0 for testing)

### Issue: "No news data found"
- Pipeline sẽ vẫn chạy với chỉ price data
- Check `PublishedAt` field trong MongoDB
- Verify date range có data

### Issue: "Binance rate limit"
- Đã có retry logic tự động
- Nếu vẫn fail, tăng sleep time trong code

---

## 📞 Need Help?

1. Run test: `python test_setup.py`
2. Check logs in console
3. Verify MongoDB connection
4. Test với date range nhỏ trước (2-3 days)

---

## 🎯 Pro Tips

1. **Start small**: Test với 2-3 days trước khi chạy full
2. **Monitor logs**: Watch console output để catch errors sớm
3. **Check data quality**: Run validation sau khi generate
4. **Backup MongoDB**: Trước khi chạy với `save_to_mongodb=True`
5. **Use config.py**: Customize settings thay vì hardcode

---

## ✅ Checklist

- [ ] Installed dependencies
- [ ] Updated MongoDB credentials
- [ ] Ran `test_setup.py` successfully
- [ ] Tested with small date range
- [ ] Generated training data
- [ ] Verified CSV file
- [ ] Checked MongoDB collection
- [ ] Ready to train model!

**Happy coding! 🚀**
