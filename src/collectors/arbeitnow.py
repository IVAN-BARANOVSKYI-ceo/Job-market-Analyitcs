import logging
import time

import config
from src.collectors.http import get_json

logger = logging.getLogger(__name__)


# Download job postings from the Arbeitnow API, page by page
def fetch_jobs(max_pages=None):
    max_pages = max_pages or config.ARBEITNOW_MAX_PAGES
    jobs = []
    for page in range(1, max_pages + 1):
        try:
            payload = get_json(config.ARBEITNOW_URL, params={"page": page})
        except Exception as exc:
            if page == 1:
                raise
            logger.warning("Arbeitnow page %s failed, keeping earlier pages: %s", page, exc)
            break

        data = payload.get("data", [])
        if not data:
            break
        jobs.extend(data)
        time.sleep(config.REQUEST_DELAY)
    return jobs
