# openagent/parsers/image_parser.py
"""
Image → Text via Tesseract OCR.

Preprocessing pipeline (improves accuracy significantly):
  1. Convert to grayscale
  2. Apply threshold (binarize) — removes background noise
  3. Resize if too small (Tesseract struggles with tiny text)

Why Tesseract:
  - Apache 2.0. Maintained by Google.
  - 100+ languages out of the box.
  - Runs fully offline on CPU.
  - No GPU needed.

Limitations:
  - Weak on handwritten text.
  - Needs clean images for best results.
  - CJK languages need extra language packs installed.
"""

from __future__ import annotations
from pathlib import Path
import logging

from PIL import Image, ImageFilter, ImageOps
import pytesseract

from openagent.config import settings

logger = logging.getLogger("openagent.parsers.image")

# Auto-detect Tesseract path on Windows
import platform
if platform.system() == "Windows":
    import shutil
    if not shutil.which("tesseract"):
        # Common Windows install locations
        for path in [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]:
            if Path(path).exists():
                pytesseract.pytesseract.tesseract_cmd = path
                break


def extract_text(filepath: Path) -> str:
    """
    Run OCR on an image file. Returns extracted text.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Image not found: {filepath}")

    cfg = settings.ocr

    try:
        img = Image.open(str(filepath))
        img = _preprocess(img)

        # Tesseract config
        # --psm {n} = page segmentation mode
        # --oem 3   = use LSTM engine (best accuracy)
        custom_config = f"--oem 3 --psm {cfg.psm}"

        text = pytesseract.image_to_string(
            img,
            lang=cfg.language,
            config=custom_config,
        )

        if not text.strip():
            logger.warning(f"OCR returned empty text for {filepath.name}")
            return "[OCR: No text detected in this image.]"

        logger.info(f"OCR extracted {len(text)} chars from {filepath.name}")
        return text.strip()

    except pytesseract.TesseractNotFoundError:
        return (
            "⚠️ Tesseract is not installed. Install it:\n"
            "  Ubuntu:  sudo apt install tesseract-ocr\n"
            "  macOS:   brew install tesseract\n"
            "  Windows: https://github.com/UB-Mannheim/tesseract/wiki"
        )
    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise RuntimeError(f"OCR failed on '{filepath.name}': {e}")


def _preprocess(img: Image.Image) -> Image.Image:
    """
    Standard OCR preprocessing pipeline.
    Each step measurably improves Tesseract accuracy on noisy images.
    """
    # 1. Convert to grayscale
    img = img.convert("L")

    # 2. Resize if too small (minimum 300 DPI equivalent)
    #    Tesseract recommends at least 300 DPI for good results.
    w, h = img.size
    if w < 500 or h < 500:
        scale = max(500 / w, 500 / h, 2.0)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # 3. Binarize (threshold) — converts to pure black & white
    #    This removes gray backgrounds and light noise.
    img = img.point(lambda px: 0 if px < 128 else 255, "1")

    return img
