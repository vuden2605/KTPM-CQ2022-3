## Hướng dẫn Setup (Crawler + API)

### Yêu cầu
- Python 3.10+
- SQL Server (hoặc tương thích ODBC) đã chạy
- ODBC Driver cho SQL Server (ví dụ: "ODBC Driver 17 for SQL Server")

### Cài đặt
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Cấu hình `.env` (Mongo-only)
Tạo file `.env` ở thư mục gốc dự án:

- DB_BACKEND=mongo
- MONGO_URI=mongodb://localhost:27017
- MONGO_DB_NAME=cryptonews
- SKIP_AI_CONFIG=1                # (tuỳ chọn) bỏ qua AI khi tạo config crawler
- ENABLE_RENDERED_FETCH=0         # (tuỳ chọn) bật Playwright nếu cần HTML render
- CRAWL_WATCH=1                   # (tuỳ chọn) bật chạy lặp liên tục
- CRAWL_INTERVAL_SECONDS=60       # (tuỳ chọn) khoảng cách giữa các lần chạy (giây)

### Khởi tạo DB (Mongo)
```powershell
python -m app.main
```
Lệnh này sẽ tạo index và seed `NewsSources` trong Mongo.

### Thêm nguồn tin mẫu
Đã gộp vào bước khởi tạo Mongo. Bạn chỉ cần chạy:
```powershell
python -m app.main
```
Hoặc chạy trực tiếp script seeding:
```powershell
python -m app.scripts.init_mongo
```

### Chạy crawler (một lần)
```powershell
python -m app.scripts.run_all_crawlers
```

### Chạy theo lịch mỗi 1 phút
Có 2 cách:

1) Dùng `.env` (khuyến nghị, không cần tham số CLI)
```powershell
# Trong .env:
CRAWL_WATCH=1
CRAWL_INTERVAL_SECONDS=60

# Chạy:
python -m app.scripts.run_all_crawlers
```

2) Dùng tham số CLI (ghi đè .env nếu có)
```powershell
python -m app.scripts.run_all_crawlers --watch --interval 60
```

Tuỳ chọn kiểm thử nhanh một vài chu kỳ:
```powershell
python -m app.scripts.run_all_crawlers --watch --interval 60 --max-runs 2
```

### (Tuỳ chọn) Lên lịch qua Windows Task Scheduler
```powershell
schtasks /Create /SC MINUTE /MO 1 /TN "CryptoNewsCrawlers" /TR "python -m app.scripts.run_all_crawlers" /RU "%USERNAME%"
# Xoá lịch:
schtasks /Delete /TN "CryptoNewsCrawlers" /F
```

### Chạy API server
```powershell
uvicorn app.api.main_api:app --reload
```

### Ghi chú
- Dự án hiện chạy MongoDB mặc định (đã bỏ SQL Server). Nếu `.env` không đặt `DB_BACKEND`, hệ thống vẫn chọn `mongo` theo mặc định.
- File `app/core/scheduler.py` cũ không còn sử dụng do phụ thuộc `crawler_runner` (không tồn tại). Vui lòng dùng `app.scripts.run_all_crawlers` như hướng dẫn ở trên.
- Các file test và SQL script mẫu đã được dọn bớt để tập trung vào crawler.
