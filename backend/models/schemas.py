"""Pydantic v2 request/response models."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# --- Auth ------------------------------------------------------------------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=80)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserPublic"


class UserPublic(BaseModel):
    id: str
    email: str
    name: str
    is_premium: bool = False


# --- Chat ------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


class SourceRef(BaseModel):
    source: str
    page: int
    score: float


class RoutingInfo(BaseModel):
    agents: list[str]
    confidence: float
    reasoning: str = ""
    method: str = "llm"


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    answer: str
    agents: list[str]
    routing: RoutingInfo
    sources: list[SourceRef] = []
    escalated: bool = False
    latency_ms: int = 0


class Message(BaseModel):
    id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    agents: list[str] = []
    sources: list[SourceRef] = []
    escalated: bool = False
    latency_ms: int = 0
    timestamp: datetime


class SessionSummary(BaseModel):
    session_id: str
    title: str
    message_count: int
    updated_at: datetime


# --- Analytics -------------------------------------------------------------
class AnalyticsResponse(BaseModel):
    total_conversations: int
    total_messages: int
    agent_usage: dict[str, int]
    escalation_rate: float
    avg_latency_ms: float
    p95_latency_ms: float


TokenResponse.model_rebuild()
