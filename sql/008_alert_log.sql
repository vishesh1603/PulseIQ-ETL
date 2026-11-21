-- ============================================================================
-- PulseIQ Phase 4 — Task 18: KPI Alert Log Table
-- File: sql/008_alert_log.sql
-- Records every KPI breach detected by scripts/alerting.py
-- ============================================================================

CREATE TABLE IF NOT EXISTS dw.alert_log (
    alert_id      SERIAL PRIMARY KEY,
    run_id        TEXT,                            -- ETL run that triggered the check
    metric_code   TEXT        NOT NULL,            -- e.g. M05
    metric_name   TEXT        NOT NULL,            -- e.g. "12-Month Attrition Rate"
    current_value NUMERIC,                         -- value at time of breach
    target_value  TEXT,                            -- human-readable target (e.g. "<=12.0%")
    severity      TEXT        NOT NULL
                      CHECK (severity IN ('CRITICAL', 'WARNING', 'INFO')),
    breach_month  TEXT,                            -- YYYY-MM of the breaching data point
    channel_used  TEXT        NOT NULL DEFAULT 'log',  -- log | webhook | email
    delivered     BOOLEAN     NOT NULL DEFAULT FALSE,
    delivered_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dashboard_url TEXT                             -- direct link to the relevant page
);

-- Index for quick lookup
CREATE INDEX IF NOT EXISTS idx_alert_log_metric  ON dw.alert_log (metric_code);
CREATE INDEX IF NOT EXISTS idx_alert_log_time    ON dw.alert_log (delivered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_log_sev     ON dw.alert_log (severity);

-- ============================================================================
-- View: active alerts in the last 30 days
-- ============================================================================
CREATE OR REPLACE VIEW dw.vw_active_alerts AS
SELECT
    alert_id,
    metric_code,
    metric_name,
    current_value,
    target_value,
    severity,
    breach_month,
    channel_used,
    delivered_at
FROM dw.alert_log
WHERE delivered_at >= NOW() - INTERVAL '30 days'
ORDER BY
    CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'WARNING' THEN 2 ELSE 3 END,
    delivered_at DESC;
