"""
PulseIQ Phase 4 — Task 18: KPI Alerting Engine
===============================================
Checks all metric views against dw.kpi_targets and fires alerts for breaches.

ALERT_CHANNEL env var controls delivery:
  log     (default) → logs/alerts.log  (always also written)
  webhook → HTTP POST to ALERT_WEBHOOK_URL
  email   → SMTP to ALERT_EMAIL_TO

Usage:
    python scripts/alerting.py              # run all checks
    python scripts/alerting.py --dry-run    # check without writing to DB
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "alerts.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("pulseiq.alerting")

# ---------------------------------------------------------------------------
# Default PostgreSQL connection
# ---------------------------------------------------------------------------
PG_CONN = os.getenv(
    "WAREHOUSE_DSN",
    "postgresql://pulseiq:pulseiq@localhost:5433/pulseiq"
)

# ---------------------------------------------------------------------------
# KPI Alert Rules
# Each rule defines:
#   metric_code, metric_name, sql (returns: year_month, value),
#   target_expr (Python lambda), severity, target_label, dashboard_url
# ---------------------------------------------------------------------------
ALERT_RULES: list[dict[str, Any]] = [
    {
        "metric_code": "M01",
        "metric_name": "Total Headcount",
        "sql": """
            SELECT year_month::text, SUM(unsuppressed_headcount) AS value
            FROM dw.metric_m01_headcount
            GROUP BY year_month
            ORDER BY year_month DESC LIMIT 1
        """,
        "breach": lambda v: v < 400,
        "severity": "WARNING",
        "target_label": ">=400 employees",
        "dashboard_url": "http://localhost:8501/",
    },
    {
        "metric_code": "M04",
        "metric_name": "Monthly Attrition Rate",
        "sql": """
            SELECT year_month::text,
                   AVG(unsuppressed_attrition_pct) AS value
            FROM dw.metric_m04_attrition_rate_monthly
            GROUP BY year_month
            ORDER BY year_month DESC LIMIT 1
        """,
        "breach": lambda v: v > 3.0,
        "severity": "WARNING",
        "target_label": "<=3.0% per month",
        "dashboard_url": "http://localhost:8501/Attrition_Analytics",
    },
    {
        "metric_code": "M05",
        "metric_name": "12-Month Attrition Rate",
        "sql": """
            SELECT year_month::text,
                   AVG(unsuppressed_attrition_12m_pct) AS value
            FROM dw.metric_m05_attrition_rate_12m
            GROUP BY year_month
            ORDER BY year_month DESC LIMIT 1
        """,
        "breach": lambda v: v > 12.0,
        "severity": "CRITICAL",
        "target_label": "<=12.0%",
        "dashboard_url": "http://localhost:8501/Attrition_Analytics",
    },
    {
        "metric_code": "M13",
        "metric_name": "Attendance Rate",
        "sql": """
            SELECT year_month::text,
                   AVG(unsuppressed_attendance_rate) AS value
            FROM dw.metric_m13_attendance_rate
            GROUP BY year_month
            ORDER BY year_month DESC LIMIT 1
        """,
        "breach": lambda v: v < 0.90,
        "severity": "WARNING",
        "target_label": ">=90%",
        "dashboard_url": "http://localhost:8501/Attendance_and_Leave",
    },
    {
        "metric_code": "M17",
        "metric_name": "Net Profit",
        "sql": """
            SELECT year_month::text, net_profit AS value
            FROM dw.metric_m17_net_profit
            ORDER BY year_month DESC LIMIT 1
        """,
        "breach": lambda v: v < 0,
        "severity": "CRITICAL",
        "target_label": ">= ₹0 (must be profitable)",
        "dashboard_url": "http://localhost:8501/Profit_and_Loss",
    },
    {
        "metric_code": "M18",
        "metric_name": "Operating Margin",
        "sql": """
            SELECT year_month::text, operating_margin_pct AS value
            FROM dw.metric_m18_operating_margin
            ORDER BY year_month DESC LIMIT 1
        """,
        "breach": lambda v: v < 10.0,
        "severity": "CRITICAL",
        "target_label": ">=10%",
        "dashboard_url": "http://localhost:8501/Profit_and_Loss",
    },
    {
        "metric_code": "M20",
        "metric_name": "Days Sales Outstanding (DSO)",
        "sql": """
            SELECT year_month::text, dso_days AS value
            FROM dw.metric_m20_dso
            WHERE dso_days IS NOT NULL
            ORDER BY year_month DESC LIMIT 1
        """,
        "breach": lambda v: v > 60,
        "severity": "WARNING",
        "target_label": "<=60 days",
        "dashboard_url": "http://localhost:8501/Invoices_and_Cash_Flow",
    },
    {
        "metric_code": "M22",
        "metric_name": "Task Completion Rate",
        "sql": """
            SELECT sprint_id::text,
                   AVG(unsuppressed_completion_rate) AS value
            FROM dw.metric_m22_task_completion_rate
            GROUP BY sprint_id
            ORDER BY sprint_id DESC LIMIT 1
        """,
        "breach": lambda v: v < 70.0,
        "severity": "WARNING",
        "target_label": ">=70%",
        "dashboard_url": "http://localhost:8501/Team_Productivity",
    },
]


def _get_last_run_id() -> str:
    """Read the run_id from logs/last_run.json if available."""
    last_run_path = LOG_DIR / "last_run.json"
    if last_run_path.exists():
        try:
            data = json.loads(last_run_path.read_text(encoding="utf-8"))
            return data.get("run_id", "MANUAL")
        except Exception:
            pass
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _deliver_alert(alert: dict[str, Any], channel: str, dry_run: bool) -> None:
    """Write alert to logs/alerts.log and optionally to external channel."""
    line = (
        f"[{alert['severity']}] {alert['metric_code']} — {alert['metric_name']} "
        f"= {alert['current_value']:.2f} (target: {alert['target_label']}) "
        f"month={alert['breach_month']}"
    )
    log.warning("ALERT %s", line)

    with open(LOG_DIR / "alerts.log", "a", encoding="utf-8") as fh:
        fh.write(
            f"{datetime.now(timezone.utc).isoformat()}  {line}\n"
        )

    if dry_run:
        return

    if channel == "webhook":
        webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")
        if webhook_url:
            import urllib.request
            payload = json.dumps(alert, default=str).encode()
            req = urllib.request.Request(
                webhook_url, data=payload,
                headers={"Content-Type": "application/json"}
            )
            try:
                urllib.request.urlopen(req, timeout=10)
            except Exception as exc:
                log.error("Webhook delivery failed: %s", exc)

    elif channel == "email":
        import smtplib
        from email.message import EmailMessage
        try:
            msg = EmailMessage()
            msg["Subject"] = f"🚨 PulseIQ Alert: {alert['metric_code']} breach"
            msg["From"] = os.getenv("ALERT_EMAIL_FROM", "pulseiq@localhost")
            msg["To"] = os.getenv("ALERT_EMAIL_TO", "admin@localhost")
            msg.set_content(
                f"KPI Breach Detected\n\n"
                f"Metric:  {alert['metric_name']} ({alert['metric_code']})\n"
                f"Value:   {alert['current_value']:.2f}\n"
                f"Target:  {alert['target_label']}\n"
                f"Month:   {alert['breach_month']}\n"
                f"Dashboard: {alert['dashboard_url']}\n"
            )
            with smtplib.SMTP(
                os.getenv("SMTP_HOST", "localhost"),
                int(os.getenv("SMTP_PORT", "25"))
            ) as smtp:
                smtp.send_message(msg)
        except Exception as exc:
            log.error("Email delivery failed: %s", exc)


def _persist_alert(cur, alert: dict[str, Any], run_id: str) -> None:
    """Insert alert into dw.alert_log."""
    cur.execute(
        """
        INSERT INTO dw.alert_log
            (run_id, metric_code, metric_name, current_value, target_value,
             severity, breach_month, channel_used, delivered, dashboard_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            run_id,
            alert["metric_code"],
            alert["metric_name"],
            alert["current_value"],
            alert["target_label"],
            alert["severity"],
            alert["breach_month"],
            alert["channel_used"],
            True,
            alert["dashboard_url"],
        ),
    )


