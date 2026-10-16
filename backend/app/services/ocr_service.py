"""Optional OCR for scanned PDFs.

Uses pytesseract + pypdfium2 when installed; otherwise returns empty with a clear status.
Install for full OCR:
  pip install pytesseract pypdfium2
  + system Tesseract OCR binary
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def ocr_available() -> bool:
    try:
        import pytesseract  # noqa: F401
        import pypdfium2  # noqa: F401

        return True
    except ImportError:
        return False


def extract_text_with_ocr(pdf_path: Path, max_pages: int = 40) -> tuple[str, dict]:
    """
    OCR a PDF. Returns (text, meta) where meta has pages_ocrd, status, warning.
    """
    meta: dict = {
        "status": "unavailable",
        "pages_ocrd": 0,
        "warning": None,
        "engine": None,
    }
    if not ocr_available():
        meta["warning"] = (
            "OCR libraries not installed. Install pytesseract + pypdfium2 and system Tesseract "
            "to extract text from scanned PDFs."
        )
        return "", meta

    try:
        import pypdfium2 as pdfium
        import pytesseract
        from PIL import Image  # pillow often comes with pypdfium2 usage

        pdf = pdfium.PdfDocument(str(pdf_path))
        n = min(len(pdf), max_pages)
        parts: list[str] = []
        for i in range(n):
            page = pdf[i]
            # scale ~2 for readable OCR
            bitmap = page.render(scale=2)
            pil_image = bitmap.to_pil()
            text = pytesseract.image_to_string(pil_image)
            if text.strip():
                parts.append(f"\n--- Page {i + 1} ---\n{text.strip()}")
        meta["pages_ocrd"] = n
        meta["engine"] = "pytesseract+pypdfium2"
        if not parts:
            meta["status"] = "completed_empty"
            meta["warning"] = "OCR ran but produced little or no text. Manual review required."
            return "", meta
        meta["status"] = "completed"
        if len(pdf) > max_pages:
            meta["warning"] = f"OCR limited to first {max_pages} pages of {len(pdf)}."
        return "\n".join(parts), meta
    except Exception as exc:  # noqa: BLE001
        logger.exception("OCR failed")
        meta["status"] = "failed"
        meta["warning"] = f"OCR failed: {exc.__class__.__name__}. Manual review required."
        return "", meta
