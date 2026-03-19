from __future__ import annotations
from math import sqrt
from typing import List, Optional, Tuple

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