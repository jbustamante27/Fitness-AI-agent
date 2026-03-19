import json
from app.flags.risk_flags import evaluate_risk_flags, assessment_to_dict

limited_sample_metrics = {
    "acwr": None,
    "duration_acwr": None,
    "weekly_distance": [12.0],
    "weekly_duration_min": [70.0],
    "volume_trend": "insufficient_data",
    "duration_trend": "insufficient_data",
    "distance_last_7_km": 12.0,
    "longest_run_pct": None,
    "easy_pct": None,
    "hard_pct": None,
    "rest_days_last_14": 5,
    "back_to_back_runs_last_14": 0,
    "monotony": None,
    "strain": None,
}

assessment = evaluate_risk_flags(limited_sample_metrics)
print(json.dumps(assessment_to_dict(assessment), indent=2))