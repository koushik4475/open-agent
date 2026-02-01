# openagent/parsers/unified.py
"""
Unified file parser.

Single entry point: parse_file(path) → str

Auto-detects format by extension and dispatches to the appropriate parser.
Adding a new format = add an import + one line in the dispatch dict.
"""

from __future__ import annotations
from pathlib import Path
import logging

from openagent.parsers import pdf_parser, docx_parser, txt_parser, image_parser

logger = logging.getLogger("openagent.parsers.unified")

# ── Format → parser function mapping ──────────────────────────
_PARSERS: dict[str, callable] = {
    ".txt":  txt_parser.extract_text,
    ".pdf":  pdf_parser.extract_text,
    ".docx": docx_parser.extract_text,
    # Image formats → OCR
    ".png":  image_parser.extract_text,
    ".jpg":  image_parser.extract_text,
    ".jpeg": image_parser.extract_text,
    ".bmp":  image_parser.extract_text,
    ".tiff": image_parser.extract_text,
    ".tif":  image_parser.extract_text,
}


def parse_file(filepath: Path) -> str:
    """
    Parse any supported file into plain text.

    Raises:
        FileNotFoundError — file doesn't exist
        ValueError — unsupported file format
        RuntimeError — parser-specific error
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    ext = filepath.suffix.lower()

    parser_fn = _PARSERS.get(ext)
    if parser_fn is None:
        supported = ", ".join(sorted(_PARSERS.keys()))
        raise ValueError(
            f"Unsupported file format: '{ext}'\n"
            f"Supported formats: {supported}"
        )

    logger.info(f"Parsing {filepath.name} (format: {ext})")
    return parser_fn(filepath)


def supported_extensions() -> list[str]:
    """Returns the list of file extensions this parser handles."""
    return sorted(_PARSERS.keys())
