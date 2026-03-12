from __future__ import annotations
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Tuple, Optional
from app.io.models import Run
from math import sqrt

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

# Take a group of runs and estimate what percentage of the total distance was 'easy' vs 'hard', based on the runner's own pace distribution
def _intensity_split_by_pace(runs: List[Run]) -> Dict[str, float]:
    '''
    Pace-based bucketing using athlete's own distribution in lookback:
        - hard: fastest 15% (lowest sec/km)
        - easy: slowest 60% (highest sec/km)
    Returns distance-weighted percentages
    If there is not enough data, returns None values
    '''
    if not runs:
        return {'easy_pct': None, 'hard_pct': None}
    
    pace_runs = [(r.pace_s_per_km, r.distance_m) for r in runs if r.distance_m > 0]
    if len(pace_runs) < 3:
        return {'easy_pct': None, 'hard_pct': None}
    
    paces = sorted(p for p, _ in pace_runs) # lower = faster

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
        return {'easy_pct': None, 'hard_pct': None}
    
    return {
        'easy_pct': round((easy_m / total_m) * 100.0, 1),
        'hard_pct': round((hard_m / total_m) * 100.0, 1),
    }

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

# get the mean of the values
def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)

# Get the standard deviation of the  list of values
def _stddev_population(values: List[float]) -> Optional[float]:
    if not values:
        return None
    mu = _mean(values)
    if mu is None:
        return None
    variance = sum((x - mu) ** 2 for x in values) / len(values)
    return sqrt(variance)

'''
Compute:
    - Monotony: how repetitive the training load is across days
        -> mean daily load / std dev of daily load
    - Strain: overall weekly stress on the runner
        -> total weekly load * monotony
'''
def _compute_monotony_and_strain(last7_daily_loads: List[float]) -> Tuple[Optional[float], Optional[float]]:
    if not last7_daily_loads:
        return None, None
    
    mean_load = _mean(last7_daily_loads)
    std_load = _stddev_population(last7_daily_loads)

    if (mean_load is None) or (std_load is None):
        return None, None
    
    # Perfectly identical daily load or all zero week; monotony is not meaningful
    if std_load == 0:
        return None, None
    
    monotony = mean_load / std_load
    weekly_load = sum(last7_daily_loads)
    strain = weekly_load * monotony

    return round(monotony, 2), round(strain, 2)

# Simple trend classification for recent weekly values
def _trend_label(values: List[float]) -> str:
    if len(values) < 2:
        return 'insufficient_data'
    
    last = values[-1]
    prev = [values[-2]]

    if prev == 0:
        if last == 0:
            return 'flat'
        return 'increasing'
    
    pct_change = (last - prev) / prev

    if pct_change >= 0.10:
        return 'increasing'
    if pct_change <= -.10:
        return 'decreasing'
    return 'flat'

# Produce the metrics dict consumed by risk_flags + LLM
def compute_metrics(runs_all: List[Run], lookback_days: int = 28) -> Dict[str, Any]:
    runs = _filter_lookback(runs_all, lookback_days)

    total_distance_m = sum(r.distance_m for r in runs)
    total_duration_s = sum(r.duration_s for r in runs)
    run_count = len(runs)

    weekly = _weekly_buckets(runs)
    weekly_distance_km = [round(dist_m / 1000.0, 2) for _, dist_m, _ in weekly]
    weekly_duration_min = [round(duration_s / 60.0, 1) for _, _, duration_s, _ in weekly]
    weekly_frequency = [cnt for _, _, _, cnt in weekly]

    # ACWR-ish: last 7 days / (28-day avg week)
    last_day = runs[-1].start_time if runs else None
    if last_day:
        cutoff_7 = last_day - timedelta(days=7)
        last7_runs = [r for r in runs if r.start_time >= cutoff_7]
        dist_7_m = sum(r.distance_m for r in last7_runs)
        duration_7_s = sum(r.duration_s for r in last7_runs)
    else:
        last7_runs = []
        dist_7_m = 0.0
        duration_7_s = 0.0
    
    # Distance-based ACWR
    dist_28_m = total_distance_m
    dist_denom = (dist_28_m / 4.0) if dist_28_m > 0 else 0.0
    acwr = round((dist_7_m / dist_denom), 2) if dist_denom > 0 else None

    # Duration-baesd ACWR
    dur_28_s = total_duration_s
    dur_denom = (dur_28_s / 4.0) if dur_28_s > 0 else 0.0
    duration_acwr = round(duration_7_s / dur_denom, 2) if dur_denom > 0 else None

    # Longest run % of last 7 days
    if dist_7_m > 0:
        longest_m = max((r.distance_m for r in last7_runs), default = 0.0)
        longest_run_pct = round(longest_m / dist_7_m, 2)
    else:
        longest_run_pct = None
    
    rest_days_last_14 = _count_rest_days_last_14(runs)
    back_to_back_runs_last_14 = _count_back_to_back_runs_last_14(runs)

    intensity = _intensity_split_by_pace(runs)

    daily_distance_last_7 = _daily_distance_series_last_7(runs)
    monotony, strain = _compute_monotony_and_strain(daily_distance_last_7)

    return {
        'lookback_days': lookback_days,
        'run_count': run_count, 
        'total_distance_km': round(total_distance_m / 1000.0, 2),
        'total_distance_min': round(total_duration_s / 60.0, 1),

        'weekly_distance': weekly_distance_km,      # list[km]
        'weekly_duration_min': weekly_duration_min, #list[min]
        'weekly_frequency': weekly_frequency,       # list[count]

        'acwr': acwr,
        'duration_acwr': duration_acwr,
        'longest_run_pct': longest_run_pct,

        'rest_days_last_14': rest_days_last_14,
        'back_to_back_runs_last_14': back_to_back_runs_last_14,

        'monotony': monotony,
        'strain': strain,

        **intensity,
    }