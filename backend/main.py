"""
FastAPI entrypoint.

Run:  uvicorn backend.main:app --reload
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import config
from backend.api import analytics, auth, chat
from backend.database.db import get_db
from backend.embeddings.embedder import get_embedder
from backend.llm.client import get_llm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("techmart")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm everything at startup rather than on the first request. Loading the
    # embedding model takes several seconds; doing it lazily means the first
    # customer of the day waits for it.
    log.info("Starting TechMart Support AI")
    get_db()
    get_llm()
    get_embedder()
    try:
        from backend.rag.retriever import get_store
        store = get_store()
        log.info("Vector store ready: %d chunks", store.size)
    except FileNotFoundError:
        log.error("NO VECTOR INDEX FOUND. Run: python -m backend.rag.ingest")
    yield
    log.info("Shutting down")


app = FastAPI(
    title="TechMart Multi-Agent Support AI",
    description=(
        "Multi-agent customer support assistant using RAG and LLMs. "
        "An orchestrator routes each query to one or two of five specialist "
        "agents, each grounded in its own slice of the company knowledge base."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(analytics.router)


@app.get("/", tags=["meta"])
def root():
    return {"service": "TechMart Multi-Agent Support AI", "docs": "/docs"}


@app.get("/health", tags=["meta"])
def health():
    """Reports which backend each swappable component actually resolved to.

    Worth checking before recording your demo: it tells you at a glance whether
    you are running on the real embedding model and a real LLM, or on the
    offline fallbacks.
    """
    from backend.rag.retriever import get_store

    try:
        chunks = get_store().size
        index_ok = True
    except FileNotFoundError:
        chunks, index_ok = 0, False

    embedder = get_embedder()
    return {
        "status": "ok" if index_ok else "degraded",
        "llm": {"provider": get_llm().name, "model": config.active_model()},
        "embeddings": {"backend": embedder.name, "dim": embedder.dim},
        "vector_store": {"ready": index_ok, "chunks": chunks},
        "database": {"backend": get_db().backend},
    }
