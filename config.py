import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
    MONGO_DB = os.getenv("MONGO_DB", "jaeger_trace_db")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-insecure-secret-key-12345")
    PORT = int(os.getenv("PORT", "5000"))
    
    # Development admin account initialized in init_db
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
