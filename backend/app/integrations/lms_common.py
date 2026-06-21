"""Shared helpers for LMS file connectors (Canvas / Moodle / Brightspace)."""
from __future__ import annotations

# Document types we can extract text from (others — images, archives — are skipped).
TEXT_EXTS = (".pdf", ".docx", ".pptx", ".txt", ".md", ".markdown", ".html", ".htm", ".csv", ".rtf")


def normalize_base(base_url: str) -> str:
    b = (base_url or "").strip().rstrip("/")
    if not b:
        return b
    if not b.startswith("http://") and not b.startswith("https://"):
        b = "https://" + b
    return b


def next_link(link_header: str) -> str | None:
    """RFC5988 Link header: follow rel="next" (Canvas pagination)."""
    for part in link_header.split(","):
        if 'rel="next"' in part:
            start, end = part.find("<"), part.find(">")
            if start != -1 and end != -1:
                return part[start + 1:end]
    return None


def enforce_size(data: bytes, max_bytes: int) -> bytes:
    if len(data) > max_bytes:
        raise ValueError("file exceeds size limit")
    return data


def is_text_file(name: str) -> bool:
    return name.lower().endswith(TEXT_EXTS)
