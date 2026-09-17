"""PDF text extraction using PyMuPDF (fitz).

All processing is in-memory: the PDF bytes are never written to disk,
never logged, and discarded immediately after text extraction.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Maximum PDF size accepted (bytes) — matches frontend validation
MAX_PDF_BYTES = 4 * 1024 * 1024  # 4 MB (Vercel proxy body limit)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF given as raw bytes.

    Args:
        pdf_bytes: Raw PDF content.

    Returns:
        Concatenated text from all pages.

    Raises:
        ValueError: If bytes cannot be parsed as a valid PDF.
        RuntimeError: If PyMuPDF is not installed.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "PyMuPDF is not installed. Add 'pymupdf' to requirements.txt."
        ) from exc

    if not pdf_bytes:
        raise ValueError("Empty file received.")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Cannot parse PDF: {exc}") from exc

    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text("text"))  # type: ignore[attr-defined]
    doc.close()

    text = "\n".join(pages).strip()
    logger.debug(
        "Extracted %d chars from %d-page PDF (%d bytes input)",
        len(text),
        len(pages),
        len(pdf_bytes),
    )
    return text
