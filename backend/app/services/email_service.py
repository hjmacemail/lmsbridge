"""Optional SMTP email notifications.

Best-effort and entirely optional: if SMTP isn't configured (no `smtp_host`/`smtp_from`),
every send is a logged no-op and the app behaves normally. Failures never raise to callers.
Guest/synthesized addresses (`@sage.local`) are skipped.
"""
from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("email")


def email_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from)


def _deliverable(addr: str | None) -> bool:
    return bool(addr) and "@" in addr and not addr.endswith("@sage.local")


def send_email(to: str, subject: str, body: str) -> bool:
    if not email_configured() or not _deliverable(to):
        return False
    try:
        msg = EmailMessage()
        msg["From"] = settings.smtp_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        ctx = ssl.create_default_context()
        host, port = settings.smtp_host, settings.smtp_port
        if settings.smtp_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=10, context=ctx) as s:
                if settings.smtp_user:
                    s.login(settings.smtp_user, settings.smtp_password or "")
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=10) as s:
                if settings.smtp_starttls:
                    s.starttls(context=ctx)
                if settings.smtp_user:
                    s.login(settings.smtp_user, settings.smtp_password or "")
                s.send_message(msg)
        return True
    except Exception as e:  # noqa: BLE001 — notifications must never break the request
        logger.warning("Email send to %s failed: %s", to, e)
        return False


def send_bulk(recipients: list[str], subject: str, body: str) -> int:
    """Send the same message to many recipients; returns how many succeeded."""
    return sum(1 for r in dict.fromkeys(recipients) if send_email(r, subject, body))
