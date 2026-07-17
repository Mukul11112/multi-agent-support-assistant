"""
Embedding generation.

Primary backend is sentence-transformers/all-MiniLM-L6-v2 (384-dim), as the
brief recommends. The first call downloads ~90 MB from HuggingFace and caches
it in ~/.cache/huggingface.

If sentence-transformers is not installed or the model cannot be downloaded,
we fall back to a hashing vectoriser so the pipeline still runs offline. The
fallback is lexical, not semantic - it matches on shared words, so paraphrased
questions retrieve worse. It exists to keep the system demonstrable without
network, NOT as an equivalent. Check /health to see which backend is live, and
use the real one for your evaluation numbers and demo video.
"""
from __future__ import annotations

import logging

import numpy as np

from backend import config

log = logging.getLogger(__name__)


class BaseEmbedder:
    name = "base"
    dim = 0

    def encode(self, texts: list[str]) -> np.ndarray:
        raise NotImplementedError

    def encode_one(self, text: str) -> np.ndarray:
        return self.encode([text])[0]


class SentenceTransformerEmbedder(BaseEmbedder):
    name = "sentence-transformers"

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()
        self.name = f"sentence-transformers ({model_name})"

    def encode(self, texts: list[str]) -> np.ndarray:
        vecs = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=len(texts) > 64,
            normalize_embeddings=True,   # so inner product == cosine similarity
            convert_to_numpy=True,
        )
        return vecs.astype("float32")


class HashingEmbedder(BaseEmbedder):
    """Offline fallback: character n-gram hashing + L2 normalisation."""

    name = "hashing-fallback (lexical only - NOT for final evaluation)"

    def __init__(self, dim: int = 384):
        from sklearn.feature_extraction.text import HashingVectorizer
        self.dim = dim
        self._vec = HashingVectorizer(
            n_features=dim,
            analyzer="char_wb",
            ngram_range=(3, 5),
            norm="l2",
            alternate_sign=False,
        )

    def encode(self, texts: list[str]) -> np.ndarray:
        mat = self._vec.transform(texts).toarray().astype("float32")
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return mat / norms


_instance: BaseEmbedder | None = None


def get_embedder() -> BaseEmbedder:
    global _instance
    if _instance is not None:
        return _instance
    try:
        _instance = SentenceTransformerEmbedder(config.EMBEDDING_MODEL)
        log.info("Embedder: %s (dim=%d)", _instance.name, _instance.dim)
    except Exception as exc:  # noqa: BLE001
        log.warning(
            "sentence-transformers unavailable (%s). Using the lexical hashing "
            "fallback - retrieval quality will be noticeably worse. Run "
            "'pip install sentence-transformers' with internet access to fix.",
            exc,
        )
        _instance = HashingEmbedder()
    return _instance


def reset_embedder() -> None:
    global _instance
    _instance = None
