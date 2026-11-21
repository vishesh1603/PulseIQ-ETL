-- ============================================================================
-- PulseIQ Phase 4 — Task 17: DQ Monitoring Log Table
-- File: sql/007_dq_monitoring.sql
-- Persists results of all 14 DQ checks after every ETL run.
-- ============================================================================

CREATE TABLE IF NOT EXISTS dw.dq_check_log (
    check_id      SERIAL PRIMARY KEY,
    run_id        TEXT        NOT NULL,           -- ETL run_id from logs/last_run.json
    check_code    TEXT        NOT NULL,           -- e.g. DQ-C01
    check_name    TEXT        NOT NULL,           -- human-readable name
    severity      TEXT        NOT NULL CHECK (severity IN ('Critical', 'Warning')),
    status        TEXT        NOT NULL CHECK (status IN ('PASS', 'FAIL', 'WARN')),
    rows_checked  INT,                            -- total records evaluated (NULL = N/A)
    rows_failed   INT         NOT NULL DEFAULT 0, -- records that broke the rule
    tolerance     TEXT,                           -- rule-specific threshold
    description   TEXT,                          -- business description of the check
    checked_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for quick lookup by run
CREATE INDEX IF NOT EXISTS idx_dq_check_log_run_id  ON dw.dq_check_log (run_id);
CREATE INDEX IF NOT EXISTS idx_dq_check_log_status  ON dw.dq_check_log (status);
CREATE INDEX IF NOT EXISTS idx_dq_check_log_checked ON dw.dq_check_log (checked_at DESC);

-- ============================================================================
-- View: latest DQ run summary
-- ============================================================================
CREATE OR REPLACE VIEW dw.vw_latest_dq_run AS
SELECT
    run_id,
    checked_at::date                                 AS check_date,
    COUNT(*)                                         AS total_checks,
    COUNT(*) FILTER (WHERE status = 'PASS')          AS passed,
    COUNT(*) FILTER (WHERE status = 'FAIL')          AS failed,
    COUNT(*) FILTER (WHERE status = 'WARN')          AS warned,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'PASS')::numeric / NULLIF(COUNT(*), 0) * 100,
        1
    )                                                AS pass_rate_pct
FROM dw.dq_check_log
WHERE run_id = (SELECT run_id FROM dw.dq_check_log ORDER BY checked_at DESC LIMIT 1)
GROUP BY run_id, checked_at::date;
