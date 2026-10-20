"""
Tests for JWT authentication and scope checks
"""
import base64
import json
from datetime import timedelta

import pytest
from pydantic import SecretStr

from app.core.config import settings
from app.core.security import create_access_token


@pytest.fixture
def auth_on(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "JWT_SECRET", SecretStr("test-secret"))


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_auth_disabled_allows_anonymous(client, workflow_calls):
    response = client.post("/api/v1/query", json={"query": "What is the leave policy?"})
    assert response.status_code == 200


def test_missing_token_is_401(client, workflow_calls, auth_on):
    response = client.post("/api/v1/query", json={"query": "hi"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_valid_token_with_scope_is_accepted(client, workflow_calls, auth_on):
    token = create_access_token("alice", ["query:read"])
    response = client.post("/api/v1/query", json={"query": "hi"}, headers=bearer(token))
    assert response.status_code == 200


def test_token_without_scope_is_403(client, workflow_calls, auth_on):
    token = create_access_token("alice", ["documents:write"])
    response = client.post("/api/v1/query", json={"query": "hi"}, headers=bearer(token))
    assert response.status_code == 403


def test_expired_token_is_401(client, workflow_calls, auth_on):
    token = create_access_token("alice", ["query:read"], expires_in=timedelta(seconds=-1))
    response = client.post("/api/v1/query", json={"query": "hi"}, headers=bearer(token))
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"


def test_token_signed_with_other_key_is_401(client, workflow_calls, auth_on, monkeypatch):
    token = create_access_token("mallory", ["query:read"])
    monkeypatch.setattr(settings, "JWT_SECRET", SecretStr("a-different-secret"))
    response = client.post("/api/v1/query", json={"query": "hi"}, headers=bearer(token))
    assert response.status_code == 401


def test_token_for_other_audience_is_401(client, workflow_calls, auth_on, monkeypatch):
    monkeypatch.setattr(settings, "JWT_AUDIENCE", "some-other-api")
    token = create_access_token("alice", ["query:read"])
    monkeypatch.setattr(settings, "JWT_AUDIENCE", "omnihelp-api")
    response = client.post("/api/v1/query", json={"query": "hi"}, headers=bearer(token))
    assert response.status_code == 401


def test_unsigned_alg_none_token_is_401(client, workflow_calls, auth_on):
    def b64(obj):
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()

    claims = {"sub": "mallory", "scope": "query:read", "iss": settings.JWT_ISSUER,
              "aud": settings.JWT_AUDIENCE, "iat": 0, "exp": 9999999999}
    token = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64(claims)}."
    response = client.post("/api/v1/query", json={"query": "hi"}, headers=bearer(token))
    assert response.status_code == 401


def test_settings_reject_auth_without_secret():
    from app.core.config import Settings
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(AUTH_ENABLED=True, JWT_SECRET=None, OPENAI_API_KEY="x")
