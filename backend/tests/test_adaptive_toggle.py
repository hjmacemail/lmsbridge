"""Admin can enable/disable which assessments feed the adaptive engine."""
from sqlalchemy import select

from app.models.assessment import Assessment
from app.models.enums import AssessmentType
from app.models.user import User
from app.services.ingestion_service import ingest_result


def _login(client, email, pw="pw"):
    r = client.post("/api/v1/auth/login", data={"username": email, "password": pw})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_toggle_and_recompute_endpoints(client, db, seeded):
    h = _login(client, seeded["instructor_email"])
    cid = seeded["course_id"]

    assessments = client.get(f"/api/v1/assessments?course_id={cid}", headers=h).json()
    assert assessments and all("adaptive_enabled" in a for a in assessments)
    aid = assessments[0]["id"]

    # Disable one assessment.
    r = client.patch(f"/api/v1/assessments/{aid}/adaptive", headers=h, json={"enabled": False})
    assert r.status_code == 200
    assert r.json()["adaptive_enabled"] is False

    # Recompute should succeed and report how many results it replayed.
    rc = client.post(f"/api/v1/assessments/recompute?course_id={cid}", headers=h)
    assert rc.status_code == 200, rc.text
    body = rc.json()
    assert "results_replayed" in body and "modules_triggered" in body

    # Re-enable.
    r2 = client.patch(f"/api/v1/assessments/{aid}/adaptive", headers=h, json={"enabled": True})
    assert r2.json()["adaptive_enabled"] is True


def test_disabled_assessment_does_not_trigger_remediation(db, seeded):
    """A disabled assessment's result is stored but creates no remediation."""
    course_id = seeded["course_id"]
    assessment = Assessment(
        course_id=course_id, title="Disabled Quiz", type=AssessmentType.quiz,
        max_score=20, adaptive_enabled=False,
    )
    db.add(assessment)
    db.flush()
    student = db.scalars(select(User).where(User.role == "student")).first()

    result, modules = ingest_result(
        db, assessment=assessment, student=student, score=0.2,
        item_scores=[{"concept_key": "binary_arithmetic", "earned": 1, "max": 5}],
    )
    assert result.id is not None       # stored for the record
    assert modules == []               # but no remediation triggered
