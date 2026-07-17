"""Semantic retrieval over the FAISS index, filtered by agent domain."""
from __future__ import annotations

import logging

from backend import config
from backend.embeddings.embedder import get_embedder
from backend.vectorstore.faiss_store import FaissStore

log = logging.getLogger(__name__)

_store: FaissStore | None = None


def get_store() -> FaissStore:
    global _store
    if _store is None:
        _store = FaissStore.load()
        log.info("Loaded vector store: %d chunks", _store.size)
    return _store


def retrieve(
    query: str,
    top_k: int | None = None,
    domain: str | None = None,
    min_score: float | None = None,
) -> list[dict]:
    """Return the top_k chunks for `query`, optionally restricted to `domain`.

    Each result: {id, text, source, domains, page, chunk_index, score}
    """
    store = get_store()
    embedder = get_embedder()
    qv = embedder.encode_one(query)
    return store.search(
        qv,
        top_k=top_k if top_k is not None else config.RETRIEVAL_TOP_K,
        domain=domain,
        min_score=min_score if min_score is not None else config.RETRIEVAL_MIN_SCORE,
    )


def format_context(chunks: list[dict]) -> str:
    """Render chunks for the prompt with source labels.

    Labelling each block with its filename and page is what lets the agent cite
    sources and lets you verify, in the demo, that the answer came from the
    knowledge base rather than the model's memory.
    """
    if not chunks:
        return "(no relevant documents found)"
    blocks = []
    for i, c in enumerate(chunks, 1):
        blocks.append(
            f"[{i}] Source: {c['source']}, page {c['page']} (similarity {c['score']})\n"
            f"{c['text']}"
        )
    return "\n\n".join(blocks)


def reset_store() -> None:
    global _store
    _store = None
