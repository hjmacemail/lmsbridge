"""Auth + student dashboard + responding to a remediation activity through the API."""
from sqlalchemy import select


def _login(client, db, email, password_set_to="pw"):
    # ensure password known: instructor seeded with 'pw'
    r = client.post("/api/v1/auth/login", data={"username": email, "password": password_set_to})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_instructor_analytics_and_student_flow(client, db, seeded):
    from app.core.security import hash_password
    from app.models.user import User

    token = _login(client, db, seeded["instructor_email"])
    headers = {"Authorization": f"Bearer {token}"}

    # Instructor analytics
    r = client.get(f"/api/v1/analytics/courses/{seeded['course_id']}", headers=headers)
    assert r.status_code == 200
    analytics = r.json()
    assert analytics["enrolled_students"] >= 0
    assert isinstance(analytics["concept_risks"], list)

    # Grab a seeded student, give them a known password, log in.
    student = db.scalars(
        select(User).where(User.role == "student")
    ).first()
    student.hashed_password = hash_password("pw")
    db.commit()

    stoken = _login(client, db, student.email)
    sheaders = {"Authorization": f"Bearer {stoken}"}

    dash = client.get("/api/v1/students/me/dashboard", headers=sheaders)
    assert dash.status_code == 200
    body = dash.json()
    assert body["full_name"] == student.full_name

    # If the student has an open module, respond to its first activity.
    modules = client.get("/api/v1/remediation/modules", headers=sheaders).json()
    if modules:
        activity = modules[0]["activities"][0]
        resp = client.post(
            f"/api/v1/remediation/activities/{activity['id']}/respond",
            headers=sheaders,
            json={"response_text": (
                "Binary arithmetic carries over at 2; I add bit by bit and "
                "carry the 1 when the column sums to two or more."
            )},
        )
        assert resp.status_code == 200, resp.text
        assert "feedback" in resp.json()
