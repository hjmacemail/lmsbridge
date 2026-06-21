"""Sage — standalone AI-augmented class Q&A board API (sage.lmsbridge.app).

Standalone auth (instructor signup, student join-by-code, guest join), classes, posts,
answers (with an automatic Socratic AI reply + misconception flag), endorsement, and an
instructor insights dashboard. Reuses the platform User + LLM layer.
"""
from __future__ import annotations

import secrets
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.sage import SageAnswer, SageClass, SageMembership, SagePost
from app.models.user import User
from app.schemas.sage import (
    AnswerCreate,
    ClassCreate,
    JoinByCode,
    PostCreate,
    SageAuthOut,
    SageGuestJoin,
    SageJoinSignup,
    SageSignup,
)
from app.services import sage_ai

router = APIRouter(prefix="/sage", tags=["sage"])

_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no ambiguous 0/O/1/I


def _gen_join_code(db: Session) -> str:
    for _ in range(20):
        code = "".join(secrets.choice(_ALPHABET) for _ in range(6))
        if not db.scalar(select(SageClass).where(SageClass.join_code == code)):
            return code
    raise HTTPException(status_code=500, detail="Could not allocate a join code")


def _auth_out(user: User) -> SageAuthOut:
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return SageAuthOut(access_token=token, user_id=user.id,
                       full_name=user.full_name, role=user.role.value)


def _class_by_code(db: Session, code: str) -> SageClass:
    sc = db.scalar(select(SageClass).where(SageClass.join_code == code.strip().upper()))
    if not sc:
        raise HTTPException(status_code=404, detail="No class with that join code")
    return sc


def _membership(db: Session, class_id: int, user_id: int) -> SageMembership | None:
    return db.scalar(
        select(SageMembership).where(
            SageMembership.class_id == class_id, SageMembership.user_id == user_id
        )
    )


def _require_member(db: Session, class_id: int, user: User) -> SageMembership:
    m = _membership(db, class_id, user.id)
    if not m:
        raise HTTPException(status_code=403, detail="You are not a member of this class")
    return m


def _ensure_membership(db: Session, sc: SageClass, user: User, role: str) -> SageMembership:
    m = _membership(db, sc.id, user.id)
    if not m:
        m = SageMembership(class_id=sc.id, user_id=user.id, role=role)
        db.add(m)
        db.flush()
    return m


# ---------------------------------------------------------------- auth / onboarding

