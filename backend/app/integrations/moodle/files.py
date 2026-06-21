"""Moodle Web Services connector — list + download course files.

Uses Moodle's REST web services with an instructor/admin web-service token
(Site administration → Server → Web services → Manage tokens, or a user token).
Reads the course contents and pulls file resources.

Returns NORMALIZED file dicts: {id, name, content_type, download_url}.
Docs: core_course_get_contents — https://docs.moodle.org/dev/Web_service_API_functions
"""
from __future__ import annotations

import httpx

from app.integrations.lms_common import enforce_size, normalize_base


def list_course_files(
    base_url: str, token: str, course_ref: str, *, limit: int = 500
) -> list[dict]:
    base = normalize_base(base_url)
    url = f"{base}/webservice/rest/server.php"
    params = {
        "wstoken": token,
        "wsfunction": "core_course_get_contents",
        "courseid": str(course_ref),
        "moodlewsrestformat": "json",
    }
    resp = httpx.get(url, params=params, timeout=30.0)
    resp.raise_for_status()
    body = resp.json()
    # Moodle returns an error object (not a list) on failure.
    if isinstance(body, dict) and body.get("exception"):
        raise RuntimeError(body.get("message") or "Moodle web service error")
    out: list[dict] = []
    for section in body if isinstance(body, list) else []:
        for module in section.get("modules", []) or []:
            for c in module.get("contents", []) or []:
                if c.get("type") == "file" and c.get("fileurl") and len(out) < limit:
                    out.append({
                        "id": str(c.get("fileurl")),
                        "name": c.get("filename") or "file",
                        "content_type": c.get("mimetype") or "",
                        "download_url": c.get("fileurl"),
                    })
    return out


def download_file(download_url: str, token: str, *, max_bytes: int) -> bytes:
    # Moodle file URLs require the token as a query param to authorize the download.
    sep = "&" if "?" in download_url else "?"
    url = f"{download_url}{sep}token={token}"
    resp = httpx.get(url, timeout=60.0, follow_redirects=True)
    resp.raise_for_status()
    return enforce_size(resp.content, max_bytes)
