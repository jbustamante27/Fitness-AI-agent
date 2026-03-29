from __future__ import annotations
from typing import Any, Dict, List
from typing import Any, Dict, List
from app.io.models import Run

from app.metrics.weekly_metrics import (
    filter_lookback,
    weekly_buckets,
    count_rest_days_last_14,
    count_back_to_back_runs_last_14,
    daily_distance_series_last_7
)

from app.metrics.intensity import intensity_split_by_pace
from app.metrics.run_metrics import compute_monotony_and_strain
from app.metrics.trend_detection import trend_label
from app.metrics.acwr import (
    compute_last7_vs_28_acwr, 
    compute_longest_run_pct_last7,
    compute_weekly_acwr,
)

# Produce the metrics dict consumed by risk_flags + LLM
def compute_metrics(runs_all: List[Run], lookback_days: int = 28) -> Dict[str, Any]:
    runs = filter_lookback(runs_all, lookback_days)

    total_distance_m = sum(r.distance_m for r in runs)
    total_duration_s = sum(r.duration_s for r in runs)
    run_count = len(runs)

    weekly = weekly_buckets(runs)
    weekly_distance_km = [round(dist_m / 1000.0, 2) for _, dist_m, _, _ in weekly]
    weekly_duration_min = [round(duration_s / 60.0, 1) for _, _, duration_s, _ in weekly]
    weekly_frequency = [cnt for _, _, _, cnt in weekly]

    acwr, duration_acwr, dist_7_m, duration_7_s = compute_last7_vs_28_acwr(runs)
    longest_run_pct = compute_longest_run_pct_last7(runs)

    weekly_acwr_result = compute_weekly_acwr(weekly_distance_km)

    rest_days_last_14 = count_rest_days_last_14(runs)
    back_to_back_runs_last_14 = count_back_to_back_runs_last_14(runs)

    intensity = intensity_split_by_pace(runs)

    daily_distance_last_7 = daily_distance_series_last_7(runs)
    monotony, strain = compute_monotony_and_strain(daily_distance_last_7)

    volume_trend = trend_label(weekly_distance_km)
    duration_trend = trend_label(weekly_duration_min)

    return {
        "lookback_days": lookback_days,
        "run_count": run_count,
        "total_distance_km": round(total_distance_m / 1000.0, 2),
        "total_duration_min": round(total_duration_s / 60.0, 1),
        "lookback_days": lookback_days,
        "run_count": run_count,
        "total_distance_km": round(total_distance_m / 1000.0, 2),
        "total_duration_min": round(total_duration_s / 60.0, 1),

        "weekly_distance": weekly_distance_km,
        "weekly_duration_min": weekly_duration_min,
        "weekly_frequency": weekly_frequency,

        "distance_last_7_km": round(dist_7_m / 1000.0, 2),
        "duration_last_7_min": round(duration_7_s / 60.0, 1),

        # legacy rolling proxy
        "acwr": acwr,
        "duration_acwr": duration_acwr,

        #new weekly ACWR
        "weekly_acute_load": weekly_acwr_result["acute_load"],
        "weekly_chronic_load": weekly_acwr_result["chronic_load"],
        "weekly_acwr": weekly_acwr_result["acwr"],
        "weekly_acwr_history_weeks_used": weekly_acwr_result["history_weeks_used"],
        "weekly_acwr_is_reliable": weekly_acwr_result["is_reliable"],

        "longest_run_pct": longest_run_pct,

        "rest_days_last_14": rest_days_last_14,
        "back_to_back_runs_last_14": back_to_back_runs_last_14,

        "monotony": monotony,
        "strain": strain,

        "volume_trend": volume_trend,
        "duration_trend": duration_trend,
        "monotony": monotony,
        "strain": strain,

        "volume_trend": volume_trend,
        "duration_trend": duration_trend,

        **intensity,
    }