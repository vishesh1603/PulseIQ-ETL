-- Dataset: Headcount Monthly
-- Used for: M01 Headcount KPI, M02 Joiners KPI, M03 Leavers KPI, M04 Attrition Rate KPI,
-- Headcount Trend (Line), Department Split (Bar), and Joiners vs Leavers (Grouped Bars).
SELECT
    d.full_date AS month_end,
    d.year,
    d.quarter,
    d.month_number,
    d.month_name,
    d.year_month,
    d.financial_year,
    dep.department_id,
    dep.department_name,
    h.headcount_start,
    h.hires AS joiners,
    h.exits AS leavers,
    h.voluntary_exits,
    h.transfers_in,
    h.transfers_out,
    h.headcount_end,
    h.attrition_rate_monthly_pct
FROM dw.fact_headcount_monthly h
JOIN dw.dim_date d ON d.date_key = h.date_key
JOIN dw.dim_department dep ON dep.department_key = h.department_key;
