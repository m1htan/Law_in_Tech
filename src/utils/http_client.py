import time
import requests
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger("http")

def get(url: str, timeout: int = 15, headers: Optional[dict] = None, sleep_after: float = 0.0) -> Optional[requests.Response]:
    try:
        resp = requests.get(url, timeout=timeout, headers=headers)
        if sleep_after > 0:
            time.sleep(sleep_after)
        if resp.status_code == 200:
            return resp
        logger.warning(f"GET {url} -> HTTP {resp.status_code}")
        return None
    except Exception as e:
        logger.warning(f"GET {url} failed: {e}")
        return None
