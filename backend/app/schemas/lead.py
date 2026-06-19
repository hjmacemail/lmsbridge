from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.schemas.common import ORMModel


class LeadCreate(BaseModel):
    kind: str = "demo"
    name: str
    email: EmailStr
    organization: str | None = None
    role: str | None = None
    plan: str | None = None
    message: str | None = None


class LeadOut(ORMModel):
    id: int
    kind: str
    name: str
    email: EmailStr
    organization: str | None = None
    role: str | None = None
    plan: str | None = None
    message: str | None = None
    status: str
    created_at: datetime
