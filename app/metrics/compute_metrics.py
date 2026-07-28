from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from math import sqrt
from typing import Iterable

from app.domain.schemas import Run, ComputedMetrics


def _week_start(dt: datetime) -> datetime:
    return datetime(dt.year, dt.month, dt.day) - timedelta(days=dt.weekday())


def _filter_lookback(runs: list[Run], lookback_days: int) -> list[Run]:
    if not runs:
        return []

    latest = max(run.start_time for run in runs)
    cutoff = latest - timedelta(days=lookback_days)
    return [run for run in runs if run.start_time >= cutoff]


def _weekly_buckets(runs: list[Run]) -> tuple[list[float], list[float], list[int]]:
    buckets: dict[datetime, dict[str, float | int]] = defaultdict(
        lambda: {"distance_km": 0.0, "duration_min": 0.0, "count": 0}
    )

    for run in runs:
        wk = _week_start(run.start_time)
        buckets[wk]["distance_km"] += run.distance_km
        buckets[wk]["duration_min"] += run.duration_min
        buckets[wk]["count"] += 1

    ordered = sorted(buckets.items(), key=lambda item: item[0])

    weekly_distance = [float(data["distance_km"]) for _, data in ordered]
    weekly_duration_min = [float(data["duration_min"]) for _, data in ordered]
    weekly_frequency = [int(data["count"]) for _, data in ordered]

    return weekly_distance, weekly_duration_min, weekly_frequency


def _count_rest_days_last_14(runs: list[Run], anchor: datetime) -> int:
    run_days = {
        run.start_time.date()
        for run in runs
        if run.start_time >= anchor - timedelta(days=14)
    }

    return sum(
        1
        for i in range(14)
        if (anchor.date() - timedelta(days=i)) not in run_days
    )


def _count_back_to_back_runs_last_14(runs: list[Run], anchor: datetime) -> int:
    run_days = sorted(
        {
            run.start_time.date()
            for run in runs
            if run.start_time >= anchor - timedelta(days=14)
        }
    )

    count = 0
    for i in range(1, len(run_days)):
        if (run_days[i] - run_days[i - 1]).days == 1:
            count += 1
    return count


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stddev_population(values: list[float]) -> float:
    if not values:
        return 0.0
    avg = _mean(values)
    variance = sum((x - avg) ** 2 for x in values) / len(values)
    return sqrt(variance)


def _intensity_split_by_pace(runs: list[Run]) -> tuple[float, float, float]:
    valid_runs = [run for run in runs if run.pace_s_per_km is not None and run.distance_m > 0]
    if not valid_runs:
        return 0.0, 0.0, 0.0

    if len(valid_runs) < 3:
        return 100.0, 0.0, 0.0

    sorted_by_pace = sorted(valid_runs, key=lambda r: r.pace_s_per_km or 0.0)
    total_distance = sum(run.distance_km for run in sorted_by_pace)

    hard_cutoff = max(1, round(len(sorted_by_pace) * 0.15))
    easy_cutoff = max(1, round(len(sorted_by_pace) * 0.60))

    hard_runs = sorted_by_pace[:hard_cutoff]
    easy_runs = sorted_by_pace[-easy_cutoff:]

    hard_distance = sum(run.distance_km for run in hard_runs)
    easy_distance = sum(run.distance_km for run in easy_runs)
    moderate_distance = max(0.0, total_distance - hard_distance - easy_distance)

    easy_pct = (easy_distance / total_distance) * 100.0 if total_distance else 0.0
    moderate_pct = (moderate_distance / total_distance) * 100.0 if total_distance else 0.0
    hard_pct = (hard_distance / total_distance) * 100.0 if total_distance else 0.0

    return easy_pct, moderate_pct, hard_pct


