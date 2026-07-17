"""
Backend test suite.

Run:  pytest backend/tests -v

These run against the mock LLM and the in-memory DB, so they need no API key,
no Mongo, and no network. They do need the vector index to exist:
    python scripts/build_kb.py && python -m backend.rag.ingest
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def token(client):
    resp = client.post("/auth/register", json={
        "email": "pytest@example.com", "password": "password123", "name": "Pytest"
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def auth(token):
    return {"Authorization": f"Bearer {token}"}


# --- health ----------------------------------------------------------------
def test_health_reports_components(client):
    body = client.get("/health").json()
    assert body["vector_store"]["ready"] is True, "run: python -m backend.rag.ingest"
    assert body["vector_store"]["chunks"] > 0
    assert "provider" in body["llm"]


# --- auth ------------------------------------------------------------------
def test_duplicate_email_rejected(client, token):
    resp = client.post("/auth/register", json={
        "email": "pytest@example.com", "password": "password123", "name": "Copy"
    })
    assert resp.status_code == 409


def test_login_wrong_password(client, token):
    resp = client.post("/auth/login", json={
        "email": "pytest@example.com", "password": "wrongpassword"
    })
    assert resp.status_code == 401


def test_login_success(client, token):
    resp = client.post("/auth/login", json={
        "email": "pytest@example.com", "password": "password123"
    })
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == "pytest@example.com"


def test_short_password_rejected(client):
    resp = client.post("/auth/register", json={
        "email": "x@example.com", "password": "short", "name": "X"
    })
    assert resp.status_code == 422


def test_chat_requires_auth(client):
    assert client.post("/chat", json={"message": "hello"}).status_code == 401


def test_bad_token_rejected(client):
    resp = client.post("/chat", json={"message": "hi"},
                       headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


# --- chat ------------------------------------------------------------------
def test_chat_returns_grounded_answer(client, auth):
    resp = client.post("/chat", headers=auth,
                       json={"message": "How long does a credit card refund take?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"]
    assert body["agents"], "at least one agent must handle every query"
    assert body["sources"], "answer must cite knowledge base sources"
    assert body["session_id"]


def test_cross_domain_query_invokes_two_agents(client, auth):
    """The brief's headline requirement: a query spanning billing and technical
    must fan out to both specialists rather than being answered by one."""
    resp = client.post("/chat", headers=auth, json={
        "message": "I paid for Premium yesterday but it is still locked"
    })
    body = resp.json()
    assert len(body["agents"]) == 2, f"expected 2 agents, got {body['agents']}"
    assert set(body["agents"]) == {"billing", "technical"}


def test_agent_never_exceeds_two(client, auth):
    resp = client.post("/chat", headers=auth, json={
        "message": "refund payment error login price complaint escalate broken"
    })
    assert len(resp.json()["agents"]) <= 2


def test_empty_message_rejected(client, auth):
    assert client.post("/chat", headers=auth, json={"message": ""}).status_code == 422


# --- memory / history ------------------------------------------------------
def test_history_persists_and_is_ordered(client, auth):
    sid = client.post("/chat", headers=auth,
                      json={"message": "What are your support hours?"}).json()["session_id"]
    client.post("/chat", headers=auth,
                json={"message": "And on Sundays?", "session_id": sid})

    rows = client.get(f"/chat/history/{sid}", headers=auth).json()
    assert len(rows) == 4  # 2 user + 2 assistant
    assert [r["role"] for r in rows] == ["user", "assistant", "user", "assistant"]


def test_sessions_listed(client, auth):
    sessions = client.get("/chat/sessions", headers=auth).json()
    assert len(sessions) >= 1
    assert all(s["message_count"] > 0 for s in sessions)


def test_session_isolation_between_users(client, auth):
    """A user must not be able to read another user's session by guessing the id."""
    sid = client.post("/chat", headers=auth,
                      json={"message": "My private billing question"}).json()["session_id"]

    other = client.post("/auth/register", json={
        "email": "intruder@example.com", "password": "password123", "name": "Intruder"
    }).json()["access_token"]

    rows = client.get(f"/chat/history/{sid}",
                      headers={"Authorization": f"Bearer {other}"}).json()
    assert rows == [], "another user's history leaked"


def test_delete_session(client, auth):
    sid = client.post("/chat", headers=auth,
                      json={"message": "Delete me"}).json()["session_id"]
    assert client.delete(f"/chat/history/{sid}", headers=auth).status_code == 204
    assert client.get(f"/chat/history/{sid}", headers=auth).json() == []


# --- analytics -------------------------------------------------------------
def test_analytics(client, auth):
    body = client.get("/analytics", headers=auth).json()
    assert body["total_messages"] > 0
    assert isinstance(body["agent_usage"], dict)
    assert 0.0 <= body["escalation_rate"] <= 1.0
