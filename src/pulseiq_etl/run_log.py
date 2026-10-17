"""Run log: one JSON line per run in logs/run_log.jsonl, plus logs/last_run.json."""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RunLog:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        self._t0 = time.monotonic()
        started = utcnow()
        self.data: dict = {
            "run_id": started.strftime("%Y%m%dT%H%M%SZ"),
            "started_at": started.isoformat(timespec="seconds"),
            "status": "RUNNING",
            "tables": {},
        }

    def __setitem__(self, key, value):
        self.data[key] = value

    def previous_success(self) -> dict | None:
        path = self.log_dir / "run_log.jsonl"
        if not path.exists():
            return None
        last = None
        for line in path.read_text().splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("status") == "SUCCESS":
                last = entry
        return last

    def finish(self, status: str, error: str | None = None) -> None:
        self.data["status"] = status
        self.data["finished_at"] = utcnow().isoformat(timespec="seconds")
        self.data["duration_seconds"] = round(time.monotonic() - self._t0, 2)
        if error:
            self.data["error"] = error
        line = json.dumps(self.data, sort_keys=True, default=str)
        with open(self.log_dir / "run_log.jsonl", "a") as fh:
            fh.write(line + "\n")
        (self.log_dir / "last_run.json").write_text(json.dumps(self.data, indent=2, sort_keys=True, default=str))


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s %(levelname)-7s %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[logging.StreamHandler(), logging.FileHandler(log_dir / "etl.log")],
        force=True,
    )
