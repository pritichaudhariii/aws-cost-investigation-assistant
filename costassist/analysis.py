"""Stage 2 - structured cost analysis over Cost & Usage data.

Compares average daily cost in the question window with a trailing baseline
and ranks drivers at three levels (service, usage type, resource). A driver's
score combines the absolute increase in $/day with a z-score against its own
baseline variability, so a large organic increase in a noisy service ranks
below a sudden step change of similar size.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timedelta

import numpy as np
import pandas as pd

from .query import QueryPlan


@dataclass
class Driver:
    service: str
    usage_type: str
    resource_id: str
    region: str
    baseline_daily: float
    window_daily: float
    delta_daily: float
    zscore: float
    first_seen: str
    new_resource: bool

    @property
    def pct_change(self) -> float:
        return float("inf") if self.baseline_daily == 0 else 100 * self.delta_daily / self.baseline_daily

    def to_dict(self) -> dict:
        d = asdict(self)
        d["pct_change"] = None if self.baseline_daily == 0 else round(self.pct_change, 1)
        return d


@dataclass
class CostAnalysis:
    total_baseline_daily: float
    total_window_daily: float
    by_service: list[dict]
    drivers: list[Driver]

    @property
    def total_delta_daily(self) -> float:
        return self.total_window_daily - self.total_baseline_daily

    @property
    def top(self) -> Driver | None:
        return self.drivers[0] if self.drivers else None


def scope(df: pd.DataFrame, plan: QueryPlan) -> pd.DataFrame:
    if plan.team:
        df = df[df["team"] == plan.team]
    return df


def analyze(df: pd.DataFrame, plan: QueryPlan, top_n: int = 5) -> CostAnalysis:
    df = scope(df, plan)
    w0, w1 = pd.Timestamp(plan.window_start), pd.Timestamp(plan.window_end)
    b1 = w0 - timedelta(days=1)
    b0 = w0 - timedelta(days=plan.baseline_days)
    base = df[(df["date"] >= b0) & (df["date"] <= b1)]
    win = df[(df["date"] >= w0) & (df["date"] <= w1)]
    n_base = max(1, (b1 - b0).days + 1)
    n_win = max(1, (w1 - w0).days + 1)

    def per_day(frame: pd.DataFrame, keys: list[str], n: int) -> pd.Series:
        return frame.groupby(keys)["cost"].sum() / n

    svc = pd.concat([per_day(base, ["service"], n_base).rename("baseline"),
                     per_day(win, ["service"], n_win).rename("window")], axis=1).fillna(0.0)
    svc["delta"] = svc["window"] - svc["baseline"]
    by_service = [
        {"service": s, "baseline_daily": round(r.baseline, 2), "window_daily": round(r.window, 2), "delta_daily": round(r.delta, 2)}
        for s, r in svc.sort_values("delta", ascending=False).iterrows()
    ]

    keys = ["service", "usage_type", "resource_id", "region"]
    daily_base = base.groupby(keys + ["date"])["cost"].sum().unstack("date").reindex(
        columns=pd.date_range(b0, b1), fill_value=0.0).fillna(0.0)
    res = pd.concat([per_day(base, keys, n_base).rename("baseline"), per_day(win, keys, n_win).rename("window")],
                    axis=1).fillna(0.0)
    res["delta"] = res["window"] - res["baseline"]
    std = daily_base.std(axis=1).reindex(res.index).fillna(0.0)
    res["z"] = res["delta"] / np.maximum(std, 0.05 * np.maximum(res["baseline"], 1.0))
    # rank: dollars first, damped by how unusual the change is
    res["score"] = res["delta"] * np.log1p(np.clip(res["z"], 0, None))
    first_seen = df.groupby(keys)["date"].min()

    drivers = []
    for idx, r in res[res["delta"] > 0].sort_values("score", ascending=False).head(top_n).iterrows():
        fs = first_seen.get(idx)
        drivers.append(Driver(
            service=idx[0], usage_type=idx[1], resource_id=idx[2], region=idx[3],
            baseline_daily=round(float(r.baseline), 2), window_daily=round(float(r.window), 2),
            delta_daily=round(float(r.delta), 2), zscore=round(float(r.z), 1),
            first_seen=str(fs.date()) if fs is not None else "", new_resource=bool(fs is not None and fs >= b0 and r.baseline == 0),
        ))
    return CostAnalysis(
        total_baseline_daily=round(float(base["cost"].sum() / n_base), 2),
        total_window_daily=round(float(win["cost"].sum() / n_win), 2),
        by_service=by_service,
        drivers=drivers,
    )
