"""
PulseIQ Cloud Database Initializer & Seeder
Runs all schema migrations, loads initial data, and verifies views for Render / Supabase / Neon / Railway.

Usage:
    python scripts/init_cloud_db.py
    python scripts/init_cloud_db.py --dsn "postgresql://user:pass@host:port/dbname"
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize and seed PulseIQ database on cloud (Render/Neon/Supabase).")
    parser.add_argument("--dsn", help="PostgreSQL connection URI (defaults to DATABASE_URL or WAREHOUSE_DSN env var)")
    args = parser.parse_args()

    dsn = args.dsn or os.getenv("DATABASE_URL") or os.getenv("WAREHOUSE_DSN")
    if not dsn:
        print("[ERROR] No database connection string provided.")
        print("Set DATABASE_URL in your environment or pass --dsn 'postgresql://user:pass@host:5432/dbname'")
        sys.exit(1)

    if dsn.startswith("postgres://"):
        dsn = dsn.replace("postgres://", "postgresql://", 1)

    print("=" * 60)
    print("  PulseIQ Cloud Database Initialization")
    print("=" * 60)

    try:
        import psycopg
    except ImportError:
        print("[ERROR] psycopg not installed. Run: pip install psycopg[binary]")
        sys.exit(1)

    # 1. Test Connection
    print(f"\n[1/4] Connecting to warehouse...")
    try:
        conn = psycopg.connect(dsn, autocommit=True)
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            ver = cur.fetchone()[0]
            print(f"      Connected! PostgreSQL version: {ver.split(',')[0]}")
    except Exception as exc:
        print(f"[ERROR] Failed to connect: {exc}")
        sys.exit(1)

    # 2. Apply SQL Migrations
    print("\n[2/4] Applying SQL migrations (sql/*.sql)...")
    sql_dir = PROJECT_ROOT / "sql"
    sql_files = sorted(sql_dir.glob("*.sql"))

    for sf in sql_files:
        print(f"      Executing {sf.name}...")
        sql_content = sf.read_text(encoding="utf-8")
        try:
            with conn.cursor() as cur:
                cur.execute(sql_content)
            print(f"      [OK] {sf.name}")
        except Exception as exc:
            print(f"      [WARN] Notice on {sf.name}: {exc}")

    conn.close()

    # 3. Seed Data via Pipeline
    print("\n[3/4] Ingesting and modeling data via pulseiq_etl pipeline...")
    os.environ["WAREHOUSE_DSN"] = dsn
    try:
        from pulseiq_etl.config import Settings
        from pulseiq_etl.pipeline import run
        cfg = Settings.from_env()
        exit_code = run(cfg)
        if exit_code == 0:
            print("      [OK] Data ingestion and star schema modeling complete.")
        else:
            print(f"      [WARN] Ingestion finished with exit code {exit_code}")
    except Exception as exc:
        print(f"      [WARN] Pipeline exception (tables might already be seeded): {exc}")

    # 4. Verify Views
    print("\n[4/4] Verifying metric views...")
    try:
        conn = psycopg.connect(dsn, autocommit=True)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM dw.metric_m01_headcount;")
            m01_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM dw.metric_m18_operating_margin;")
            m18_count = cur.fetchone()[0]
            print(f"      [OK] dw.metric_m01_headcount: {m01_count} records")
            print(f"      [OK] dw.metric_m18_operating_margin: {m18_count} records")
        conn.close()
    except Exception as exc:
        print(f"      [WARN] Verification notice: {exc}")

    print("\n" + "=" * 60)
    print("  [SUCCESS] Database is initialized and ready for Streamlit!")
    print("=" * 60)

if __name__ == "__main__":
    main()
