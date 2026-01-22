import os
from dotenv import load_dotenv

load_dotenv(override=True)

def init_mongo_db():
    # Dùng script khởi tạo MongoDB (tạo index + seed NewsSources)
    from .scripts.init_mongo import main as init_mongo
    init_mongo()

def main():
    backend = os.getenv("DB_BACKEND", "sql").lower()
    if backend == "mongo":
        init_mongo_db()
    else:
        print("SQL backend đã được loại bỏ. Vui lòng đặt DB_BACKEND=mongo trong .env.")

if __name__ == "__main__":
    main()