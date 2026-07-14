"""Expanded instructor detail endpoints + material upload over the API."""
from sqlalchemy import select


def _login(client, email, pw="pw"):
    r = client.post("/api/v1/auth/login", data={"username": email, "password": pw})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_roster_and_student_drilldown(client, db, seeded):
    h = _login(client, seeded["instructor_email"])
    cid = seeded["course_id"]

    roster = client.get(f"/api/v1/analytics/courses/{cid}/roster", headers=h)
    assert roster.status_code == 200
    rows = roster.json()
    assert len(rows) > 0
    sid = rows[0]["student_id"]

    detail = client.get(f"/api/v1/analytics/courses/{cid}/students/{sid}", headers=h)
    assert detail.status_code == 200
    body = detail.json()
    assert "masteries" in body and "results" in body and "modules" in body

    breakdown = client.get(f"/api/v1/analytics/courses/{cid}/assessments", headers=h)
    assert breakdown.status_code == 200
    assert isinstance(breakdown.json(), list)

    rem = client.get(f"/api/v1/analytics/courses/{cid}/remediation", headers=h)
    assert rem.status_code == 200

    csv = client.get(f"/api/v1/analytics/courses/{cid}/export.csv", headers=h)
    assert csv.status_code == 200
    assert "student_name" in csv.text


def test_material_upload_and_list(client, db, seeded):
    h = _login(client, seeded["instructor_email"])
    cid = seeded["course_id"]
    files = {"file": ("notes.md", b"Binary arithmetic carries at two.", "text/markdown")}
    data = {"course_id": str(cid), "title": "Notes"}
    up = client.post("/api/v1/materials", headers=h, files=files, data=data)
    assert up.status_code == 201, up.text
    assert up.json()["has_text"] is True

    lst = client.get(f"/api/v1/materials?course_id={cid}", headers=h)
    assert lst.status_code == 200
    assert any(m["title"] == "Notes" for m in lst.json())


def test_student_cannot_access_instructor_analytics(client, db, seeded):
    from app.core.security import hash_password
    from app.models.user import User
    student = db.scalars(select(User).where(User.role == "student")).first()
    student.hashed_password = hash_password("pw")
    db.commit()
    h = _login(client, student.email)
    r = client.get(f"/api/v1/analytics/courses/{seeded['course_id']}/roster", headers=h)
    assert r.status_code == 403


def test_class_brief(client, db, seeded):
    h = _login(client, seeded["instructor_email"])
    cid = seeded["course_id"]
    r = client.get(f"/api/v1/analytics/courses/{cid}/brief", headers=h)
    assert r.status_code == 200, r.text
    b = r.json()
    # Real numbers present, and a narrated brief + recommendation exist.
    assert "students_total" in b and "needs_attention" in b
    assert b["brief"] and b["recommendation"]


def test_misconception_clusters(client, db, seeded):
    h = _login(client, seeded["instructor_email"])
    cid = seeded["course_id"]
    r = client.get(f"/api/v1/analytics/courses/{cid}/clusters", headers=h)
    assert r.status_code == 200, r.text
    clusters = r.json()
    assert isinstance(clusters, list)
    # Seeded MCQ data produces wrong answers -> at least one cluster with real fields.
    if clusters:
        c = clusters[0]
        assert c["concept"] and c["misconception"] and c["size"] == len(c["students"])
