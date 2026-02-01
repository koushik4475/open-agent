# openagent/core/router.py
"""
Tool Router — decides WHICH tool to call based on user input.

Strategy (intentionally simple, not ML-based):
  1. Keyword matching for high-confidence routes (file ops, search, etc.)
  2. LLM-based intent classification for ambiguous queries.
  3. Default fallback: general-purpose summarize/respond.

This keeps the router fast and debuggable.
A future upgrade path is to use the LLM to output a structured
JSON tool-call (like OpenAI function-calling), but that requires
fine-tuned models which we don't have locally yet.
"""

from __future__ import annotations
import re
from pathlib import Path
from enum import Enum

from openagent.core.network import check_connectivity


class ToolName(str, Enum):
    SUMMARIZE = "summarize"
    PARSE_FILE = "parse_file"
    OCR_IMAGE = "ocr_image"
    RUN_COMMAND = "run_command"
    WEB_SEARCH = "web_search"
    WEB_FETCH = "web_fetch"
    GENERAL = "general"  # Just send to LLM directly


# ── keyword patterns ──────────────────────────────────────────
_FILE_PATTERN = re.compile(r"\[FILE:(.*?)\]", re.IGNORECASE)

_SEARCH_KEYWORDS = {
    "search", "google", "find online", "look up", "what is the latest",
    "current", "news", "today", "web", "internet", "search for",
    "who is", "who was", "tell me about", "info on", "biography of",
    "history of", "price of", "stock", "weather", "latest on",
}

_FETCH_KEYWORDS = {
    "fetch", "open url", "visit", "go to", "load page", "read website",
    "http://", "https://",
}

_COMMAND_KEYWORDS = {
    "run command", "execute", "shell", "terminal", "run this",
}

_OCR_KEYWORDS = {
    "ocr", "read image", "extract text from image", "scan image",
}

_SUMMARIZE_KEYWORDS = {
    "summarize", "summary", "tldr", "tl;dr", "shorten", "brief",
    "key points", "main points",
}

# File extensions we can parse
_PARSEABLE_EXTENSIONS = {".txt", ".pdf", ".docx", ".png", ".jpg", ".jpeg", ".bmp", ".tiff"}


async def route(user_input: str) -> tuple[ToolName, dict]:
    """
    Returns (tool_name, context_dict).
    context_dict carries extracted info (file path, URL, query, etc.)
    """
    text = user_input.strip()
    text_lower = text.lower()

    # ── 1. Explicit file reference ────────────────────────────
    file_match = _FILE_PATTERN.search(text)
    if file_match:
        filepath = Path(file_match.group(1).strip())
        if filepath.exists():
            ext = filepath.suffix.lower()
            if ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff"):
                return ToolName.OCR_IMAGE, {"filepath": filepath, "prompt": text}
            if ext in _PARSEABLE_EXTENSIONS:
                return ToolName.PARSE_FILE, {"filepath": filepath, "prompt": text}
        return ToolName.GENERAL, {"prompt": text}

    # ── 2. OCR keywords ───────────────────────────────────────
    if any(kw in text_lower for kw in _OCR_KEYWORDS):
        return ToolName.OCR_IMAGE, {"prompt": text}

    # ── 3. Command execution keywords ─────────────────────────
    if any(kw in text_lower for kw in _COMMAND_KEYWORDS):
        return ToolName.RUN_COMMAND, {"prompt": text}

    # ── 4. URL fetch (check for http links) ───────────────────
    url_match = re.search(r"(https?://[^\s]+)", text)
    if url_match or any(kw in text_lower for kw in _FETCH_KEYWORDS):
        url = url_match.group(1) if url_match else None
        online = await check_connectivity()
        if not online:
            return ToolName.GENERAL, {
                "prompt": text,
                "offline_warning": "Web fetch requires internet. You are currently offline."
            }
        return ToolName.WEB_FETCH, {"url": url, "prompt": text}

    # ── 5. Web search keywords ────────────────────────────────
    if any(kw in text_lower for kw in _SEARCH_KEYWORDS):
        online = await check_connectivity()
        if not online:
            return ToolName.GENERAL, {
                "prompt": text,
                "offline_warning": "Web search requires internet. You are currently offline."
            }
        return ToolName.WEB_SEARCH, {"query": text, "prompt": text}

    # ── 6. Summarization keywords ─────────────────────────────
    if any(kw in text_lower for kw in _SUMMARIZE_KEYWORDS):
        return ToolName.SUMMARIZE, {"prompt": text}

    # ── 7. Default: send to LLM directly ──────────────────────
    return ToolName.GENERAL, {"prompt": text}
