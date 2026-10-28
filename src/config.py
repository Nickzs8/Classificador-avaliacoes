import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

MONGO_USER = os.getenv("MONGO_USER", "admin")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB = os.getenv("MONGO_DB", "reviews_db")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "reviews")
MODEL_PATH = os.getenv("MODEL_PATH", "models/modelo_v1.joblib")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# quote_plus escapes special characters in the password
MONGO_URI = (
    f"mongodb://{quote_plus(MONGO_USER)}:{quote_plus(MONGO_PASSWORD)}"
    f"@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
)
