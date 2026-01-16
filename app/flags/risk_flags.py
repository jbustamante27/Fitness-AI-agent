from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass(frozen=True)
class RiskAssessment:
    risk_level: str                    # "low" | "moderate" | "high"
    risk_flags: List[str]              # deterministic flags
    limitations: List[str]             # missing-metric notes
    flag_details: Dict[str, str]       # human-readable explanations


def _get(metrics: Dict[str, Any], key: str, expected_type: Any = None) -> Any:
    """Safe getter with optional type checking (soft)."""
    if key not in metrics:
        return None
    val = metrics.get(key)
    if expected_type is None:
        return val
    try:
        if expected_type is list:
            return val if isinstance(val, list) else None
        return val if isinstance(val, expected_type) else None
    except Exception:
        return None


def _trend_is_flat_or_decreasing(weekly_distance: List[float]) -> bool:
    """
    Conservative heuristic:
    - If we have >= 3 weeks, compare last vs average of previous 2.
    - If we have 2 weeks, last <= previous.
    """
    if len(weekly_distance) < 2:
        return True
    if len(weekly_distance) == 2:
        return weekly_distance[-1] <= weekly_distance[-2]
    prev_avg = (weekly_distance[-2] + weekly_distance[-3]) / 2.0
    return weekly_distance[-1] <= prev_avg


def evaluate_risk_flags(metrics: Dict[str, Any]) -> RiskAssessment:
    """
    Deterministically derive risk flags + overall risk level from aggregated metrics.

    Flags implemented (v1):
      - volume_spike
      - undertraining
      - long_run_dominance
      - insufficient_easy_running
      - excessive_hard_running
      - insufficient_recovery

    Overall risk level:
      - low:       0-1 flags
      - moderate:  2-3 flags
      - high:      4+ flags OR (volume_spike AND insufficient_recovery)
    """
    flags: List[str] = []
    limitations: List[str] = []
    details: Dict[str, str] = {}

    acwr = _get(metrics, "acwr", (int, float))
    weekly_distance = _get(metrics, "weekly_distance", list)
    longest_run_pct = _get(metrics, "longest_run_pct", (int, float))
    easy_pct = _get(metrics, "easy_pct", (int, float))
    hard_pct = _get(metrics, "hard_pct", (int, float))
    rest_days_last_14 = _get(metrics, "rest_days_last_14", int)
    b2b_runs_last_14 = _get(metrics, "back_to_back_runs_last_14", int)

    # --- A) volume_spike ---
    volume_spike_triggered = False
    if acwr is None and not weekly_distance:
        limitations.append("Missing acwr and weekly_distance; cannot assess volume spikes reliably.")
    else:
        # Trigger if acwr >= 1.5
        if isinstance(acwr, (int, float)) and acwr >= 1.5:
            volume_spike_triggered = True

        # Trigger if last week >= 1.25 * previous week (if we have >=2 weeks)
        if isinstance(weekly_distance, list) and len(weekly_distance) >= 2:
            try:
                last_wk = float(weekly_distance[-1])
                prev_wk = float(weekly_distance[-2])
                if prev_wk > 0 and last_wk >= 1.25 * prev_wk:
                    volume_spike_triggered = True
            except Exception:
                limitations.append("weekly_distance values invalid; spike check skipped.")

    if volume_spike_triggered:
        flags.append("volume_spike")
        details["volume_spike"] = (
            "Training volume increased sharply relative to your recent baseline. "
            "Sudden spikes elevate short-term injury and fatigue risk."
        )

    # --- B) undertraining ---
    if acwr is None or not isinstance(weekly_distance, list) or len(weekly_distance) < 2:
        limitations.append("Missing acwr or sufficient weekly_distance; undertraining check may be incomplete.")
    else:
        if acwr < 0.8 and _trend_is_flat_or_decreasing([float(x) for x in weekly_distance]):
            flags.append("undertraining")
            details["undertraining"] = (
                "Recent training load is below your longer-term baseline and appears flat or declining. "
                "This can reduce fitness and make harder efforts feel disproportionately taxing."
            )

    # --- C) long_run_dominance ---
    if longest_run_pct is None:
        limitations.append("Missing longest_run_pct; cannot assess long-run dominance.")
    else:
        try:
            lr = float(longest_run_pct)
            if lr >= 0.40:
                flags.append("long_run_dominance")
                details["long_run_dominance"] = (
                    "A large share of your weekly volume is concentrated in one run. "
                    "When the long run dominates the week, connective tissues often have less time to adapt."
                )
        except Exception:
            limitations.append("longest_run_pct invalid; long-run dominance check skipped.")

    # --- D) insufficient_easy_running ---
    if easy_pct is None:
        limitations.append("Missing easy_pct; cannot assess easy-running balance.")
    else:
        try:
            ep = float(easy_pct)
            if ep < 65.0:
                flags.append("insufficient_easy_running")
                details["insufficient_easy_running"] = (
                    "A relatively low portion of your running is truly easy. "
                    "Too much moderate/hard running can accumulate fatigue and limit recovery between sessions."
                )
        except Exception:
            limitations.append("easy_pct invalid; easy-running balance check skipped.")

    # --- E) excessive_hard_running ---
    if hard_pct is None:
        limitations.append("Missing hard_pct; cannot assess hard-running proportion.")
    else:
        try:
            hp = float(hard_pct)
            if hp >= 20.0:
                flags.append("excessive_hard_running")
                details["excessive_hard_running"] = (
                    "A relatively high portion of your mileage is hard intensity. "
                    "Sustained high-intensity volume is effective but increases recovery demand and injury risk."
                )
        except Exception:
            limitations.append("hard_pct invalid; hard-running proportion check skipped.")

    # --- F) insufficient_recovery ---
    recovery_triggered = False
    if rest_days_last_14 is None and b2b_runs_last_14 is None:
        limitations.append("Missing rest_days_last_14 and back_to_back_runs_last_14; cannot assess recovery density.")
    else:
        if isinstance(rest_days_last_14, int) and rest_days_last_14 <= 1:
            recovery_triggered = True
        if isinstance(b2b_runs_last_14, int) and b2b_runs_last_14 >= 5:
            recovery_triggered = True

    if recovery_triggered:
        flags.append("insufficient_recovery")
        details["insufficient_recovery"] = (
            "Recent training has limited recovery spacing (few rest days and/or frequent back-to-back runs). "
            "Insufficient recovery increases fatigue and can make small issues linger into injuries."
        )

    # --- Overall risk level ---
    flag_set = set(flags)
    if (len(flags) >= 4) or ("volume_spike" in flag_set and "insufficient_recovery" in flag_set):
        risk_level = "high"
    elif len(flags) >= 2:
        risk_level = "moderate"
    else:
        risk_level = "low"

    # Keep output stable: sorted flags for consistent diffs
    flags_sorted = sorted(flags)

    return RiskAssessment(
        risk_level=risk_level,
        risk_flags=flags_sorted,
        limitations=sorted(set(limitations)),
        flag_details=details,
    )


def assessment_to_dict(assessment: RiskAssessment) -> Dict[str, Any]:
    """Helper for JSON serialization."""
    return asdict(assessment)
