"""PII minimization for content sent to the LLM.

By design the remediation prompts carry concept + answer text + course material — not
names, emails, or LMS IDs. This module is the enforced safety net: it redacts anything
that slips through (emails, and any supplied student names) before a request leaves the
process. It is applied centrally at the LLM provider boundary.
"""
from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# Long digit runs that could be student/LMS IDs.
_ID_RE = re.compile(r"\b\d{6,}\b")


def redact_pii(text: str, names: list[str] | None = None) -> str:
    if not text:
        return text
    text = _EMAIL_RE.sub("[email redacted]", text)
    text = _ID_RE.sub("[id redacted]", text)
    for name in sorted(filter(None, names or []), key=len, reverse=True):
        if len(name) >= 3:
            text = re.sub(rf"\b{re.escape(name)}\b", "[name redacted]", text, flags=re.IGNORECASE)
    return text
