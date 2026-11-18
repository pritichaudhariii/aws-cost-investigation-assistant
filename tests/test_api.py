import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from costassist.api import app  # noqa: E402

client = TestClient(app)


def test_investigate_as_engineer():
    r = client.post("/investigate", json={"question": "Why did payments networking cost spike last week?"},
                    headers={"X-User-Role": "engineer", "X-User-Team": "payments"})
    assert r.status_code == 200
    assert r.json()["root_cause"] == "nat_gateway_data_processing"


def test_cross_team_forbidden_and_bad_role():
    r = client.post("/investigate", json={"question": "Why did payments costs rise last week?"},
                    headers={"X-User-Role": "engineer", "X-User-Team": "mobile"})
    assert r.status_code == 403
    r = client.post("/investigate", json={"question": "Why did costs rise?"}, headers={"X-User-Role": "root"})
    assert r.status_code == 400
