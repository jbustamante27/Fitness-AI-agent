from __future__ import annotations

from datetime import timedelta
from typing import List

from app.domain.schemas import ComputedMetrics, Run
from app.metrics.acwr import compute_longest_run_pct_last7, compute_weekly_acwr
from app.metrics.intensity import intensity_split_by_pace
from app.metrics.run_metrics import compute_monotony_and_strain
from app.metrics.trend_detection import trend_label
from app.metrics.weekly_metrics import (
    count_back_to_back_runs_last_14,
    count_rest_days_last_14,
    daily_distance_series_last_7,
    filter_lookback,
    latest_run_time,
    weekly_buckets,
)


def _empty(lookback_days: int) -> ComputedMetrics:
    return ComputedMetrics(
        lookback_days=lookback_days,
        run_count=0,
        total_distance_km=0.0,
        total_duration_min=0.0,
    )


def compute_metrics(runs: List[Run], lookback_days: int = 35) -> ComputedMetrics:
    """
    Orchestrator. Owns no maths of its own -- it selects the window, delegates
    to the metric modules, and assembles the result.
    """
    if not runs:
        return _empty(lookback_days)

    lookback_runs = sorted(
        filter_lookback(runs, lookback_days), key=lambda r: r.start_time
    )
    if not lookback_runs:
        return _empty(lookback_days)

    anchor = latest_run_time(lookback_runs)

    # --- totals ---
    total_distance_km = sum(r.distance_km for r in lookback_runs)
    total_duration_min = sum(r.duration_min for r in lookback_runs)

    # --- weekly series (zero-filled, oldest first) ---
    buckets = weekly_buckets(lookback_runs)
    weekly_distance = [dist_m / 1000.0 for _, dist_m, _, _ in buckets]
    weekly_duration_min = [dur_s / 60.0 for _, _, dur_s, _ in buckets]
    weekly_frequency = [count for _, _, _, count in buckets]

    # --- rolling windows ---
    last_7 = [r for r in lookback_runs if r.start_time >= anchor - timedelta(days=7)]
    last_14 = [r for r in lookback_runs if r.start_time >= anchor - timedelta(days=14)]

    # --- ACWR (calendar-week based) ---
    acwr_dist = compute_weekly_acwr(weekly_distance)
    acwr_dur = compute_weekly_acwr(weekly_duration_min)

    # --- intensity, recovery, monotony ---
    split = intensity_split_by_pace(lookback_runs)
    daily_km_last_7 = [m / 1000.0 for m in daily_distance_series_last_7(lookback_runs)]
    monotony_last_7, strain_last_7 = compute_monotony_and_strain(daily_km_last_7)

    return ComputedMetrics(
        lookback_days=lookback_days,
        run_count=len(lookback_runs),
        total_distance_km=round(total_distance_km, 2),
        total_duration_min=round(total_duration_min, 2),
        weekly_distance=[round(v, 2) for v in weekly_distance],
        weekly_duration_min=[round(v, 2) for v in weekly_duration_min],
        weekly_frequency=weekly_frequency,
        distance_last_7_km=round(sum(r.distance_km for r in last_7), 2),
        duration_last_7_min=round(sum(r.duration_min for r in last_7), 2),
        distance_last_14_km=round(sum(r.distance_km for r in last_14), 2),
        duration_last_14_min=round(sum(r.duration_min for r in last_14), 2),
        acwr_distance=acwr_dist["acwr"],
        acwr_duration=acwr_dur["acwr"],
        acwr_weeks_used=int(acwr_dist["history_weeks_used"] or 0),
        acwr_is_reliable=bool(acwr_dist["is_reliable"]),
        longest_run_km_last_7=round(max((r.distance_km for r in last_7), default=0.0), 2),
        longest_run_pct=compute_longest_run_pct_last7(lookback_runs) or 0.0,
        easy_pct=split["easy_pct"],
        moderate_pct=split["moderate_pct"],
        hard_pct=split["hard_pct"],
        rest_days_last_14=count_rest_days_last_14(lookback_runs),
        back_to_back_runs_last_14=count_back_to_back_runs_last_14(lookback_runs),
        monotony_last_7=monotony_last_7,
        strain_last_7=strain_last_7,
        weekly_distance_trend=trend_label(weekly_distance),
    )