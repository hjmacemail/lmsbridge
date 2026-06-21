"""Canvas Files connector: client pagination + import endpoint."""
from __future__ import annotations

from app.core.security import hash_password
from app.integrations.canvas import files as cf
from app.models.course import Course
from app.models.enums import UserRole
from app.models.user import User


def _instructor_headers(client, db) -> dict:
    u = User(email="prof@ex.edu", full_name="Prof", role=UserRole.instructor,
             hashed_password=hash_password("pw"))
    db.add(u)
    db.commit()
    r = client.post("/api/v1/auth/login", data={"username": "prof@ex.edu", "password": "pw"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


class _Resp:
    def __init__(self, data, link=""):
        self._data = data
        self.headers = {"Link": link} if link else {}

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def test_list_course_files_follows_pagination(monkeypatch):
    pages = {
        "https://c.test/api/v1/courses/9/files?per_page=100": _Resp(
            [{"id": 1, "display_name": "a.pdf"}],
            link='<https://c.test/page2>; rel="next"',
        ),
        "https://c.test/page2": _Resp([{"id": 2, "display_name": "b.docx"}]),
    }
    monkeypatch.setattr(cf.httpx, "get", lambda url, **kw: pages[url])
    out = cf.list_course_files("c.test", "tok", "9")
    assert [f["id"] for f in out] == [1, 2]  # both pages collected


def test_import_from_canvas_endpoint(client, db, monkeypatch):
    course = Course(code="ARCH 101", title="Architecture", term="LTI")
    db.add(course)
    db.commit()
    headers = _instructor_headers(client, db)

    from app.api.routes import materials as mat
    listing = [
        {"id": 1, "display_name": "notes.txt", "content-type": "text/plain",
         "url": "https://c.test/files/1"},
        {"id": 2, "display_name": "diagram.png", "content-type": "image/png",
         "url": "https://c.test/files/2"},  # unsupported -> skipped
    ]
    monkeypatch.setattr(mat.canvas_files, "list_course_files", lambda b, t, c, **k: listing)
    monkeypatch.setattr(mat.canvas_files, "download_file", lambda url, token, **k: b"hello world")

    payload = {"course_id": course.id, "base_url": "https://c.test",
               "access_token": "tok", "canvas_course_id": "999"}
    r = client.post("/api/v1/materials/import/canvas", headers=headers, json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body == {"imported": 1, "skipped": 1, "total": 2}

    # Idempotent: a second run imports nothing new.
    r2 = client.post("/api/v1/materials/import/canvas", headers=headers, json=payload)
    assert r2.json()["imported"] == 0

    # The imported file is now in the library with extracted text.
    mats = client.get(f"/api/v1/materials?course_id={course.id}", headers=headers).json()
    assert len(mats) == 1 and mats[0]["filename"] == "notes.txt" and mats[0]["has_text"] is True
