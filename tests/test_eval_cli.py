import json

from costassist.cli import main
from evaluation.run_eval import evaluate


def test_evaluation_guardrails():
    s = evaluate("engineer")["summary"]
    assert s["scenarios"] == 30
    assert s["isolation_violations"] == 0
    assert s["pii_leaks"] == 0
    assert s["cross_team_requests_blocked"] == 30
    assert s["driver_accuracy"] >= 0.9
    assert s["root_cause_accuracy"] >= 0.9


def test_multi_stage_beats_single_stage_baseline():
    multi = evaluate("engineer")["summary"]
    single = evaluate("engineer", retrieval_mode="question")["summary"]
    assert multi["mrr"] > single["mrr"]


def test_cli_investigate_and_export(tmp_path, capsys):
    assert main(["investigate", "--scenario", "S04", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["root_cause"] == "s3_request_spike"
    csv = tmp_path / "s04.csv"
    assert main(["export-scenario", "S04", "-o", str(csv)]) == 0
    assert main(["investigate", "Why is the S3 bill so high last week?", "--cur", str(csv), "--role", "engineer",
                 "--team", "mobile"]) == 0


def test_cli_access_denied():
    assert main(["investigate", "Why did payments costs rise last week?", "--scenario", "S04", "--team", "mobile"]) == 2
