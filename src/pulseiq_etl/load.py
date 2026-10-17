"""Load: write clean tables and rejected rows. Output is deterministic and replaces the old files."""
from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

from .config import SPECS, Settings
from .extract import sha256_file

log = logging.getLogger(__name__)


def write_audit(settings: Settings, results: dict) -> dict[str, str]:
    """Write <table>_rejected.csv and <table>_repaired.csv for every table (header-only when empty)."""
    settings.rejected_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, res in results.items():
        for suffix, df in (("rejected", res.rejected), ("repaired", res.repairs)):
            path = settings.rejected_dir / f"{name}_{suffix}.csv"
            tmp = path.with_suffix(".csv.tmp")
            df.to_csv(tmp, index=False)
            os.replace(tmp, path)
            paths[f"{name}_{suffix}"] = str(path)
    return paths


def write_clean(settings: Settings, clean: dict[str, pd.DataFrame]) -> dict[str, dict]:
    """Write every table to a temp file first, then swap them in. A failure leaves clean/ untouched."""
    settings.clean_dir.mkdir(parents=True, exist_ok=True)
    ext = settings.output_format
    staged: list[tuple[Path, Path]] = []
    try:
        for name, df in clean.items():
            out = df.sort_values(list(SPECS[name].sort), kind="mergesort").reset_index(drop=True)
            final = settings.clean_dir / f"{name}.{ext}"
            tmp = final.with_name(final.name + ".tmp")
            if ext == "parquet":
                out.to_parquet(tmp, index=False, engine="pyarrow", compression="snappy")
            else:
                out.to_csv(tmp, index=False, date_format="%Y-%m-%d")
            staged.append((tmp, final))
    except Exception:
        for tmp, _ in staged:
            tmp.unlink(missing_ok=True)
        raise

    result = {}
    for tmp, final in staged:
        os.replace(tmp, final)
        other = final.with_suffix(".csv" if ext == "parquet" else ".parquet")
        other.unlink(missing_ok=True)  # no stale copy in the other format
        name = final.stem
        result[name] = {"path": str(final), "rows": len(clean[name]), "sha256": sha256_file(final)}
    return result
