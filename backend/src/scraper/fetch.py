import httpx
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import logger
from .cache import get_cached_html, save_cached_html


async def fetch_html(url: str) -> str:
    """
    Fetch HTML from a URL with caching, proper headers, and error handling.

    Checks cache first to avoid repeated requests. Cache expires after 24 hours.
    Returns empty string on failure to allow graceful fallback.
    """
    # Check cache first
    cached_html = get_cached_html(url)
    if cached_html:
        logger.info("Using cached data for:", url)
        return cached_html

    try:
        # Add headers to avoid being blocked as a bot
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text

            # Save to cache
            save_cached_html(url, html)

            logger.info("Successfully fetched:", url)
            return html

    except httpx.TimeoutException:
        logger.warn("Timeout fetching URL:", url)
        return ""
    except httpx.HTTPStatusError as e:
        logger.warn(f"HTTP error {e.response.status_code} for URL:", url)
        return ""
    except Exception as e:
        logger.warn("Failed to fetch URL:", url, str(e))
        return ""