# 🚀 Development Guide - Hot Reload Setup

## 📋 Overview

Dự án này sử dụng 2 servers để development:
- **Vite Dev Server** (port 5173) - Frontend với hot reload
- **FastAPI Backend** (port 8000) - API server

## 🛠️ Setup

### 1. Cài đặt Node.js dependencies

```bash
npm install
```

### 2. Cài đặt Python dependencies (Backend)

```bash
pip install -r requirements.txt
```

Yêu cầu tối thiểu cho backend:
```
fastapi
uvicorn
pydantic
pymongo
```

### 3. Chạy cả 2 servers

**Terminal 1 - Backend (FastAPI):**
```bash
python run_server.py
```
→ Chạy trên http://localhost:8000

**Terminal 2 - Frontend (Vite):**
```bash
npm run dev
```
→ Chạy trên http://localhost:5173

## 🎯 Cách sử dụng

### Development Mode (có hot reload)

1. Start backend: `python run_server.py` (API dùng MongoDB qua `app/core/storage.py`)
2. Start frontend: `npm run dev`
3. Mở browser: http://localhost:5173
4. Sửa code trong `app/templates/`, `app/static/`
5. **Tự động reload** ngay lập tức! ⚡

### Production Mode (không cần Vite)

```bash
python run_server.py
```
→ Mở http://localhost:8000 (FastAPI serve static files)

## 📁 File Structure

```
app/
├── templates/
│   └── index.html        # Sửa ở đây → Auto reload
├── static/
│   ├── style.css         # Sửa ở đây → Auto reload
│   └── app.js            # Sửa ở đây → Auto reload
└── api/
    └── main_api.py       # Backend code

vite.config.js            # Vite configuration
package.json              # NPM dependencies
```

## ⚡ Hot Reload Features

### ✅ Được hỗ trợ:
- ✨ HTML changes
- 🎨 CSS changes
- 💻 JavaScript changes
- 🖼️ Static assets

### ❌ Không tự động reload:
- Python backend code (cần restart `python run_server.py`)
- Database changes
- Environment variables

## 🔧 Vite Configuration

Vite đã được cấu hình để:
- ✅ Proxy `/api/*` requests đến FastAPI (port 8000)
- ✅ Serve static files từ `app/static/`
- ✅ Hot Module Replacement (HMR)
- ✅ Auto open browser

Ví dụ proxy (vite.config.js):
```js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

## 📝 NPM Scripts

```bash
npm run dev      # Start Vite dev server (hot reload)
npm run build    # Build for production
npm run preview  # Preview production build
```

## 🐛 Troubleshooting

### Port 5173 đã được sử dụng
```bash
# Thay đổi port trong vite.config.js
server: {
  port: 3000  # Đổi port khác
}
```

### API calls không hoạt động
- Đảm bảo FastAPI server đang chạy trên port 8000
- Kiểm tra console của browser và terminal để xem lỗi
- Kiểm tra kết nối MongoDB (biến `.env`: `MONGO_URI`, `MONGO_DB_NAME`)

### Hot reload không hoạt động
- Hard refresh: Ctrl+Shift+R (Windows) hoặc Cmd+Shift+R (Mac)
- Check terminal Vite có errors không
- Restart Vite server

## 💡 Tips

1. **Luôn chạy cả 2 servers** khi development
2. **Sử dụng Vite URL** (5173) để có hot reload
3. **Python code thay đổi** → Restart `run_server.py`
4. **Frontend code thay đổi** → Tự động reload!

## 🚀 Quick Start

```bash
# Terminal 1
python run_server.py

# Terminal 2
npm install
npm run dev

# Mở browser: http://localhost:5173
```

Enjoy hot reload! 🔥
