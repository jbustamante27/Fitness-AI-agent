from __future__ import annotations
from typing import List

# Simple trend classification for recent weekly values
def _trend_label(values: List[float]) -> str:
    if len(values) < 2:
        return 'insufficient_data'
    
    last = values[-1]
    prev = values[-2]

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