"""
The orchestrator: route -> run agent(s) -> aggregate -> decide escalation.

This is the top of the multi-agent system. Everything the API layer needs is
behind `Orchestrator.handle()`.

Design note on aggregation: when two agents answer, we do NOT simply concatenate
them. Two specialists answering "I paid but Premium is locked" will both open by
restating the problem and both offer to help - stapling them together reads like
a bureaucracy. A third LLM call merges them into one voice. That call is skipped
entirely for single-agent queries, which is the common case, so the latency cost
lands only where it buys something.
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor

from backend.agents.base import AgentResponse
from backend.agents.router import route
from backend.agents.specialists import AGENTS
from backend.llm.client import get_llm

log = logging.getLogger(__name__)

AGGREGATOR_SYSTEM = """
You merge answers from two specialist support agents into a single reply to the
customer, written in one consistent voice as TechMart Electronics support.

Rules:
- Merge, do not concatenate. Remove duplicated greetings, restatements of the
  problem, and repeated offers to help. The customer must not be able to tell
  that two agents were involved.
- Keep every concrete fact, figure, timeline, and source citation from both
  answers. Losing a detail in the merge is the one unacceptable failure.
- Lead with whichever part unblocks the customer fastest, then the rest.
- If the two answers conflict, say what the customer should do first and note
  that support will confirm the rest. Never silently pick one.
- Keep it under 200 words. No preamble, no "here is the merged answer" - output
  only the reply itself.
"""

ESCALATION_NOTE = (
    "\n\nI am also passing this to a human agent so someone can follow up with "
    "you directly. You can reach the team any time at support@techmart.example.com."
)


class Orchestrator:
    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers

    def _run_agents(self, names: list[str], query: str, history: str) -> list[AgentResponse]:
        # Two agents run concurrently. Each is an independent network-bound LLM
        # call, so running them in parallel makes a two-agent query cost roughly
        # the same wall-clock time as a one-agent query.
        if len(names) == 1:
            return [AGENTS[names[0]].handle(query, history)]
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = [pool.submit(AGENTS[n].handle, query, history) for n in names]
            return [f.result() for f in futures]

    def _aggregate(self, responses: list[AgentResponse], query: str) -> str:
        if len(responses) == 1:
            return responses[0].answer
        blocks = "\n\n".join(
            f"--- {r.agent.upper()} AGENT ---\n{r.answer}" for r in responses
        )
        try:
            return get_llm().complete(
                system=AGGREGATOR_SYSTEM,
                user=f"CUSTOMER QUESTION:\n{query}\n\nSPECIALIST ANSWERS:\n{blocks}",
            )
        except Exception as exc:  # noqa: BLE001
            # Degrade to labelled concatenation rather than dropping an answer.
            log.warning("Aggregation failed (%s); falling back to concatenation.", exc)
            return "\n\n".join(r.answer for r in responses)

    def handle(self, query: str, history: str = "") -> dict:
        t0 = time.perf_counter()

        decision = route(query, history)
        names = decision["agents"]
        log.info("Routed %r -> %s (confidence=%.2f, %s)",
                 query[:60], names, decision["confidence"], decision["method"])

        responses = self._run_agents(names, query, history)
        answer = self._aggregate(responses, query)

        # Escalate if any specialist could not ground its answer, or if the
        # router itself was unsure who should even be answering.
        escalate = any(r.escalate for r in responses) or decision["confidence"] < 0.35
        if escalate and "human agent" not in answer.lower():
            answer += ESCALATION_NOTE

        # Deduplicate sources across agents; two agents often cite the same doc.
        seen: set[tuple[str, int]] = set()
        sources: list[dict] = []
        for r in responses:
            for s in r.sources:
                key = (s["source"], s["page"])
                if key not in seen:
                    seen.add(key)
                    sources.append({"source": s["source"], "page": s["page"],
                                    "score": s["score"]})

        return {
            "answer": answer,
            "agents": names,
            "routing": decision,
            "sources": sources,
            "escalated": escalate,
            "agent_details": [r.to_dict() for r in responses],
            "latency_ms": int((time.perf_counter() - t0) * 1000),
        }


orchestrator = Orchestrator()
