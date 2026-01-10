"""Simple caching mechanism for scraped data"""
import json
import os
import hashlib
from typing import Optional
from datetime import datetime, timedelta


CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
CACHE_DURATION = timedelta(hours=24)  # Cache for 24 hours


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def _get_cache_path(url: str) -> str:
    """Generate cache file path for a URL"""
    _ensure_cache_dir()
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{url_hash}.json")


def get_cached_html(url: str) -> Optional[str]:
    """
    Get cached HTML for a URL if it exists and is not expired.

    Returns None if cache miss or expired.
    """
    cache_path = _get_cache_path(url)

    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)

        # Check if cache is expired
        cached_time = datetime.fromisoformat(cache_data['timestamp'])
        if datetime.now() - cached_time > CACHE_DURATION:
            return None

        return cache_data['html']

    except Exception:
        return None


def save_cached_html(url: str, html: str):
    """Save HTML to cache"""
    cache_path = _get_cache_path(url)

    try:
        cache_data = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'html': html
        }

        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)

    except Exception:
        pass  # Silently fail on cache write errors
