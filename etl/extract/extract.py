import os
import requests
import pandas as pd

DEFAULT_URL = "https://data.cityofnewyork.us/resource/h9gi-nx95.json"

def extract(limit: int = 50000) -> pd.DataFrame:
    """
    Live extract from NYC Open Data (Motor Vehicle Collisions - Crashes)
    """
    url = os.getenv("NYC_CRASHES_API_URL", DEFAULT_URL)

    params = {
        "$limit": limit,
        "$order": "crash_date DESC",
        # Only rows with location
        "$where": "latitude IS NOT NULL AND longitude IS NOT NULL"
    }

    headers = {}
    # optional app token (helps rate limits)
    token = os.getenv("SOCRATA_APP_TOKEN")
    if token:
        headers["X-App-Token"] = token

    r = requests.get(url, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    return pd.DataFrame(data)
