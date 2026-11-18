"""Synthetic AWS Cost & Usage data with labelled anomalies.

Real CUR exports are private, so the evaluation set is generated: 60 days of
daily line items for several teams/accounts, plus one injected anomaly per
scenario (10 anomaly categories x 3 variants = 30 scenarios). Each scenario
also adds *decoy* growth in an unrelated service so the analysis has to rank
drivers rather than just pick "the thing that went up".

Columns follow a trimmed-down CUR schema:
date, account_id, team, region, service, usage_type, resource_id, usage_amount, cost
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

START = date(2026, 8, 1)
DAYS = 60
END = START + timedelta(days=DAYS - 1)

TEAMS = {
    "payments": "210987654321",
    "search": "320198765432",
    "data-platform": "430219876543",
    "mobile": "540321987654",
}
REGIONS = ["us-east-1", "us-west-2", "eu-west-1"]
REGION_PREFIX = {"us-east-1": "USE1", "us-west-2": "USW2", "eu-west-1": "EU"}

# steady-state spend per team: (service, usage_type template, resource template, daily cost)
BASELINE = [
    ("AmazonEC2", "{p}-BoxUsage:m6i.xlarge", "i-{team}-app{n}", 46.0),
    ("AmazonEC2", "{p}-EBS:VolumeUsage.gp3", "vol-{team}-{n}", 9.0),
    ("AmazonS3", "{p}-TimedStorage-ByteHrs", "{team}-assets", 12.0),
    ("AmazonS3", "{p}-Requests-Tier1", "{team}-assets", 3.0),
    ("AmazonRDS", "{p}-InstanceUsage:db.r6g.large", "db-{team}-main", 38.0),
    ("AWSLambda", "{p}-Lambda-GB-Second", "fn-{team}-worker", 4.0),
    ("AmazonCloudWatch", "{p}-DataProcessing-Bytes", "/aws/{team}/app", 5.0),
    ("AmazonDynamoDB", "{p}-WriteRequestUnits", "tbl-{team}-events", 6.0),
    ("AmazonEC2", "{p}-NatGateway-Bytes", "nat-{team}-a", 7.0),
    ("AWSDataTransfer", "{p}-DataTransfer-Out-Bytes", "{team}-edge", 8.0),
]


@dataclass(frozen=True)
class AnomalyType:
    category: str
    service: str
    usage_type: str  # template with {p}
    resource: str  # template
    daily_cost: float  # extra cost per day once active
    description: str
    question: str  # template


ANOMALIES: list[AnomalyType] = [
    AnomalyType("nat_gateway_data_processing", "AmazonEC2", "{p}-NatGateway-Bytes", "nat-{team}-a", 260.0,
                "Container image pulls and S3 traffic routed through the NAT gateway instead of VPC endpoints",
                "Why did {team}'s networking cost spike {window}?"),
    AnomalyType("idle_ec2_instances", "AmazonEC2", "{p}-BoxUsage:m6i.4xlarge", "i-{team}-loadtest{n}", 180.0,
                "Load-test instances left running after the test finished",
                "What is driving the increase in {team}'s EC2 spend {window}?"),
    AnomalyType("ebs_snapshot_growth", "AmazonEC2", "{p}-EBS:SnapshotUsage", "snap-{team}-nightly", 95.0,
                "Nightly snapshots without a retention policy accumulating",
                "{team} storage costs keep creeping up {window}, what changed?"),
    AnomalyType("s3_request_spike", "AmazonS3", "{p}-Requests-Tier1", "{team}-assets", 210.0,
                "A client retry loop issuing millions of PUT/LIST requests",
                "Why is the S3 bill for {team} so high {window}?"),
    AnomalyType("s3_storage_no_lifecycle", "AmazonS3", "{p}-TimedStorage-ByteHrs", "{team}-raw-logs", 120.0,
                "Raw log bucket growing without lifecycle rules to Glacier or expiry",
                "Investigate the jump in {team}'s S3 storage spend {window}."),
    AnomalyType("cloudwatch_logs_ingestion", "AmazonCloudWatch", "{p}-DataProcessing-Bytes", "/aws/{team}/app", 150.0,
                "Debug-level logging enabled in production",
                "Why did {team}'s CloudWatch charges increase {window}?"),
    AnomalyType("lambda_recursive_loop", "AWSLambda", "{p}-Lambda-GB-Second", "fn-{team}-thumbnailer", 230.0,
                "A Lambda writing back to the bucket that triggers it, causing a recursive loop",
                "{team} Lambda costs exploded {window}, can you find out why?"),
    AnomalyType("rds_overprovisioned", "AmazonRDS", "{p}-InstanceUsage:db.r6g.4xlarge", "db-{team}-reporting", 140.0,
                "A new reporting database sized far above its utilisation",
                "Explain the RDS cost increase for {team} {window}."),
    AnomalyType("dynamodb_on_demand_spike", "AmazonDynamoDB", "{p}-WriteRequestUnits", "tbl-{team}-events", 170.0,
                "A backfill job writing to an on-demand table at full speed",
                "What happened to {team}'s DynamoDB bill {window}?"),
    AnomalyType("cross_region_transfer", "AWSDataTransfer", "{p}-USW2-AWS-Out-Bytes", "{team}-replication", 160.0,
                "Cross-region replication of a high-churn bucket",
                "Why are {team}'s data transfer charges up {window}?"),
]

DECOYS = [
    ("AmazonEC2", "{p}-BoxUsage:m6i.xlarge", "i-{team}-app9", 45.0),  # organic scale-out
    ("AmazonRDS", "{p}-InstanceUsage:db.r6g.large", "db-{team}-replica", 38.0),
]

WINDOWS = [("last week", 7), ("over the last 7 days", 7), ("in the last 10 days", 10)]


@dataclass
class Scenario:
    id: str
    category: str
    team: str
    account_id: str
    region: str
    question: str
    anomaly_start: date
    window_days: int
    service: str
    usage_type: str
    resource_id: str
    description: str

    @property
    def gold_runbook(self) -> str:
        return self.category


def _rows_for_team(rng, team, account, region, days):
    p = REGION_PREFIX[region]
    rows = []
    for service, ut, res, cost in BASELINE:
        for n in (1, 2) if "BoxUsage" in ut else (1,):
            for d in days:
                weekly = 1.0 + 0.06 * np.sin(2 * np.pi * d.weekday() / 7)
                c = cost * weekly * rng.normal(1.0, 0.04)
                rows.append((d, account, team, region, service, ut.format(p=p), res.format(team=team, n=n), c * 10, round(c, 4)))
    return rows


def build_scenario(idx: int, seed: int = 7) -> tuple[Scenario, pd.DataFrame]:
    """Scenario `idx` in [0, 30): anomaly type idx % 10, variant idx // 10."""
    rng = np.random.default_rng(seed + idx)
    atype = ANOMALIES[idx % len(ANOMALIES)]
    variant = idx // len(ANOMALIES)
    team_names = list(TEAMS)
    team = team_names[(idx + variant) % len(team_names)]
    region = REGIONS[variant % len(REGIONS)]
    window_label, window_days = WINDOWS[variant]
    days = [START + timedelta(days=i) for i in range(DAYS)]
    start = END - timedelta(days=window_days - 1 - int(rng.integers(0, 3)))

    rows = []
    for t, acct in TEAMS.items():
        rows += _rows_for_team(rng, t, acct, REGIONS[team_names.index(t) % len(REGIONS)] if t != team else region, days)

    p = REGION_PREFIX[region]
    ut = atype.usage_type.format(p=p)
    res = atype.resource.format(team=team, n=1)
    magnitude = atype.daily_cost * (0.8 + 0.4 * variant)
    for d in days:
        if d >= start:
            ramp = min(1.0, (d - start).days / 2 + 0.4)
            c = magnitude * ramp * rng.normal(1.0, 0.05)
            rows.append((d, TEAMS[team], team, region, atype.service, ut, res, c * 10, round(c, 4)))

    # decoy: smaller organic growth in a different service, same window
    d_service, d_ut, d_res, d_cost = DECOYS[idx % len(DECOYS)]
    if d_service != atype.service:
        for d in days:
            if d >= start - timedelta(days=3):
                c = d_cost * 0.6 * rng.normal(1.0, 0.05)
                rows.append((d, TEAMS[team], team, region, d_service, d_ut.format(p=p), d_res.format(team=team), c * 10, round(c, 4)))

    df = pd.DataFrame(rows, columns=["date", "account_id", "team", "region", "service", "usage_type", "resource_id",
                                     "usage_amount", "cost"])
    df["date"] = pd.to_datetime(df["date"])
    scenario = Scenario(
        id=f"S{idx + 1:02d}",
        category=atype.category,
        team=team,
        account_id=TEAMS[team],
        region=region,
        question=atype.question.format(team=team, window=window_label),
        anomaly_start=start,
        window_days=window_days,
        service=atype.service,
        usage_type=ut,
        resource_id=res,
        description=atype.description,
    )
    return scenario, df


def all_scenarios(seed: int = 7) -> list[tuple[Scenario, pd.DataFrame]]:
    return [build_scenario(i, seed) for i in range(len(ANOMALIES) * 3)]
