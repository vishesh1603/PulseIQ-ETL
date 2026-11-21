"""
PulseIQ ETL Scheduler
=====================
Runs the full ETL pipeline on a daily schedule (default 02:00 AM local time).
Usage:
    python scripts/scheduler.py              # run on schedule (daemon mode)
    python scripts/scheduler.py --run-now    # run immediately and exit
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so we can import the ETL package
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "scheduler.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("pulseiq.scheduler")

# ---------------------------------------------------------------------------
# Schedule time (24-hour, local time)
# ---------------------------------------------------------------------------
SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", "2"))
SCHEDULE_MINUTE = int(os.getenv("SCHEDULE_MINUTE", "0"))


def _write_heartbeat(status: str, message: str = "") -> None:
    """Append a one-line JSON heartbeat to logs/scheduler.log."""
    import json
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "message": message,
    }
    with open(LOG_DIR / "scheduler.log", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def run_etl() -> bool:
    """
    Execute the full PulseIQ ETL pipeline.
    Returns True on SUCCESS, False on FAILED.
    """
    log.info("=" * 60)
    log.info("PulseIQ Scheduler — starting ETL run at %s",
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    _write_heartbeat("RUNNING", "ETL pipeline started")

    try:
        from pulseiq_etl.config import Settings
        from pulseiq_etl.pipeline import run as etl_run

        settings = Settings()
        exit_code = etl_run(settings)

        if exit_code == 0:
            log.info("ETL run SUCCEEDED")
            _write_heartbeat("SUCCESS", "ETL pipeline completed successfully")
            return True
        else:
            log.error("ETL run FAILED with exit code %d", exit_code)
            _write_heartbeat("FAILED", f"ETL pipeline exited with code {exit_code}")
            _notify_failure(f"ETL pipeline exited with code {exit_code}")
            return False

    except Exception as exc:
        log.exception("ETL run CRASHED: %s", exc)
        _write_heartbeat("FAILED", f"ETL crashed: {exc}")
        _notify_failure(str(exc))
        return False


def run_alerting() -> None:
    """Run KPI alerting checks after a successful ETL run."""
    try:
        alerting_path = PROJECT_ROOT / "scripts" / "alerting.py"
        if not alerting_path.exists():
            log.warning("alerting.py not found — skipping KPI alert checks")
            return
        # Import and run alerting module
        import importlib.util
        spec = importlib.util.spec_from_file_location("alerting", alerting_path)
        alerting_mod = importlib.util.load_module_from_spec(spec)  # type: ignore[attr-defined]
        spec.loader.exec_module(alerting_mod)  # type: ignore[union-attr]
        alerting_mod.run_all_kpi_checks()
        log.info("KPI alerting checks completed")
    except Exception as exc:
        log.error("KPI alerting checks failed: %s", exc)


def _notify_failure(error_msg: str) -> None:
    """
    Deliver a failure notification.
    Respects ALERT_CHANNEL env var: 'webhook', 'email', or 'log' (default).
    """
    channel = os.getenv("ALERT_CHANNEL", "log").lower()

    if channel == "webhook":
        webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")
        if webhook_url:
            try:
                import urllib.request, json
                payload = json.dumps({
                    "text": f"🚨 *PulseIQ ETL FAILED*\nError: {error_msg}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }).encode()
                req = urllib.request.Request(webhook_url, data=payload,
                                            headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=10)
                log.info("Failure webhook delivered to %s", webhook_url)
            except Exception as exc:
                log.error("Failed to deliver webhook: %s", exc)
        else:
            log.warning("ALERT_CHANNEL=webhook but ALERT_WEBHOOK_URL is not set")

    elif channel == "email":
        import smtplib
        from email.message import EmailMessage
        try:
            msg = EmailMessage()
            msg["Subject"] = "🚨 PulseIQ ETL Pipeline FAILED"
            msg["From"] = os.getenv("ALERT_EMAIL_FROM", "pulseiq@localhost")
            msg["To"] = os.getenv("ALERT_EMAIL_TO", "")
            msg.set_content(f"PulseIQ ETL run FAILED at {datetime.now()}.\n\nError: {error_msg}")
            with smtplib.SMTP(os.getenv("SMTP_HOST", "localhost"),
                              int(os.getenv("SMTP_PORT", "25"))) as smtp:
                smtp.send_message(msg)
            log.info("Failure email sent to %s", msg["To"])
        except Exception as exc:
            log.error("Failed to send failure email: %s", exc)

    else:
        # Default: write to alerts.log
        with open(LOG_DIR / "alerts.log", "a", encoding="utf-8") as fh:
            fh.write(
                f"{datetime.now(timezone.utc).isoformat()} [SCHEDULER] ETL_FAILED — {error_msg}\n"
            )
        log.info("Failure alert written to logs/alerts.log")


def _time_until_next_run() -> float:
    """Return seconds until the next scheduled run."""
    now = datetime.now()
    next_run = now.replace(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE,
                           second=0, microsecond=0)
    if next_run <= now:
        from datetime import timedelta
        next_run += timedelta(days=1)
    return (next_run - now).total_seconds()


def main() -> None:
    parser = argparse.ArgumentParser(description="PulseIQ ETL Scheduler")
    parser.add_argument(
        "--run-now", action="store_true",
        help="Run the ETL pipeline immediately and exit (no scheduling)."
    )
    args = parser.parse_args()

    if args.run_now:
        log.info("--run-now flag detected. Running ETL immediately.")
        success = run_etl()
        if success:
            run_alerting()
        sys.exit(0 if success else 1)

    # Daemon mode: run on a daily schedule
    log.info(
        "PulseIQ Scheduler started. Daily ETL scheduled at %02d:%02d local time.",
        SCHEDULE_HOUR, SCHEDULE_MINUTE
    )
    _write_heartbeat("STARTED", f"Scheduler daemon started. Daily run at {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}")

    while True:
        wait_seconds = _time_until_next_run()
        next_run_str = datetime.now().replace(
            hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE, second=0, microsecond=0
        ).strftime("%Y-%m-%d %H:%M:%S")
        log.info("Next ETL run scheduled at %s (%.0f seconds)", next_run_str, wait_seconds)

        time.sleep(wait_seconds)

        success = run_etl()
        if success:
            run_alerting()

        # Small sleep to avoid running twice at the boundary
        time.sleep(60)


if __name__ == "__main__":
    main()
