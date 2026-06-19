"""Pytest fixtures: isolated in-memory DB + TestClient with dependency overrides."""
from __future__ import annotations

import os

os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("BRIGHTSPACE_ADAPTER", "mock")
os.environ.setdefault("SECRET_KEY", "test-secret")
# Default the suite to hosted mode so the platform-role + licensing tests exercise the
# full multi-tenant behavior. Community-mode behavior is covered explicitly where needed.
os.environ.setdefault("DEPLOYMENT_MODE", "hosted")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app

# Shared in-memory SQLite for the whole test session.
engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _fresh_schema():
    """Recreate the schema before every test for full isolation."""
    import app.models  # noqa: F401  (register models)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db():
    s = TestSession()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture()
def client():
    def _override_get_db():
        s = TestSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded(db):
    """Seed a minimal course + instructor + run the mock pipeline into the test DB."""
    from app.core.security import hash_password
    from app.models.concept import Concept
    from app.models.course import Course, Enrollment
    from app.models.enums import UserRole
    from app.models.user import User
    from app.services.sync_service import sync_course_results

    instructor = User(
        email="instructor@test.edu", full_name="Test Instructor",
        role=UserRole.instructor, hashed_password=hash_password("pw"),
    )
    db.add(instructor)
    db.flush()
    course = Course(code="CS-TEST", title="Test Arch", term="2026SP",
                    brightspace_course_id="BS-CS201")
    db.add(course)
    db.flush()
    db.add(Enrollment(user_id=instructor.id, course_id=course.id, role=UserRole.instructor))
    for key, name, seq in [
        ("binary_representation", "Binary Representation", 0),
        ("binary_arithmetic", "Binary Arithmetic", 1),
        ("boolean_logic", "Boolean Logic", 2),
        ("machine_code", "Machine Code", 3),
    ]:
        db.add(Concept(course_id=course.id, key=key, name=name, sequence=seq,
                       common_misconceptions="common slip"))
    db.commit()
    sync_course_results(db, course_id=course.id, course_external_id="BS-CS201")
    return {"course_id": course.id, "instructor_email": "instructor@test.edu"}
