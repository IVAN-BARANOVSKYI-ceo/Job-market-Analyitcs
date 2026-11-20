import json
from datetime import datetime
from pathlib import Path

import config


# Save raw API data to a new timestamped JSON file (never overwrites)
def save_raw(source, jobs, raw_dir=None):
    raw_dir = Path(raw_dir or config.RAW_DIR)
    raw_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = raw_dir / f"{source}_{timestamp}.json"
    with open(path, "x", encoding="utf-8") as file:
        json.dump(jobs, file, ensure_ascii=False)
    return path


# Load the most recent raw file of a source
def load_latest_raw(source, raw_dir=None):
    raw_dir = Path(raw_dir or config.RAW_DIR)
    files = sorted(raw_dir.glob(f"{source}_*.json"))
    if not files:
        raise FileNotFoundError(f"No raw files found for source '{source}' in {raw_dir}")
    with open(files[-1], "r", encoding="utf-8") as file:
        return json.load(file)
