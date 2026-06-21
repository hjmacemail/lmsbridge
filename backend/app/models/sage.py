"""Sage — standalone AI-augmented class Q&A board (sage.lmsbridge.app).

A lightweight, LMS-independent surface: an instructor creates a class, shares a join
code, students post questions, and Sage (the AI) replies Socratically while peers and
the instructor answer and endorse. Reuses the platform's User + LLM layer.
"""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class SageClass(Base, TimestampMixin):
    __tablename__ = "sage_classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(120))
    join_code: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    posts: Mapped[list[SagePost]] = relationship(  # noqa: F821
        back_populates="sage_class", cascade="all, delete-orphan"
    )
    memberships: Mapped[list[SageMembership]] = relationship(  # noqa: F821
        back_populates="sage_class", cascade="all, delete-orphan"
    )


class SageMembership(Base, TimestampMixin):
    __tablename__ = "sage_memberships"

    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(
        ForeignKey("sage_classes.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16), default="student")  # instructor | student

    sage_class: Mapped[SageClass] = relationship(back_populates="memberships")

    __table_args__ = (UniqueConstraint("class_id", "user_id", name="uq_sage_member"),)


class SagePost(Base, TimestampMixin):
    __tablename__ = "sage_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(
        ForeignKey("sage_classes.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str | None] = mapped_column(String(255))  # comma-separated
    anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    # Concept-level misconception the AI flagged from the question (drives instructor insights).
    ai_misconception: Mapped[str | None] = mapped_column(String(255))

    sage_class: Mapped[SageClass] = relationship(back_populates="posts")
    answers: Mapped[list[SageAnswer]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class SageAnswer(Base, TimestampMixin):
    __tablename__ = "sage_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("sage_posts.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    is_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    is_instructor: Mapped[bool] = mapped_column(Boolean, default=False)
    endorsed: Mapped[bool] = mapped_column(Boolean, default=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    post: Mapped[SagePost] = relationship(back_populates="answers")
