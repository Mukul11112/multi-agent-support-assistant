"""
FAISS-backed vector store with metadata and per-domain filtering.

Index type is IndexFlatIP over L2-normalised vectors, which makes the inner
product exactly cosine similarity. Flat = exhaustive search: at a few hundred
chunks it is instant and, unlike IVF/HNSW, it has no recall loss and needs no
training. Swap to IndexIVFFlat only past ~100k vectors.

Domain filtering is done by over-fetching then filtering, rather than by
building one index per domain. Documents belong to multiple domains, so
separate indexes would duplicate vectors and drift out of sync on re-ingest.
"""
from __future__ import annotations

import json
import logging
import pathlib

import faiss
import numpy as np

from backend import config

log = logging.getLogger(__name__)

INDEX_FILE = "index.faiss"
META_FILE = "metadata.json"


class FaissStore:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.metadata: list[dict] = []

    # --- build ---------------------------------------------------------
    def add(self, vectors: np.ndarray, metadata: list[dict]) -> None:
        if len(vectors) != len(metadata):
            raise ValueError("vectors and metadata length mismatch")
        vectors = np.ascontiguousarray(vectors.astype("float32"))
        faiss.normalize_L2(vectors)  # idempotent if already normalised
        self.index.add(vectors)
        self.metadata.extend(metadata)

    # --- search --------------------------------------------------------
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 4,
        domain: str | None = None,
        min_score: float = 0.0,
    ) -> list[dict]:
        if self.index.ntotal == 0:
            return []

        q = np.ascontiguousarray(query_vector.reshape(1, -1).astype("float32"))
        faiss.normalize_L2(q)

        # Over-fetch when filtering: the top_k globally-nearest chunks may all
        # belong to other domains, which would return nothing after filtering.
        fetch = min(top_k * 6 if domain else top_k, self.index.ntotal)
        scores, ids = self.index.search(q, fetch)

        results: list[dict] = []
        for score, idx in zip(scores[0], ids[0]):
            if idx < 0:
                continue
            meta = self.metadata[idx]
            if domain and domain not in meta.get("domains", []):
                continue
            if float(score) < min_score:
                continue
            results.append({**meta, "score": round(float(score), 4)})
            if len(results) >= top_k:
                break
        return results

    # --- persistence ---------------------------------------------------
    def save(self, directory: pathlib.Path | None = None) -> pathlib.Path:
        directory = pathlib.Path(directory or config.VECTORSTORE_DIR)
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / INDEX_FILE))
        (directory / META_FILE).write_text(
            json.dumps({"dim": self.dim, "metadata": self.metadata}, indent=1),
            encoding="utf-8",
        )
        return directory

    @classmethod
    def load(cls, directory: pathlib.Path | None = None) -> "FaissStore":
        directory = pathlib.Path(directory or config.VECTORSTORE_DIR)
        index_path = directory / INDEX_FILE
        meta_path = directory / META_FILE
        if not index_path.exists() or not meta_path.exists():
            raise FileNotFoundError(
                f"No vector index in {directory}. Run 'python -m backend.rag.ingest' first."
            )
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
        store = cls.__new__(cls)
        store.index = faiss.read_index(str(index_path))
        store.metadata = payload["metadata"]
        store.dim = payload["dim"]
        if store.index.ntotal != len(store.metadata):
            raise ValueError(
                f"Index/metadata mismatch ({store.index.ntotal} vs "
                f"{len(store.metadata)}). Re-run ingestion."
            )
        return store

    @property
    def size(self) -> int:
        return self.index.ntotal
