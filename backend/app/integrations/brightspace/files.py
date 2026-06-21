"""Brightspace (D2L) Valence connector — list + download course content files.

Uses the Brightspace LE Content API with an OAuth2 bearer token (the institution's
Brightspace admin issues one for a registered app). `course_ref` is the org unit id —
which is also the LTI `context_id`, so it can be captured automatically at launch.

Returns NORMALIZED file dicts: {id, name, content_type, download_url}.
Docs: https://docs.valence.desire2learn.com/res/content.html
"""
from __future__ import annotations

import httpx

from app.integrations.lms_common import enforce_size, normalize_base

LE_VERSION = "1.74"


def list_course_files(
    base_url: str, token: str, course_ref: str, *, version: str = LE_VERSION, limit: int = 500
) -> list[dict]:
    base = normalize_base(base_url)
    url = f"{base}/d2l/api/le/{version}/{course_ref}/content/toc"
    resp = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30.0)
    resp.raise_for_status()
    toc = resp.json()
    out: list[dict] = []

    def walk(modules: list | None) -> None:
        for m in modules or []:
            for t in m.get("Topics", []) or []:
                # TopicType 1 = file/content topic (2 = link). Only files are downloadable.
                if t.get("TopicType") == 1 and t.get("TopicId") is not None and len(out) < limit:
                    tid = t.get("TopicId")
                    out.append({
                        "id": str(tid),
                        "name": t.get("Title") or f"topic-{tid}",
                        "content_type": "",
                        "download_url":
                            f"{base}/d2l/api/le/{version}/{course_ref}/content/topics/{tid}/file",
                    })
            walk(m.get("Modules"))

    walk((toc or {}).get("Modules"))
    return out


def download_file(download_url: str, token: str, *, max_bytes: int) -> bytes:
    resp = httpx.get(
        download_url, headers={"Authorization": f"Bearer {token}"},
        timeout=60.0, follow_redirects=True,
    )
    resp.raise_for_status()
    return enforce_size(resp.content, max_bytes)
