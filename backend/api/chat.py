"""Modules 2 and 8: chat endpoint, conversation memory, session history."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend import config
from backend.agents.orchestrator import orchestrator
from backend.api.auth import current_user
from backend.database.db import get_db, new_id, now
from backend.models.schemas import (ChatRequest, ChatResponse, Message,
                                    SessionSummary)

router = APIRouter(prefix="/chat", tags=["chat"])


def build_history(session_id: str, user_id: str) -> str:
    """Render the last N turns as plain text for the LLM.

    Only the last MEMORY_TURNS messages go in. Full history would blow the
    context window on a long session and, worse, bury the current question under
    stale text - routing accuracy drops when the model over-weights old turns.
    """
    rows = get_db().get_messages(session_id, user_id, limit=config.MEMORY_TURNS)
    if not rows:
        return ""
    return "\n".join(
        f"{'Customer' if m['role'] == 'user' else 'Support'}: {m['content']}"
        for m in rows
    )


@router.post("", response_model=ChatResponse)
def chat(body: ChatRequest, user: dict = Depends(current_user)):
    db = get_db()
    session_id = body.session_id or new_id()
    history = build_history(session_id, user["id"])

    db.insert_message({
        "id": new_id(), "session_id": session_id, "user_id": user["id"],
        "role": "user", "content": body.message, "agents": [], "sources": [],
        "escalated": False, "latency_ms": 0, "timestamp": now(),
    })

    result = orchestrator.handle(body.message, history)

    assistant_id = new_id()
    db.insert_message({
        "id": assistant_id, "session_id": session_id, "user_id": user["id"],
        "role": "assistant", "content": result["answer"],
        "agents": result["agents"], "sources": result["sources"],
        "escalated": result["escalated"], "latency_ms": result["latency_ms"],
        "timestamp": now(),
    })

    return ChatResponse(
        session_id=session_id,
        message_id=assistant_id,
        answer=result["answer"],
        agents=result["agents"],
        routing=result["routing"],
        sources=result["sources"],
        escalated=result["escalated"],
        latency_ms=result["latency_ms"],
    )


@router.get("/sessions", response_model=list[SessionSummary])
def sessions(user: dict = Depends(current_user)):
    return get_db().get_sessions(user["id"])


@router.get("/history/{session_id}", response_model=list[Message])
def history(session_id: str, user: dict = Depends(current_user)):
    # Scoped by user_id, so one user cannot read another's session by guessing
    # the id.
    return get_db().get_messages(session_id, user["id"], limit=500)


@router.delete("/history/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, user: dict = Depends(current_user)):
    deleted = get_db().delete_session(session_id, user["id"])
    if deleted == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
