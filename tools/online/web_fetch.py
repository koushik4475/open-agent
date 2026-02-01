# openagent/tools/online/web_fetch.py
"""
Web Page Fetch Tool (Online).

Downloads a URL and extracts clean, readable text.
Uses requests + BeautifulSoup — no headless browser needed.

LIMITATIONS:
  - Cannot execute JavaScript (pages that are JS-rendered will be empty).
  - Does not handle paywalls or login walls.
  - Timeout after 15 seconds.

For JS-heavy sites, the user should search instead of fetch.
"""

from __future__ import annotations
import logging
import asyncio
import re

import requests
from bs4 import BeautifulSoup

from openagent.config import settings

logger = logging.getLogger("openagent.tools.web_fetch")

# Polite User-Agent
_USER_AGENT = (
    "Mozilla/5.0 (compatible; OpenAgent/0.1; "
    "https://github.com/openagent) — open-source AI agent"
)

# Tags to strip (scripts, styles, nav cruft)
_STRIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"}


async def web_fetch(url: str) -> str:
    """
    Fetch a URL and return cleaned text content.
    """
    if not url:
        return "[No URL provided.]"

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info(f"Fetching URL: {url}")

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _do_fetch, url)


def _do_fetch(url: str) -> str:
    """Blocking HTTP fetch — runs in thread pool."""
    timeout = settings.search.timeout_seconds

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": _USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
        )
        resp.raise_for_status()

        # Only process HTML responses
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return f"[Non-HTML content type: {content_type}. Cannot extract text.]"

        return _extract_text(resp.text)

    except requests.exceptions.Timeout:
        return f"[Fetch timed out after {timeout}s. The page may be too slow.]"
    except requests.exceptions.ConnectionError:
        return "[Connection failed. Check your internet or the URL.]"
    except requests.exceptions.HTTPError as e:
        return f"[HTTP error: {e}]"
    except Exception as e:
        logger.error(f"Fetch error: {e}")
        return f"[Fetch failed: {e}]"


def _extract_text(html: str) -> str:
    """
    Parse HTML → clean text.

    Pipeline:
      1. Parse with BeautifulSoup
      2. Strip script/style/nav tags
      3. Get all text
      4. Collapse whitespace
      5. Remove empty lines
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise tags
    for tag in soup.find_all(_STRIP_TAGS):
        tag.decompose()

    # Extract text
    text = soup.get_text(separator="\n")

    # Clean up whitespace
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            lines.append(stripped)

    clean = "\n".join(lines)

    if not clean:
        return "[Page loaded but no readable text was found. It may be JS-rendered.]"

    logger.info(f"Extracted {len(clean)} chars from page")
    return clean
