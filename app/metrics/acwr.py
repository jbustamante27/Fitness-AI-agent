from __future__ import annotations
from datetime import timedelta
from typing import List, Optional, Tuple, Dict
from app.io.models import Run


def compute_last7_vs_28_acwr(runs: List[Run]) -> Tuple[Optional[float], Optional[float], float, float]:
    """
    Current legacy project logic:
      - distance ACWR-ish = last 7 day distance / (28-day distance / 4)
      - duration ACWR-ish = last 7 day duration / (28-day duration / 4)

    Returns:
      (acwr, duration_acwr, dist_7_m, duration_7_s)
    """
    if not runs:
        return None, None, 0.0, 0.0

    last_day = runs[-1].start_time
    cutoff_7 = last_day - timedelta(days=7)
    last7_runs = [r for r in runs if r.start_time >= cutoff_7]

    dist_7_m = sum(r.distance_m for r in last7_runs)
    duration_7_s = sum(r.duration_s for r in last7_runs)

    dist_28_m = sum(r.distance_m for r in runs)
    duration_28_s = sum(r.duration_s for r in runs)

    dist_denom = (dist_28_m / 4.0) if dist_28_m > 0 else 0.0
    dur_denom = (duration_28_s / 4.0) if duration_28_s > 0 else 0.0

    acwr = round(dist_7_m / dist_denom, 2) if dist_denom > 0 else None
    duration_acwr = round(duration_7_s / dur_denom, 2) if dur_denom > 0 else None

    return acwr, duration_acwr, dist_7_m, duration_7_s


def compute_longest_run_pct_last7(runs: List[Run]) -> Optional[float]:
    if not runs:
        return None

    last_day = runs[-1].start_time
    cutoff_7 = last_day - timedelta(days=7)
    last7_runs = [r for r in runs if r.start_time >= cutoff_7]

    dist_7_m = sum(r.distance_m for r in last7_runs)
    if dist_7_m <= 0:
        return None

    longest_m = max((r.distance_m for r in last7_runs), default=0.0)
    return round(longest_m / dist_7_m, 2)


def compute_weekly_acwr(loads: List[float]) -> Dict[str, Optional[float]]:
    """
    Compute wee-based ACWR using:
      - Acute load = current week load
      - Chronic load = average of up to 4 prior weeks
      
    loads must be in chronological order, oldest to neweset
    Example:
        [18.0, 22.0, 26.0, 24.0, 30.0]
        acute = 30.0
        chronic = average(18,22,26,24) = 22.5
        acwr = 1.33    
    """
    if not loads:
        return {
            "acute_load": None,
            "chronic_load": None,
            "acwr": None,
            "history_weeks_used": 0,
            "is_reliable": False,
        }
    
    if len(loads) < 2:
        return {
            "acute_load": round(loads[-1], 2),
            "chronic_load": None,
            "acwr": None,
            "history_weeks_used": 0,
            "is_reliable": False,
        }
    
    acute_load = loads[-1]
    prior_weeks = loads[-5:-1] if len(loads) >= 5 else loads [:-1]

    if not prior_weeks:
        return {
            "acute_load": round(acute_load, 2),
            "chronic_load": None,
            "acwr": None,
            "history_weeks_used": 0,
            "is_reliable": False,
        }
    
    chronic_load = sum(prior_weeks) / len(prior_weeks)

    if chronic_load <= 0:
        return {
            "acute_load": round(acute_load, 2),
            "chronic_load": round(chronic_load, 2),
            "acwr": None,
            "history_weeks_used": len(prior_weeks),
            "is_reliable": False,
        }
    
    acwr = round(acute_load / chronic_load, 2)

    return {
        "acute_load": round(acute_load, 2),
        "chronic_load": round(chronic_load, 2),
        "acwr": acwr,
        "history_weeks_used": len(prior_weeks),
        "is_reliable": len(prior_weeks) == 4,
    }