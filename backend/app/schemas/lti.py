from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import ORMModel


class DeploymentOut(ORMModel):
    id: int
    deployment_id: str
    label: str | None = None


class RegistrationOut(ORMModel):
    id: int
    name: str
    issuer: str
    client_id: str
    auth_login_url: str
    auth_token_url: str
    key_set_url: str
    audience: str | None = None
    active: bool
    auto_register_deployments: bool
    deployments: list[DeploymentOut] = []


class RegistrationCreate(BaseModel):
    name: str
    issuer: str
    client_id: str
    auth_login_url: str
    auth_token_url: str
    key_set_url: str
    audience: str | None = None
    deployment_id: str | None = None  # optional first deployment


class RegistrationUpdate(BaseModel):
    name: str | None = None
    client_id: str | None = None
    auth_login_url: str | None = None
    auth_token_url: str | None = None
    key_set_url: str | None = None
    audience: str | None = None
    active: bool | None = None


class DeploymentCreate(BaseModel):
    deployment_id: str
    label: str | None = None
