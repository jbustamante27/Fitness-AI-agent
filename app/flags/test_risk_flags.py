from app.flags.risk_flags import evaluate_risk_flags


def test_high_risk_case():
    metrics = {
        "acwr": 1.62,
        "duration_acwr": 1.58,
        "weekly_distance": [18.0, 22.0, 29.0, 38.0],
        "weekly_duration_min": [105.0, 128.0, 170.0, 225.0],
        "volume_trend": "increasing",
        "duration_trend": "increasing",
        "distance_last_7_km": 38.0,
        "longest_run_pct": 0.42,
        "easy_pct": 58.0,
        "hard_pct": 22.0,
        "rest_days_last_14": 1,
        "back_to_back_runs_last_14": 6,
        "monotony": 2.18,
        "strain": 82840.0,
    }

    assessment = evaluate_risk_flags(metrics)

    assert assessment.risk_level == "high"
    assert "volume_spike" in assessment.risk_flags
    assert "duration_spike" in assessment.risk_flags
    assert "long_run_dominance" in assessment.risk_flags
    assert "insufficient_easy_running" in assessment.risk_flags
    assert "excessive_hard_running" in assessment.risk_flags
    assert "insufficient_recovery" in assessment.risk_flags
    assert "high_monotony" in assessment.risk_flags
    assert "high_strain" in assessment.risk_flags
    assert assessment.limitations == []


def test_balanced_case():
    metrics = {
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

    assessment = evaluate_risk_flags(metrics)

    assert assessment.risk_level == "low"
    assert assessment.risk_flags == []
    assert assessment.limitations == []


def test_limited_data_case():
    metrics = {
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

    assessment = evaluate_risk_flags(metrics)

    assert assessment.risk_level == "low"
    assert assessment.risk_flags == []
    assert "Missing longest_run_pct; cannot assess long-run dominance." in assessment.limitations
    assert "Missing easy_pct; cannot assess easy-running balance." in assessment.limitations
    assert "Missing hard_pct; cannot assess hard-running proportion." in assessment.limitations
    assert "Missing monotony; cannot assess day-to-day load variability." in assessment.limitations
    assert "Missing strain; cannot assess combined weekly load and monotony." in assessment.limitations