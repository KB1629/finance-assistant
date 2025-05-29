"""Configuration settings for data ingestion services."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(".") / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# API keys
ALPHAVANTAGE_API_KEY: str = os.getenv("ALPHAVANTAGE_KEY", "demo")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AIzaSyC3EI4LbmU1-AhjbCMQc8noKS_cV7cITkc")

# LLM configuration
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")

# Cache directories
API_CACHE_DIR = Path("./cache/api")
SCRAPER_CACHE_DIR = Path("./cache/scraper")
DOCUMENT_CACHE_DIR = Path("./cache/documents")

# Create cache directories if they don't exist
os.makedirs(API_CACHE_DIR, exist_ok=True)
os.makedirs(SCRAPER_CACHE_DIR, exist_ok=True)
os.makedirs(DOCUMENT_CACHE_DIR, exist_ok=True)

# Service URLs
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")

# Scraper settings
SEC_API_BASE_URL: str = "https://www.sec.gov/cgi-bin/browse-edgar"
USER_AGENT: str = (
    "Finance Assistant (academic project) Contact: example@example.com"
)
REQUEST_DELAY_SEC: float = 0.1  # To respect SEC's rate limits 