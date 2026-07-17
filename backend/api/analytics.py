"""Module 9 (optional in the brief): analytics dashboard data."""
from __future__ import annotations

import collections

from fastapi import APIRouter, Depends

from backend.api.auth import current_user
from backend.database.db import get_db
from backend.models.schemas import AnalyticsResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile. No numpy dependency for one number, and it is
    well defined on tiny samples where interpolation is meaningless."""
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, round(pct / 100 * len(ordered) + 0.5) - 1))
    return ordered[k]


@router.get("", response_model=AnalyticsResponse)
def analytics(user: dict = Depends(current_user)):
    rows = [m for m in get_db().all_messages() if m.get("user_id") == user["id"]]
    assistant = [m for m in rows if m["role"] == "assistant"]

    usage: collections.Counter = collections.Counter()
    for m in assistant:
        usage.update(m.get("agents", []))

    latencies = [float(m.get("latency_ms", 0)) for m in assistant]
    escalated = sum(1 for m in assistant if m.get("escalated"))

    return AnalyticsResponse(
        total_conversations=len({m["session_id"] for m in rows}),
        total_messages=len(rows),
        agent_usage=dict(usage),
        escalation_rate=round(escalated / len(assistant), 3) if assistant else 0.0,
        avg_latency_ms=round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
        p95_latency_ms=round(_percentile(latencies, 95), 1),
    )
