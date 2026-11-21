-- ============================================================================
-- PulseIQ Phase 4 — Task 17: Role-Based Access Control (RBAC)
-- File: sql/006_rbac.sql
-- Run as superuser (pulseiq) after the warehouse schema is loaded.
-- ============================================================================
-- Idempotent: safe to run multiple times.
-- ============================================================================

-- ============================================================================
-- 1. ROLES (no login — used as permission groups)
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_hr') THEN
        CREATE ROLE role_hr NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_finance') THEN
        CREATE ROLE role_finance NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_executive') THEN
        CREATE ROLE role_executive NOLOGIN;
    END IF;
END
$$;

-- ============================================================================
-- 2. LOGIN USERS (map to roles)
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hr_readonly') THEN
        CREATE USER hr_readonly WITH PASSWORD 'hr_pass_2026';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fin_readonly') THEN
        CREATE USER fin_readonly WITH PASSWORD 'fin_pass_2026';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'exec_readonly') THEN
        CREATE USER exec_readonly WITH PASSWORD 'exec_pass_2026';
    END IF;
END
$$;

GRANT role_hr        TO hr_readonly;
GRANT role_finance   TO fin_readonly;
GRANT role_executive TO exec_readonly;

-- Allow all roles to connect to the pulseiq database
GRANT CONNECT ON DATABASE pulseiq TO role_hr, role_finance, role_executive;

-- ============================================================================
-- 3. SCHEMA USAGE
-- ============================================================================

GRANT USAGE ON SCHEMA dw TO role_hr, role_finance, role_executive;

-- ============================================================================
-- 4. ROLE_HR — People data: HR tables + metric views M01-M15
-- ============================================================================

GRANT SELECT ON
    dw.dim_employee,
    dw.dim_department,
    dw.dim_role,
    dw.dim_date,
    dw.dim_leave_type,
    dw.fact_payroll,
    dw.fact_attendance_monthly,
    dw.fact_leave,
    dw.fact_headcount_monthly,
    dw.fact_attrition_risk,
    dw.budget_payroll_dept_month,
    dw.kpi_targets,
    dw.metric_catalog,
    dw.metric_m01_headcount,
    dw.metric_m02_hires,
    dw.metric_m03_exits,
    dw.metric_m04_attrition_rate_monthly,
    dw.metric_m05_attrition_rate_12m,
    dw.metric_m06_voluntary_attrition_rate_12m,
    dw.metric_m07_gross_pay,
    dw.metric_m08_net_pay,
    dw.metric_m09_payroll_cost,
    dw.metric_m10_cost_per_head,
    dw.metric_m11_overtime_share,
    dw.metric_m12_variable_pay_share,
    dw.metric_m13_attendance_rate,
    dw.metric_m14_late_arrival_rate,
    dw.metric_m15_lop_days,
    dw.metric_m27_high_risk_share,
    dw.metric_m29_wfh_share,
    dw.dq_check_log
TO role_hr;

-- ============================================================================
-- 5. ROLE_FINANCE — Finance data: ledger, invoice, expense + metric views M16-M21
-- ============================================================================

GRANT SELECT ON
    dw.dim_account,
    dw.dim_vendor,
    dw.dim_client,
    dw.dim_department,
    dw.dim_date,
    dw.fact_ledger,
    dw.fact_invoice,
    dw.fact_expense,
    dw.reconciliation_answer_key,
    dw.kpi_targets,
    dw.metric_catalog,
    dw.metric_m16_revenue,
    dw.metric_m17_net_profit,
    dw.metric_m18_operating_margin,
    dw.metric_m19_payroll_pct_revenue,
    dw.metric_m20_dso,
    dw.metric_m21_overdue_receivables,
    dw.dq_check_log,
    dw.alert_log
TO role_finance;

-- Finance also needs payroll totals for M19 (payroll % of revenue)
GRANT SELECT ON
    dw.metric_m09_payroll_cost,
    dw.metric_m07_gross_pay
TO role_finance;

-- ============================================================================
-- 6. ROLE_EXECUTIVE — Metric views ONLY (no raw tables)
-- ============================================================================

GRANT SELECT ON
    dw.metric_catalog,
    dw.metric_m01_headcount,
    dw.metric_m02_hires,
    dw.metric_m03_exits,
    dw.metric_m04_attrition_rate_monthly,
    dw.metric_m05_attrition_rate_12m,
    dw.metric_m06_voluntary_attrition_rate_12m,
    dw.metric_m07_gross_pay,
    dw.metric_m08_net_pay,
    dw.metric_m09_payroll_cost,
    dw.metric_m10_cost_per_head,
    dw.metric_m11_overtime_share,
    dw.metric_m12_variable_pay_share,
    dw.metric_m13_attendance_rate,
    dw.metric_m14_late_arrival_rate,
    dw.metric_m15_lop_days,
    dw.metric_m16_revenue,
    dw.metric_m17_net_profit,
    dw.metric_m18_operating_margin,
    dw.metric_m19_payroll_pct_revenue,
    dw.metric_m20_dso,
    dw.metric_m21_overdue_receivables,
    dw.metric_m22_task_completion_rate,
    dw.metric_m23_ontime_delivery_rate,
    dw.metric_m24_velocity,
    dw.metric_m25_average_cycle_time,
    dw.metric_m26_anomaly_flag_rate,
    dw.metric_m27_high_risk_share,
    dw.metric_m28_forecast_error,
    dw.metric_m29_wfh_share,
    dw.kpi_targets,
    dw.alert_log
TO role_executive;

-- ============================================================================
-- 7. VERIFICATION QUERIES (run manually to confirm grants)
-- ============================================================================
-- psql -U pulseiq -d pulseiq -c "\du role_hr role_finance role_executive"
-- psql -U hr_readonly  -d pulseiq -c "SELECT COUNT(*) FROM dw.metric_m01_headcount;"
-- psql -U hr_readonly  -d pulseiq -c "SELECT COUNT(*) FROM dw.fact_ledger;" -- should FAIL
-- psql -U fin_readonly -d pulseiq -c "SELECT COUNT(*) FROM dw.metric_m17_net_profit;"
-- psql -U fin_readonly -d pulseiq -c "SELECT COUNT(*) FROM dw.dim_employee;" -- should FAIL
-- psql -U exec_readonly -d pulseiq -c "SELECT COUNT(*) FROM dw.metric_catalog;"
-- psql -U exec_readonly -d pulseiq -c "SELECT COUNT(*) FROM dw.fact_payroll;" -- should FAIL
