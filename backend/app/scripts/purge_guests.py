"""Purge stale Sage guest accounts.

Guest joins (`POST /sage/guest`) create throwaway users with an `@sage.local` email so someone
can try a course without signing up. Those accounts (and their enrollments, results, and
remediation modules) otherwise accumulate forever. This script deletes guests whose last quiz
activity — or, if they never submitted, their account creation — is older than a cutoff.

Usage:
    python -m app.scripts.purge_guests --days 30            # delete guests idle > 30 days
    python -m app.scripts.purge_guests --days 30 --dry-run  # show what would be deleted
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.assessment import AssessmentResult
from app.models.course import Enrollment
from app.models.remediation import RemediationModule
from app.models.user import User

logger = get_logger("purge_guests")

GUEST_SUFFIX = "@sage.local"


def purge_guests(days: int = 30, dry_run: bool = False) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    db = SessionLocal()
    try:
        guests = db.scalars(select(User).where(User.email.like(f"%{GUEST_SUFFIX}"))).all()
        to_delete: list[User] = []
        for g in guests:
            last = db.scalar(
                select(func.max(AssessmentResult.ingested_at))
                .where(AssessmentResult.student_id == g.id)
            )
            # Age a guest by their last quiz activity, or by account creation if they never
            # submitted. A freshly-joined guest is therefore always kept.
            activity = last or g.created_at
            if activity is not None:
                # Some backends (SQLite) return naive datetimes — treat those as UTC.
                if activity.tzinfo is None:
                    activity = activity.replace(tzinfo=timezone.utc)
                if activity < cutoff:
                    to_delete.append(g)

        deleted = 0
        for g in to_delete:
            if dry_run:
                logger.info("[dry-run] would delete guest #%s %s", g.id, g.email)
                deleted += 1
                continue
            # Remove dependents first in case the DB has no ON DELETE CASCADE.
            for row in db.scalars(select(RemediationModule)
                                  .where(RemediationModule.student_id == g.id)).all():
                db.delete(row)
            for row in db.scalars(select(AssessmentResult)
                                  .where(AssessmentResult.student_id == g.id)).all():
                db.delete(row)
            for row in db.scalars(select(Enrollment)
                                  .where(Enrollment.user_id == g.id)).all():
                db.delete(row)
            db.delete(g)
            deleted += 1
        if not dry_run:
            db.commit()
        logger.info("Guest purge complete: %s guests %s (cutoff %s).",
                    deleted, "matched (dry-run)" if dry_run else "deleted", cutoff.date())
        return {"scanned": len(guests), "deleted": deleted, "dry_run": dry_run}
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Purge stale Sage guest accounts.")
    ap.add_argument("--days", type=int, default=30, help="Delete guests idle longer than this.")
    ap.add_argument("--dry-run", action="store_true", help="Report without deleting.")
    args = ap.parse_args()
    print(purge_guests(days=args.days, dry_run=args.dry_run))
