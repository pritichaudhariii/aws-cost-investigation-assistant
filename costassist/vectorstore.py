"""Vector stores with metadata filtering.

Role isolation is enforced *inside* the store query (as a filter), not by
post-filtering results in Python, so a chunk the caller may not see is never
returned from the store at all. Both backends implement the same filter
semantics, which the tests check against each other.
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from .knowledge import Chunk


@dataclass
class Filter:
    role: str
    service: str | None = None  # match chunks for this service or service "*"


@dataclass
class Hit:
    chunk: Chunk
    score: float


class VectorStore(Protocol):
    def upsert(self, chunks: list[Chunk], vectors: np.ndarray) -> None: ...

    def search(self, vector: np.ndarray, flt: Filter, k: int = 5) -> list[Hit]: ...


def _allowed(chunk: Chunk, flt: Filter) -> bool:
    if flt.role not in chunk.allowed_roles:
        return False
    if flt.service and chunk.metadata.get("service") not in (flt.service, "*"):
        return False
    return True


class InMemoryVectorStore:
    def __init__(self):
        self.chunks: list[Chunk] = []
        self.matrix = np.zeros((0, 0), dtype=np.float32)

    def upsert(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        self.chunks.extend(chunks)
        self.matrix = vectors if self.matrix.size == 0 else np.vstack([self.matrix, vectors])

    def search(self, vector: np.ndarray, flt: Filter, k: int = 5) -> list[Hit]:
        mask = np.array([_allowed(c, flt) for c in self.chunks], dtype=bool)
        if not mask.any():
            return []
        scores = self.matrix @ vector
        scores = np.where(mask, scores, -np.inf)
        top = np.argsort(-scores)[:k]
        return [Hit(self.chunks[i], float(scores[i])) for i in top if np.isfinite(scores[i])]


class QdrantVectorStore:
    """Qdrant backend. Start one with `docker compose up qdrant`."""

    def __init__(self, url: str | None = None, collection: str = "cost_runbooks", dim: int = 1024):
        from qdrant_client import QdrantClient
        from qdrant_client.http import models as qm

        self.qm = qm
        self.client = QdrantClient(url=url or os.environ.get("QDRANT_URL", "http://localhost:6333"))
        self.collection = collection
        if not self.client.collection_exists(collection):
            self.client.create_collection(collection, vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE))
            for field in ("allowed_roles", "service"):
                self.client.create_payload_index(collection, field, qm.PayloadSchemaType.KEYWORD)
        self._chunks: dict[str, Chunk] = {}

    def upsert(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        points = []
        for c, v in zip(chunks, vectors):
            pid = str(uuid.uuid5(uuid.NAMESPACE_URL, c.id))
            self._chunks[pid] = c
            payload = {"chunk_id": c.id, "doc_id": c.doc_id, "title": c.title, "section": c.section, "text": c.text,
                       "service": c.metadata.get("service", "*"), "allowed_roles": c.allowed_roles,
                       "category": c.metadata.get("category")}
            points.append(self.qm.PointStruct(id=pid, vector=v.tolist(), payload=payload))
        self.client.upsert(self.collection, points=points, wait=True)

    def search(self, vector: np.ndarray, flt: Filter, k: int = 5) -> list[Hit]:
        qm = self.qm
        must = [qm.FieldCondition(key="allowed_roles", match=qm.MatchAny(any=[flt.role]))]
        if flt.service:
            must.append(qm.FieldCondition(key="service", match=qm.MatchAny(any=[flt.service, "*"])))
        res = self.client.query_points(self.collection, query=vector.tolist(), query_filter=qm.Filter(must=must),
                                       limit=k, with_payload=True).points
        hits = []
        for p in res:
            pl = p.payload
            chunk = self._chunks.get(str(p.id)) or Chunk(pl["chunk_id"], pl["doc_id"], pl["title"], pl["section"], pl["text"],
                                                         {"service": pl["service"], "allowed_roles": pl["allowed_roles"],
                                                          "category": pl.get("category")})
            hits.append(Hit(chunk, float(p.score)))
        return hits


def get_store(name: str | None = None, dim: int = 1024) -> VectorStore:
    name = name or os.environ.get("VECTOR_STORE", "memory")
    if name == "memory":
        return InMemoryVectorStore()
    if name == "qdrant":
        return QdrantVectorStore(dim=dim)
    raise ValueError(f"unknown vector store {name!r}")
