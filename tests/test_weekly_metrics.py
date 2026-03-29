from datetime import datetime

from app.io.models import Run
from app.metrics.weekly_metrics import (
    weekly_buckets,
    count_rest_days_last_14,
    count_back_to_back_runs_last_14,
    daily_distance_series_last_7,
)


def make_run(dt: datetime, distance_m: float, duration_s: float) -> Run:
    return Run(
        start_time = dt,
        distance_m = distance_m, 
        duration_s = duration_s,
        avg_hr = None,
    )

def test_weekly_buckets_groups_runs_by_week_start():
    runs = [
        make_run(datetime(2026, 3, 2, 7, 0), 5000, 1500),   # Monday
        make_run(datetime(2026, 3, 4, 7, 0), 7000, 2100),   # Wednesday, same week
        make_run(datetime(2026, 3, 10, 7, 0), 10000, 3300), # Next week
    ]

    weekly = weekly_buckets(runs)

    assert len(weekly) == 2

    week1_start, week1_dist, week1_dur, week1_count = weekly[0]
    week2_start, week2_dist, week2_dur, week2_count = weekly[1]

    assert week1_start == datetime(2026, 3, 2, 0, 0)
    assert week1_dist == 12000
    assert week1_dur == 3600
    assert week1_count == 2

    assert week2_start == datetime(2026, 3, 9, 0, 0)
    assert week2_dist == 10000
    assert week2_dur == 3300
    assert week2_count == 1

def test_weekly_buckets_returns_empty_for_no_runs():
    assert weekly_buckets([]) == []


def test_count_rest_days_last_14_counts_days_without_runs():
    runs = [
        make_run(datetime(2026, 3, 10, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 12, 7, 0), 6000, 1800),
        make_run(datetime(2026, 3, 15, 7, 0), 8000, 2400),  # last day in window
    ]

    # 14-day window ending on 2026-03-15 includes 3 run days, so 11 rest days
    assert count_rest_days_last_14(runs) == 11


def test_count_rest_days_last_14_returns_14_for_no_runs():
    assert count_rest_days_last_14([]) == 14


def test_count_back_to_back_runs_last_14_counts_consecutive_days():
    runs = [
        make_run(datetime(2026, 3, 10, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 11, 7, 0), 5000, 1500),  # consecutive with 10th
        make_run(datetime(2026, 3, 13, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 14, 7, 0), 5000, 1500),  # consecutive with 13th
        make_run(datetime(2026, 3, 15, 7, 0), 5000, 1500),  # consecutive with 14th
    ]

    # consecutive pairs: (10,11), (13,14), (14,15) => 3
    assert count_back_to_back_runs_last_14(runs) == 3


def test_count_back_to_back_runs_last_14_returns_0_for_no_runs():
    assert count_back_to_back_runs_last_14([]) == 0


def test_daily_distance_series_last_7_returns_oldest_to_newest():
    runs = [
        make_run(datetime(2026, 3, 9, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 11, 7, 0), 7000, 2100),
        make_run(datetime(2026, 3, 15, 7, 0), 10000, 3300),  # last day
    ]

    series = daily_distance_series_last_7(runs)

    # Window is 2026-03-09 through 2026-03-15, oldest -> newest
    assert series == [5000, 0.0, 7000, 0.0, 0.0, 0.0, 10000]


def test_daily_distance_series_last_7_sums_multiple_runs_on_same_day():
    runs = [
        make_run(datetime(2026, 3, 14, 7, 0), 4000, 1200),
        make_run(datetime(2026, 3, 14, 18, 0), 6000, 1800),
        make_run(datetime(2026, 3, 15, 7, 0), 5000, 1500),
    ]

    series = daily_distance_series_last_7(runs)

    # Window ends on 2026-03-15; 2026-03-14 total should be 10000
    assert series == [0.0, 0.0, 0.0, 0.0, 0.0, 10000, 5000]


def test_daily_distance_series_last_7_returns_all_zeros_for_no_runs():
    assert daily_distance_series_last_7([]) == [0.0] * 7