# openagent/parsers/txt_parser.py
"""
TXT → Text extraction.

Handles encoding detection (UTF-8, Latin-1 fallback).
Simple but robust.
"""

from __future__ import annotations
from pathlib import Path
import logging

logger = logging.getLogger("openagent.parsers.txt")


def extract_text(filepath: Path) -> str:
    """Read a text file, auto-detecting encoding."""
    if not filepath.exists():
        raise FileNotFoundError(f"TXT not found: {filepath}")

    # Try UTF-8 first (most common), fall back to Latin-1 (never fails)
    for encoding in ("utf-8", "latin-1"):
        try:
            text = filepath.read_text(encoding=encoding)
            logger.info(f"Read {len(text)} chars from {filepath.name} (encoding={encoding})")
            return text
        except UnicodeDecodeError:
            continue

    raise RuntimeError(f"Could not decode '{filepath.name}' with any supported encoding.")
