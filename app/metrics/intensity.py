from __future__ import annotations
from typing import Dict, List, Optional
from app.domain.schemas import Run

# Take a group of runs and estimate what percentage of the total distance was 'easy' vs 'hard', based on the runner's own pace distribution
def intensity_split_by_pace(runs: List[Run]) -> Dict[str, Optional[float]]:
    '''
    Pace-based bucketing using athlete's own distribution in lookback:
        - hard: fastest 15% (lowest sec/km)
        - easy: slowest 60% (highest sec/km)
    Returns distance-weighted percentages
    If there is not enough data, returns None values
    '''
    empty: Dict[str, Optional[float]] = {'easy_pct': None, 'moderate_pct': None, 'hard_pct': None}
    if not runs:
        return empty
    
    pace_runs = [
        (r.pace_s_per_km, r.distance_m)
        for r in runs
        if r.distance_m > 0 and r.pace_s_per_km is not None
    ]
    if len(pace_runs) < 3:
        return empty
    
    paces = sorted(p for p, _ in pace_runs) # lower = faster

    def pct_value(vals: List[float], pct: float) -> float:
        idx = max(0, min(len(vals) - 1, int(round((len(vals) - 1) * pct))))
        return vals[idx]
    
    hard_cut = pct_value(paces, 0.15) # <= hard_cut => hard
    easy_cut = pct_value(paces, 0.60) # >= easy cut => easy

    hard_m = easy_m = moderate_m = total_m = 0.0
    for pace, dist_m in pace_runs:
        total_m += dist_m
        if pace <= hard_cut:
            hard_m += dist_m
        elif pace >= easy_cut:
            easy_m += dist_m
        else:
            moderate_m += dist_m
    
    if total_m <= 0:
        return empty
    
    return {
        'easy_pct': round((easy_m / total_m) * 100.0, 1),
        'moderate_pct': round((moderate_m / total_m) * 100.0, 1),
        'hard_pct': round((hard_m / total_m) * 100.0, 1)
    }