@router.post("/signup", response_model=SageAuthOut, status_code=201)
def signup(payload: SageSignup, db: Session = Depends(get_db)) -> SageAuthOut:
    """Create a standalone instructor account (no LMS needed)."""
    email = payload.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    user = User(email=email, full_name=payload.full_name.strip(), role=UserRole.instructor,
                hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return _auth_out(user)


@router.post("/join", response_model=SageAuthOut, status_code=201)
def join_with_signup(payload: SageJoinSignup, db: Session = Depends(get_db)) -> SageAuthOut:
    """Create a student account and join a class by code in one step."""
    sc = _class_by_code(db, payload.join_code)
    email = payload.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    user = User(email=email, full_name=payload.full_name.strip(), role=UserRole.student,
                hashed_password=hash_password(payload.password))
    db.add(user)
    db.flush()
    _ensure_membership(db, sc, user, "student")
    db.commit()
    db.refresh(user)
    return _auth_out(user)


@router.post("/guest", response_model=SageAuthOut, status_code=201)
def guest_join(payload: SageGuestJoin, db: Session = Depends(get_db)) -> SageAuthOut:
    """Join a class with just a name — a frictionless guest account is created."""
    sc = _class_by_code(db, payload.join_code)
    email = f"guest-{secrets.token_hex(8)}@sage.local"
    user = User(email=email, full_name=payload.full_name.strip(), role=UserRole.student,
                hashed_password=hash_password(secrets.token_urlsafe(24)))
    db.add(user)
    db.flush()
    _ensure_membership(db, sc, user, "student")
    db.commit()
    db.refresh(user)
    return _auth_out(user)


@router.post("/classes/join")
def join_existing(
    payload: JoinByCode, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    """An already-signed-in user joins a class by code."""
    sc = _class_by_code(db, payload.join_code)
    _ensure_membership(db, sc, user, "student")
    db.commit()
    return {"class_id": sc.id, "name": sc.name}


# ---------------------------------------------------------------- classes

def _class_summary(db: Session, sc: SageClass, role: str) -> dict:
    members = db.scalar(select(func.count(SageMembership.id)).where(
        SageMembership.class_id == sc.id)) or 0
    posts = db.scalar(select(func.count(SagePost.id)).where(SagePost.class_id == sc.id)) or 0
    return {
        "id": sc.id, "name": sc.name, "subject": sc.subject, "role": role,
        "join_code": sc.join_code, "member_count": members, "post_count": posts,
    }


@router.post("/classes", status_code=201)
def create_class(
    payload: ClassCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    sc = SageClass(name=payload.name.strip(), subject=(payload.subject or None),
                   join_code=_gen_join_code(db), owner_id=user.id)
    db.add(sc)
    db.flush()
    db.add(SageMembership(class_id=sc.id, user_id=user.id, role="instructor"))
    db.commit()
    db.refresh(sc)
    return _class_summary(db, sc, "instructor")


@router.get("/classes")
def my_classes(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    pairs = db.execute(
        select(SageClass, SageMembership.role)
        .join(SageMembership, SageMembership.class_id == SageClass.id)
        .where(SageMembership.user_id == user.id)
        .order_by(SageClass.created_at.desc())
    ).all()
    return [_class_summary(db, sc, role) for sc, role in pairs]


@router.get("/classes/{class_id}")
def class_detail(
    class_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    sc = db.get(SageClass, class_id)
    if not sc:
        raise HTTPException(status_code=404, detail="Class not found")
    m = _require_member(db, class_id, user)
    return _class_summary(db, sc, m.role)


# ---------------------------------------------------------------- posts & answers

def _display_name(db: Session, user_id: int | None) -> str:
    if user_id is None:
        return "Removed user"
    u = db.get(User, user_id)
    return u.full_name if u else "Unknown"


def _post_author(db: Session, post: SagePost, viewer_is_instructor: bool) -> str:
    if post.anonymous and not viewer_is_instructor:
        return "Anonymous"
    name = _display_name(db, post.author_id)
    if post.anonymous:  # instructor sees the real name, flagged
        name = f"{name} (anonymous)"
    return name


def _answer_out(db: Session, a: SageAnswer) -> dict:
    if a.is_ai:
        author = "Sage (AI)"
    elif a.is_instructor:
        author = f"{_display_name(db, a.author_id)} (instructor)"
    else:
        author = _display_name(db, a.author_id)
    return {
        "id": a.id, "body": a.body, "is_ai": a.is_ai, "is_instructor": a.is_instructor,
        "endorsed": a.endorsed, "author": author, "created_at": a.created_at,
    }


def _post_list_item(db: Session, p: SagePost, viewer_is_instructor: bool) -> dict:
    answer_count = db.scalar(select(func.count(SageAnswer.id)).where(
        SageAnswer.post_id == p.id, SageAnswer.is_ai.is_(False))) or 0
    endorsed = db.scalar(select(func.count(SageAnswer.id)).where(
        SageAnswer.post_id == p.id, SageAnswer.endorsed.is_(True))) or 0
    item = {
        "id": p.id, "title": p.title, "tags": p.tags, "anonymous": p.anonymous,
        "resolved": p.resolved, "author": _post_author(db, p, viewer_is_instructor),
        "answer_count": answer_count, "has_endorsed": endorsed > 0, "created_at": p.created_at,
    }
    if viewer_is_instructor:
        item["ai_misconception"] = p.ai_misconception
    return item


@router.get("/classes/{class_id}/posts")
def list_posts(
    class_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[dict]:
    m = _require_member(db, class_id, user)
    posts = db.scalars(
        select(SagePost).where(SagePost.class_id == class_id).order_by(SagePost.created_at.desc())
    ).all()
    return [_post_list_item(db, p, m.role == "instructor") for p in posts]


@router.post("/classes/{class_id}/posts", status_code=201)
def create_post(
    class_id: int, payload: PostCreate,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
) -> dict:
    sc = db.get(SageClass, class_id)
    if not sc:
        raise HTTPException(status_code=404, detail="Class not found")
    _require_member(db, class_id, user)
    post = SagePost(
        class_id=class_id, author_id=user.id, title=payload.title.strip(),
        body=payload.body or "", tags=(payload.tags or None), anonymous=payload.anonymous,
    )
    db.add(post)
    db.flush()

    # Socratic AI reply + misconception flag (best-effort; never blocks the post).
    try:
        reply, misconception = sage_ai.socratic_reply(post.title, post.body, sc.subject)
        post.ai_misconception = misconception
        db.add(SageAnswer(post_id=post.id, author_id=None, is_ai=True, body=reply))
    except Exception:  # noqa: BLE001
        pass

    db.commit()
    db.refresh(post)
    return _post_detail(db, post, viewer_is_instructor=False)


def _post_detail(db: Session, post: SagePost, *, viewer_is_instructor: bool) -> dict:
    answers = db.scalars(
        select(SageAnswer).where(SageAnswer.post_id == post.id)
        .order_by(SageAnswer.endorsed.desc(), SageAnswer.created_at.asc())
    ).all()
    out = {
        "id": post.id, "class_id": post.class_id, "title": post.title, "body": post.body,
        "tags": post.tags, "anonymous": post.anonymous, "resolved": post.resolved,
        "author": _post_author(db, post, viewer_is_instructor),
        "answers": [_answer_out(db, a) for a in answers], "created_at": post.created_at,
    }
    if viewer_is_instructor:
        out["ai_misconception"] = post.ai_misconception
    return out


@router.get("/posts/{post_id}")
def get_post(
    post_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    post = db.get(SagePost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    m = _require_member(db, post.class_id, user)
    return _post_detail(db, post, viewer_is_instructor=m.role == "instructor")


@router.post("/posts/{post_id}/answers", status_code=201)
def add_answer(
    post_id: int, payload: AnswerCreate,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
) -> dict:
    post = db.get(SagePost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    m = _require_member(db, post.class_id, user)
    db.add(SageAnswer(post_id=post_id, author_id=user.id,
                      is_instructor=(m.role == "instructor"), body=payload.body.strip()))
    db.commit()
    db.refresh(post)
    return _post_detail(db, post, viewer_is_instructor=m.role == "instructor")


@router.post("/answers/{answer_id}/endorse")
def endorse_answer(
    answer_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    a = db.get(SageAnswer, answer_id)
    if not a:
        raise HTTPException(status_code=404, detail="Answer not found")
    post = db.get(SagePost, a.post_id)
    m = _require_member(db, post.class_id, user)
    if m.role != "instructor":
        raise HTTPException(status_code=403, detail="Only the instructor can endorse answers")
    a.endorsed = not a.endorsed
    db.commit()
    return {"id": a.id, "endorsed": a.endorsed}


@router.post("/posts/{post_id}/resolve")
def resolve_post(
    post_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    post = db.get(SagePost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    m = _require_member(db, post.class_id, user)
    if m.role != "instructor" and post.author_id != user.id:
        raise HTTPException(status_code=403, detail="Only the instructor or author can resolve")
    post.resolved = not post.resolved
    db.commit()
    return {"id": post.id, "resolved": post.resolved}


# ---------------------------------------------------------------- instructor insights

@router.get("/classes/{class_id}/insights")
def insights(
    class_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    m = _require_member(db, class_id, user)
    if m.role != "instructor":
        raise HTTPException(status_code=403, detail="Instructors only")

    posts = db.scalars(select(SagePost).where(SagePost.class_id == class_id)).all()
    members = db.scalar(select(func.count(SageMembership.id)).where(
        SageMembership.class_id == class_id)) or 0

    tag_counter: Counter[str] = Counter()
    mis_counter: Counter[str] = Counter()
    unanswered = 0
    for p in posts:
        for t in (p.tags or "").split(","):
            t = t.strip()
            if t:
                tag_counter[t] += 1
        if p.ai_misconception:
            mis_counter[p.ai_misconception] += 1
        human = db.scalar(select(func.count(SageAnswer.id)).where(
            SageAnswer.post_id == p.id, SageAnswer.is_ai.is_(False))) or 0
        if human == 0:
            unanswered += 1

    return {
        "members": members,
        "total_posts": len(posts),
        "open_count": sum(1 for p in posts if not p.resolved),
        "resolved_count": sum(1 for p in posts if p.resolved),
        "unanswered_by_humans": unanswered,
        "top_tags": [{"tag": t, "count": c} for t, c in tag_counter.most_common(8)],
        "top_misconceptions": [{"label": x, "count": c} for x, c in mis_counter.most_common(8)],
    }
