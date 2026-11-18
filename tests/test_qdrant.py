"""Runs against a real Qdrant when QDRANT_URL is set (CI starts one as a service container)."""
import os
import uuid

import pytest

qdrant_client = pytest.importorskip("qdrant_client")
pytestmark = pytest.mark.skipif(not os.environ.get("QDRANT_URL"), reason="QDRANT_URL not set")

from costassist.embeddings import HashingEmbedder  # noqa: E402
from costassist.vectorstore import Filter, InMemoryVectorStore, QdrantVectorStore  # noqa: E402


def test_qdrant_matches_in_memory_filter_semantics(chunks):
    emb = HashingEmbedder()
    vecs = emb.embed([c.text for c in chunks])
    mem = InMemoryVectorStore()
    mem.upsert(chunks, vecs)
    qd = QdrantVectorStore(collection=f"test_{uuid.uuid4().hex[:8]}", dim=emb.dim)
    qd.upsert(chunks, vecs)
    q = emb.embed(["escalation contacts and savings plan commitments for lambda"])[0]
    for flt in (Filter("engineer"), Filter("finance"), Filter("admin"), Filter("engineer", "AWSLambda")):
        a = {h.chunk.id for h in mem.search(q, flt, k=len(chunks))}
        b = {h.chunk.id for h in qd.search(q, flt, k=len(chunks))}
        assert a == b, flt
    qd.client.delete_collection(qd.collection)
