"""Canvas REST API connector — import course files as CourseMaterial.

LTI itself does not expose an instructor's course files, so this uses Canvas's own REST
API with an instructor/admin-supplied access token (Account → Settings → New Access Token).
Only read endpoints are used: list a course's files, then download each one.

Docs: https://canvas.instructure.com/doc/api/files.html
"""
from __future__ import annotations

import httpx

# Document types we can extract text from (others are skipped — images, archives, etc.).
TEXT_EXTS = (".pdf", ".docx", ".pptx", ".txt", ".md", ".markdown", ".html", ".htm", ".csv", ".rtf")


def normalize_base(base_url: str) -> str:
    b = (base_url or "").strip().rstrip("/")
    if not b:
        return b
    if not b.startswith("http://") and not b.startswith("https://"):
        b = "https://" + b
    return b


def _next_link(link_header: str) -> str | None:
    """RFC5988 Link header: follow rel="next" for Canvas pagination."""
    for part in link_header.split(","):
        if 'rel="next"' in part:
            start, end = part.find("<"), part.find(">")
            if start != -1 and end != -1:
                return part[start + 1:end]
    return None


def list_course_files(
    base_url: str, token: str, canvas_course_id: str, *, limit: int = 500
) -> list[dict]:
    """Return Canvas file objects for a course (paginated)."""
    base = normalize_base(base_url)
    url: str | None = f"{base}/api/v1/courses/{canvas_course_id}/files?per_page=100"
    headers = {"Authorization": f"Bearer {token}"}
    out: list[dict] = []
    while url and len(out) < limit:
        resp = httpx.get(url, headers=headers, timeout=30.0)
        resp.raise_for_status()
        batch = resp.json()
        if not isinstance(batch, list):
            break
        out.extend(batch)
        url = _next_link(resp.headers.get("Link", ""))
    return out[:limit]


def download_file(file_url: str, token: str, *, max_bytes: int) -> bytes:
    """Download a Canvas file. `file_url` is the (often pre-signed) URL from the file object."""
    resp = httpx.get(
        file_url, headers={"Authorization": f"Bearer {token}"},
        timeout=60.0, follow_redirects=True,
    )
    resp.raise_for_status()
    data = resp.content
    if len(data) > max_bytes:
        raise ValueError("file exceeds size limit")
    return data
