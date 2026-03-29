from datetime import datetime

from app.io.models import Run
from app.metrics.compute_metrics import compute_metrics


def make_run(dt: datetime, distance_m: float, duration_s: float) -> Run:
    return Run(
        start_time = dt, 
        distance_m = distance_m,
        duration_s = duration_s,
        avg_hr = None,
    )


def test_compute_metrics_returns_expected_core_keys():
    runs = [
        make_run(datetime(2026, 3, 1, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 5, 7, 0), 6000, 1800),
        make_run(datetime(2026, 3, 10, 7, 0), 8000, 2400),
        make_run(datetime(2026, 3, 15, 7, 0), 10000, 3000),
    ]

    metrics = compute_metrics(runs)

    expected_keys = {
        "lookback_days",
        "run_count",
        "total_distance_km",
        "total_duration_min",
        "weekly_distance",
        "weekly_duration_min",
        "weekly_frequency",
        "distance_last_7_km",
        "duration_last_7_min",
        "acwr",
        "duration_acwr",

        "weekly_acute_load",
        "weekly_chronic_load",
        "weekly_acwr",
        "weekly_acwr_history_weeks_used",
        "weekly_acwr_is_reliable",

        "longest_run_pct",
        "rest_days_last_14",
        "back_to_back_runs_last_14",
        "monotony",
        "strain",
        "volume_trend",
        "duration_trend",
        "easy_pct",
        "hard_pct",
    }

    assert expected_keys.issubset(metrics.keys())


def test_compute_metrics_computes_basic_totals_correctly():
    runs = [
        make_run(datetime(2026, 3, 10, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 12, 7, 0), 7000, 2100),
        make_run(datetime(2026, 3, 15, 7, 0), 10000, 3000),
    ]

    metrics = compute_metrics(runs)

    assert metrics["run_count"] == 3
    assert metrics["total_distance_km"] == 22.0
    assert metrics["total_duration_min"] == 110.0


def test_compute_metrics_returns_weekly_lists():
    runs = [
        make_run(datetime(2026, 3, 2, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 4, 7, 0), 7000, 2100),
        make_run(datetime(2026, 3, 10, 7, 0), 10000, 3000),
    ]

    metrics = compute_metrics(runs)

    assert metrics["weekly_distance"] == [12.0, 10.0]
    assert metrics["weekly_duration_min"] == [60.0, 50.0]
    assert metrics["weekly_frequency"] == [2, 1]


def test_compute_metrics_handles_empty_runs():
    metrics = compute_metrics([])

    assert metrics["run_count"] == 0
    assert metrics["total_distance_km"] == 0.0
    assert metrics["total_duration_min"] == 0.0
    assert metrics["weekly_distance"] == []
    assert metrics["weekly_duration_min"] == []
    assert metrics["weekly_frequency"] == []
    assert metrics["acwr"] is None
    assert metrics["duration_acwr"] is None
    assert metrics["longest_run_pct"] is None


def test_compute_metrics_computes_last_7_day_values():
    runs = [
        make_run(datetime(2026, 3, 1, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 5, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 10, 7, 0), 10000, 3000),
        make_run(datetime(2026, 3, 15, 7, 0), 10000, 3000),
    ]

    metrics = compute_metrics(runs)

    assert metrics["distance_last_7_km"] == 20.0
    assert metrics["duration_last_7_min"] == 100.0
    assert metrics["acwr"] == 2.67
    assert metrics["duration_acwr"] == 2.67
    assert metrics["longest_run_pct"] == 0.5

def test_compute_metrics_includes_weekly_acwr_fields():
    runs = [
        make_run(datetime(2026, 2, 17, 7, 0), 8000, 2400),   # week 1
        make_run(datetime(2026, 2, 24, 7, 0), 10000, 3000),  # week 2
        make_run(datetime(2026, 3, 3, 7, 0), 12000, 3600),   # week 3
        make_run(datetime(2026, 3, 10, 7, 0), 14000, 4200),  # week 4
        make_run(datetime(2026, 3, 17, 7, 0), 16000, 4800),  # week 5/current
    ]

    metrics = compute_metrics(runs)

    assert metrics["weekly_acute_load"] == 16.0
    assert metrics["weekly_chronic_load"] == 11.0
    assert metrics["weekly_acwr"] == 1.45
    assert metrics["weekly_acwr_history_weeks_used"] == 4
    assert metrics["weekly_acwr_is_reliable"] is True