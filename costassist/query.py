"""Stage 1 - turn a free-text question into a structured query plan."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

SERVICE_ALIASES = {
    "AmazonEC2": ["ec2", "instance", "instances", "compute", "nat", "networking", "ebs", "snapshot"],
    "AmazonS3": ["s3", "bucket", "storage", "object"],
    "AmazonRDS": ["rds", "database", "postgres", "mysql", "aurora"],
    "AWSLambda": ["lambda", "function", "serverless"],
    "AmazonCloudWatch": ["cloudwatch", "logs", "logging", "metrics"],
    "AmazonDynamoDB": ["dynamodb", "dynamo", "table"],
    "AWSDataTransfer": ["data transfer", "transfer", "egress", "bandwidth", "replication"],
}


@dataclass
class QueryPlan:
    question: str
    team: str | None
    service_hint: str | None
    window_start: date
    window_end: date
    baseline_days: int = 21

    @property
    def window_days(self) -> int:
        return (self.window_end - self.window_start).days + 1


def _window(question: str, today: date) -> tuple[date, date]:
    q = question.lower()
    m = re.search(r"(?:last|past)\s+(\d+)\s+days?", q)
    if m:
        n = int(m.group(1))
    elif "last week" in q or "past week" in q or "this week" in q:
        n = 7
    elif "last month" in q or "past month" in q:
        n = 30
    elif "yesterday" in q:
        return today - timedelta(days=1), today - timedelta(days=1)
    else:
        n = 7
    return today - timedelta(days=n - 1), today


def plan(question: str, today: date, known_teams: list[str]) -> QueryPlan:
    q = question.lower()
    team = next((t for t in sorted(known_teams, key=len, reverse=True) if t.lower() in q), None)
    service = None
    for svc, words in SERVICE_ALIASES.items():
        if any(re.search(rf"\b{re.escape(w)}\b", q) for w in words):
            service = svc
            break
    start, end = _window(question, today)
    return QueryPlan(question=question, team=team, service_hint=service, window_start=start, window_end=end)
