"""Load the clean tables into the PostgreSQL star schema with upserts.

How a load works, all in ONE transaction (any error rolls everything back):
  1. Run sql/001_schema.sql (does nothing if the tables already exist).
  2. Copy each clean table into a temporary staging table.
  3. For each file in sql/load/ (dimensions first, then facts, then the derived headcount fact):
       a. run its SELECT into a temporary table, which resolves keys,
       b. stop if the SELECT lost rows (a fact pointing at a missing dimension row),
       c. delete warehouse rows that are no longer in the feed (only when 'mirror: true'),
       d. INSERT ... ON CONFLICT (key) DO UPDATE, changing only rows whose values differ,
       e. check every feed row is now in the warehouse.
Running the same load twice therefore inserts, updates and deletes nothing.
"""
from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path

import pandas as pd
import psycopg

from .errors import WarehouseError

log = logging.getLogger(__name__)

SQL_DIR = Path(os.environ.get("SQL_DIR") or Path(__file__).resolve().parents[2] / "sql")
HEADER = re.compile(r"^--\s*(target|key|stage|mirror):\s*(.+?)\s*$", re.M)


def _pg_type(dtype) -> str:
    if pd.api.types.is_bool_dtype(dtype):
        return "boolean"
    if pd.api.types.is_integer_dtype(dtype):
        return "bigint"
    if pd.api.types.is_float_dtype(dtype):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "date"
    return "text"


def _connect(dsn: str, attempts: int = 15) -> psycopg.Connection:
    last = None
    for _ in range(attempts):
        try:
            return psycopg.connect(dsn, connect_timeout=5)
        except psycopg.OperationalError as exc:  # the database may still be starting
            last = exc
            time.sleep(2)
    raise WarehouseError(f"Cannot connect to the warehouse: {last}")


def _stage(cur, name: str, df: pd.DataFrame) -> None:
    cols = ", ".join(f'"{c}" {_pg_type(t)}' for c, t in df.dtypes.items())
    cur.execute(f"CREATE TEMP TABLE stg_{name} ({cols}) ON COMMIT DROP")
    names = ", ".join(f'"{c}"' for c in df.columns)
    csv = df.to_csv(index=False, header=False, na_rep="", date_format="%Y-%m-%d")
    with cur.copy(f"COPY stg_{name} ({names}) FROM STDIN WITH (FORMAT csv, NULL '')") as copy:
        copy.write(csv)


def _read_load_file(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    meta = {k: v for k, v in HEADER.findall(text)}
    if "target" not in meta or "key" not in meta:
        raise WarehouseError(f"{path.name}: needs '-- target:' and '-- key:' header lines")
    meta["keys"] = [k.strip() for k in meta["key"].split(",")]
    meta["mirror"] = meta.get("mirror", "false").lower() == "true"
    return meta, text.strip().rstrip(";")


def _load_table(cur, path: Path) -> tuple[str, dict]:
    meta, select_sql = _read_load_file(path)
    target, keys = meta["target"], meta["keys"]
    short = target.split(".")[-1]
    src = f"src_{short}"
    t0 = time.monotonic()

    cur.execute(f"CREATE TEMP TABLE {src} ON COMMIT DROP AS {select_sql}")
    cur.execute(f"SELECT count(*) FROM {src}")
    n_src = cur.fetchone()[0]
    if "stage" in meta:
        cur.execute(f"SELECT count(*) FROM {meta['stage']}")
        n_stage = cur.fetchone()[0]
        if n_stage != n_src:
            raise WarehouseError(
                f"{target}: {n_stage - n_src} of {n_stage} rows were lost while looking up dimension keys. "
                f"A row points at a date, employee version, department, role or leave type that is not in the warehouse.")

    cur.execute(f"SELECT * FROM {src} LIMIT 0")
    cols = [c.name for c in cur.description]
    nonkey = [c for c in cols if c not in keys]
    same_key = " AND ".join(f's."{k}" = t."{k}"' for k in keys)

    deleted = 0
    if meta["mirror"]:
        cur.execute(f"DELETE FROM {target} t WHERE NOT EXISTS (SELECT 1 FROM {src} s WHERE {same_key})")
        deleted = cur.rowcount

    col_list = ", ".join(f'"{c}"' for c in cols)
    key_list = ", ".join(f'"{k}"' for k in keys)
    set_list = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in nonkey)
    old = ", ".join(f't."{c}"' for c in nonkey)
    new = ", ".join(f'EXCLUDED."{c}"' for c in nonkey)
    cur.execute(f"""
        WITH up AS (
            INSERT INTO {target} AS t ({col_list})
            SELECT {col_list} FROM {src}
            ON CONFLICT ({key_list}) DO UPDATE SET {set_list}
            WHERE ({old}) IS DISTINCT FROM ({new})
            RETURNING (xmax = 0) AS inserted)
        SELECT count(*) FILTER (WHERE inserted), count(*) FILTER (WHERE NOT inserted) FROM up""")
    inserted, updated = cur.fetchone()

    cur.execute(f"SELECT count(*) FROM {src} s WHERE NOT EXISTS (SELECT 1 FROM {target} t WHERE {same_key})")
    missing = cur.fetchone()[0]
    cur.execute(f"SELECT count(*) FROM {target}")
    n_wh = cur.fetchone()[0]
    if missing or (meta["mirror"] and n_wh != n_src):
        raise WarehouseError(f"{target}: after the load {missing} feed rows are missing and the table holds {n_wh} rows for {n_src} in the feed")
    cur.execute(f"DROP TABLE {src}")

    stats = {"rows_in_feed": n_src, "inserted": inserted, "updated": updated,
             "unchanged": n_src - inserted - updated, "deleted": deleted, "rows_in_warehouse": n_wh,
             "seconds": round(time.monotonic() - t0, 2)}
    log.info("Warehouse %-26s feed=%-6d inserted=%-6d updated=%-5d unchanged=%-6d deleted=%-4d",
             short, n_src, inserted, updated, stats["unchanged"], deleted)
    return short, stats


def load_warehouse(clean: dict[str, pd.DataFrame], dsn: str) -> dict:
    """Load all clean tables. Returns per-table stats. Raises WarehouseError and rolls back on any problem."""
    files = sorted((SQL_DIR / "load").glob("*.sql"))
    if not files:
        raise WarehouseError(f"No load files found in {SQL_DIR / 'load'}")
    stats: dict = {}
    try:
        with _connect(dsn) as conn, conn.cursor() as cur:
            cur.execute((SQL_DIR / "001_schema.sql").read_text())
            for name, df in clean.items():
                _stage(cur, name, df)
            for path in files:
                short, table_stats = _load_table(cur, path)
                stats[short] = table_stats
            for short in stats:
                cur.execute(f"ANALYZE dw.{short}")
    except WarehouseError:
        raise
    except psycopg.Error as exc:
        raise WarehouseError(f"Warehouse load failed and was rolled back: {exc}") from exc
    return stats
