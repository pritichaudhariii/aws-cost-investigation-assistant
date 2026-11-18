"""Embedding backends.

``HashingEmbedder`` needs no model download and is the default so the whole
pipeline (and CI) runs offline. ``SentenceTransformerEmbedder`` and
``OpenAICompatibleEmbedder`` are drop-in replacements for better recall.
"""
from __future__ import annotations

import os
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> np.ndarray: ...


class HashingEmbedder:
    """Word + bigram feature hashing with L2 normalisation."""

    def __init__(self, dim: int = 1024):
        from sklearn.feature_extraction.text import HashingVectorizer

        self.dim = dim
        self._vec = HashingVectorizer(
            n_features=dim, ngram_range=(1, 2), alternate_sign=False, norm="l2",
            token_pattern=r"(?u)\b[\w:\-\.]{2,}\b", lowercase=True,
        )

    def embed(self, texts: list[str]) -> np.ndarray:
        return self._vec.transform(texts).toarray().astype(np.float32)


class SentenceTransformerEmbedder:
    def __init__(self, model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model)
        self.dim = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self._model.encode(texts, normalize_embeddings=True), dtype=np.float32)


class OpenAICompatibleEmbedder:
    """Any server exposing POST /v1/embeddings (OpenAI, Azure OpenAI, Ollama, vLLM, ...)."""

    def __init__(self, model: str | None = None, base_url: str | None = None, api_key: str | None = None, dim: int = 1536):
        self.model = model or os.environ.get("EMBED_MODEL", "text-embedding-3-small")
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.dim = dim

    def embed(self, texts: list[str]) -> np.ndarray:
        import requests

        r = requests.post(f"{self.base_url}/embeddings", json={"model": self.model, "input": texts},
                          headers={"Authorization": f"Bearer {self.api_key}"}, timeout=60)
        r.raise_for_status()
        vecs = np.asarray([d["embedding"] for d in r.json()["data"]], dtype=np.float32)
        return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)


def get_embedder(name: str | None = None) -> Embedder:
    name = name or os.environ.get("EMBEDDER", "hashing")
    if name == "hashing":
        return HashingEmbedder()
    if name == "sentence-transformers":
        return SentenceTransformerEmbedder()
    if name == "openai":
        return OpenAICompatibleEmbedder()
    raise ValueError(f"unknown embedder {name!r}")
