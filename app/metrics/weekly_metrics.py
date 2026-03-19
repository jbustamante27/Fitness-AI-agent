from __future__ import annotations
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple
from app.io.models import Run

# Compute the start of the week (Monday) for any given datetime
def _week_start(d: datetime) -> datetime:
    return (d - timedelta(days=d.weekday())).replace(hour = 0, minute = 0, second = 0, microsecond = 0)

# Return a list of runs after a certain cutoff relative to the latest run in the list
def _filter_lookback(runs: List[Run], days: int) -> List[Run]:
    if not runs:
        return []
    cutoff = runs[-1].start_time - timedelta(days=days)
    return [r for r in runs if r.start_time >= cutoff]

# Group runs by week and return summary stats per week
def _weekly_buckets(runs: List[Run]) -> List[Tuple[datetime, float, int]]:
    '''
    Returns (week_start, total_distance_m, run_count) sorted ascending
    '''
    buckets: Dict[datetime, Dict[str, float]] = {}
    for r in runs:
        ws = _week_start(r.start_time)
        if ws not in buckets:
            buckets[ws] = {'dist_m': 0.0,
                           'duration_s': 0.0,
                           'count': 0.0
                           }
        buckets[ws]['dist_m'] += r.distance_m
        buckets[ws]['duration_s'] += r.duration_s
        buckets[ws]['count'] += 1.0

    out: List[Tuple[datetime, float, float, int]] = []
    for ws in sorted(buckets.keys()):
        out.append((ws,
                    float(buckets[ws]['dist_m']),
                    float(buckets[ws]['duration_s']),
                    int(buckets[ws]['count'])))
    return out

# Count how many days without running in last 2 weeks
def _count_rest_days_last_14(runs: List[Run]) -> int:
    if not runs:
        return 14
    last_day = runs[-1].start_time.date()
    days_with_run = {
        r.start_time.date()
        for r in runs if 0 <= (last_day - r.start_time.date()).days <= 13
    }
    return 14 - len(days_with_run)

# Count how many 2 back to back days with a run in each in last 2 weeks
def _count_back_to_back_runs_last_14(runs: List[Run]) -> int:
    if not runs:
        return 0
    last_day = runs[-1].start_time.date()
    days = sorted(
        {
            r.start_time.date()
            for r in runs if 0 <= (last_day - r.start_time.date()).days <= 13
        }
    )
    b2b = 0
    for i in range(1, len(days)):
        if (days[i] - days[i - 1]).days == 1:
            b2b += 1
    return b2b

# Return a 7 element list of daily distance totals in meters for the last 7 calendar days ending on the most recent run date (Missing days are filled with 0)
def _daily_distance_series_last_7(runs: List[Run]) -> List[float]:
    if not runs:
        return [0.0] * 7
    
    last_day = runs[-1].start_time.date()
    day_totals: Dict[date, float] = {}

    for r in runs:
        d = r.start_time.date()
        delta = (last_day - d).days 
        if 0 <= delta <= 6:
            day_totals[d] = day_totals.get(d, 0.0) + r.distance_m
        
    days = [last_day - timedelta(days = i) for i in range(6, -1, -1)]
    return [day_totals.get(d, 0.0) for d in days]