def run_all_kpi_checks(dry_run: bool = False) -> list[dict[str, Any]]:
    """
    Run all KPI alert rules. Returns a list of triggered alerts.
    """
    import psycopg

    channel = os.getenv("ALERT_CHANNEL", "log").lower()
    run_id = _get_last_run_id()
    triggered: list[dict[str, Any]] = []

    log.info("Starting KPI alert checks (channel=%s, dry_run=%s)", channel, dry_run)

    try:
        conn = psycopg.connect(PG_CONN)
    except Exception as exc:
        log.error("Cannot connect to warehouse: %s", exc)
        return []

    with conn:
        with conn.cursor() as cur:
            # Ensure alert_log table exists
            try:
                cur.execute(
                    "SELECT to_regclass('dw.alert_log')"
                )
                if cur.fetchone()[0] is None:
                    log.warning("dw.alert_log does not exist — run sql/008_alert_log.sql first")
            except Exception:
                pass

            for rule in ALERT_RULES:
                try:
                    cur.execute(rule["sql"])
                    row = cur.fetchone()
                    if row is None:
                        log.warning("%s — no data returned, skipping", rule["metric_code"])
                        continue
                    breach_month, value = row[0], float(row[1]) if row[1] is not None else None
                    if value is None:
                        continue

                    if rule["breach"](value):
                        alert = {
                            "metric_code": rule["metric_code"],
                            "metric_name": rule["metric_name"],
                            "current_value": value,
                            "target_label": rule["target_label"],
                            "severity": rule["severity"],
                            "breach_month": breach_month,
                            "channel_used": channel,
                            "dashboard_url": rule["dashboard_url"],
                        }
                        triggered.append(alert)
                        _deliver_alert(alert, channel, dry_run)
                        if not dry_run:
                            try:
                                _persist_alert(cur, alert, run_id)
                            except Exception as exc:
                                log.warning("Could not persist alert to DB: %s", exc)
                    else:
                        log.info(
                            "%s OK: %.2f (target: %s)",
                            rule["metric_code"], value, rule["target_label"]
                        )

                except Exception as exc:
                    log.error("Error checking %s: %s", rule["metric_code"], exc)

    conn.close()

    if triggered:
        log.warning(
            "%d KPI breach(es) detected: %s",
            len(triggered),
            ", ".join(a["metric_code"] for a in triggered),
        )
    else:
        log.info("All %d KPI checks passed — no breaches detected.", len(ALERT_RULES))

    return triggered


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PulseIQ KPI Alerting Engine")
    parser.add_argument("--dry-run", action="store_true",
                        help="Check KPIs without writing to DB or sending external alerts.")
    args = parser.parse_args()
    alerts = run_all_kpi_checks(dry_run=args.dry_run)
    sys.exit(0 if not any(a["severity"] == "CRITICAL" for a in alerts) else 1)
