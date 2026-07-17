"""
Intent detection + agent routing.

This is Module 3 and Module 4 of the brief combined: a single LLM call performs
intent classification and returns the agent(s) to invoke. One call rather than
two because the classification IS the routing decision - splitting them doubles
latency and cost to produce the same answer.

The router can return MULTIPLE agents. That is the requirement the brief calls
out explicitly: "I paid yesterday but Premium is still locked" is a billing fact
and a technical fault, and answering only half of it is a wrong answer.
"""
from __future__ import annotations

import logging
import re

from backend.agents.specialists import AGENT_DIRECTORY, AGENTS
from backend.llm.client import LLMError, get_llm

log = logging.getLogger(__name__)

VALID = set(AGENTS.keys())

ROUTER_SYSTEM = f"""
You are the intent detection and routing component of a multi-agent customer
support system for TechMart Electronics, an Indian electronics retailer.

Your job is to read a customer message and route it to the correct specialist
agent or agents. You must respond with JSON and nothing else.

Available agents:
{AGENT_DIRECTORY}

Routing rules:
- Return one agent for a single-domain question.
- Return TWO agents when the message genuinely spans two domains. Example:
  "I paid for Premium yesterday but it is still locked" is BOTH billing (the
  payment) and technical (the entitlement not provisioning). Route to both.
- Never return more than two agents. Three-way routing produces bloated,
  repetitive answers.
- Route to "complaint" when the dominant signal is anger, dissatisfaction, a
  repeated failure, or a demand to escalate - even if the underlying topic is
  billing or technical. How the customer feels determines who should answer.
- Route to "faq" only when no specialist fits.
- confidence is your certainty in the routing decision, 0.0 to 1.0. Use below
  0.4 when the message is vague or you are guessing.

Respond with exactly this JSON shape and no other text:
{{"agents": ["billing"], "confidence": 0.9, "reasoning": "one short sentence"}}
"""

# Cheap deterministic backstop for when the LLM is unavailable or returns junk.
# Ordered by specificity: complaint signals win because they override topic.
_FALLBACK_PATTERNS: list[tuple[str, str]] = [
    ("complaint", r"\b(complaint|escalat|worst|terrible|unacceptable|furious|angry|"
                  r"consumer court|legal action|grievance|third time|fed up|disgust)"),
    ("billing", r"\b(refund|payment|paid|invoice|charge|charged|debit|money|"
                r"subscription|premium|emi|cod|wallet|gst|bill)"),
    ("technical", r"\b(login|log in|password|otp|error|crash|bug|not working|broken|"
                  r"install|setup|pair|wifi|wi-fi|connect|reset|blue screen|"
                  r"overheat|charging|offline)"),
    ("product", r"\b(price|cost|spec|feature|compare|comparison|difference|"
                r"available|stock|deliver|shipping|warranty|recommend|which)"),
]


def _fallback_route(query: str) -> dict:
    low = query.lower()
    hits = [name for name, pattern in _FALLBACK_PATTERNS if re.search(pattern, low)]
    if not hits:
        hits = ["faq"]
    return {
        "agents": hits[:2],
        "confidence": 0.35,
        "reasoning": "keyword fallback (LLM router unavailable)",
        "method": "fallback",
    }


def _sanitise(payload: dict, query: str) -> dict:
    """Trust nothing the LLM returns. It will occasionally invent an agent name,
    return a bare string instead of a list, or omit confidence entirely."""
    agents = payload.get("agents", [])
    if isinstance(agents, str):
        agents = [agents]
    if not isinstance(agents, list):
        agents = []

    clean: list[str] = []
    for a in agents:
        if not isinstance(a, str):
            continue
        a = a.strip().lower().replace(" agent", "").replace("_agent", "")
        if a in VALID and a not in clean:
            clean.append(a)

    if not clean:
        log.warning("Router returned no valid agents (%r); using fallback.", agents)
        return _fallback_route(query)

    try:
        confidence = float(payload.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5

    return {
        "agents": clean[:2],
        "confidence": max(0.0, min(1.0, confidence)),
        "reasoning": str(payload.get("reasoning", ""))[:200],
        "method": "llm",
    }


def route(query: str, history: str = "") -> dict:
    """Return {"agents": [...], "confidence": float, "reasoning": str, "method": str}."""
    user = f"CONVERSATION SO FAR:\n{history}\n\nCUSTOMER MESSAGE:\n{query}" if history \
        else f"CUSTOMER MESSAGE:\n{query}"
    try:
        payload = get_llm().complete_json(system=ROUTER_SYSTEM, user=user)
        if not isinstance(payload, dict):
            raise LLMError(f"Router returned {type(payload).__name__}, expected object")
        return _sanitise(payload, query)
    except Exception as exc:  # noqa: BLE001
        log.warning("Router LLM call failed (%s); using keyword fallback.", exc)
        return _fallback_route(query)
