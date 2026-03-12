from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Run:
    start_time: datetime
    distance_m: float
    duration_s: float
    avg_hr: Optional[float] = None

    @property
    def pace_s_per_km(self) -> float:
        # Defensive: avoid divide-by-zero
        km = self.distance_m / 1000.0
        if km <= 0:
            return float("inf")
        return self.duration_s / km
