from datetime import datetime

from app.domain.schemas import Run
from app.metrics.compute_metrics import compute_metrics
from app.flags.risk_flags import assess_risk


def make_run(dt: datetime, distance_m: float, duration_s: float) -> Run:
    return Run(
        start_time=dt,
        distance_m=distance_m,
        duration_s=duration_s,
        avg_hr=None,
    )


def test_full_pipeline():
    runs = [
        make_run(datetime(2026, 3, 1, 7, 0), 5000, 1500),
        make_run(datetime(2026, 3, 5, 7, 0), 7000, 2100),
        make_run(datetime(2026, 3, 10, 7, 0), 10000, 3000),
        make_run(datetime(2026, 3, 15, 7, 0), 12000, 3600),
    ]

    metrics = compute_metrics(runs)
    risk = assess_risk(metrics)

    assert metrics.run_count == 4
    assert metrics.total_distance_km == 34.0
    assert risk.risk_level in {"minimal", "low", "moderate", "high"}
    assert isinstance(risk.flags, list)
    assert isinstance(risk.explanations, list)