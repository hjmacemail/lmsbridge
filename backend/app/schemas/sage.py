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


class ClassCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    subject: str | None = Field(None, max_length=120)


class JoinByCode(BaseModel):
    join_code: str = Field(..., min_length=4, max_length=12)


class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field("", max_length=8000)
    tags: str | None = Field(None, max_length=255)
    anonymous: bool = False


class AnswerCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=8000)
