from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional


@dataclass(slots=True)
class Run:
    start_time = datetime
    distance_m = float
    duration_s = float
    avg_hr = Optional[float] = None
    max_hr = Optional[float] = None
    elevation_gain_m: Optional[float] = None
    source_file: Optional[str] = None

    @property
    def distance_km(self) -> float:
        return self.distance_m / 1000.0
    
    @property
    def pace_s_per_km(self) -> Optional[float]:
        if self.distance_m <= 0:
            return None
        return self.duration_s / (self.distance_m / 1000.0)


@dataclass(slots=True)
class WeeklySummary:
    week_start: date
    total_distance_km: float
    total_duration_min: float
    run_count: int


@dataclass(slots=True)
class ComputedMetrics:
    lookback_days: int
    run_count: int
    total_distance_km: float
    total_duration_min: float

    weekly_distance: list[float] = field(default_factory=list)
    weekly_duration_min: list[float] = field(default_factory=list)
    weekly_frequency: list[int] = field(default_factory=list)

    distance_last_7_km: float = 0.0
    duration_last_7_min: float = 0.0
    distance_last_14_km: float = 0.0
    duration_last_14_min: float = 0.0

    acwr_distance: Optional[float] = None
    acwr_duration: Optional[float] = None

    longest_run_km_last_7: float = 0.0
    longest_run_pct: float = 0.0

    easy_pct: float = 0.0
    moderate_pct: float = 0.0
    hard_pct: float = 0.0

    rest_days_last_14: int = 0
    back_to_back_runs_last_14: int = 0

    monotony_last_7: Optional[float] = None
    strain_last_7: Optional[float] = None


@dataclass(slots=True)
class RiskAssessment:
    risk_level: str
    flags: list[str] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)