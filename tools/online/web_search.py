# openagent/tools/online/web_search.py
"""
Web Search Tool — DuckDuckGo (Online).

Uses the `duckduckgo-search` library (MIT license, PyPI).
No API key required. No registration. No cost.

WHY DuckDuckGo:
  - Privacy-focused (no tracking).
  - No API key = no account = no cost.
  - The library scrapes DDG's lite HTML endpoint directly.
  - MIT licensed. Safe to use in any project.

LIMITATIONS:
  - Rate limiting: DDG may throttle if you spam requests.
    We add a 1-second delay between calls to be respectful.
  - Result quality varies (no personalization = sometimes less relevant).
  - Can be blocked in rare cases. Graceful fallback is built in.
"""

from __future__ import annotations
import logging
import time
import asyncio

from duckduckgo_search import DDGS

from openagent.config import settings

logger = logging.getLogger("openagent.tools.web_search")

# Minimum delay between searches to avoid rate limiting
_MIN_DELAY_SECONDS = 1.0
_last_search_time: float = 0.0


async def web_search(query: str) -> str:
    """
    Search DuckDuckGo and return formatted results.
    Returns a string ready to inject into an LLM prompt.
    """
    global _last_search_time
    cfg = settings.search

    # Rate-limit ourselves — be a good citizen
    elapsed = time.time() - _last_search_time
    if elapsed < _MIN_DELAY_SECONDS:
        await asyncio.sleep(_MIN_DELAY_SECONDS - elapsed)

    logger.info(f"Web search: '{query}'")

    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            _do_search,
            query,
            cfg.max_results,
            cfg.region,
            cfg.safesearch,
            cfg.timeout_seconds,
        )

        _last_search_time = time.time()

        if not results:
            return "[No search results found for this query.]"

        # Format results for LLM consumption
        formatted_parts = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "Untitled")
            url = r.get("href", "N/A")
            snippet = r.get("body", "No snippet available.")
            formatted_parts.append(f"{i}. {title}\n   URL: {url}\n   {snippet}")

        return "\n\n".join(formatted_parts)

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return f"[Web search failed: {e}. You may be offline or rate-limited.]"


def _do_search(query: str, max_results: int, region: str, safesearch: str, timeout: int) -> list[dict]:
    """Blocking DDG search — runs in thread pool."""
    with DDGS(timeout=timeout) as ddgs:
        return list(ddgs.text(
            query,
            max_results=max_results,
            region=region,
            safesearch=safesearch,
        ))
