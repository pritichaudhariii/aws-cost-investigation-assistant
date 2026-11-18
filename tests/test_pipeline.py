import json

import pytest

from costassist.llm import LLMResult
from costassist.pii import contains_pii
from costassist.pipeline import AccessDenied, CostInvestigator, Requester


class FakeLLM:
    def __init__(self, text):
        self.text = text
        self.calls = 0

    def complete(self, system, user, max_tokens=700):
        self.calls += 1
        assert "RUNBOOK EXCERPTS" in user and not contains_pii(user)
        return LLMResult(self.text, input_tokens=1200, output_tokens=200)


@pytest.fixture
def lambda_inv(scenario_lambda, chunks):
    sc, df = scenario_lambda
    return sc, CostInvestigator(df, chunks=chunks, llm=None)


def test_end_to_end_offline(lambda_inv):
    sc, inv = lambda_inv
    r = inv.investigate(sc.question, Requester("engineer", sc.team))
    assert r.root_cause == "lambda_recursive_loop"
    assert sc.resource_id in r.answer
    assert r.actions and all("[lambda_recursive_loop]" in a for a in r.actions)
    assert set(r.timings_ms) == {"plan", "analysis", "retrieval", "synthesis"}
    assert json.dumps(r.to_dict(), default=str)


def test_engineer_cannot_query_other_team(lambda_inv):
    sc, inv = lambda_inv
    with pytest.raises(AccessDenied):
        inv.investigate(sc.question, Requester("engineer", "payments"))


def test_requester_validation():
    with pytest.raises(ValueError):
        Requester("engineer")
    with pytest.raises(ValueError):
        Requester("superuser", "x")


def test_admin_sees_contacts_but_pii_is_redacted(scenario_lambda, chunks):
    sc, df = scenario_lambda
    inv = CostInvestigator(df, chunks=chunks, llm=None, retrieval_mode="question", k=13)
    r = inv.investigate("who are the escalation contacts for a cost incident", Requester("admin"))
    contacts = [s for s in r.sources if s["doc_id"] == "escalation_contacts_admin"]
    assert contacts
    assert "[REDACTED_EMAIL]" in contacts[0]["snippet"]
    assert not any(contains_pii(s["snippet"]) for s in r.sources)
    assert r.redactions.get("EMAIL", 0) >= 2
    # the stored chunk is untouched (redaction works on copies)
    assert any("@example.com" in c.text for c in inv.store.chunks)


def test_llm_synthesis_and_cost(scenario_lambda, chunks):
    sc, df = scenario_lambda
    llm = FakeLLM(json.dumps({"summary": "Recursive Lambda; contact ops@example.com", "root_cause": "lambda_recursive_loop",
                              "actions": ["Fix the trigger prefix [lambda_recursive_loop]"]}))
    r = CostInvestigator(df, chunks=chunks, llm=llm).investigate(sc.question, Requester("finance"))
    assert llm.calls == 1
    assert r.root_cause == "lambda_recursive_loop"
    assert "[REDACTED_EMAIL]" in r.answer
    assert r.llm_cost_usd == pytest.approx((1200 * 0.15 + 200 * 0.60) / 1e6)


def test_llm_invalid_json_and_unknown_category_fall_back(scenario_lambda, chunks):
    sc, df = scenario_lambda
    r = CostInvestigator(df, chunks=chunks, llm=FakeLLM("not json")).investigate(sc.question, Requester("finance"))
    assert r.root_cause == "lambda_recursive_loop" and r.answer
    r2 = CostInvestigator(df, chunks=chunks, llm=FakeLLM(json.dumps({"summary": "x", "root_cause": "aliens", "actions": []})))
    assert r2.investigate(sc.question, Requester("finance")).root_cause == "lambda_recursive_loop"
