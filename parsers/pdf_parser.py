# openagent/parsers/pdf_parser.py
"""
PDF → Text extraction using PyMuPDF (fitz).

Why PyMuPDF:
  - LGPL-3.0 (free for any use).
  - Handles 99% of PDFs correctly.
  - Extracts text, tables (basic), and metadata.
  - Pure Python API, no external binaries needed.
  - Offline. Fast.
"""

from __future__ import annotations
from pathlib import Path
import logging

import fitz  # PyMuPDF

logger = logging.getLogger("openagent.parsers.pdf")


def extract_text(filepath: Path) -> str:
    """
    Extract all text from a PDF file.
    Returns the concatenated text of all pages.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"PDF not found: {filepath}")

    try:
        with fitz.open(str(filepath)) as doc:
            pages: list[str] = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text")  # plain text extraction
                if text.strip():
                    pages.append(f"--- Page {page_num + 1} ---\n{text.strip()}")

            if not pages:
                logger.warning(f"No text extracted from {filepath}. May be image-based PDF.")
                return "[PDF contains no extractable text. It may be scanned/image-based. Use OCR.]"

            full_text = "\n\n".join(pages)
            logger.info(f"Extracted {len(full_text)} chars from {filepath.name} ({len(doc)} pages)")
            return full_text

    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise RuntimeError(f"Failed to parse PDF '{filepath.name}': {e}")
