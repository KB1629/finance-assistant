"""Configuration for data ingestion agents."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# API keys
ALPHAVANTAGE_API_KEY: str = os.getenv("ALPHAVANTAGE_KEY", "demo")

# Caching
CACHE_DIR: Path = Path("./cache")
API_CACHE_DIR: Path = CACHE_DIR / "api"
SCRAPER_CACHE_DIR: Path = CACHE_DIR / "scraper"

# Ensure cache directories exist
os.makedirs(API_CACHE_DIR, exist_ok=True)
os.makedirs(SCRAPER_CACHE_DIR, exist_ok=True)

# Scraper settings
SEC_API_BASE_URL: str = "https://www.sec.gov/cgi-bin/browse-edgar"
USER_AGENT: str = (
    "Finance Assistant (academic project) Contact: example@example.com"
)
REQUEST_DELAY_SEC: float = 0.1  # To respect SEC's rate limits 