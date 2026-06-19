"""Extract plain text from uploaded course material (PDF, DOCX, Markdown, text).

Keeps a hard cap on extracted length so a huge upload can't blow up prompts or rows.
Unsupported types are stored for download but yield no extracted text.
"""
from __future__ import annotations

import io

from app.core.logging import get_logger

logger = get_logger("extraction")

MAX_EXTRACTED_CHARS = 100_000

PDF_TYPES = {"application/pdf"}
DOCX_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
TEXT_TYPES = {"text/plain", "text/markdown", "text/x-markdown", "application/octet-stream"}


def extract_text(filename: str, content_type: str, data: bytes) -> str:
    name = (filename or "").lower()
    ctype = (content_type or "").lower()
    try:
        if ctype in PDF_TYPES or name.endswith(".pdf"):
            text = _from_pdf(data)
        elif ctype in DOCX_TYPES or name.endswith(".docx"):
            text = _from_docx(data)
        elif name.endswith((".txt", ".md", ".markdown")) or ctype in TEXT_TYPES:
            text = data.decode("utf-8", errors="replace")
        else:
            logger.info("No text extractor for %s (%s)", filename, content_type)
            return ""
    except Exception as e:  # noqa: BLE001
        logger.warning("Text extraction failed for %s: %s", filename, e)
        return ""
    text = text.strip()
    return text[:MAX_EXTRACTED_CHARS]


def _from_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _from_docx(data: bytes) -> str:
    import docx  # python-docx

    document = docx.Document(io.BytesIO(data))
    return "\n".join(p.text for p in document.paragraphs)
