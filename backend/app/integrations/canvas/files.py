"""Canvas REST API connector — list + download course files.

LTI itself does not expose an instructor's course files, so this uses Canvas's own REST
API with an instructor/admin-supplied access token (Account → Settings → New Access Token).

Returns NORMALIZED file dicts: {id, name, content_type, download_url}.
Docs: https://canvas.instructure.com/doc/api/files.html
"""
from __future__ import annotations

import httpx

from app.integrations.lms_common import enforce_size, next_link, normalize_base


def list_course_files(
    base_url: str, token: str, course_ref: str, *, limit: int = 500
) -> list[dict]:
    base = normalize_base(base_url)
    url: str | None = f"{base}/api/v1/courses/{course_ref}/files?per_page=100"
    headers = {"Authorization": f"Bearer {token}"}
    out: list[dict] = []
    while url and len(out) < limit:
        resp = httpx.get(url, headers=headers, timeout=30.0)
        resp.raise_for_status()
        batch = resp.json()
        if not isinstance(batch, list):
            break
        for f in batch:
            out.append({
                "id": str(f.get("id")),
                "name": f.get("display_name") or f.get("filename") or "file",
                "content_type": f.get("content-type") or "",
                "download_url": f.get("url") or "",
            })
        url = next_link(resp.headers.get("Link", ""))
    return out[:limit]


def download_file(download_url: str, token: str, *, max_bytes: int) -> bytes:
    resp = httpx.get(
        download_url, headers={"Authorization": f"Bearer {token}"},
        timeout=60.0, follow_redirects=True,
    )
    resp.raise_for_status()
    return enforce_size(resp.content, max_bytes)
