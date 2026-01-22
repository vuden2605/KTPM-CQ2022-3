# 🔍 Sentiment Analysis với FinBERT (tối ưu cho tin tài chính)

## 📋 Tóm tắt

**Sentiment Analysis** (Phân tích cảm xúc) giúp xác định thái độ/cảm xúc trong văn bản.

Trong dự án này, mặc định dùng **FinBERT** (transformers) cho tin tức tài chính/crypto; nếu không khả dụng, sẽ fallback sang **VADER** để tránh gián đoạn.

---

## 🎯 Cách hoạt động

### 1️⃣ FinBERT là gì?

FinBERT là mô hình BERT fine-tune cho miền tài chính, cho nhãn: `positive`, `negative`, `neutral`.
Ưu điểm:
- ✅ Hiểu ngữ nghĩa tốt hơn với văn bản tin tức tài chính
- ✅ Nhãn chuyên biệt cho finance/news
- ✅ Phù hợp crypto/markets

Fallback: khi không thể tải/chạy FinBERT, hệ thống dùng VADER (nhanh, không tốn tài nguyên) để đảm bảo hoạt động.

### 2️⃣ Quy trình phân tích

```
Văn bản đầu vào
    ↓
FinBERT (transformers) hoặc VADER (fallback)
    ↓
Tính toán điểm số (Compound Score: -1 to +1)
    ↓
Phân loại (Positive/Negative/Neutral)
    ↓
Trả về: Score + Label + Confidence
```

### 3️⃣ Scoring System

FinBERT:
- Trả về phân phối xác suất 3 nhãn: `positive`, `negative`, `neutral`.
- `label`: nhãn có xác suất cao nhất.
- `confidence`: xác suất của nhãn dự đoán.
- `compound`: được suy ra từ `positive - negative` (phạm vi -1 → +1).
- `score`: chuẩn hóa từ compound về 0 → 1: `(compound + 1) / 2`.

VADER (fallback): dùng ngưỡng compound chuẩn (≥ 0.05: positive, ≤ -0.05: negative, else neutral).

---

## 📊 Ví dụ thực tế (FinBERT)

### ✅ Tin Tích cực (Positive)

```
Tiêu đề: "Bitcoin Reaches New All-Time High"
Nội dung: "Bitcoin has surpassed the previous all-time high, reaching new levels 
          of adoption and market interest. Institutions continue buying..."

📈 FinBERT: label=positive, confidence≈0.85, score≈0.9 ✅
```

**Từ khóa tích cực được phát hiện:**
- "New All-Time High" - tốt lành
- "adoption" - tiến bộ
- "interest" - hứng thú
- "continue buying" - mua tích cực

---

### 😞 Tin Tiêu cực (Negative)

```
Tiêu đề: "Bitcoin Price Crashes Following Negative News"
Nội dung: "Bitcoin has crashed dramatically following negative regulatory news. 
          Panic selling dominates trading volumes."

📉 FinBERT: label=negative, confidence≈0.78, score≈0.2 ❌
```

**Từ khóa tiêu cực được phát hiện:**
- "Crashes" - sụp đổ
- "Negative" - xấu
- "Panic" - hoảng sợ
- "selling" - bán tháo

---

### 😐 Tin Trung lập (Neutral)

```
Tiêu đề: "Market Volatility Increases Amid Bearish Pressure"
Nội dung: "Recent market trends show increased volatility as investors react 
          to macroeconomic factors."

⚪ FinBERT: label=neutral, confidence≈0.60, score≈0.5 ⚪
```

**Phân tích:**
- "Volatility" - trung tính (không tốt, không xấu)
- "Increased" - có thể tốt hoặc xấu
- "Macroeconomic factors" - chuyên nghiệp, trung lập

---

## 🔧 Cài đặt & Sử dụng

### 1. Cài đặt (FinBERT + fallback VADER)

```bash
pip install transformers torch nltk
```

Lần đầu chạy, transformers sẽ tự tải mô hình `yiyanghkust/finbert-tone`.

### 2. Sử dụng trong code

```python
from app.services.sentiment_analyzer import analyze_news_sentiment

# Phân tích một bài báo
result = analyze_news_sentiment(
    title="Bitcoin Reaches New All-Time High",
    content="Bitcoin has surpassed...",
    summary="Bitcoin breaks records"
)

print(result)
# Output (FinBERT):
# {
#     'score': 0.90,            # 0-1 (từ compound chuẩn hóa)
#     'label': 'positive',      # positive/negative/neutral
#     'compound': 0.80,         # pos - neg (ước lượng)
#     'confidence': 0.85,       # xác suất nhãn dự đoán
#     'positive': 0.85,
#     'negative': 0.05,
#     'neutral': 0.10
# }
```

