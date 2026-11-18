"""CLI: investigate a question against a CUR extract (CSV/Parquet) or a built-in scenario."""
from __future__ import annotations

import argparse
import json
import sys

import pandas as pd

from .pipeline import AccessDenied, CostInvestigator, Requester
from .scenarios import all_scenarios, build_scenario


def load_cur(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path) if path.endswith(".parquet") else pd.read_csv(path)
    required = {"date", "account_id", "team", "region", "service", "usage_type", "resource_id", "cost"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"CUR file is missing columns: {sorted(missing)}")
    df["date"] = pd.to_datetime(df["date"])
    return df


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="costassist", description="Investigate AWS cost anomalies")
    sub = ap.add_subparsers(dest="cmd", required=True)

    inv = sub.add_parser("investigate", help="answer a cost question")
    inv.add_argument("question", nargs="?")
    src = inv.add_mutually_exclusive_group(required=True)
    src.add_argument("--cur", help="CSV or Parquet with CUR-style columns")
    src.add_argument("--scenario", help="built-in scenario id, e.g. S07 (uses its question if none is given)")
    inv.add_argument("--role", default="engineer", choices=["engineer", "finance", "admin"])
    inv.add_argument("--team", help="caller's team (required for engineers)")
    inv.add_argument("--json", action="store_true")

    exp = sub.add_parser("export-scenario", help="write a scenario's CUR data to CSV")
    exp.add_argument("scenario")
    exp.add_argument("-o", "--output", required=True)

    sub.add_parser("scenarios", help="list built-in scenarios")
    args = ap.parse_args(argv)

    if args.cmd == "scenarios":
        for sc, _ in all_scenarios():
            print(f"{sc.id}  {sc.team:<14} {sc.category:<28} {sc.question}")
        return 0

    if args.cmd == "export-scenario":
        _, df = build_scenario(int(args.scenario.lstrip("S")) - 1)
        df.to_csv(args.output, index=False)
        print(f"wrote {len(df)} rows to {args.output}", file=sys.stderr)
        return 0

    if args.scenario:
        sc, df = build_scenario(int(args.scenario.lstrip("S")) - 1)
        question = args.question or sc.question
        team = args.team or (sc.team if args.role == "engineer" else None)
    else:
        if not args.question:
            ap.error("a question is required with --cur")
        df, question, team = load_cur(args.cur), args.question, args.team

    try:
        result = CostInvestigator(df).investigate(question, Requester(args.role, team))
    except AccessDenied as exc:
        print(f"access denied: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, default=str))
        return 0
    print(f"Q: {question}\n")
    print(result.answer + "\n")
    if result.actions:
        print("Recommended actions:")
        for a in result.actions:
            print(f"  - {a}")
    print("\nSources: " + ", ".join(sorted({s['doc_id'] for s in result.sources})))
    print(f"Latency: {result.latency_ms:.0f} ms  |  LLM cost: ${result.llm_cost_usd:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
