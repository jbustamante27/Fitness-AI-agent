from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional
from fitparse import FitFile
from app.io.models import Run


def _to_datetime(value) -> Optional[datetime]:
    if value is None:
        return None
    # fitparse typically yields datetime already for timestamp fields
    if isinstance(value, datetime):
        return value
    return None


def parse_garmin_fit(filepath: str) -> List[Run]:
    """
    Parse a Garmin .fit file into a list of Run objects.
    Uses 'session' messages when available (best source of totals).
    Falls back to 'activity' where necessary.

    Returns:
      List[Run] (usually length 1 for a single activity FIT)
    """
    fitfile = FitFile(filepath)

    runs: List[Run] = []

    # Prefer session totals
    sessions = list(fitfile.get_messages("session"))
    if sessions:
        for s in sessions:
            fields = {f.name: f.value for f in s if f.value is not None}

            start_time = _to_datetime(fields.get("start_time")) or _to_datetime(fields.get("timestamp"))
            total_distance = fields.get("total_distance")  # meters
            total_timer_time = fields.get("total_timer_time") or fields.get("total_elapsed_time")  # seconds
            avg_hr = fields.get("avg_heart_rate")

            # Some FITs may contain multiple sports; we only want running
            sport = fields.get("sport")
            if sport is not None and str(sport).lower() not in ("running", "run"):
                continue

            if start_time is None or total_distance is None or total_timer_time is None:
                # Skip incomplete sessions
                continue

            runs.append(
                Run(
                    start_time=start_time,
                    distance_m=float(total_distance),
                    duration_s=float(total_timer_time),
                    avg_hr=float(avg_hr) if avg_hr is not None else None,
                )
            )

        if runs:
            return runs

    # Fallback: activity message (less detailed)
    activities = list(fitfile.get_messages("activity"))
    for a in activities:
        fields = {f.name: f.value for f in a if f.value is not None}
        timestamp = _to_datetime(fields.get("timestamp"))
        total_timer_time = fields.get("total_timer_time")
        # activity often doesn't include distance; if absent, caller should use CSV
        total_distance = fields.get("total_distance")

        if timestamp is None or total_timer_time is None or total_distance is None:
            continue

        runs.append(
            Run(
                start_time=timestamp,
                distance_m=float(total_distance),
                duration_s=float(total_timer_time),
                avg_hr=None,
            )
        )

    return runs
