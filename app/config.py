import os
from dotenv import load_dotenv

load_dotenv()

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./urls.db")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds