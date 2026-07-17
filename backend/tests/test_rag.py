"""Unit tests for the RAG pipeline and the router."""
from __future__ import annotations

import pytest

from backend.agents.router import _sanitise, route
from backend.rag.chunker import load_all_chunks, split_text
from backend.rag.retriever import format_context, retrieve


# --- chunking --------------------------------------------------------------
def test_split_respects_size():
    text = "\n".join(f"Paragraph number {i} with some filler content." for i in range(40))
    chunks = split_text(text, size=300, overlap=50)
    assert chunks
    # Allow slack for the overlap tail that gets prepended to the next chunk.
    assert all(len(c) <= 300 + 50 for c in chunks)


def test_oversized_paragraph_is_windowed():
    chunks = split_text("x" * 2000, size=300, overlap=50)
    assert len(chunks) > 1


def test_all_kb_docs_chunked_with_domains():
    chunks = load_all_chunks()
    assert len(chunks) > 20
    assert all(c.domains for c in chunks), "every chunk needs a domain tag"
    assert len({c.source for c in chunks}) == 8


def test_every_agent_domain_has_coverage():
    """A domain with no chunks means that agent can never answer anything."""
    chunks = load_all_chunks()
    covered = {d for c in chunks for d in c.domains}
    assert {"billing", "technical", "product", "complaint", "faq"} <= covered


# --- retrieval -------------------------------------------------------------
def test_retrieval_returns_scored_chunks():
    results = retrieve("How long does a refund take?", domain="billing")
    assert results
    assert results[0]["score"] >= results[-1]["score"], "results must be ranked"
    assert "text" in results[0]


def test_domain_filter_is_enforced():
    for r in retrieve("refund", domain="technical"):
        assert "technical" in r["domains"]


def test_refund_query_finds_refund_policy():
    sources = {r["source"] for r in retrieve("refund timeline credit card",
                                             domain="billing", top_k=4)}
    assert "refund_policy.pdf" in sources


def test_format_context_handles_empty():
    assert "no relevant documents" in format_context([])


def test_format_context_labels_sources():
    ctx = format_context(retrieve("refund", domain="billing", top_k=2))
    assert "Source:" in ctx and "page" in ctx


# --- router ----------------------------------------------------------------
def test_router_returns_valid_agents():
    decision = route("I want a refund for my order")
    assert decision["agents"]
    assert set(decision["agents"]) <= {"billing", "technical", "product",
                                       "complaint", "faq"}
    assert 0.0 <= decision["confidence"] <= 1.0


def test_router_never_returns_more_than_two():
    assert len(route("refund payment login error price complaint")["agents"]) <= 2


@pytest.mark.parametrize("payload", [
    {"agents": "billing"},                      # string instead of list
    {"agents": ["Billing Agent"]},              # display name
    {"agents": ["billing", "billing"]},         # duplicates
    {"agents": ["nonsense_agent", "billing"]},  # hallucinated agent
])
def test_sanitise_repairs_bad_llm_output(payload):
    out = _sanitise(payload, "I want a refund")
    assert out["agents"] == ["billing"]


def test_sanitise_falls_back_when_nothing_valid():
    out = _sanitise({"agents": ["made_up"]}, "I want a refund for my payment")
    assert out["agents"] == ["billing"]
    assert out["method"] == "fallback"


def test_sanitise_clamps_confidence():
    assert _sanitise({"agents": ["faq"], "confidence": 9.5}, "hi")["confidence"] == 1.0
    assert _sanitise({"agents": ["faq"], "confidence": "abc"}, "hi")["confidence"] == 0.5
