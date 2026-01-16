import json
from app.flags.risk_flags import evaluate_risk_flags, assessment_to_dict

sample_metrics = {
    "acwr": 1.62,
    "weekly_distance": [18.0, 22.0, 29.0, 38.0],
    "longest_run_pct": 0.42,
    "easy_pct": 58.0,
    "hard_pct": 22.0,
    "rest_days_last_14": 1,
    "back_to_back_runs_last_14": 6
}

assessment = evaluate_risk_flags(sample_metrics)
print(json.dumps(assessment_to_dict(assessment), indent=2))
