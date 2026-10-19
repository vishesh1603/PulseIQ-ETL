-- SQL Script: 004_additional_tables.sql
-- Creates additional dimension and fact tables in schema dw from PulseIQ_Star_Schema_Dataset.xlsx

CREATE SCHEMA IF NOT EXISTS dw;

-- Dimensions
CREATE TABLE IF NOT EXISTS dw.dim_location (
    work_location TEXT PRIMARY KEY,
    state TEXT,
    city_tier TEXT,
    tier_number INTEGER
);

CREATE TABLE IF NOT EXISTS dw.dim_account (
    account_code INTEGER PRIMARY KEY,
    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    normal_balance TEXT NOT NULL,
    parent_code INTEGER,
    is_group TEXT NOT NULL,
    statement TEXT NOT NULL,
    is_active TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.dim_client (
    client_id TEXT PRIMARY KEY,
    client_name TEXT NOT NULL,
    industry TEXT,
    city TEXT,
    state_or_region TEXT,
    country TEXT,
    client_type TEXT,
    gst_registration TEXT,
    payment_terms_days INTEGER,
    payment_behaviour TEXT,
    primary_service_line INTEGER,
    contact_email TEXT,
    onboarded_on TIMESTAMP,
    is_active TEXT
);

CREATE TABLE IF NOT EXISTS dw.dim_vendor (
    vendor_id TEXT PRIMARY KEY,
    vendor_name TEXT NOT NULL,
    primary_expense_account INTEGER,
    payment_terms_days INTEGER,
    city TEXT,
    gst_registration TEXT,
    is_active TEXT
);

CREATE TABLE IF NOT EXISTS dw.dim_team (
    team_id TEXT PRIMARY KEY,
    team_name TEXT NOT NULL,
    department_id TEXT NOT NULL,
    team_lead_employee_id TEXT,
    active_members INTEGER,
    planning_cadence TEXT,
    board_tool TEXT
);

CREATE TABLE IF NOT EXISTS dw.dim_sprint (
    sprint_id TEXT PRIMARY KEY,
    sprint_name TEXT NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    working_days INTEGER,
    financial_year TEXT
);

-- Facts
CREATE TABLE IF NOT EXISTS dw.fact_ledger (
    line_id TEXT PRIMARY KEY,
    entry_id TEXT NOT NULL,
    date_key INTEGER NOT NULL,
    entry_date TIMESTAMP NOT NULL,
    posting_period TEXT NOT NULL,
    financial_year TEXT NOT NULL,
    account_code INTEGER NOT NULL,
    debit NUMERIC(16,2) DEFAULT 0,
    credit NUMERIC(16,2) DEFAULT 0,
    signed_amount_debit_positive NUMERIC(16,2) NOT NULL,
    cost_center_department_id TEXT,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.fact_invoice (
    invoice_id TEXT PRIMARY KEY,
    invoice_number TEXT NOT NULL,
    client_id TEXT NOT NULL,
    invoice_date_key INTEGER NOT NULL,
    invoice_date TIMESTAMP NOT NULL,
    due_date TIMESTAMP NOT NULL,
    service_line_account INTEGER NOT NULL,
    subtotal NUMERIC(16,2) NOT NULL,
    gst_rate_percent INTEGER NOT NULL,
    gst_amount NUMERIC(16,2) NOT NULL,
    total_amount NUMERIC(16,2) NOT NULL,
    amount_paid NUMERIC(16,2) NOT NULL,
    balance_due NUMERIC(16,2) NOT NULL,
    status TEXT NOT NULL,
    last_payment_date TIMESTAMP,
    days_to_pay INTEGER,
    days_past_due_at_cutoff INTEGER,
    ageing_bucket_at_cutoff TEXT,
    carried_in_from_prior_period TEXT,
    ledger_entry_id TEXT
);

CREATE TABLE IF NOT EXISTS dw.fact_invoice_payment (
    payment_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    payment_date_key INTEGER NOT NULL,
    payment_date TIMESTAMP NOT NULL,
    amount NUMERIC(16,2) NOT NULL,
    payment_mode TEXT,
    reference_no TEXT,
    received_by TEXT,
    ledger_entry_id TEXT
);

CREATE TABLE IF NOT EXISTS dw.fact_expense (
    expense_id TEXT PRIMARY KEY,
    expense_date TIMESTAMP NOT NULL,
    expense_date_key INTEGER NOT NULL,
    category_account INTEGER NOT NULL,
    vendor_id TEXT NOT NULL,
    bill_reference TEXT,
    description TEXT,
    department_id TEXT,
    amount_excl_gst NUMERIC(16,2) NOT NULL,
    gst_rate_percent INTEGER NOT NULL,
    gst_amount NUMERIC(16,2) NOT NULL,
    total_amount NUMERIC(16,2) NOT NULL,
    due_date TIMESTAMP NOT NULL,
    paid_date TIMESTAMP,
    status TEXT NOT NULL,
    payment_mode TEXT,
    submitted_by TEXT,
    approved_by TEXT,
    ledger_entry_id TEXT,
    payment_ledger_entry_id TEXT
);

CREATE TABLE IF NOT EXISTS dw.fact_task (
    task_id TEXT PRIMARY KEY,
    team_id TEXT NOT NULL,
    sprint_id TEXT NOT NULL,
    assignee_employee_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    priority TEXT NOT NULL,
    story_points INTEGER NOT NULL,
    created_date TIMESTAMP NOT NULL,
    started_date TIMESTAMP,
    due_date TIMESTAMP NOT NULL,
    completed_date TIMESTAMP,
    status TEXT NOT NULL,
    reopened_count INTEGER DEFAULT 0,
    cycle_time_days NUMERIC(8,2),
    is_overdue_at_cutoff TEXT,
    completed_on_time TEXT
);

CREATE TABLE IF NOT EXISTS dw.fact_attrition_risk (
    prediction_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL,
    as_of_date_key INTEGER NOT NULL,
    department_id TEXT NOT NULL,
    as_of_date TIMESTAMP NOT NULL,
    risk_score_12m NUMERIC(8,4) NOT NULL,
    risk_band TEXT NOT NULL,
    top_reason_1 TEXT,
    top_reason_2 TEXT,
    top_reason_3 TEXT,
    model_version TEXT,
    model_note TEXT,
    employee_key BIGINT
);

CREATE TABLE IF NOT EXISTS dw.fact_forecast (
    forecast_id TEXT PRIMARY KEY,
    metric TEXT NOT NULL,
    department_id TEXT NOT NULL,
    forecast_month TIMESTAMP NOT NULL,
    forecast_value NUMERIC(12,4) NOT NULL,
    lower_80 NUMERIC(12,4),
    upper_80 NUMERIC(12,4),
    method TEXT,
    trained_through TEXT,
    model_version TEXT,
    forecast_month_key INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.budget_payroll_dept_month (
    department_id TEXT NOT NULL,
    month TIMESTAMP NOT NULL,
    budget_payroll_cost NUMERIC(16,2) NOT NULL,
    PRIMARY KEY (department_id, month)
);

CREATE TABLE IF NOT EXISTS dw.kpi_targets (
    month TIMESTAMP NOT NULL,
    department_id TEXT NOT NULL,
    attendance_rate_target NUMERIC(6,4),
    overtime_share_target_pct NUMERIC(6,4),
    attrition_monthly_target_pct NUMERIC(6,2),
    task_completion_target_pct NUMERIC(6,2),
    PRIMARY KEY (department_id, month)
);
