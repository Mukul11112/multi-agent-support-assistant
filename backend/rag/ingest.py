"""
Ingestion: knowledge_base/*.pdf -> chunks -> embeddings -> FAISS index on disk.

Run:  python -m backend.rag.ingest
Re-run this every time the knowledge base PDFs change.
"""
from __future__ import annotations

import collections
import logging
import time

from backend import config
from backend.embeddings.embedder import get_embedder
from backend.rag.chunker import load_all_chunks
from backend.vectorstore.faiss_store import FaissStore

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("ingest")


def main() -> None:
    t0 = time.perf_counter()

    log.info("Reading PDFs from %s", config.KNOWLEDGE_BASE_DIR)
    chunks = load_all_chunks()
    log.info("Produced %d chunks from %d documents",
             len(chunks), len({c.source for c in chunks}))

    per_source = collections.Counter(c.source for c in chunks)
    for src, n in sorted(per_source.items()):
        log.info("   %-28s %3d chunks", src, n)

    per_domain: collections.Counter = collections.Counter()
    for c in chunks:
        per_domain.update(c.domains)
    log.info("Chunks reachable per agent domain: %s", dict(per_domain))

    embedder = get_embedder()
    log.info("Embedding with %s (dim=%d)", embedder.name, embedder.dim)
    vectors = embedder.encode([c.text for c in chunks])

    store = FaissStore(dim=embedder.dim)
    store.add(vectors, [c.to_dict() for c in chunks])
    out = store.save()

    log.info("Wrote index of %d vectors to %s (%.1fs)",
             store.size, out, time.perf_counter() - t0)
    log.info("Next: uvicorn backend.main:app --reload")


if __name__ == "__main__":
    main()
