import numpy as np
import pytest

from costassist.embeddings import HashingEmbedder
from costassist.vectorstore import Filter, InMemoryVectorStore


@pytest.fixture(scope="module")
def store(chunks):
    emb = HashingEmbedder()
    s = InMemoryVectorStore()
    s.upsert(chunks, emb.embed([c.text for c in chunks]))
    return s, emb


def _search(store, text, flt, k=50):
    s, emb = store
    return s.search(emb.embed([text])[0], flt, k)


def test_embeddings_are_normalised():
    v = HashingEmbedder().embed(["nat gateway bytes", "lambda"])
    assert np.allclose(np.linalg.norm(v, axis=1), 1.0)


@pytest.mark.parametrize("role, forbidden", [
    ("engineer", {"commitments_finance", "escalation_contacts_admin"}),
    ("finance", {"escalation_contacts_admin"}),
    ("admin", set()),
])
def test_role_filter_is_applied_inside_search(store, role, forbidden):
    hits = _search(store, "escalation contacts savings plan commitments", Filter(role=role))
    assert hits
    assert not {h.chunk.doc_id for h in hits} & forbidden


def test_service_filter_keeps_generic_docs(store):
    hits = _search(store, "lambda recursive invocations", Filter(role="engineer", service="AWSLambda"))
    services = {h.chunk.metadata["service"] for h in hits}
    assert services <= {"AWSLambda", "*"}
    assert hits[0].chunk.doc_id == "lambda_recursive_loop"


def test_unknown_role_gets_nothing(store):
    assert _search(store, "anything", Filter(role="intern")) == []
