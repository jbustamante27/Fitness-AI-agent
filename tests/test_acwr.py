from datetime import datetime

from app.metrics.acwr import (compute_longest_run_pct_last7)


def make_run(dt: datetime, distance_m: float, duration_s: float) -> Run:
    return Run(
        start_time = dt, 
        distance_m = distance_m,
        duration_s = duration_s,
        avg_hr = None,
    )

def test_compute_longest_run_pct_last7_returns_none_for_no_runs():
    assert compute_longest_run_pct_last7([]) is None


def test_compute_longest_run_pct_last7_returns_none_when_last7_distance_is_zero():
    runs = [
        make_run(datetime(2026, 3, 15, 7, 0), 0, 0),
    ]

    assert compute_longest_run_pct_last7(runs) is None


def test_compute_longest_run_pct_last7_computes_expected_share():
    runs = [
        make_run(datetime(2026, 3, 10, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 12, 7, 0), 7000, 2100),
        make_run(datetime(2026, 3, 15, 7, 0), 10000, 3000), # longest in last 7
    ]

    pct = compute_longest_run_pct_last7(runs)

    #total last-7 distance = 22000, longest = 10000 => 0.45 rounded
    assert pct == 0.45

def test_compute_weekly_acwr_returns_none_for_empty_loads():
    from app.metrics.acwr import compute_weekly_acwr

    result = compute_weekly_acwr([])

    assert result["acute_load"] is None
    assert result["chronic_load"] is None
    assert result["acwr"] is None
    assert result["history_weeks_used"] == 0
    assert result["is_reliable"] is False


def test_compute_weekly_acwr_returns_unreliable_for_one_week_only():
    from app.metrics.acwr import compute_weekly_acwr

    result = compute_weekly_acwr([20.0])

    assert result["acute_load"] == 20.0
    assert result["chronic_load"] is None
    assert result["acwr"] is None
    assert result["history_weeks_used"] == 0
    assert result["is_reliable"] is False


def test_compute_weekly_acwr_computes_expected_values_with_5_weeks():
    from app.metrics.acwr import compute_weekly_acwr

    result = compute_weekly_acwr([18.0, 22.0, 26.0, 24.0, 30.0])

    assert result["acute_load"] == 30.0
    assert result["chronic_load"] == 22.5
    assert result["acwr"] == 1.33
    assert result["history_weeks_used"] == 4
    assert result["is_reliable"] is True


def test_compute_weekly_acwr_uses_available_history_when_less_than_5_weeks():
    from app.metrics.acwr import compute_weekly_acwr

    result = compute_weekly_acwr([20.0, 25.0, 30.0])

    # acute = 30
    # chronic = average(20,25) = 22.5
    # acwr = 1.33
    assert result["acute_load"] == 30.0
    assert result["chronic_load"] == 22.5
    assert result["acwr"] == 1.33
    assert result["history_weeks_used"] == 2
    assert result["is_reliable"] is False


def test_compute_weekly_acwr_returns_none_when_chronic_load_is_zero():
    from app.metrics.acwr import compute_weekly_acwr

    result = compute_weekly_acwr([0.0, 0.0, 10.0])

    assert result["acute_load"] == 10.0
    assert result["chronic_load"] == 0.0
    assert result["acwr"] is None
    assert result["history_weeks_used"] == 2
    assert result["is_reliable"] is False