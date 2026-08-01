# openagent/tools/online/lookup.py
"""
Lookup Tool — DuckDuckGo text + image search (Online).

Product/visual lookups ("lookup nothing phone 3", "show images of ...")
return ready-to-render Markdown cards: a linked title, a clickable
thumbnail and a snippet per result — the ChatGPT-style product answer.

The output intentionally bypasses the LLM: the agent returns it
verbatim so real URLs reach the UI instead of being paraphrased away
(the system prompt forbids the model from inventing URLs, so links
would otherwise be dropped). The web UI already renders Markdown
images and links (marked.js + .bubble img/a styling).
"""

from __future__ import annotations

import asyncio
import logging
import re
import time

try:
    from duckduckgo_search import DDGS
except ImportError:  # package renamed duckduckgo-search → ddgs after v7
    from ddgs import DDGS

from openagent.config import settings

logger = logging.getLogger("openagent.tools.lookup")

# Minimum delay between lookups to avoid rate limiting
_MIN_DELAY_SECONDS = 1.0
_last_lookup_time: float = 0.0

_RESULT_COUNT = 3

# Trigger phrases stripped from the user text to isolate the search term
_LEAD_RE = re.compile(
    r"^(?:please\s+|can\s+you\s+|hey\s+)*"
    r"(?:lookup|look\s*up|show\s+me|show|find|search\s+for|search)\s+",
    re.IGNORECASE,
)
_TAIL_RE = re.compile(
    r"\s+with\s+(?:an?\s+)?(?:image|images|picture|pictures|photo|photos|link|links)s?\s*[.?!]*$",
    re.IGNORECASE,
)
_OF_RE = re.compile(
    r"^(?:the\s+)?(?:image|images|picture|pictures|photo|photos|product|products)\s+(?:of|for)\s+",
    re.IGNORECASE,
)


def _clean_query(text: str) -> str:
    q = text.strip()
    prev = None
    while prev != q:
        prev = q
        q = _LEAD_RE.sub("", q)
        q = _TAIL_RE.sub("", q)
        q = _OF_RE.sub("", q)
        q = q.strip()
    return q or text.strip()


def _md_safe(s: str) -> str:
    """Strip characters that would break Markdown link/image syntax."""
    return re.sub(r"[\[\]()]", " ", s).strip()


async def lookup(query: str) -> str:
    """
    Search DuckDuckGo (text + images) and return Markdown cards.
    Returns a string that is displayed directly, not fed to the LLM.
    """
    global _last_lookup_time
    cfg = settings.search

    q = _clean_query(query)

    # Rate-limit ourselves — be a good citizen
    elapsed = time.time() - _last_lookup_time
    if elapsed < _MIN_DELAY_SECONDS:
        await asyncio.sleep(_MIN_DELAY_SECONDS - elapsed)

    logger.info(f"Lookup: '{q}'")

    try:
        loop = asyncio.get_event_loop()
        texts, images = await loop.run_in_executor(
            None, _do_lookup, q, _RESULT_COUNT,
            cfg.region, cfg.safesearch, cfg.timeout_seconds,
        )
        _last_lookup_time = time.time()
    except Exception as e:
        logger.error(f"Lookup failed: {e}")
        return f"⚠️ Lookup failed: {e}. You may be offline or rate-limited."

    if not texts and not images:
        return f"No results found for **{_md_safe(q)}**."

    parts = [f"Here's what I found for **{_md_safe(q)}**:"]

    for i, r in enumerate(texts):
        title = _md_safe(r.get("title", "Untitled"))
        url = r.get("href", "")
        snippet = r.get("body", "").strip()
        parts.append(f"### {i + 1}. [{title}]({url})" if url else f"### {i + 1}. {title}")
        if i < len(images):
            img = images[i]
            thumb = img.get("thumbnail") or img.get("image")
            if thumb:
                target = url or img.get("url") or img.get("image", "")
                parts.append(f"[![{title}]({thumb})]({target})")
        if snippet:
            parts.append(snippet)

    if not texts:  # image-only fallback
        for img in images[:_RESULT_COUNT]:
            thumb = img.get("thumbnail") or img.get("image")
            if not thumb:
                continue
            title = _md_safe(img.get("title", "image"))
            target = img.get("url") or img.get("image", "")
            parts.append(f"[![{title}]({thumb})]({target})")

    return "\n\n".join(parts)


def _do_lookup(query: str, max_results: int, region: str,
               safesearch: str, timeout: int) -> tuple[list[dict], list[dict]]:
    """Blocking DDG text + image search — runs in thread pool."""
    with DDGS(timeout=timeout) as ddgs:
        texts = list(ddgs.text(
            query, max_results=max_results, region=region, safesearch=safesearch,
        ))
        try:
            images = list(ddgs.images(
                query, max_results=max_results, region=region, safesearch=safesearch,
            ))
        except Exception as e:  # images are best-effort garnish
            logger.warning(f"Image lookup failed: {e}")
            images = []
        return texts, images
