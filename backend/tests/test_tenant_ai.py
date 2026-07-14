"""Per-institution BYO-AI config (admin-only) + privacy guard behavior."""
from app.llm.base import LLMMessage, LLMProvider, LLMResponse
from app.llm.guard import GuardedProvider
from app.llm.providers.mock import MockProvider


class _CapturingExternal(LLMProvider):
    name = "openai"  # external

    def __init__(self):
        super().__init__("ext-model")
        self.seen: list[str] = []
        self.called = False

    def complete(self, messages, *, json_mode=False):
        self.called = True
        self.seen = [m.content for m in messages]
        return LLMResponse(text='{"reply":"x","complete":false}',
                           model=self.model, provider=self.name)


class _FailingExternal(LLMProvider):
    name = "anthropic"  # external

    def __init__(self):
        super().__init__("ext-model")

    def complete(self, messages, *, json_mode=False):
        raise RuntimeError("401 authentication_error: invalid api key")


def test_provider_error_falls_back_to_mock_not_500():
    g = GuardedProvider(_FailingExternal(), fallback=MockProvider("m"), external_allowed=True)
    out = g.complete([LLMMessage("user", "Concept: Inheritance")], json_mode=True)
    assert out.provider == "mock", "a provider runtime error must degrade to the local fallback"


def test_external_blocked_falls_back_locally():
    ext = _CapturingExternal()
    g = GuardedProvider(ext, fallback=MockProvider("m"), external_allowed=False)
    out = g.complete([LLMMessage("user", "Concept: Inheritance")], json_mode=True)
    assert ext.called is False, "external provider must not be called when blocked"
    assert out.provider == "mock"


def test_pii_is_redacted_before_send():
    ext = _CapturingExternal()
    g = GuardedProvider(ext, fallback=MockProvider("m"),
                        external_allowed=True, pii_minimization=True, redact_names=["Ada Lovelace"])
    g.complete([LLMMessage("user", "Ada Lovelace a@b.edu id 9988776 on binary")], json_mode=True)
    sent = "\n".join(ext.seen)
    assert "a@b.edu" not in sent and "9988776" not in sent and "Ada Lovelace" not in sent


def _login(client, email, pw="pw"):
    r = client.post("/api/v1/auth/login", data={"username": email, "password": pw})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_tenant_ai_settings_admin_only(client, db):
    from app.core.security import hash_password
    from app.models.enums import UserRole
    from app.models.tenant import Tenant
    from app.models.user import User

    t = Tenant(name="Inst", slug="inst")
    db.add(t)
    db.flush()
    admin = User(email="admin@x.edu", full_name="Admin", role=UserRole.admin,
                 tenant_id=t.id, hashed_password=hash_password("pw"))
    inst = User(email="prof@x.edu", full_name="Prof", role=UserRole.instructor,
                tenant_id=t.id, hashed_password=hash_password("pw"))
    db.add_all([admin, inst])
    db.commit()

    h = _login(client, "admin@x.edu")
    got = client.get("/api/v1/tenants/me", headers=h)
    assert got.status_code == 200 and got.json()["ai_key_set"] is False

    upd = client.put("/api/v1/tenants/me/ai", headers=h, json={
        "ai_provider": "azure_openai", "ai_model": "gpt-4o",
        "ai_endpoint": "https://x.openai.azure.com", "ai_deployment": "gpt4o",
        "ai_api_key": "super-secret", "external_ai_allowed": False, "pii_minimization": True,
    })
    assert upd.status_code == 200
    body = upd.json()
    assert body["ai_key_set"] is True
    assert "super-secret" not in str(body)  # key never returned
    assert body["external_ai_allowed"] is False

    # Instructor is forbidden.
    assert client.get("/api/v1/tenants/me", headers=_login(client, "prof@x.edu")).status_code == 403
