"""Per-course authorization — prevents one instructor/student from reading another
course's data (roster, grades, materials) by guessing its id (IDOR / tenant isolation)."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course, Enrollment
from app.models.enums import UserRole
from app.models.user import User


def _enrollment(db: Session, course_id: int, user_id: int) -> Enrollment | None:
    return db.scalar(select(Enrollment).where(
        Enrollment.user_id == user_id, Enrollment.course_id == course_id))


def is_course_instructor(db: Session, course: Course, user: User) -> bool:
    if getattr(user, "is_platform_admin", False):
        return True
    if course.owner_id is not None and course.owner_id == user.id:
        return True
    enr = _enrollment(db, course.id, user.id)
    if enr and enr.role in (UserRole.instructor, UserRole.admin):
        return True
    # Institution admin whose tenant owns the course.
    if user.role == UserRole.admin and user.tenant_id and course.tenant_id == user.tenant_id:
        return True
    return False


def is_course_member(db: Session, course: Course, user: User) -> bool:
    return is_course_instructor(db, course, user) or _enrollment(db, course.id, user.id) is not None


def require_course_instructor(db: Session, course_id: int, user: User) -> Course:
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not is_course_instructor(db, course, user):
        raise HTTPException(status_code=403, detail="You do not have access to this course")
    return course


def require_course_member(db: Session, course_id: int, user: User) -> Course:
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not is_course_member(db, course, user):
        raise HTTPException(status_code=403, detail="You are not a member of this course")
    return course
