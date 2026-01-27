# app/main.py
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime

from app.io.fit_parser import parse_garmin_fit
from app.io.csv_parser import parse_garmin_csv
from app.metrics.compute_metrics import compute_metrics
from app.flags.risk_flags import evaluate_risk_flags, assessment_to_dict
from app.llm.analyze import generate_narrative


def parse_args():
    p = argparse.ArgumentParser(description="Running Coach: generate metrics, risk flags, and narrative report.")
    p.add_argument("--input", required=True, help="Path to .fit or .csv file")
    p.add_argument("--name", default="Runner", help="Runner name for labeling outputs")
    p.add_argument("--days", type=int, default=28, help="Lookback window in days (default 28)")
    p.add_argument("--csv-distance-unit", default="km", choices=["km", "m", "mi"],
                   help="Default distance unit for CSV if not inferable from columns (default km)")
    p.add_argument("--model", default="gpt-4o-mini", help="OpenAI model for narrative generation")
    return p.parse_args()


def main():
    args = parse_args()
    path = args.input
    ext = os.path.splitext(path)[1].lower()

    if ext == ".fit":
        runs = parse_garmin_fit(path)
    elif ext == ".csv":
        runs = parse_garmin_csv(path, distance_unit_default=args.csv_distance_unit)
    else:
        raise ValueError("Unsupported input type. Provide a .fit or .csv file.")

    if not runs:
        raise RuntimeError("No runs could be parsed from the input file.")

    metrics = compute_metrics(runs, lookback_days=args.days)

    assessment = evaluate_risk_flags(metrics)
    risk = assessment_to_dict(assessment)

    narrative = generate_narrative(metrics, risk, model=args.model)

    payload = {
        "runner_name": args.name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "metrics": metrics,
        "risk": risk,
        "narrative": {
            "interpretation": narrative["interpretation"],
            "recommendations": narrative["recommendations"],
            "takeaways": narrative["takeaways"],
        },
    }

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
