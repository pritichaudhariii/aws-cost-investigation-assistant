from datetime import date

from costassist.analysis import analyze
from costassist.query import plan


def test_query_plan_window_and_team():
    p = plan("Why did payments' S3 bill go up in the last 10 days?", date(2026, 9, 29), ["payments", "search"])
    assert p.team == "payments"
    assert p.service_hint == "AmazonS3"
    assert p.window_days == 10 and p.window_end == date(2026, 9, 29)
    assert plan("what happened last week", date(2026, 9, 29), []).window_days == 7
    assert plan("what happened yesterday", date(2026, 9, 29), []).window_days == 1


def test_top_driver_is_the_injected_anomaly_not_the_decoy(scenario_nat):
    sc, df = scenario_nat
    p = plan(sc.question, df["date"].max().date(), list(df["team"].unique()))
    a = analyze(df, p)
    assert a.top.resource_id == sc.resource_id
    assert a.total_delta_daily > 0
    assert a.drivers[0].delta_daily >= a.drivers[-1].delta_daily or a.drivers[0].zscore > a.drivers[-1].zscore


def test_analysis_is_scoped_to_team(scenario_nat):
    sc, df = scenario_nat
    p = plan("why did mobile spend change last week", df["date"].max().date(), list(df["team"].unique()))
    a = analyze(df, p)
    assert all("mobile" in d.resource_id for d in a.drivers)
