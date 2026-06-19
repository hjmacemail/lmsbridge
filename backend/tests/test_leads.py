"""Marketing-site lead capture (public create, admin-only list)."""
from sqlalchemy import select


def test_create_lead_public_and_admin_list(client, db):
    from app.core.security import hash_password
    from app.models.enums import UserRole
    from app.models.user import User

    # Public submit (no auth).
    r = client.post("/api/v1/leads", json={
        "kind": "purchase", "name": "Dana Pike", "email": "dana@uni.edu",
        "organization": "State U", "role": "Department chair", "plan": "Department",
        "message": "Pilot in intro CS on Canvas",
    })
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "new"

    # Listing requires admin.
    assert client.get("/api/v1/leads").status_code == 401

    admin = User(email="admin@x.edu", full_name="Admin", role=UserRole.admin,
                 is_platform_admin=True, hashed_password=hash_password("pw"))
    db.add(admin)
    db.commit()
    tok = client.post("/api/v1/auth/login",
                      data={"username": "admin@x.edu", "password": "pw"}).json()["access_token"]
    lst = client.get("/api/v1/leads", headers={"Authorization": f"Bearer {tok}"})
    assert lst.status_code == 200
    assert any(le["email"] == "dana@uni.edu" for le in lst.json())

    # Instructor (non-admin) is forbidden.
    inst = User(email="prof@x.edu", full_name="Prof", role=UserRole.instructor,
                hashed_password=hash_password("pw"))
    db.add(inst)
    db.commit()
    itok = client.post("/api/v1/auth/login",
                       data={"username": "prof@x.edu", "password": "pw"}).json()["access_token"]
    assert client.get("/api/v1/leads",
                      headers={"Authorization": f"Bearer {itok}"}).status_code == 403
    assert db.scalars(select(__import__('app.models.lead', fromlist=['Lead']).Lead)).all()
