# 📰 CryptoNews UI - Hướng dẫn sử dụng

## 🎯 Tổng quan

Giao diện CryptoNews là một ứng dụng web hiện đại được xây dựng để hiển thị tin tức cryptocurrency theo thời gian thực với các tính năng:

✨ **Tính năng chính:**
- 📰 Hiển thị tin tức từ nhiều nguồn (CoinDesk, Cointelegraph, TradingView News)
- 🔍 Tìm kiếm tin tức theo từ khóa
- 🏷️ Lọc tin tức theo nguồn
- 😊 Phân tích cảm xúc (Sentiment Analysis)
- 🎨 Giao diện responsive, đẹp mắt
- ⚡ Tự động làm mới dữ liệu mỗi 5 phút
- 📱 Tối ưu hóa cho thiết bị di động

## 🚀 Cách chạy

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

Đảm bảo `requirements.txt` có các gói tối thiểu cho UI/API:
```
fastapi
uvicorn
pydantic
pymongo
```

### 2. Chạy server

```bash
python run_server.py
```

Hoặc chạy trực tiếp:

```bash
uvicorn app.api.main_api:app --reload --host 0.0.0.0 --port 8000
```

### 3. Truy cập giao diện

Mở trình duyệt và go tới:
```
http://localhost:8000
```

## 📁 Cấu trúc file

```
app/
├── templates/
│   └── index.html          # Giao diện chính
├── static/
│   ├── style.css           # CSS styling
│   └── app.js              # JavaScript logic
├── api/
│   └── main_api.py         # FastAPI endpoints
└── ...
```

## 🎮 Cách sử dụng

### Tìm kiếm tin tức
1. Nhập từ khóa vào ô "Tìm kiếm tin tức"
2. Kết quả sẽ lọc tự động khi bạn gõ

### Lọc theo nguồn tin
1. Chọn "Nguồn tin" từ dropdown
2. Chỉ tin từ nguồn đó sẽ được hiển thị

### Lọc theo cảm xúc
1. Chọn "Tích cực", "Tiêu cực", hoặc "Trung lập"
2. Xem tin có cảm xúc tương ứng

### Xem chi tiết tin tức
1. Click vào bất kỳ thẻ tin nào
2. Một cửa sổ chi tiết sẽ mở ra
3. Click "Đọc toàn bộ" để xem bài viết gốc

### Làm mới dữ liệu
- Click nút "Làm mới" để tải dữ liệu mới nhất
- Hoặc đợi 5 phút để tự động làm mới

## 🔌 API Endpoints

### Lấy tin tức
```
GET /api/news?limit=100&source=coindesk&offset=0
```

**Response:**
```json
[
  {
    "id": "1",
    "source": "coindesk",
    "title": "Bitcoin Reaches New All-Time High",
    "content": "Bitcoin has surpassed...",
    "summary": "Bitcoin breaks records",
    "published_at": "2025-12-20T10:30:00",
    "url": "https://...",
    "language": "en",
    "sentiment_score": 0.85,
    "sentiment_label": "positive"
  }
]
```

### Lấy chi tiết một tin
```
GET /api/news/{news_id}
```

### Tìm kiếm tin tức
```
GET /api/news/search?q=bitcoin&limit=20
```

### Lấy danh sách nguồn tin
```
GET /api/sources
```

## 🎨 Tùy chỉnh giao diện

### Thay đổi màu sắc

Chỉnh sửa file `app/static/style.css`:

```css
:root {
    --primary-color: #1f2937;
    --secondary-color: #3b82f6;
    --success-color: #10b981;
    /* ... */
}
```

### Thay đổi tốc độ làm mới

Chỉnh sửa file `app/static/app.js`:

```javascript
// Thay 5 * 60 * 1000 bằng thời gian mong muốn (milliseconds)
setInterval(() => {
    loadNews();
}, 5 * 60 * 1000);  // 5 minutes
```

### Thêm/Xóa nguồn tin

Chỉnh sửa file `app/templates/index.html` và thêm option vào select:

```html
<option value="your_source">Your Source Name</option>
```

## 🔌 Kết nối cơ sở dữ liệu

Giao diện dùng MongoDB. Để kết nối dữ liệu thực:

1. Bỏ comment các dòng `TODO` trong [app/api/main_api.py](app/api/main_api.py)
2. Sử dụng `db_session()` từ [app/core/storage.py](app/core/storage.py) (mặc định backend là Mongo)
3. Query từ collection `News`

**Ví dụ (Mongo/PyMongo):**
```python
from typing import Optional, List
from fastapi import FastAPI
from app.core.storage import db_session

app = FastAPI()

@app.get("/api/news")
def get_news(source: Optional[str] = None, limit: int = 10, offset: int = 0):
  with db_session() as db:
    q = {}
    if source:
      q["SourceCode"] = source  # hoặc lọc theo SourceId tùy dữ liệu lưu
    cursor = db.News.find(q).sort("PublishedAt", -1).skip(offset).limit(limit)
    items = []
    for doc in cursor:
      items.append({
        "id": str(doc.get("_id")),
        "source": doc.get("SourceCode"),
        "title": doc.get("Title"),
        "content": doc.get("Content"),
        "summary": doc.get("Summary"),
        "published_at": doc.get("PublishedAt"),
        "url": doc.get("Url"),
        "language": doc.get("Language"),
        "sentiment_score": doc.get("SentimentScore"),
        "sentiment_label": doc.get("SentimentLabel"),
      })
    return items
```

## 🛠️ Troubleshooting

### "Address already in use"
```bash
# Sử dụng port khác
uvicorn app.api.main_api:app --reload --port 8001
```

### "Module not found"
```bash
# Cài đặt dependencies
pip install -r requirements.txt
```

### Giao diện không tải
1. Kiểm tra console browser (F12) để xem lỗi
2. Đảm bảo server đang chạy
3. Xóa cache: Ctrl+Shift+Delete

## 📚 Tài liệu thêm

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Bootstrap 5](https://getbootstrap.com/)
- [MongoDB PyMongo](https://pymongo.readthedocs.io/en/stable/)

## 📝 License

MIT License - Tự do sử dụng, sửa đổi và phân phối

---

**Hỗ trợ:** Nếu có câu hỏi hoặc vấn đề, hãy kiểm tra tệp này hoặc xem logs của server.
