import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Paths
RAW_DIR = BASE_DIR / "data" / "raw"
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "data" / "database" / "jobs.db"))
if not DB_PATH.is_absolute():
    DB_PATH = BASE_DIR / DB_PATH
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# API endpoints
ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"
REMOTIVE_URL = "https://remotive.com/api/remote-jobs"

# Collection settings
ARBEITNOW_MAX_PAGES = int(os.getenv("ARBEITNOW_MAX_PAGES", "6"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.0"))
REQUEST_TIMEOUT = 30
USER_AGENT = os.getenv("USER_AGENT", "job-market-intelligence/1.0 (portfolio project)")

# Analysis settings: minimum number of jobs in a group to show it in comparisons
MIN_GROUP_SIZE = 10
