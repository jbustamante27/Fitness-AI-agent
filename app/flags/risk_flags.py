from __future__ import annotations

from app.domain.schemas import ComputedMetrics, RiskAssessment


# Determine whether the training load is stable or decreasing
def _trend_is_flat_or_decreasing(values: list[float]) -> bool:
    """
    Returns True if the series is flat or trending down overall.
    Used to avoid overreacting to ACWR when weekly volume is not actually rising
    """
    if len(values) < 2:
        return True
    return values[-1] <= values[0]

def assess_risk(metrics: ComputedMetrics) -> RiskAssessment:
    flags: list[str] = []
    explanations: list[str] = []

    acwr_distance = metrics.acwr_distance
    acwr_duration = metrics.acwr_duration
    weekly_distance = metrics.weekly_distance
    weekly_duration_min = metrics.weekly_duration_min
    longest_run_pct = metrics.longest_run_pct
    easy_pct = metrics.easy_pct
    hard_pct = metrics.hard_pct
    rest_days_last_14 = metrics.rest_days_last_14
    back_to_back_runs_last_14 = metrics.back_to_back_runs_last_14
    monotony_last_7 = metrics.monotony_last_7
    strain_last_7 = metrics.strain_last_7


    # --- A) volume_spike ---
    if (
        acwr_distance is not None
        and acwr_distance >= 1.5
        and not _trend_is_flat_or_decreasing(weekly_distance)
    ):
        flags.append("volume_spike")
        explanations.append(
            f"Distance ACWR is elevated at {acwr_distance:.2f}, indicating a sharp recent increase in running volume."
        )


    # --- B) duration_spike ---
    if (
        acwr_duration is not None
        and acwr_duration >= 1.5
        and not _trend_is_flat_or_decreasing(weekly_duration_min)
    ):
        flags.append("duration_spike")
        explanations.append(
            f"Duration ACWR is elevated at {acwr_duration:.2f}, indicating a sharp recent increase in time-on-feet."
        )
    

    # --- C) long_run_dominance ---
    if longest_run_pct >= 0.40:
        flags.append("long_run_dominance")
        explanations.append(
            f"The longest run made up {longest_run_pct:.0%} of the last 7 days of distance, which may indicate unbalanced loading."
        )


    # --- D) Insufficient easy running ---
    if easy_pct < 70.0:
        flags.append("insufficient_easy_running")
        explanations.append(
            f"Only {easy_pct:.1f}% of running volume was easy, which is below the usual durability-focused range."
        )

    
    # --- E) Excessive hard running ---
    if hard_pct > 20.0:
        flags.append("excessive_hard_running")
        explanations.append(
            f"{hard_pct:.1f}% of running volume was hard, which may reduce recovery capacity and increase injury risk."
        )


    # --- F) Insufficient Recovery ---
    if rest_days_last_14 <= 1:
        flags.append("insufficient_recovery")
        explanations.append(
            f"There were only {rest_days_last_14} rest day(s) in the last 14 days, suggesting limited recovery opportunity."
        )
    if back_to_back_runs_last_14 >= 5:
        flags.append("frequent_back_to_back_runs")
        explanations.append(
            f"There were {back_to_back_runs_last_14} back-to-back run pair(s) in the last 14 days, which may indicate accumulated fatigue."
        )


    # --- G) High monotony ---
    if monotony_last_7 is not None and monotony_last_7 >= 2.0:
        flags.append("high_monotony")
        explanations.append(
            f"Training monotony is high at {monotony_last_7:.2f}, meaning daily load distribution has been relatively uniform."
        )
    
    # --- H) High strain ---
    if strain_last_7 is not None and strain_last_7 >= 150.0:
        flags.append("high_strain")
        explanations.append(
            f"Training strain is elevated at {strain_last_7:.1f}, reflecting a high combination of load and monotony."
        )
    
    
    # --- Overall risk level ---
    if len(flags) >= 5:
        risk_level = "high"
    elif len(flags) >= 3:
        risk_level = "moderate"
    elif len(flags) >= 1:
        risk_level = "low"
    else:
        risk_level = "minimal"

    return RiskAssessment(
        risk_level = risk_level,
        flags = flags,
        explanations = explanations,
    )



