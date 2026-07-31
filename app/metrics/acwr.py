from __future__ import annotations
from datetime import timedelta
from typing import List, Optional, Dict
from app.domain.schemas import Run

CHRONIC_WEEKS = 4

def compute_longest_run_pct_last7(runs: List[Run]) -> Optional[float]:
    if not runs:
        return None

    last_day = max(r.start_time for r in runs)
    cutoff_7 = last_day - timedelta(days=7)
    last7_runs = [r for r in runs if r.start_time >= cutoff_7]

    dist_7_m = sum(r.distance_m for r in last7_runs)
    if dist_7_m <= 0:
        return None

    longest_m = max((r.distance_m for r in last7_runs), default=0.0)
    return round(longest_m / dist_7_m, 2)


def compute_weekly_acwr(loads: List[float]) -> Dict[str, Optional[float]]:
    """
    Compute week-based ACWR using:
      - Acute load = current week load
      - Chronic load = average of up to 4 prior weeks
      
    loads must be in chronological order, oldest to newest
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
    
    acute_load = loads[-1]
    prior_weeks = loads[-(CHRONIC_WEEKS + 1):-1]
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
        "is_reliable": len(prior_weeks) == CHRONIC_WEEKS,
    }