### 3. Phân tích hàng loạt

```python
from app.services.sentiment_analyzer import batch_analyze_sentiment

news_items = [
    {"title": "...", "content": "...", "summary": "..."},
    {"title": "...", "content": "...", "summary": "..."},
]

# Tự động thêm sentiment_score và sentiment_label
results = batch_analyze_sentiment(news_items)
```

---

## 🧪 Kiểm thử nhanh

Chạy test nội bộ của service:
```bash
python -m app.services.sentiment_analyzer
```
Kết quả sẽ hiển thị nhãn, score, compound, confidence cho một số câu ví dụ.

---

## 🎨 Hiển thị UI

Giao diện sẽ hiển thị badges:

```html
<!-- Tích cực -->
<span class="sentiment-badge sentiment-positive">TÍCH CỰC</span>

<!-- Tiêu cực -->
<span class="sentiment-badge sentiment-negative">TIÊU CỰC</span>

<!-- Trung lập -->
<span class="sentiment-badge sentiment-neutral">TRUNG LẬP</span>
```

---

## ⚙️ Cách VADER tính toán

### Bước 1: Tokenize văn bản
```
"Bitcoin Reaches New All-Time High"
↓
["Bitcoin", "Reaches", "New", "All-Time", "High"]
```

### Bước 2: Tra từ điển
```
"Reaches" → neutral (0.0)
"New" → positive (0.1)
"High" → positive (0.2)
↓
Tổng = Positive
```

### Bước 3: Tính Compound Score
```
VADER formula: compound = Σ(sentiment scores) / √(Σ|scores|²)
Range: -1.0 (very negative) to +1.0 (very positive)

Result: 0.612 → POSITIVE
```

---

## 🔬 So sánh nhanh

| Method | Ưu điểm | Nhược điểm | Chi phí |
|---|---|---|---|
| **FinBERT** (mặc định) | Hiểu ngữ cảnh tài chính tốt | Cần tài nguyên, tải model | $0 |
| VADER (fallback) | Nhanh, nhẹ, miễn phí | Hiểu ngữ cảnh hạn chế | $0 |
| OpenAI/LLM | Chính xác, ngữ cảnh sâu | Chi phí, latency | $0.01-0.05/call |

---

## 🚀 Cải thiện trong tương lai

### 1. Bổ sung lexicon crypto khi fallback VADER
```python
# Thêm crypto-specific words vào VADER lexicon
custom_lexicon = {
    'bullish': 0.8,      # Tích cực
    'bearish': -0.8,     # Tiêu cực
    'hodl': 0.5,         # Tích cực
    'dump': -0.6,        # Tiêu cực
    'pump': 0.7,         # Tích cực
}
```

### 2. Kết hợp với AI models
```python
# Sử dụng OpenAI nếu cần độ chính xác cao
if need_high_accuracy:
    result = openai.analyze_sentiment(text)
else:
    result = vader_analyzer.analyze(text)
```

### 3. Multi-language support
```python
# Hỗ trợ nhiều ngôn ngữ
from transformers import pipeline
classifier = pipeline("sentiment-analysis", model="xlm-roberta-base")
```

---

## 📚 Tài liệu

- [FinBERT tone model](https://huggingface.co/yiyanghkust/finbert-tone)
- [Transformers (HuggingFace)](https://huggingface.co/docs/transformers)
- [VADER sentiment (fallback)](https://github.com/cjhutto/vaderSentiment)

---

## ❓ FAQ

**Q: Tại sao tin "Crypto Markets Face Downturn" lại là POSITIVE?**
A: Vì từ "Face" có thể được hiểu là tiếp cận (positive). Đây là giới hạn của VADER. Với AI models, sẽ chính xác hơn.

**Q: Độ chính xác của VADER là bao nhiêu?**
A: FinBERT thường chính xác hơn VADER với tin tức tài chính; VADER ~80-85% cho tiếng Anh, kém hơn với sarcasm/ngữ nghĩa phức tạp.

**Q: Có cách nào để cải thiện độ chính xác?**
A: Có! Thêm crypto-specific lexicon hoặc sử dụng transformer models (BERT, etc.)

---

## 🎓 Học thêm

Chạy demo tích hợp:
```bash
python -m app.services.sentiment_analyzer
```
