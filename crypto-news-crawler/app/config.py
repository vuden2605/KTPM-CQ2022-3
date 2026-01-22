import os
from dotenv import load_dotenv

# Nạp biến môi trường từ .env (Mongo-only)
load_dotenv(override=True)

# Backend mặc định: MongoDB
DB_BACKEND = os.getenv("DB_BACKEND", "mongo")

# Thông số MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "cryptonews")

def get_mongo_config():
    return {
        "backend": DB_BACKEND,
        "uri": MONGO_URI,
        "db_name": MONGO_DB_NAME,
    }