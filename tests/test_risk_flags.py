from app.domain.schemas import ComputedMetrics
from app.flags.risk_flags import assess_risk


def test_assess_risk_high_case():
    metrics = ComputedMetrics(
        lookback_days=28,
        run_count=10,
        total_distance_km=38.0,
        total_duration_min=240.0,
        weekly_distance=[18.0, 22.0, 29.0, 38.0],
        weekly_duration_min=[110.0, 130.0, 160.0, 210.0],
        weekly_frequency=[2, 3, 3, 4],
        acwr_distance=1.62,
        acwr_duration=1.55,
        longest_run_pct=0.42,
        easy_pct=58.0,
        hard_pct=22.0,
        rest_days_last_14=1,
        back_to_back_runs_last_14=6,
        monotony_last_7=2.10,
        strain_last_7=165.0,
    )

    result = assess_risk(metrics)

    assert result.risk_level == "high"
    assert "volume_spike" in result.flags
    assert "duration_spike" in result.flags
    assert "long_run_dominance" in result.flags
    assert "insufficient_easy_running" in result.flags
    assert "excessive_hard_running" in result.flags
    assert "insufficient_recovery" in result.flags
    assert "frequent_back_to_back_runs" in result.flags
    assert "high_monotony" in result.flags
    assert "high_strain" in result.flags
    assert len(result.explanations) == len(result.flags)


def test_assess_risk_low_case():
    metrics = ComputedMetrics(
        lookback_days=28,
        run_count=9,
        total_distance_km=35.0,
        total_duration_min=225.0,
        weekly_distance=[24.0, 26.0, 29.0, 35.0],
        weekly_duration_min=[150.0, 165.0, 185.0, 225.0],
        weekly_frequency=[2, 2, 2, 3],
        acwr_distance=1.30,
        acwr_duration=1.25,
        longest_run_pct=0.41,
        easy_pct=65.0,
        hard_pct=18.0,
        rest_days_last_14=3,
        back_to_back_runs_last_14=2,
        monotony_last_7=1.7,
        strain_last_7=110.0,
    )

    result = assess_risk(metrics)

    assert result.risk_level == "low"
    assert "long_run_dominance" in result.flags
    assert "insufficient_easy_running" in result.flags
    assert len(result.flags) == 2
    assert len(result.explanations) == 2


def test_assess_risk_minimal_case():
    metrics = ComputedMetrics(
        lookback_days=28,
        run_count=8,
        total_distance_km=32.0,
        total_duration_min=210.0,
        weekly_distance=[30.0, 31.0, 32.0, 32.0],
        weekly_duration_min=[200.0, 205.0, 208.0, 210.0],
        weekly_frequency=[2, 2, 2, 2],
        acwr_distance=1.02,
        acwr_duration=1.01,
        longest_run_pct=0.28,
        easy_pct=80.0,
        hard_pct=10.0,
        rest_days_last_14=4,
        back_to_back_runs_last_14=1,
        monotony_last_7=1.5,
        strain_last_7=90.0,
    )

    result = assess_risk(metrics)

    assert result.risk_level == "minimal"
    assert result.flags == []
    assert result.explanations == []