"""LMS file connectors (Canvas / Moodle / Brightspace) + generic import endpoint."""
from __future__ import annotations

from sqlalchemy import select

from app.core.security import hash_password
from app.integrations.brightspace import files as bs
from app.integrations.canvas import files as cf
from app.integrations.moodle import files as mf
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


def test_canvas_normalizes_and_paginates(monkeypatch):
    pages = {
        "https://c.test/api/v1/courses/9/files?per_page=100": _Resp(
            [{"id": 1, "display_name": "a.pdf", "content-type": "application/pdf",
              "url": "https://c.test/f/1"}],
            link='<https://c.test/p2>; rel="next"',
        ),
        "https://c.test/p2": _Resp(
            [{"id": 2, "filename": "b.docx", "content-type": "x", "url": "https://c.test/f/2"}]),
    }
    monkeypatch.setattr(cf.httpx, "get", lambda url, **kw: pages[url])
    out = cf.list_course_files("c.test", "tok", "9")
    assert [f["id"] for f in out] == ["1", "2"]
    assert out[0] == {"id": "1", "name": "a.pdf", "content_type": "application/pdf",
                      "download_url": "https://c.test/f/1"}


def test_moodle_extracts_file_resources(monkeypatch):
    sections = [{
        "modules": [{
            "contents": [
                {"type": "file", "filename": "wk1.pdf", "mimetype": "application/pdf",
                 "fileurl": "https://m.test/pluginfile/wk1.pdf"},
                {"type": "url", "filename": "link"},  # not a file -> skipped
            ],
        }],
    }]
    monkeypatch.setattr(mf.httpx, "get", lambda url, **kw: _Resp(sections))
    out = mf.list_course_files("m.test", "tok", "5")
    assert len(out) == 1
    assert out[0]["name"] == "wk1.pdf" and out[0]["download_url"].endswith("wk1.pdf")


def test_brightspace_walks_toc_topics(monkeypatch):
    toc = {"Modules": [{
        "Topics": [
            {"TopicId": 11, "TopicType": 1, "Title": "Lecture 1.pdf"},
            {"TopicId": 12, "TopicType": 2, "Title": "External link"},  # link -> skipped
        ],
        "Modules": [{"Topics": [{"TopicId": 13, "TopicType": 1, "Title": "Lab.docx"}]}],
    }]}
    monkeypatch.setattr(bs.httpx, "get", lambda url, **kw: _Resp(toc))
    out = bs.list_course_files("https://d2l.test", "tok", "OU123")
    ids = [f["id"] for f in out]
    assert ids == ["11", "13"]
    assert out[0]["download_url"].endswith("/content/topics/11/file")


def test_import_from_lms_endpoint(client, db, monkeypatch):
    from app.models.course import Enrollment
    headers = _instructor_headers(client, db)
    instr = db.scalar(select(User).where(User.email == "prof@ex.edu"))
    course = Course(code="ARCH 101", title="Architecture", term="LTI", owner_id=instr.id)
    db.add(course)
    db.flush()
    db.add(Enrollment(user_id=instr.id, course_id=course.id, role=UserRole.instructor))
    db.commit()

    from app.integrations import lms_files
    listing = [
        {"id": "1", "name": "notes.txt", "content_type": "text/plain",
         "download_url": "https://c.test/f/1"},
        {"id": "2", "name": "diagram.png", "content_type": "image/png",
         "download_url": "https://c.test/f/2"},  # unsupported -> skipped
    ]
    monkeypatch.setattr(
        lms_files.canvas_files, "list_course_files", lambda b, t, c, **k: listing)
    monkeypatch.setattr(
        lms_files.canvas_files, "download_file", lambda url, token, **k: b"hello world")

    payload = {"course_id": course.id, "provider": "canvas", "base_url": "https://c.test",
               "access_token": "tok", "lms_course_id": "999"}
    r = client.post("/api/v1/materials/import/lms", headers=headers, json=payload)
    assert r.status_code == 200, r.text
    assert r.json() == {"imported": 1, "skipped": 1, "total": 2}

    # Idempotent.
    r2 = client.post("/api/v1/materials/import/lms", headers=headers, json=payload)
    assert r2.json()["imported"] == 0

    mats = client.get(f"/api/v1/materials?course_id={course.id}", headers=headers).json()
    assert len(mats) == 1 and mats[0]["filename"] == "notes.txt" and mats[0]["has_text"] is True
