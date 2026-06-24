from __future__ import annotations

from pydantic import BaseModel, Field


class SageSignup(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=6, max_length=128)


class SageJoinSignup(BaseModel):
    join_code: str = Field(..., min_length=4, max_length=12)
    full_name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=6, max_length=128)


class SageGuestJoin(BaseModel):
    join_code: str = Field(..., min_length=4, max_length=12)
    full_name: str = Field(..., min_length=1, max_length=255)


class SageAuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    full_name: str
    role: str


class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    subject: str | None = Field(None, max_length=120)


class JoinByCode(BaseModel):
    join_code: str = Field(..., min_length=4, max_length=12)


class QuizQuestionIn(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    qtype: str = Field("mcq", description="mcq | true_false | multi | short")
    choices: list[str] = Field(default_factory=list, max_length=10)
    # Correct option(s) for mcq/true_false/multi, or accepted answer(s) for short.
    # Accepts a single string or a list.
    correct: list[str] | str = Field(...)
    concept: str = Field(..., min_length=1, max_length=120)


class QuizCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    questions: list[QuizQuestionIn] = Field(..., min_length=1, max_length=50)
    due_at: str | None = None  # ISO 8601 datetime, optional


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field("", max_length=8000)


class QuizAnswer(BaseModel):
    question_id: int
    choice: str | None = None          # mcq / true_false / short
    choices: list[str] | None = None   # multi-select


class QuizSubmit(BaseModel):
    answers: list[QuizAnswer]


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    title: str | None = Field(None, max_length=160)
    bio: str | None = Field(None, max_length=2000)


class SyllabusUpdate(BaseModel):
    syllabus: str = Field("", max_length=20000)


class MaterialTextCreate(BaseModel):
    kind: str = Field("note", description="note | code")
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1, max_length=100000)
    language: str | None = Field(None, max_length=32)
