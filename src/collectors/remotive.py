import config
from src.collectors.http import get_json


# Download remote job postings from the Remotive API (a single request)
def fetch_jobs():
    payload = get_json(config.REMOTIVE_URL)
    return payload.get("jobs", [])
