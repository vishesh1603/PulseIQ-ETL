"""Extract: read each table from <table>.csv, or from a sheet of any .xlsx in RAW_DIR."""
from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

import pandas as pd

from .config import RECONCILIATION_SHEET, SPECS, TABLE_ORDER, Settings
from .errors import ExtractError

log = logging.getLogger(__name__)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _snake(name: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip().lower()).strip("_")


class Source:
    """Finds a table either as a CSV or as a sheet in an Excel workbook."""

    def __init__(self, raw_dir: Path):
        self.raw_dir = raw_dir
        self._books = {p: pd.ExcelFile(p) for p in sorted(raw_dir.glob("*.xlsx")) if not p.name.startswith("~$")}
        self._hashes: dict[Path, str] = {}

    def _hash(self, path: Path) -> str:
        if path not in self._hashes:
            self._hashes[path] = sha256_file(path)
        return self._hashes[path]

    def has(self, table: str) -> bool:
        return (self.raw_dir / f"{table}.csv").exists() or any(table in b.sheet_names for b in self._books.values())

    def read(self, table: str) -> tuple[pd.DataFrame, dict]:
        csv = self.raw_dir / f"{table}.csv"
        if csv.exists():
            df = pd.read_csv(csv, dtype=str, keep_default_na=False, encoding="utf-8-sig")
            return df, {"file": csv.name, "sha256": self._hash(csv)}
        for path, book in self._books.items():
            if table in book.sheet_names:
                df = book.parse(table, dtype=str, keep_default_na=False)
                return df, {"file": f"{path.name}#{table}", "sha256": self._hash(path)}
        raise ExtractError(f"Missing input for '{table}': expected {self.raw_dir}/{table}.csv "
                           f"or a sheet named '{table}' in an .xlsx file in {self.raw_dir}")


def extract(settings: Settings):
    """Return (frames, file_info, source). Stops if a table or a required column is missing."""
    source = Source(settings.raw_dir)
    frames: dict[str, pd.DataFrame] = {}
    info: dict[str, dict] = {}
    for table in TABLE_ORDER:
        spec = SPECS[table]
        df, meta = source.read(table)
        df.columns = [_snake(c) for c in df.columns]
        missing = [c for c in spec.required if c not in df.columns]
        if missing:
            raise ExtractError(f"{meta['file']}: missing required column(s) {missing}. Found: {list(df.columns)}")
        extra = [c for c in df.columns if c not in spec.cols]
        if extra:
            log.warning("%s: ignoring unexpected column(s) %s", table, extra)
        df = df[[c for c in spec.cols if c in df.columns]].copy()
        # Line number in the original file (header is line 1). Used in the rejected-rows file.
        df.insert(0, "source_row", range(2, len(df) + 2))
        frames[table] = df
        info[table] = {**meta, "rows": len(df)}
        log.info("Extracted %-24s %6d rows from %s", table, len(df), meta["file"])
    return frames, info, source
