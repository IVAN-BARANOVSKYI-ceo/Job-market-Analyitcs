
# Imports
import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")

# Data directories
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")

RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_DIR = DATA_DIR / "database"

# Reports directories
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Database configuration
DATABASE_PATH = BASE_DIR / os.getenv(
    "DATABASE_PATH",
    "data/database/jobs.db"
)

# API configuration
ARBEITNOW_API_URL = (
    "https://www.arbeitnow.com/api/job-board-api"
)

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

# API request settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3