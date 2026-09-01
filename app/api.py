from __future__ import annotations

import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile

from app.flags.risk_flags import assess_risk
from app.llm.analyze import generate_narrative
from app.metrics.compute_metrics import compute_metrics
from app.parsing.csv_parser import parse_garmin_csv
from app.parsing.fit_parser import parse_garmin_fit
from app.storage.db import (
    connect,
    get_cached_narrative,
    get_or_create_user,
    get_runs,
    metrics_fingerprint,
    save_narrative,
    save_runs,
)

load_dotenv()
app = FastAPI(title = "Running Coach")

# Single user for now. Auth replaces this later; every query already
# filters on user_id, so the change is confined to this function
DEMO_EMAIL = "demo@example.com"

def get_db():
    """One connection per request, closed when the request finishes"""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()

def current_user_id(conn=Depends(get_db)) -> int:
    return get_or_create_user(conn, DEMO_EMAIL)


@app.post("/runs")
async def upload_runs(
    file: UploadFile = File(...),
    conn=Depends(get_db),
):
    """Accept a .fit or .csv upload, parse it, and store any new runs"""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".fit", ".csv"}:
        raise HTTPException(400, "Upload a .fit or .csv file")

    # The parsers read from disk, so buffer the upload to a temp file.
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        if suffix == ".fit":
            runs = parse_garmin_fit(str(tmp_path))
        else:
            runs = parse_garmin_csv(str(tmp_path))
    except Exception as exc:
        raise HTTPException(400, f"Could not parse file: {exc}")
    finally:
        tmp_path.unlink(missing_ok=True)

    if not runs:
        raise HTTPException(400, "No runs found in that file")

    user_id = get_or_create_user(conn, DEMO_EMAIL)
    inserted = save_runs(conn, user_id, runs)

    return {
        "parsed": len(runs),
        "inserted": inserted,
        "duplicates_skipped": len(runs) - inserted,
        "total_runs": len(get_runs(conn, user_id)),
    }


@app.get("/report")
def get_report(conn=Depends(get_db)):
    """Metrics and risk flags. Fast, deterministic, always current."""
    user_id = get_or_create_user(conn, DEMO_EMAIL)
    runs = get_runs(conn, user_id)

    if not runs:
        raise HTTPException(404, "No runs stored yet. Upload a file first.")

    metrics = compute_metrics(runs)
    risk = assess_risk(metrics)

    from dataclasses import asdict

    return {
        "metrics": asdict(metrics),
        "risk": asdict(risk),
        "has_narrative": get_cached_narrative(
            conn, user_id, metrics_fingerprint(metrics)
        )
        is not None,
    }


@app.post("/narrative")
def create_narrative(conn=Depends(get_db)):
    """LLM analysis. Cached against the metrics it describes."""
    user_id = get_or_create_user(conn, DEMO_EMAIL)
    runs = get_runs(conn, user_id)

    if not runs:
        raise HTTPException(404, "No runs stored yet. Upload a file first.")

    metrics = compute_metrics(runs)
    fingerprint = metrics_fingerprint(metrics)

    cached = get_cached_narrative(conn, user_id, fingerprint)
    if cached is not None:
        return {"narrative": cached, "cached": True}

    risk = assess_risk(metrics)
    narrative = generate_narrative(metrics, risk)
    save_narrative(conn, user_id, fingerprint, narrative)

    return {"narrative": narrative, "cached": False} 