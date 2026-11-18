"""Evaluate the investigator on the 30 labelled scenarios.

Metrics
- root_cause_accuracy   predicted category == labelled category
- driver_accuracy       top-ranked resource == the injected anomalous resource
- retrieval_hit@1 / @3  the gold runbook is the first / within the first 3 retrieved docs
- mrr                   mean reciprocal rank of the gold runbook
- latency p50 / p95     end-to-end wall clock per question (ms)
- cost_per_query        LLM token cost in USD (0 when running the offline synthesizer)
- isolation_violations  chunks returned to a role not in their allowed_roles, or cross-team data access (must be 0)
- pii_leaks             answers or sources containing an email / phone / access key after filtering (must be 0)

Usage:  python -m evaluation.run_eval [--role engineer] [--out evaluation/results]
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import numpy as np

from costassist.knowledge import load_knowledge
from costassist.pii import contains_pii
from costassist.pipeline import AccessDenied, CostInvestigator, Requester
from costassist.scenarios import TEAMS, all_scenarios


def _rank(doc_ids: list[str], gold: str) -> int | None:
    seen: list[str] = []
    for d in doc_ids:
        if d not in seen:
            seen.append(d)
    return seen.index(gold) + 1 if gold in seen else None


def evaluate(role: str = "engineer", seed: int = 7, retrieval_mode: str = "driver") -> dict:
    chunks = load_knowledge()
    rows = []
    violations = 0
    pii_leaks = 0
    cross_team_blocked = 0
    for sc, df in all_scenarios(seed):
        inv = CostInvestigator(df, chunks=chunks, retrieval_mode=retrieval_mode)
        who = Requester(role, sc.team if role == "engineer" else None)
        r = inv.investigate(sc.question, who)

        # role isolation: every source must be visible to this role
        violations += sum(1 for s in r.sources if role not in s["allowed_roles"])
        # an engineer from another team must be refused
        if role == "engineer":
            other = next(t for t in TEAMS if t != sc.team)
            try:
                inv.investigate(sc.question, Requester("engineer", other))
                violations += 1
            except AccessDenied:
                cross_team_blocked += 1
        text = r.answer + " ".join(r.actions) + " ".join(s["snippet"] for s in r.sources)
        pii_leaks += int(contains_pii(text))

        rank = _rank([s["doc_id"] for s in r.sources], sc.gold_runbook)
        top = r.analysis.top
        rows.append({
            "id": sc.id,
            "category": sc.category,
            "predicted": r.root_cause,
            "correct": r.root_cause == sc.category,
            "driver_correct": bool(top and top.resource_id == sc.resource_id),
            "gold_rank": rank,
            "latency_ms": round(r.latency_ms, 1),
            "cost_usd": r.llm_cost_usd,
        })

    lat = [r["latency_ms"] for r in rows]
    n = len(rows)
    summary = {
        "role": role,
        "retrieval_mode": retrieval_mode,
        "scenarios": n,
        "root_cause_accuracy": round(sum(r["correct"] for r in rows) / n, 3),
        "driver_accuracy": round(sum(r["driver_correct"] for r in rows) / n, 3),
        "retrieval_hit@1": round(sum(r["gold_rank"] == 1 for r in rows) / n, 3),
        "retrieval_hit@3": round(sum(bool(r["gold_rank"]) and r["gold_rank"] <= 3 for r in rows) / n, 3),
        "mrr": round(statistics.mean(1 / r["gold_rank"] if r["gold_rank"] else 0 for r in rows), 3),
        "latency_p50_ms": round(float(np.percentile(lat, 50)), 1),
        "latency_p95_ms": round(float(np.percentile(lat, 95)), 1),
        "cost_per_query_usd": round(statistics.mean(r["cost_usd"] for r in rows), 5),
        "isolation_violations": violations,
        "cross_team_requests_blocked": cross_team_blocked,
        "pii_leaks": pii_leaks,
    }
    return {"summary": summary, "rows": rows}


def to_markdown(result: dict) -> str:
    s = result["summary"]
    lines = ["# Evaluation results", "", "| Metric | Value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in s.items()]
    lines += ["", "| Scenario | Labelled cause | Predicted | Correct | Top driver correct | Gold runbook rank | Latency (ms) |",
              "|---|---|---|---|---|---|---|"]
    for r in result["rows"]:
        lines.append(f"| {r['id']} | {r['category']} | {r['predicted']} | {'yes' if r['correct'] else 'no'} | "
                     f"{'yes' if r['driver_correct'] else 'no'} | {r['gold_rank']} | {r['latency_ms']} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", default="engineer", choices=["engineer", "finance", "admin"])
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--retrieval-mode", default="driver", choices=["driver", "question"],
                    help="'question' retrieves on the raw question only (single-stage RAG baseline)")
    ap.add_argument("--out", default="evaluation/results")
    args = ap.parse_args()
    result = evaluate(args.role, args.seed, args.retrieval_mode)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(result, indent=2))
    out.with_suffix(".md").write_text(to_markdown(result))
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
