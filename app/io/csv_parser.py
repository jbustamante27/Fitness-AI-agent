from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from dateutil import parser as dateparser

from app.io.models import Run


def _norm(col: str) -> str:
    return col.strip().lower().replace(' ', '_').replace('-', '_')

def _parse_datetime(value: str) -> datetime:
    dt = dateparser.parse(str(value))
    if dt is None:
        raise ValueError(f'Could not parse datetime: {value}')
    return dt

def _to_seconds(value) -> float:
    '''
    This accepts either:
        - Seconds numeric
        - h:mm:ss or mm:ss strings
    '''
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError("Missing duration")  
    
    if isinstance(value, (int, float)):
        return float(value)
    
    s = str(value).strip()
    if ':' not in s:
        return float(s)
    
    parts = [float(p) for p in s.split(':')]
    if len(parts) == 2:
        mm, ss = parts
        return mm * 60 + ss
    if len(parts) == 3:
        hh, mm, ss = parts
        return hh * 3600 + mm * 60 + ss
    
    raise ValueError(f"Unrecognized time format: {value}")


def parse_garmin_csv(filepath: str, distance_unit_default: str = "km") -> List[Run]:
    '''
    Parse a Garmin-exported CSV into Run objects

    distance_unit_default:
        - 'km' (default) or 'm' or 'mi'
        Used only if we can't infer from column naming
    '''
    df = pd.read_csv(filepath)

    # Normalize columns
    col_map = {_norm(c): c for c in df.columns}
    norm_cols = list(col_map.keys())

    # Candidate mappings (normalized) — adjust once we see your Garmin CSV header
    candidates: List[Dict[str, str]] = [
        {"start_time": "date", "distance": "distance", "duration": "time", "avg_hr": "avg_hr"},
        {"start_time": "activity_date", "distance": "distance", "duration": "time", "avg_hr": "average_heart_rate"},
        {"start_time": "start_time", "distance": "distance", "duration": "elapsed_time", "avg_hr": "avg_hr"},
        {"start_time": "start_time", "distance": "distance", "duration": "time", "avg_hr": "avg_hr"},
    ]

    chosen: Optional[Dict[str, str]] = None
    for cand in candidates:
        if (
            cand['start_time'] in norm_cols
            and cand['distance'] in norm_cols
            and cand['duration'] in norm_cols
        ):
            chosen = cand
            break
    
    if chosen is None:
        raise ValueError(
            "Could not map Garmin CSV columns automatically.\n"
            f"Columns found (normalized): {norm_cols}\n"
            "Update candidates in parse_garmin_csv() to match your export."
        )
    
    start_col = col_map[chosen['start_time']]
    dist_col = col_map[chosen['distance']]
    dur_col = col_map[chosen['duration']]
    avg_hr_col = col_map[chosen["avg_hr"]] if chosen.get("avg_hr") in col_map else None

    runs: List[Run] = []
    for _, row in df.iterrows():
        start_time = _parse_datetime(row[start_col])
        dist_raw = row[dist_col]
        dur_raw = row[dur_col]

        # Distance unit handling
        dist = float(dist_raw)
        dist_norm_col = _norm(dist_col)

        if dist_norm_col.endswith("_m") or "meter" in dist_norm_col:
            distance_m = dist
        elif dist_norm_col.endswith("_km") or "kilometer" in dist_norm_col:
            distance_m = dist * 1000.0
        elif dist_norm_col.endswith('_mi') or "mile" in dist_norm_col:
            distance_m = dist * 1609.344
        else:
            if distance_unit_default == 'm':
                distance_m = dist
            elif distance_unit_default == 'mi':
                distance_m = dist * 1609.344
            else:
                distance_m = dist * 1000.0 # km default
        
        duration_s = _to_seconds(dur_raw)

        avg_hr = None
        if avg_hr_col is not None and avg_hr_col in df.columns:
            val = row[avg_hr_col]
            if val is not None and not (isinstance(val, float) and pd.isna(val)):
                try:
                    avg_hr = float(val)
                except Exception:
                    avg_hr = None
        
        if distance_m > 0 and duration_s > 0:
            runs.append(Run(start_time=start_time, distance_m=distance_m, duration_s=duration_s, avg_hr=avg_hr))

    runs.sort(key = lambda r: r.start_time)
    return runs