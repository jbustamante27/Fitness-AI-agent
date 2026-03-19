import json
from app.flags.risk_flags import evaluate_risk_flags, assessment_to_dict

balanced_sample_metrics = {
    "acwr": 1.05,
    "duration_acwr": 1.02,
    "weekly_distance": [24.0, 26.0, 25.0, 27.0],
    "weekly_duration_min": [150.0, 160.0, 155.0, 165.0],
    "volume_trend": "flat",
    "duration_trend": "flat",
    "distance_last_7_km": 27.0,
    "longest_run_pct": 0.31,
    "easy_pct": 72.0,
    "hard_pct": 14.0,
    "rest_days_last_14": 3,
    "back_to_back_runs_last_14": 2,
    "monotony": 1.45,
    "strain": 39150.0,
}

assessment = evaluate_risk_flags(balanced_sample_metrics)
print(json.dumps(assessment_to_dict(assessment), indent=2))