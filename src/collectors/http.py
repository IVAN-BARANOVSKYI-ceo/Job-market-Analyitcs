import time

import requests

import config


# GET a JSON response with retries and basic rate-limit handling
def get_json(url, params=None, retries=3):
    headers = {"User-Agent": config.USER_AGENT}
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(
                url, params=params, headers=headers, timeout=config.REQUEST_TIMEOUT
            )
            if response.status_code == 429:
                time.sleep(config.REQUEST_DELAY * attempt * 5)
                continue
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError):
            if attempt == retries:
                raise
            time.sleep(config.REQUEST_DELAY * attempt)
    raise RuntimeError(f"Request failed after {retries} attempts: {url}")
