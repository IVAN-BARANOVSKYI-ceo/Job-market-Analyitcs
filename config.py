import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"

RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_DIR = DATA_DIR / "database"

REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

DATABASE_PATH = BASE_DIR / "data" / "database" / "jobs.db"

ARBEITNOW_API_URL = "https://www.arbeitnow.com/api/job-board-api"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3