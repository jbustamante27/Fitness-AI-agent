from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from app.io.models import Run

def _week_start(d: datetime) -> datetime:
    # Monday = start of the week
    return (d - timedelta(days=d.weekday())).replace(hour = 0, minute = 0, second = 0, microsecond = 0)

def _filter_lookback(runs: List[Run], days: int) -> List[Run]:
    if not runs:
        return []
    cutoff = runs[-1].start_time - timedelta(days=days)
    return [r for r in runs if r.start_time >= cutoff]

def _weekly_buckets(runs: List[Run]) -> List[Tuple[datetime, float, int]]:
    '''
    Returns (week_start, total_distance_m, run_count) sorted ascending
    '''
    buckets: Dict[datetime, Dict[str, float]] = {}
    for r in runs:
        ws = _week_start(r.start_time)
        if ws not in buckets:
            buckets[ws] = {'dist_m': 0.0, 'count': 0.0}
        buckets[ws]['dist_m'] += r.distance_m
        buckets[ws]['count'] += 1.0

    out: List[Tuple[datetime, float, int]] = []
    for ws in sorted(buckets.keys()):
        out.append((ws, float(buckets[ws]['dist_m']), int(buckets[ws]['count'])))
    return out

def _count_rest_days_last_14(runs: List[Run]) -> int:
    if not runs:
        return 14
    last_day = runs[-1].start_time.date()
    days_with_run = set(
        r.start_time.date() for r in runs if (last_day - r.start_time.date()).days <= 13
    )
    return 14 - len(days_with_run)

def _count_back_to_back_runs_last_14(runs: List[Run]) -> int:
    if not runs:
        return 0
    last_day = runs[-1].start_time.date()
    days = sorted(set(r.start_time.date() for r in runs if (last_day - r.start_time.date()).days <= 13))
    b2b = 0
    for i in range(1, len(days)):
        if (days[i] - days[i - 1]).days == 1:
            b2b += 1
    return b2b

def _intensity_split_by_pace(runs: List[Run]) -> Dict[str, float]:
    '''
    Pace-based bucketing using athlete's own distribution in lookback:
        - hard: fastest 15% (lowest sec/km)
        - easy: slowest 60% (highest sec/km)
    Returns distance-weighted percentages
    '''
    if not runs:
        return {'easy_pct': 0.0, 'hard_pct': 0.0}
    
    pace_runs = [(r.pace_s_per_km, r.distance_m) for r in runs if r.distance_m > 0]
    if len(pace_runs) < 3:
        # not enough history, use safe defaults
        return {'easy_pct': 70.0, 'hard_pct': 0.0}
    
    paces = sorted(p for p, _ in pace_runs) # lowers = faster

    def pct_value(vals: List[float], pct: float) -> float:
        idx = max(0, min(len(vals) - 1, int(round((len(vals) - 1) * pct))))
        return vals[idx]
    
    hard_cut = pct_value(paces, 0.15) # <= hard_cut => hard
    easy_cut = pct_value(paces, 0.60) # >= easy cut => easy

    hard_m = easy_m = total_m = 0.0
    for pace, dist_m in pace_runs:
        total_m += dist_m
        if pace <= hard_cut:
            hard_m += dist_m
        elif pace >= easy_cut:
            easy_m += dist_m
    
    if total_m <= 0:
        return {'easy_pct': 0.0, 'hard_pct': 0.0}
    
    return {
        'easy_pct': round((easy_m / total_m) * 100.0, 1),
        'hard_pct': round((hard_m / total_m) * 100.0, 1),
    }

def compute_metrics(runs_all: List[Run], lookback_days: int = 28) -> Dict[str, Any]:
    '''
    Produces the metrics dict consumed by risk_flags + LLM
    '''
    runs = _filter_lookback(runs_all, lookback_days)

    total_distance_m = sum(r.distance_m for r in runs)
    run_count = len(runs)

    weekly = _weekly_buckets(runs)
    weekly_distance_km = [round(dist_m / 1000.0, 2) for _, dist_m, _ in weekly]
    weekly_frequency = [cnt for _, _, cnt in weekly]

    # ACWR-ish: last 7 days / (28-day avg week)
    last_day = runs[-1].start_time if runs else None
    if last_day:
        cutoff_7 = last_day - timedelta(days=7)
        dist_7_m = sum(r.distance_m for r in runs if r.start_time >= cutoff_7)
    else:
        dist_7_m = 0.0
    
    dist_28_m = total_distance_m
    denom = (dist_28_m / 4.0) if dist_28_m > 0 else 0.0
    acwr = round((dist_7_m / denom), 2) if denom > 0 else None

    # Longest run % of last 7 days
    if last_day and dist_7_m > 0:
        last7_runs = [r for r in runs if r.start_time >= cutoff_7]
        longest_m = max((r.distance_m for r in last7_runs), default = 0.0)
        longest_run_pct = round(longest_m / dist_7_m, 2)
    else:
        longest_run_pct = None
    
    rest_days_last_14 = _count_rest_days_last_14(runs)
    back_to_back_runs_last_14 = _count_back_to_back_runs_last_14(runs)

    intensity = _intensity_split_by_pace(runs)

    return {
        'lookback_days': lookback_days,
        'run_count': run_count, 
        'total_distance_km': round(total_distance_m / 1000.0, 2),
        'weekly_distance': weekly_distance_km,  # list[km]
        'weekly_frequency': weekly_frequency,   # list[count]
        'acwr': acwr,
        'longest_run_pct': longest_run_pct,
        'rest_days_last_14': rest_days_last_14,
        'back_to_back_runs_last_14': back_to_back_runs_last_14,
        **intensity,
    }