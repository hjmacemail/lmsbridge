"""Manual course / concept / assessment management (for pilots without an LMS)."""
from sqlalchemy import select


def _instructor(db):
    from app.core.security import hash_password
    from app.models.enums import UserRole
    from app.models.user import User
    u = User(email="prof@test.edu", full_name="Prof", role=UserRole.instructor,
             hashed_password=hash_password("pw"))
    db.add(u)
    db.commit()
    return u


def _login(client, email, pw="pw"):
    r = client.post("/api/v1/auth/login", data={"username": email, "password": pw})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_create_course_concepts_assessment(client, db):
    _instructor(db)
    h = _login(client, "prof@test.edu")

    # Create a course (creator is auto-enrolled).
    c = client.post("/api/v1/courses", headers=h,
                    json={"code": "CS-101", "title": "Intro CS", "term": "2026FA"})
    assert c.status_code == 201, c.text
    cid = c.json()["id"]
    # It shows up in the creator's course list.
    assert any(x["id"] == cid for x in client.get("/api/v1/courses", headers=h).json())

    # Add two concepts, the second depending on the first.
    a = client.post(f"/api/v1/courses/{cid}/concepts", headers=h, json={
        "key": "variables", "name": "Variables", "sequence": 0,
        "common_misconceptions": "confusing assignment with equality"})
    assert a.status_code == 201
    b = client.post(f"/api/v1/courses/{cid}/concepts", headers=h, json={
        "key": "loops", "name": "Loops", "sequence": 1, "prerequisite_keys": ["variables"]})
    assert b.status_code == 201
    assert b.json()["prerequisite_keys"] == ["variables"]

    # Course detail returns concepts with prerequisites.
    detail = client.get(f"/api/v1/courses/{cid}", headers=h).json()
    assert len(detail["concepts"]) == 2
    loops = next(x for x in detail["concepts"] if x["key"] == "loops")
    assert loops["prerequisite_keys"] == ["variables"]

    # Create an assessment.
    ass = client.post(f"/api/v1/courses/{cid}/assessments", headers=h,
                      json={"title": "Quiz 1", "type": "quiz", "max_score": 20})
    assert ass.status_code == 201
    assert ass.json()["title"] == "Quiz 1"

    # Delete a concept.
    bid = b.json()["id"]
    assert client.delete(f"/api/v1/courses/{cid}/concepts/{bid}", headers=h).status_code == 204
    assert len(client.get(f"/api/v1/courses/{cid}", headers=h).json()["concepts"]) == 1


def test_course_creation_requires_instructor(client, db):
    from app.core.security import hash_password
    from app.models.enums import UserRole
    from app.models.user import User
    s = User(email="stu@test.edu", full_name="Stu", role=UserRole.student,
             hashed_password=hash_password("pw"))
    db.add(s)
    db.commit()
    h = _login(client, "stu@test.edu")
    assert client.post("/api/v1/courses", headers=h,
                       json={"code": "X", "title": "Y", "term": "Z"}).status_code == 403
    assert db.scalars(select(User)).all()  # sanity
