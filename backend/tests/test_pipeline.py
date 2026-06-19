"""End-to-end: mock Brightspace sync should create mastery + remediation modules."""
from sqlalchemy import select

from app.models.mastery import ConceptMastery
from app.models.remediation import RemediationModule


def test_sync_creates_mastery_and_modules(db, seeded):
    masteries = db.scalars(select(ConceptMastery)).all()
    modules = db.scalars(select(RemediationModule)).all()
    assert len(masteries) > 0, "mastery records should be produced"
    assert len(modules) > 0, "at-risk concepts should trigger remediation"
    # Every generated module must have at least one active activity.
    for m in modules:
        assert m.activities, "module should contain activities"
