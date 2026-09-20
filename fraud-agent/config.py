import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# TigerGraph Settings
TG_HOST = os.getenv("TG_HOST", "")
TG_GRAPHNAME = os.getenv("TG_GRAPHNAME", "GraphmeetsAIdetective")
TG_SECRET = os.getenv("TG_SECRET", "")
TG_USERNAME = os.getenv("TG_USERNAME", "")
TG_PASSWORD = os.getenv("TG_PASSWORD", "")
TG_TGCLOUD = os.getenv("TG_TGCLOUD", "false").lower() in ("true", "1", "yes")

# Gemini Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
TG_API_TOKEN = os.getenv("TG_API_TOKEN", "")

# Paths
DATA_DIR = BASE_DIR
CASES_OUTPUT_DIR = BASE_DIR / "cases"
DUCKDB_PATH = BASE_DIR / "fraud_data.duckdb"
PARQUET_PATH = BASE_DIR / "transactions.parquet"
EMBEDDINGS_CACHE_PATH = BASE_DIR / "embeddings_cache.json"

# Ensure directories exist
CASES_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
