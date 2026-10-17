"""Load AI anomaly results from PulseIQ_Star_Schema_Dataset.xlsx into dw.fact_anomaly.

Safe to run repeatedly (idempotent upsert on result_id).
"""
import os
import sys
from pathlib import Path
import pandas as pd
import psycopg

RAW_DIR = Path(os.environ.get("RAW_DIR") or "data/raw")
WAREHOUSE_DSN = os.environ.get(
    "WAREHOUSE_DSN",
    "postgresql://pulseiq:pulseiq@localhost:5433/pulseiq"
)

def find_raw_excel(raw_dir: Path) -> Path:
    candidates = list(raw_dir.glob("PulseIQ_Star_Schema_Dataset*.xlsx"))
    if not candidates:
        candidates = [p for p in raw_dir.glob("*.xlsx") if not p.name.startswith("~$")]
    if not candidates:
        raise FileNotFoundError(f"No Excel dataset found in {raw_dir}")
    return candidates[0]

def load_anomalies(dsn: str, raw_dir: Path):
    excel_path = find_raw_excel(raw_dir)
    print(f"Reading fact_anomaly sheet from {excel_path.name}...")
    df = pd.read_excel(excel_path, sheet_name="fact_anomaly")
    
    # Rename columns to standard names
    df = df.rename(columns={"period": "period_date"})
    df["result_id"] = df["result_id"].astype(str).str.strip()
    df["source_dataset"] = df["source_dataset"].astype(str).str.strip()
    df["record_id"] = df["record_id"].astype(str).str.strip()
    df["employee_id"] = df["employee_id"].astype(str).str.strip()
    df["period_date"] = pd.to_datetime(df["period_date"]).dt.date
    df["period_key"] = df["period_key"].astype(int)
    df["anomaly_score"] = df["anomaly_score"].astype(float).round(4)
    df["flagged"] = df["flagged"].astype(str).str.strip().str.upper()
    df["reason_code"] = df["reason_code"].astype(str).str.strip()
    df["reason_text"] = df["reason_text"].astype(str).str.strip()
    df["money_at_risk"] = df["money_at_risk"].apply(lambda v: None if pd.isna(v) else round(float(v), 2))
    df["model_version"] = df["model_version"].astype(str).str.strip()
    df["scored_at"] = pd.to_datetime(df["scored_at"])

    total_rows = len(df)
    att_rows = len(df[df["source_dataset"] == "attendance_monthly_features"])
    pay_rows = len(df[df["source_dataset"] == "payroll_monthly_features"])
    print(f"Extracted {total_rows} anomaly rows ({att_rows} attendance, {pay_rows} payroll)")

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            # Create staging table
            cur.execute("""
                CREATE TEMP TABLE stg_fact_anomaly (
                    result_id       text,
                    source_dataset  text,
                    record_id       text,
                    employee_id     text,
                    period_date     date,
                    period_key      integer,
                    anomaly_score   numeric(6,4),
                    flagged         text,
                    reason_code     text,
                    reason_text     text,
                    money_at_risk   numeric(14,2),
                    model_version   text,
                    scored_at       timestamp
                ) ON COMMIT DROP;
            """)

            with cur.copy("""
                COPY stg_fact_anomaly (
                    result_id, source_dataset, record_id, employee_id,
                    period_date, period_key, anomaly_score, flagged,
                    reason_code, reason_text, money_at_risk, model_version, scored_at
                ) FROM STDIN
            """) as copy:
                for row in df.itertuples(index=False):
                    copy.write_row((
                        row.result_id,
                        row.source_dataset,
                        row.record_id,
                        row.employee_id,
                        row.period_date,
                        row.period_key,
                        row.anomaly_score,
                        row.flagged,
                        row.reason_code,
                        row.reason_text,
                        row.money_at_risk,
                        row.model_version,
                        row.scored_at
                    ))

            # Upsert into dw.fact_anomaly
            cur.execute("""
                WITH up AS (
                    INSERT INTO dw.fact_anomaly (
                        result_id, source_dataset, record_id, employee_id,
                        period_date, period_key, anomaly_score, flagged,
                        reason_code, reason_text, money_at_risk, model_version, scored_at
                    )
                    SELECT 
                        result_id, source_dataset, record_id, employee_id,
                        period_date, period_key, anomaly_score, flagged,
                        reason_code, reason_text, money_at_risk, model_version, scored_at
                    FROM stg_fact_anomaly
                    ON CONFLICT (result_id) DO UPDATE SET
                        source_dataset = EXCLUDED.source_dataset,
                        record_id = EXCLUDED.record_id,
                        employee_id = EXCLUDED.employee_id,
                        period_date = EXCLUDED.period_date,
                        period_key = EXCLUDED.period_key,
                        anomaly_score = EXCLUDED.anomaly_score,
                        flagged = EXCLUDED.flagged,
                        reason_code = EXCLUDED.reason_code,
                        reason_text = EXCLUDED.reason_text,
                        money_at_risk = EXCLUDED.money_at_risk,
                        model_version = EXCLUDED.model_version,
                        scored_at = EXCLUDED.scored_at
                    RETURNING (xmax = 0) AS inserted
                )
                SELECT 
                    count(*) FILTER (WHERE inserted) AS inserted,
                    count(*) FILTER (WHERE NOT inserted) AS updated
                FROM up;
            """)
            inserted, updated = cur.fetchone()

            cur.execute("SELECT count(*) FROM dw.fact_anomaly;")
            n_wh = cur.fetchone()[0]
            cur.execute("ANALYZE dw.fact_anomaly;")

        conn.commit()

    print(f"Loaded dw.fact_anomaly: inserted={inserted}, updated={updated}, unchanged={total_rows - inserted - updated}, total_in_wh={n_wh}")
    return {"inserted": inserted, "updated": updated, "total": n_wh}

if __name__ == "__main__":
    load_anomalies(WAREHOUSE_DSN, RAW_DIR)
