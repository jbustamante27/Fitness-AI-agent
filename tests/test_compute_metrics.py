from datetime import datetime

from app.domain.schemas import Run
from app.metrics.compute_metrics import compute_metrics


def make_run(dt: datetime, distance_m: float, duration_s: float) -> Run:
    return Run(
        start_time=dt,
        distance_m=distance_m,
        duration_s=duration_s,
        avg_hr=None,
    )


def test_compute_metrics_returns_expected_core_fields():
    runs = [
        make_run(datetime(2026, 3, 1, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 5, 7, 0), 6000, 1800),
        make_run(datetime(2026, 3, 10, 7, 0), 8000, 2400),
        make_run(datetime(2026, 3, 15, 7, 0), 10000, 3000),
    ]

    metrics = compute_metrics(runs)

    assert hasattr(metrics, "lookback_days")
    assert hasattr(metrics, "run_count")
    assert hasattr(metrics, "total_distance_km")
    assert hasattr(metrics, "total_duration_min")
    assert hasattr(metrics, "weekly_distance")
    assert hasattr(metrics, "weekly_duration_min")
    assert hasattr(metrics, "weekly_frequency")
    assert hasattr(metrics, "distance_last_7_km")
    assert hasattr(metrics, "duration_last_7_min")
    assert hasattr(metrics, "distance_last_14_km")
    assert hasattr(metrics, "duration_last_14_min")
    assert hasattr(metrics, "acwr_distance")
    assert hasattr(metrics, "acwr_duration")
    assert hasattr(metrics, "longest_run_km_last_7")
    assert hasattr(metrics, "longest_run_pct")
    assert hasattr(metrics, "rest_days_last_14")
    assert hasattr(metrics, "back_to_back_runs_last_14")
    assert hasattr(metrics, "monotony_last_7")
    assert hasattr(metrics, "strain_last_7")
    assert hasattr(metrics, "easy_pct")
    assert hasattr(metrics, "moderate_pct")
    assert hasattr(metrics, "hard_pct")


def test_compute_metrics_computes_basic_totals_correctly():
    runs = [
        make_run(datetime(2026, 3, 10, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 12, 7, 0), 7000, 2100),
        make_run(datetime(2026, 3, 15, 7, 0), 10000, 3000),
    ]

    metrics = compute_metrics(runs)

    assert metrics.run_count == 3
    assert metrics.total_distance_km == 22.0
    assert metrics.total_duration_min == 110.0


def test_compute_metrics_returns_weekly_lists():
    runs = [
        make_run(datetime(2026, 3, 2, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 4, 7, 0), 7000, 2100),
        make_run(datetime(2026, 3, 10, 7, 0), 10000, 3000),
    ]

    metrics = compute_metrics(runs)

    assert metrics.weekly_distance == [12.0, 10.0]
    assert metrics.weekly_duration_min == [60.0, 50.0]
    assert metrics.weekly_frequency == [2, 1]


def test_compute_metrics_handles_empty_runs():
    metrics = compute_metrics([])

    assert metrics.run_count == 0
    assert metrics.total_distance_km == 0.0
    assert metrics.total_duration_min == 0.0
    assert metrics.weekly_distance == []
    assert metrics.weekly_duration_min == []
    assert metrics.weekly_frequency == []
    assert metrics.acwr_distance is None
    assert metrics.acwr_duration is None
    assert metrics.longest_run_pct == 0.0


def test_compute_metrics_computes_last_7_day_values():
    runs = [
        make_run(datetime(2026, 3, 1, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 5, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 10, 7, 0), 10000, 3000),
        make_run(datetime(2026, 3, 15, 7, 0), 10000, 3000),
    ]

    metrics = compute_metrics(runs)

    assert metrics.distance_last_7_km == 20.0
    assert metrics.duration_last_7_min == 100.0
    assert round(metrics.acwr_distance, 2) == 2.67
    assert round(metrics.acwr_duration, 2) == 2.67
    assert metrics.longest_run_pct == 0.5


def test_compute_metrics_includes_acwr_fields():
    runs = [
        make_run(datetime(2026, 2, 17, 7, 0), 8000, 2400),
        make_run(datetime(2026, 2, 24, 7, 0), 10000, 3000),
        make_run(datetime(2026, 3, 3, 7, 0), 12000, 3600),
        make_run(datetime(2026, 3, 10, 7, 0), 14000, 4200),
        make_run(datetime(2026, 3, 17, 7, 0), 16000, 4800),
    ]

    metrics = compute_metrics(runs)

    assert metrics.acwr_distance is not None
    assert metrics.acwr_duration is not None