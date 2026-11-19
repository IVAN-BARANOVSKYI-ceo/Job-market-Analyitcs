import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import requests
import json
from datetime import datetime
from config import ARBEITNOW_API_URL, REQUEST_TIMEOUT, RAW_DATA_DIR


def fetch_page(url):
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()



def fetch_jobs(max_pages=2):
    all_jobs = []
    url = ARBEITNOW_API_URL
    pages_fetched = 0
    while url and pages_fetched < max_pages:
        data = fetch_page(url)
        all_jobs.extend(data.get("data", []))
        url = data.get("links", {}).get("next")
        pages_fetched += 1
    return all_jobs

def save_raw_data(jobs):
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = RAW_DATA_DIR / f"arbeitnow_jobs_{timestamp}.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(jobs, file, ensure_ascii=False, indent=4)

    return file_path

def collect():
    jobs = fetch_jobs()
    file_path = save_raw_data(jobs)
    print(f"Saved {len(jobs)} jobs to {file_path}")

if __name__ == "__main__":
    collect()