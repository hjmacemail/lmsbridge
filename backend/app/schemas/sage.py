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
    choices: list[str] = Field(..., min_length=2, max_length=8)
    correct: str = Field(..., min_length=1)
    concept: str = Field(..., min_length=1, max_length=120)


class QuizCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    questions: list[QuizQuestionIn] = Field(..., min_length=1, max_length=50)


class QuizAnswer(BaseModel):
    question_id: int
    choice: str


class QuizSubmit(BaseModel):
    answers: list[QuizAnswer]
