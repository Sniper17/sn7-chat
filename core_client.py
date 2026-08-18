import os
import requests

SN7_CORE_URL = os.getenv("SN7_CORE_URL", "https://sn7-core.onrender.com").strip().rstrip("/")
BROADCASTER_USER_ID = os.getenv("BROADCASTER_USER_ID", "1").strip()
TIMEOUT = float(os.getenv("SN7_CORE_TIMEOUT", "10"))

def core_get(path, params=None):
    url = f"{SN7_CORE_URL}{path}"
    response = requests.get(
        url,
        params=params or {},
        timeout=TIMEOUT,
        headers={"Accept": "application/json"}
    )
    response.raise_for_status()
    return response.json()

def get_balance(username):
    return core_get(
        f"/api/economy/{BROADCASTER_USER_ID}/balance",
        {"username": username}
    )

def get_settings():
    return core_get(f"/api/settings/{BROADCASTER_USER_ID}")

def get_ranking(limit=None):
    params = {}
    if limit:
        params["limit"] = limit
    return core_get(f"/api/ranking/{BROADCASTER_USER_ID}", params)
