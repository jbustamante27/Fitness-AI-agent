# Main backend file for Running Coach MVP
from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
from fitparse import FitFile
import io
from pathlib import Path
import uuid

# Define FastAPI instance
app = FastAPI(title="Running Coach MVP")

# Ensure storage folders exist
DATA_DIR = Path("data")
UPLOADS_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Schema: Summary of each run
run_summary_columns = [
    "run_id", "user_id", "start_time", "duration_min", "distance_miles", 
    "avg_hr", "max_hr", "device_name"
]
run_summary_df = pd.DataFrame(columns = run_summary_columns)

# Schema: per-record data
record_columns = [
    "run_id", "timestamp", "heart_rate", "distance_miles",
    "speed", "cadence", "elevation"
]
run_records_df = pd.DataFrame(columns = record_columns)

@app.get("/")
def root():
    return {"message": "running agent backend online"}

@app.post("/upload_run")
async def upload_run(file: UploadFile = File(...), user_id: str = "demo_user"):
    """
    Accept a .FIT file upload, parse record messages into a DataFrame, save both
    summary and record tables as Parquet, and return a small JSON summary.
    """
    contents = await file.read()

    # Keep an original copy
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    upload_path = UPLOADS_DIR / unique_name
    upload_path.write_bytes(contents)

    # Parse FIT file from bytes
    fitfile = FitFile(io.BytesIO(contents))

    # Extract record messages
    records = []
    for record in fitfile.get_messages("record"):
        row = {}
        for data in record:
            row[data.name] = data.value
        if row:
            records.append(row)

    if not records:
        raise HTTPException(status_code=400, detail="No 'record' messages found in FIT file")
    
    # Convert to DataFrame
    df = pd.DataFrame(records)

    # Ensure timestamp column is parsed
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

    # Convert distance to miles
    if "distance" in df.columns:
        df["distance_miles"] = df["distance"] * 0.000621371
    else:
        df["distance_miles"] = None

    # --- Build record table ---
    global run_records_df
    df_records = pd.DataFrame({
        "run_id": unique_name,
        "timestamp": df["timestamp"] if "timestamp" in df.columns else None,
        "heart_rate": df["heart_rate"] if "heart_rate" in df.columns else None,
        "distance_miles": df["distance_miles"],
        "speed": df["speed"] if "speed" in df.columns else None,
        "cadence": df["cadence"] if "cadence" in df.columns else None,
        "elevation": df["enhanced_altitude"] if "enhanced_altitude" in df.columns else None
    })
    run_records_df = pd.concat([run_records_df, df_records], ignore_index=True)

    # --- Build summary table ---
    global run_summary_df
    summary_row = {
        "run_id": unique_name,
        "user_id": user_id,
        "start_time": df["timestamp"].iloc[0] if "timestamp" in df.columns else None,
        "duration_min": (df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).total_seconds()/60
                        if "timestamp" in df.columns else None,
        "distance_miles": df["distance_miles"].max() if "distance_miles" in df.columns else None,
        "avg_hr": float(df["heart_rate"].mean()) if "heart_rate" in df.columns else None,
        "max_hr": int(df["heart_rate"].max()) if "heart_rate" in df.columns else None,
        "device_name": None
    }

    # Try to get device name if available
    device_info_messages = list(fitfile.get_messages("device_info"))
    if device_info_messages:
        summary_row["device_name"] = device_info_messages[0].get_value("manufacturer")

    run_summary_df = pd.concat([run_summary_df, pd.DataFrame([summary_row])], ignore_index=True)

    # --- Save tables ---
    run_summary_df.to_parquet(PROCESSED_DIR / "run_summary.parquet", index=False)
    run_records_df.to_parquet(PROCESSED_DIR / "run_records.parquet", index=False)

    # --- Return JSON summary ---
    return summary_row
