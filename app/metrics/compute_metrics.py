from __future__ import annotations
from typing import Any, Dict, List
from app.io.models import Run

from app.metrics.weekly_metrics import (
    _filter_lookback,
    _weekly_buckets,
    _count_rest_days_last_14,
    _count_back_to_back_runs_last_14,
    _daily_distance_series_last_7
)

from app.metrics.intensity import _intensity_split_by_pace
from app.metrics.run_metrics import _compute_monotony_and_strain
from app.metrics.trend_detection import _trend_label
from app.metrics.acwr import compute_last7_vs_28_acwr, compute_longest_run_pct_last7

# Produce the metrics dict consumed by risk_flags + LLM
def compute_metrics(runs_all: List[Run], lookback_days: int = 28) -> Dict[str, Any]:
    runs = _filter_lookback(runs_all, lookback_days)

    total_distance_m = sum(r.distance_m for r in runs)
    total_duration_s = sum(r.duration_s for r in runs)
    run_count = len(runs)

    weekly = _weekly_buckets(runs)
    weekly_distance_km = [round(dist_m / 1000.0, 2) for _, dist_m, _, _ in weekly]
    weekly_duration_min = [round(duration_s / 60.0, 1) for _, _, duration_s, _ in weekly]
    weekly_frequency = [cnt for _, _, _, cnt in weekly]

    acwr, duration_acwr, dist_7_m, duration_7_s = compute_last7_vs_28_acwr(runs)
    longest_run_pct = compute_longest_run_pct_last7(runs)

    rest_days_last_14 = _count_rest_days_last_14(runs)
    back_to_back_runs_last_14 = _count_back_to_back_runs_last_14(runs)

    intensity = _intensity_split_by_pace(runs)

    daily_distance_last_7 = _daily_distance_series_last_7(runs)
    monotony, strain = _compute_monotony_and_strain(daily_distance_last_7)

    volume_trend = _trend_label(weekly_distance_km)
    duration_trend = _trend_label(weekly_duration_min)

    return {
        "lookback_days": lookback_days,
        "run_count": run_count,
        "total_distance_km": round(total_distance_m / 1000.0, 2),
        "total_duration_min": round(total_duration_s / 60.0, 1),

        "weekly_distance": weekly_distance_km,
        "weekly_duration_min": weekly_duration_min,
        "weekly_frequency": weekly_frequency,

        "distance_last_7_km": round(dist_7_m / 1000.0, 2),
        "duration_last_7_min": round(duration_7_s / 60.0, 1),

        "acwr": acwr,
        "duration_acwr": duration_acwr,
        "longest_run_pct": longest_run_pct,

        "rest_days_last_14": rest_days_last_14,
        "back_to_back_runs_last_14": back_to_back_runs_last_14,

        "monotony": monotony,
        "strain": strain,

        "volume_trend": volume_trend,
        "duration_trend": duration_trend,

        **intensity,
    }