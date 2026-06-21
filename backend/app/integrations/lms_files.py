"""Registry of LMS file connectors. Each provider module exposes:

    list_course_files(base_url, token, course_ref) -> list[{id, name, content_type, download_url}]
    download_file(download_url, token, *, max_bytes) -> bytes
"""
from __future__ import annotations

from app.integrations.brightspace import files as brightspace_files
from app.integrations.canvas import files as canvas_files
from app.integrations.moodle import files as moodle_files

PROVIDERS = {
    "canvas": canvas_files,
    "moodle": moodle_files,
    "brightspace": brightspace_files,
}


def get_provider(name: str):
    provider = PROVIDERS.get((name or "").lower())
    if provider is None:
        raise ValueError(f"Unsupported LMS provider: {name!r}")
    return provider