def compute_metrics(runs: list[Run], lookback_days: int = 28) -> ComputedMetrics:
    if not runs:
        return ComputedMetrics(
            lookback_days=lookback_days,
            run_count=0,
            total_distance_km=0.0,
            total_duration_min=0.0,
        )

    lookback_runs = sorted(_filter_lookback(runs, lookback_days), key=lambda r: r.start_time)
    if not lookback_runs:
        return ComputedMetrics(
            lookback_days=lookback_days,
            run_count=0,
            total_distance_km=0.0,
            total_duration_min=0.0,
        )

    anchor = max(run.start_time for run in lookback_runs)
    last_7_cutoff = anchor - timedelta(days=7)
    last_14_cutoff = anchor - timedelta(days=14)

    run_count = len(lookback_runs)
    total_distance_km = sum(run.distance_km for run in lookback_runs)
    total_duration_min = sum(run.duration_min for run in lookback_runs)

    weekly_distance, weekly_duration_min, weekly_frequency = _weekly_buckets(lookback_runs)

    last_7_runs = [run for run in lookback_runs if run.start_time >= last_7_cutoff]
    last_14_runs = [run for run in lookback_runs if run.start_time >= last_14_cutoff]

    distance_last_7_km = sum(run.distance_km for run in last_7_runs)
    duration_last_7_min = sum(run.duration_min for run in last_7_runs)
    distance_last_14_km = sum(run.distance_km for run in last_14_runs)
    duration_last_14_min = sum(run.duration_min for run in last_14_runs)

    avg_weekly_distance = total_distance_km / (lookback_days / 7)
    avg_weekly_duration = total_duration_min / (lookback_days / 7)

    acwr_distance = (
        distance_last_7_km / avg_weekly_distance
        if avg_weekly_distance > 0
        else None
    )
    acwr_duration = (
        duration_last_7_min / avg_weekly_duration
        if avg_weekly_duration > 0
        else None
    )

    longest_run_km_last_7 = max((run.distance_km for run in last_7_runs), default=0.0)
    longest_run_pct = (
        longest_run_km_last_7 / distance_last_7_km
        if distance_last_7_km > 0
        else 0.0
    )

    easy_pct, moderate_pct, hard_pct = _intensity_split_by_pace(lookback_runs)

    rest_days_last_14 = _count_rest_days_last_14(lookback_runs, anchor)
    back_to_back_runs_last_14 = _count_back_to_back_runs_last_14(lookback_runs, anchor)

    daily_distance_last_7 = []
    for i in range(6, -1, -1):
        day = (anchor - timedelta(days=i)).date()
        day_total = sum(
            run.distance_km
            for run in lookback_runs
            if run.start_time.date() == day
        )
        daily_distance_last_7.append(day_total)

    daily_mean = _mean(daily_distance_last_7)
    daily_std = _stddev_population(daily_distance_last_7)
    monotony_last_7 = (daily_mean / daily_std) if daily_std > 0 else None
    strain_last_7 = (sum(daily_distance_last_7) * monotony_last_7) if monotony_last_7 is not None else None

    return ComputedMetrics(
        lookback_days=lookback_days,
        run_count=run_count,
        total_distance_km=total_distance_km,
        total_duration_min=total_duration_min,
        weekly_distance=weekly_distance,
        weekly_duration_min=weekly_duration_min,
        weekly_frequency=weekly_frequency,
        distance_last_7_km=distance_last_7_km,
        duration_last_7_min=duration_last_7_min,
        distance_last_14_km=distance_last_14_km,
        duration_last_14_min=duration_last_14_min,
        acwr_distance=acwr_distance,
        acwr_duration=acwr_duration,
        longest_run_km_last_7=longest_run_km_last_7,
        longest_run_pct=longest_run_pct,
        easy_pct=easy_pct,
        moderate_pct=moderate_pct,
        hard_pct=hard_pct,
        rest_days_last_14=rest_days_last_14,
        back_to_back_runs_last_14=back_to_back_runs_last_14,
        monotony_last_7=monotony_last_7,
        strain_last_7=strain_last_7,
    )