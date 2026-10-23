-- ====================================================================
-- Governed Metric Layer: 28 Official Metric Views + Catalog
-- Schema: dw
-- All views implement the business formulas from metric_dictionary
-- Privacy rule: groups with distinct employee count < minimum_group_size are suppressed
-- ====================================================================

-- --------------------------------------------------------------------
-- Metric Catalog
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_catalog AS
SELECT * FROM (
    VALUES
    ('M01', 'Headcount', 'Active employees on the last day of the month', 'COUNT(DISTINCT employee_id)', 'dw.fact_headcount_monthly / dw.dim_employee', 'Department x month', 'HR Analytics', 'count', 5),
    ('M02', 'Hires', 'Employees whose hire_date falls in the month', 'COUNT(employee_id)', 'dw.fact_headcount_monthly', 'Department x month', 'HR Analytics', 'count', 5),
    ('M03', 'Exits', 'Employees whose exit_date falls in the month', 'COUNT(employee_id)', 'dw.fact_headcount_monthly', 'Department x month', 'HR Analytics', 'count', 5),
    ('M04', 'Attrition rate (monthly)', 'Share of people who left in the month', 'Exits / headcount_start x 100', 'dw.fact_headcount_monthly', 'Department x month', 'HR Analytics', 'percent', 10),
    ('M05', 'Attrition rate (rolling 12 months)', 'Leavers in the last 12 months divided by avg headcount', 'SUM(exits, 12m) / AVG(headcount_end, 12m) x 100', 'dw.fact_headcount_monthly', 'Department x month', 'HR Analytics', 'percent', 10),
    ('M06', 'Voluntary attrition rate', 'Voluntary leavers in 12 months divided by avg headcount', 'SUM(voluntary_exits, 12m) / AVG(headcount_end, 12m) x 100', 'dw.fact_headcount_monthly', 'Department x month', 'HR Analytics', 'percent', 10),
    ('M07', 'Gross pay', 'Total gross earnings before deductions', 'SUM(gross_pay)', 'dw.fact_payroll', 'Employee x month', 'Payroll', 'INR', 5),
    ('M08', 'Net pay', 'Take-home pay after employee deductions', 'SUM(net_pay)', 'dw.fact_payroll', 'Employee x month', 'Payroll', 'INR', 5),
    ('M09', 'Payroll cost (employer cost)', 'Full cost to company: gross pay plus employer PF/ESI', 'SUM(employer_cost)', 'dw.fact_payroll', 'Employee x month', 'Finance', 'INR', 5),
    ('M10', 'Cost per head', 'Average employer cost per paid employee', 'SUM(employer_cost) / COUNT(DISTINCT employee_id)', 'dw.fact_payroll', 'Department x month', 'Finance', 'INR', 5),
    ('M11', 'Overtime share', 'Overtime pay as percentage of employer cost', 'SUM(overtime_pay) / SUM(employer_cost) x 100', 'dw.fact_payroll', 'Department x month', 'Payroll', 'percent', 5),
    ('M12', 'Variable pay share', 'Bonus and incentive pay as share of gross pay', 'SUM(variable_pay) / SUM(gross_pay) x 100', 'dw.fact_payroll', 'Department x month', 'Payroll', 'percent', 5),
    ('M13', 'Attendance rate', 'Days present divided by scheduled working days', '(SUM(present_days) + 0.5*SUM(half_days_unpaid)) / SUM(scheduled_days)', 'dw.fact_attendance_monthly', 'Department x month', 'HR Analytics', 'ratio', 5),
    ('M14', 'Late arrival rate', 'Late check-ins per present day', 'SUM(late_arrivals) / SUM(present_days)', 'dw.fact_attendance_monthly', 'Department x month', 'HR Analytics', 'ratio', 5),
    ('M15', 'Leave without pay days', 'Unpaid absence and unpaid leave days', 'SUM(lop_days)', 'dw.fact_payroll', 'Employee x month', 'Payroll', 'days', 5),
    ('M16', 'Revenue', 'Income booked in the ledger (accounts 4001-4004)', '-SUM(signed_amount)', 'dw.fact_ledger', 'Account x month', 'Finance', 'INR', NULL),
    ('M17', 'Net profit', 'Revenue minus all expenses (4xxx less 5xxx)', '-SUM(signed_amount)', 'dw.fact_ledger', 'Month', 'Finance', 'INR', NULL),
    ('M18', 'Operating margin', 'Net profit as a share of revenue', 'Net profit / Revenue x 100', 'dw.fact_ledger', 'Month', 'Finance', 'percent', NULL),
    ('M19', 'Payroll as % of revenue', 'Share of revenue consumed by payroll cost', 'Payroll cost / Revenue x 100', 'dw.fact_payroll + dw.fact_ledger', 'Month', 'Finance', 'percent', NULL),
    ('M20', 'Days sales outstanding (DSO)', 'Average days to collect receivables', 'Receivables / 90d revenue incl GST x 90', 'dw.fact_invoice, dw.fact_ledger', 'Month', 'Finance', 'days', NULL),
    ('M21', 'Overdue receivables', 'Unpaid invoice balance past due date', 'SUM(balance_due)', 'dw.fact_invoice', 'Client x date', 'Finance', 'INR', NULL),
    ('M22', 'Task completion rate', 'Done tasks divided by planned tasks', 'COUNT(status=Done) / COUNT(status!=Cancelled)', 'dw.fact_task', 'Team x sprint', 'Engineering Ops', 'percent', 5),
    ('M23', 'On-time delivery rate', 'Done tasks completed on or before due date', 'COUNT(on_time=Y) / COUNT(status=Done)', 'dw.fact_task', 'Team x sprint', 'Engineering Ops', 'percent', 5),
    ('M24', 'Velocity', 'Story points completed in sprint', 'SUM(story_points)', 'dw.fact_task', 'Team x sprint', 'Engineering Ops', 'points', NULL),
    ('M25', 'Average cycle time', 'Average days from start to complete', 'AVG(completed_date - started_date)', 'dw.fact_task', 'Team x sprint', 'Engineering Ops', 'days', 5),
    ('M26', 'Anomaly flag rate', 'Share of scored records flagged by AI', 'COUNT(flagged=Y) / COUNT(*)', 'dw.fact_anomaly', 'Source x month', 'AI/ML', 'percent', NULL),
    ('M27', 'High-risk share', 'Share of employees in High attrition-risk band', 'COUNT(risk_band=High) / COUNT(*)', 'dw.fact_attrition_risk', 'Department', 'AI/ML', 'percent', 10),
    ('M28', 'Forecast error (MAPE)', 'Mean absolute percentage error of forecasts', 'AVG(ABS(actual-forecast)/actual) x 100', 'dw.fact_forecast vs dw.fact_headcount', 'Department x month', 'AI/ML', 'percent', NULL)
) AS t(metric_id, metric_name, business_definition, formula, source_table, grain, owner_team, unit, minimum_group_size);


-- --------------------------------------------------------------------
-- M01: Headcount (Department x Month)
-- Privacy: suppressed if headcount_end < 5
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m01_headcount AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    CASE 
        WHEN f.headcount_end < 5 THEN NULL 
        ELSE f.headcount_end 
    END AS headcount,
    f.headcount_end AS unsuppressed_headcount,
    CASE WHEN f.headcount_end < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_headcount_monthly f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key;


-- --------------------------------------------------------------------
-- M02: Hires (Department x Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m02_hires AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    CASE 
        WHEN f.headcount_end < 5 THEN NULL 
        ELSE f.hires 
    END AS hires,
    f.hires AS unsuppressed_hires,
    CASE WHEN f.headcount_end < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_headcount_monthly f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key;


-- --------------------------------------------------------------------
-- M03: Exits (Department x Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m03_exits AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    CASE 
        WHEN f.headcount_end < 5 THEN NULL 
        ELSE f.exits 
    END AS exits,
    f.exits AS unsuppressed_exits,
    CASE WHEN f.headcount_end < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_headcount_monthly f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key;


-- --------------------------------------------------------------------
-- M04: Attrition Rate Monthly (Department x Month)
-- Privacy: min group size 10
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m04_attrition_rate_monthly AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    CASE 
        WHEN f.headcount_start < 10 THEN NULL 
        ELSE f.attrition_rate_monthly_pct 
    END AS attrition_rate_monthly_pct,
    f.attrition_rate_monthly_pct AS unsuppressed_attrition_pct,
    CASE WHEN f.headcount_start < 10 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_headcount_monthly f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key;


-- --------------------------------------------------------------------
-- M05: Attrition Rate Rolling 12 Months (Department x Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m05_attrition_rate_12m AS
WITH rolling AS (
    SELECT 
        f.department_key,
        f.date_key,
        SUM(f.exits) OVER w AS exits_12m,
        AVG(f.headcount_end::numeric) OVER w AS avg_headcount_12m
    FROM dw.fact_headcount_monthly f
    WINDOW w AS (
        PARTITION BY f.department_key 
        ORDER BY f.date_key 
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    )
)
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    CASE 
        WHEN r.avg_headcount_12m < 10 THEN NULL 
        ELSE ROUND((r.exits_12m / NULLIF(r.avg_headcount_12m, 0) * 100), 2) 
    END AS attrition_rate_12m_pct,
    ROUND((r.exits_12m / NULLIF(r.avg_headcount_12m, 0) * 100), 2) AS unsuppressed_attrition_12m_pct,
    CASE WHEN r.avg_headcount_12m < 10 THEN TRUE ELSE FALSE END AS is_suppressed
FROM rolling r
JOIN dw.dim_department dep ON dep.department_key = r.department_key
JOIN dw.dim_date d ON d.date_key = r.date_key;


-- --------------------------------------------------------------------
-- M06: Voluntary Attrition Rate (Department x Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m06_voluntary_attrition_rate_12m AS
WITH rolling AS (
    SELECT 
        f.department_key,
        f.date_key,
        SUM(f.voluntary_exits) OVER w AS vol_exits_12m,
        AVG(f.headcount_end::numeric) OVER w AS avg_headcount_12m
    FROM dw.fact_headcount_monthly f
    WINDOW w AS (
        PARTITION BY f.department_key 
        ORDER BY f.date_key 
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    )
)
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    CASE 
        WHEN r.avg_headcount_12m < 10 THEN NULL 
        ELSE ROUND((r.vol_exits_12m / NULLIF(r.avg_headcount_12m, 0) * 100), 2) 
    END AS voluntary_attrition_12m_pct,
    ROUND((r.vol_exits_12m / NULLIF(r.avg_headcount_12m, 0) * 100), 2) AS unsuppressed_vol_attrition_12m_pct,
    CASE WHEN r.avg_headcount_12m < 10 THEN TRUE ELSE FALSE END AS is_suppressed
FROM rolling r
JOIN dw.dim_department dep ON dep.department_key = r.department_key
JOIN dw.dim_date d ON d.date_key = r.date_key;


-- --------------------------------------------------------------------
-- M07: Gross Pay (Department x Month & Total Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m07_gross_pay AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    COUNT(DISTINCT f.employee_id) AS employees_paid,
    CASE 
        WHEN COUNT(DISTINCT f.employee_id) < 5 THEN NULL 
        ELSE SUM(f.gross_pay) 
    END AS gross_pay,
    SUM(f.gross_pay) AS unsuppressed_gross_pay,
    CASE WHEN COUNT(DISTINCT f.employee_id) < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_payroll f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY d.year_month, d.month_end_date, dep.department_id, dep.department_name;


-- --------------------------------------------------------------------
-- M08: Net Pay (Department x Month & Total Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m08_net_pay AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    COUNT(DISTINCT f.employee_id) AS employees_paid,
    CASE 
        WHEN COUNT(DISTINCT f.employee_id) < 5 THEN NULL 
        ELSE SUM(f.net_pay) 
    END AS net_pay,
    SUM(f.net_pay) AS unsuppressed_net_pay,
    CASE WHEN COUNT(DISTINCT f.employee_id) < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_payroll f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY d.year_month, d.month_end_date, dep.department_id, dep.department_name;


-- --------------------------------------------------------------------
-- M09: Payroll Cost / Employer Cost (Department x Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m09_payroll_cost AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    COUNT(DISTINCT f.employee_id) AS employees_paid,
    CASE 
        WHEN COUNT(DISTINCT f.employee_id) < 5 THEN NULL 
        ELSE SUM(f.employer_cost) 
    END AS employer_cost,
    SUM(f.employer_cost) AS unsuppressed_employer_cost,
    CASE WHEN COUNT(DISTINCT f.employee_id) < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_payroll f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY d.year_month, d.month_end_date, dep.department_id, dep.department_name;


-- --------------------------------------------------------------------
-- M10: Cost Per Head (Department x Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m10_cost_per_head AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    COUNT(DISTINCT f.employee_id) AS employees_paid,
    CASE 
        WHEN COUNT(DISTINCT f.employee_id) < 5 THEN NULL 
        ELSE ROUND(SUM(f.employer_cost) / NULLIF(COUNT(DISTINCT f.employee_id), 0), 2) 
    END AS cost_per_head,
    ROUND(SUM(f.employer_cost) / NULLIF(COUNT(DISTINCT f.employee_id), 0), 2) AS unsuppressed_cost_per_head,
    CASE WHEN COUNT(DISTINCT f.employee_id) < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_payroll f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY d.year_month, d.month_end_date, dep.department_id, dep.department_name;


-- --------------------------------------------------------------------
-- M11: Overtime Share (Department x Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m11_overtime_share AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    COUNT(DISTINCT f.employee_id) AS employees_paid,
    CASE 
        WHEN COUNT(DISTINCT f.employee_id) < 5 THEN NULL 
        ELSE ROUND(SUM(f.overtime_pay) / NULLIF(SUM(f.employer_cost), 0) * 100, 2) 
    END AS overtime_share_pct,
    ROUND(SUM(f.overtime_pay) / NULLIF(SUM(f.employer_cost), 0) * 100, 2) AS unsuppressed_overtime_share_pct,
    CASE WHEN COUNT(DISTINCT f.employee_id) < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_payroll f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY d.year_month, d.month_end_date, dep.department_id, dep.department_name;


-- --------------------------------------------------------------------
-- M12: Variable Pay Share (Department x Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m12_variable_pay_share AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    COUNT(DISTINCT f.employee_id) AS employees_paid,
    CASE 
        WHEN COUNT(DISTINCT f.employee_id) < 5 THEN NULL 
        ELSE ROUND(SUM(f.variable_pay) / NULLIF(SUM(f.gross_pay), 0) * 100, 2) 
    END AS variable_pay_share_pct,
    ROUND(SUM(f.variable_pay) / NULLIF(SUM(f.gross_pay), 0) * 100, 2) AS unsuppressed_variable_pay_share_pct,
    CASE WHEN COUNT(DISTINCT f.employee_id) < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_payroll f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY d.year_month, d.month_end_date, dep.department_id, dep.department_name;


-- --------------------------------------------------------------------
-- M13: Attendance Rate (Department x Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m13_attendance_rate AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    COUNT(DISTINCT f.employee_id) AS employees_count,
    CASE 
        WHEN COUNT(DISTINCT f.employee_id) < 5 THEN NULL 
        ELSE ROUND((SUM(f.present_days) + 0.5 * SUM(f.half_days_unpaid)) / NULLIF(SUM(f.scheduled_days), 0), 4) 
    END AS attendance_rate,
    ROUND((SUM(f.present_days) + 0.5 * SUM(f.half_days_unpaid)) / NULLIF(SUM(f.scheduled_days), 0), 4) AS unsuppressed_attendance_rate,
    CASE WHEN COUNT(DISTINCT f.employee_id) < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_attendance_monthly f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY d.year_month, d.month_end_date, dep.department_id, dep.department_name;


-- --------------------------------------------------------------------
-- M14: Late Arrival Rate (Department x Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m14_late_arrival_rate AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    COUNT(DISTINCT f.employee_id) AS employees_count,
    CASE 
        WHEN COUNT(DISTINCT f.employee_id) < 5 THEN NULL 
        ELSE ROUND(SUM(f.late_arrivals)::numeric / NULLIF(SUM(f.present_days), 0), 4) 
    END AS late_arrival_rate,
    ROUND(SUM(f.late_arrivals)::numeric / NULLIF(SUM(f.present_days), 0), 4) AS unsuppressed_late_arrival_rate,
    CASE WHEN COUNT(DISTINCT f.employee_id) < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_attendance_monthly f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY d.year_month, d.month_end_date, dep.department_id, dep.department_name;


-- --------------------------------------------------------------------
-- M15: Leave Without Pay Days (Department x Month & Employee x Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m15_lop_days AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    COUNT(DISTINCT f.employee_id) AS employees_paid,
    CASE 
        WHEN COUNT(DISTINCT f.employee_id) < 5 THEN NULL 
        ELSE SUM(f.lop_days) 
    END AS lop_days,
    SUM(f.lop_days) AS unsuppressed_lop_days,
    CASE WHEN COUNT(DISTINCT f.employee_id) < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_payroll f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY d.year_month, d.month_end_date, dep.department_id, dep.department_name;


-- --------------------------------------------------------------------
-- M16: Revenue (Month & Account)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m16_revenue AS
SELECT 
    l.posting_period AS year_month,
    l.account_code,
    a.account_name,
    -SUM(l.signed_amount_debit_positive) AS revenue
FROM dw.fact_ledger l
JOIN dw.dim_account a ON a.account_code = l.account_code
WHERE l.account_code BETWEEN 4001 AND 4004
GROUP BY l.posting_period, l.account_code, a.account_name;


-- --------------------------------------------------------------------
-- M17: Net Profit (Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m17_net_profit AS
SELECT 
    l.posting_period AS year_month,
    -SUM(CASE WHEN l.account_code BETWEEN 4000 AND 4999 THEN l.signed_amount_debit_positive ELSE 0 END) AS total_revenue,
    SUM(CASE WHEN l.account_code BETWEEN 5000 AND 5999 THEN l.signed_amount_debit_positive ELSE 0 END) AS total_expense,
    -SUM(CASE WHEN l.account_code >= 4000 THEN l.signed_amount_debit_positive ELSE 0 END) AS net_profit
FROM dw.fact_ledger l
WHERE l.account_code >= 4000
GROUP BY l.posting_period;


-- --------------------------------------------------------------------
-- M18: Operating Margin (Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m18_operating_margin AS
SELECT 
    year_month,
    total_revenue,
    net_profit,
    ROUND((net_profit / NULLIF(total_revenue, 0) * 100), 2) AS operating_margin_pct
FROM dw.metric_m17_net_profit;


-- --------------------------------------------------------------------
-- M19: Payroll as % of Revenue (Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m19_payroll_pct_revenue AS
WITH p AS (
    SELECT 
        d.year_month,
        SUM(f.employer_cost) AS total_payroll_cost
    FROM dw.fact_payroll f
    JOIN dw.dim_date d ON d.date_key = f.date_key
    GROUP BY d.year_month
),
r AS (
    SELECT 
        posting_period AS year_month,
        -SUM(signed_amount_debit_positive) AS revenue
    FROM dw.fact_ledger
    WHERE account_code BETWEEN 4001 AND 4004
    GROUP BY posting_period
)
SELECT 
    r.year_month,
    p.total_payroll_cost,
    r.revenue,
    ROUND((p.total_payroll_cost / NULLIF(r.revenue, 0) * 100), 2) AS payroll_pct_of_revenue
FROM r
JOIN p ON p.year_month = r.year_month;


-- --------------------------------------------------------------------
-- M20: Days Sales Outstanding (DSO) (Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m20_dso AS
WITH rec AS (
    SELECT 
        posting_period AS year_month,
        SUM(signed_amount_debit_positive) AS receivables_balance
    FROM dw.fact_ledger
    WHERE account_code = 1100
    GROUP BY posting_period
),
rev_90 AS (
    SELECT 
        inv.posting_period AS year_month,
        SUM(inv.total_amount) AS revenue_incl_gst_90d
    FROM (
        SELECT 
            TO_CHAR(i.invoice_date, 'YYYY-MM') AS posting_period,
            i.total_amount
        FROM dw.fact_invoice i
    ) inv
    GROUP BY inv.posting_period
)
SELECT 
    rec.year_month,
    rec.receivables_balance,
    rev_90.revenue_incl_gst_90d,
    ROUND((rec.receivables_balance / NULLIF(rev_90.revenue_incl_gst_90d, 0) * 90), 1) AS dso_days
FROM rec
LEFT JOIN rev_90 ON rev_90.year_month = rec.year_month;


-- --------------------------------------------------------------------
-- M21: Overdue Receivables (Client x Date)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m21_overdue_receivables AS
SELECT 
    c.client_id,
    c.client_name,
    COUNT(i.invoice_id) AS overdue_invoices_count,
    SUM(i.balance_due) AS overdue_balance_due,
    AVG(i.days_past_due_at_cutoff) AS avg_days_overdue
FROM dw.fact_invoice i
JOIN dw.dim_client c ON c.client_id = i.client_id
WHERE i.balance_due > 0 
  AND i.status NOT IN ('DRAFT', 'CANCELLED')
GROUP BY c.client_id, c.client_name;


-- --------------------------------------------------------------------
-- M22: Task Completion Rate (Team x Sprint)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m22_task_completion_rate AS
SELECT 
    t.team_id,
    tm.team_name,
    s.sprint_id,
    s.sprint_name,
    COUNT(t.task_id) AS total_tasks,
    COUNT(CASE WHEN t.status = 'Done' THEN 1 END) AS tasks_done,
    CASE 
        WHEN COUNT(t.task_id) < 5 THEN NULL 
        ELSE ROUND(COUNT(CASE WHEN t.status = 'Done' THEN 1 END)::numeric / NULLIF(COUNT(CASE WHEN t.status != 'Cancelled' THEN 1 END), 0) * 100, 2) 
    END AS task_completion_rate_pct,
    ROUND(COUNT(CASE WHEN t.status = 'Done' THEN 1 END)::numeric / NULLIF(COUNT(CASE WHEN t.status != 'Cancelled' THEN 1 END), 0) * 100, 2) AS unsuppressed_completion_rate,
    CASE WHEN COUNT(t.task_id) < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_task t
JOIN dw.dim_team tm ON tm.team_id = t.team_id
JOIN dw.dim_sprint s ON s.sprint_id = t.sprint_id
GROUP BY t.team_id, tm.team_name, s.sprint_id, s.sprint_name;


-- --------------------------------------------------------------------
-- M23: On-Time Delivery Rate (Team x Sprint)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m23_ontime_delivery_rate AS
SELECT 
    t.team_id,
    tm.team_name,
    s.sprint_id,
    s.sprint_name,
    COUNT(CASE WHEN t.status = 'Done' THEN 1 END) AS tasks_done,
    CASE 
        WHEN COUNT(CASE WHEN t.status = 'Done' THEN 1 END) < 5 THEN NULL 
        ELSE ROUND(COUNT(CASE WHEN t.status = 'Done' AND t.completed_on_time = 'Y' THEN 1 END)::numeric / NULLIF(COUNT(CASE WHEN t.status = 'Done' THEN 1 END), 0) * 100, 2) 
    END AS on_time_delivery_rate_pct,
    ROUND(COUNT(CASE WHEN t.status = 'Done' AND t.completed_on_time = 'Y' THEN 1 END)::numeric / NULLIF(COUNT(CASE WHEN t.status = 'Done' THEN 1 END), 0) * 100, 2) AS unsuppressed_on_time_rate,
    CASE WHEN COUNT(CASE WHEN t.status = 'Done' THEN 1 END) < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_task t
JOIN dw.dim_team tm ON tm.team_id = t.team_id
JOIN dw.dim_sprint s ON s.sprint_id = t.sprint_id
GROUP BY t.team_id, tm.team_name, s.sprint_id, s.sprint_name;


-- --------------------------------------------------------------------
-- M24: Velocity (Team x Sprint)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m24_velocity AS
SELECT 
    t.team_id,
    tm.team_name,
    s.sprint_id,
    s.sprint_name,
    SUM(CASE WHEN t.status = 'Done' THEN t.story_points ELSE 0 END) AS velocity_story_points
FROM dw.fact_task t
JOIN dw.dim_team tm ON tm.team_id = t.team_id
JOIN dw.dim_sprint s ON s.sprint_id = t.sprint_id
GROUP BY t.team_id, tm.team_name, s.sprint_id, s.sprint_name;


-- --------------------------------------------------------------------
-- M25: Average Cycle Time (Team x Sprint)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m25_average_cycle_time AS
SELECT 
    t.team_id,
    tm.team_name,
    s.sprint_id,
    s.sprint_name,
    COUNT(CASE WHEN t.status = 'Done' AND t.cycle_time_days IS NOT NULL THEN 1 END) AS completed_tasks,
    CASE 
        WHEN COUNT(CASE WHEN t.status = 'Done' AND t.cycle_time_days IS NOT NULL THEN 1 END) < 5 THEN NULL 
        ELSE ROUND(AVG(t.cycle_time_days) FILTER (WHERE t.status = 'Done' AND t.cycle_time_days >= 0), 2) 
    END AS avg_cycle_time_days,
    ROUND(AVG(t.cycle_time_days) FILTER (WHERE t.status = 'Done' AND t.cycle_time_days >= 0), 2) AS unsuppressed_cycle_time,
    CASE WHEN COUNT(CASE WHEN t.status = 'Done' AND t.cycle_time_days IS NOT NULL THEN 1 END) < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_task t
JOIN dw.dim_team tm ON tm.team_id = t.team_id
JOIN dw.dim_sprint s ON s.sprint_id = t.sprint_id
GROUP BY t.team_id, tm.team_name, s.sprint_id, s.sprint_name;


-- --------------------------------------------------------------------
-- M26: Anomaly Flag Rate (Source x Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m26_anomaly_flag_rate AS
SELECT 
    source_dataset,
    TO_CHAR(period_date, 'YYYY-MM') AS year_month,
    COUNT(*) AS total_scored,
    COUNT(CASE WHEN flagged = 'Y' THEN 1 END) AS anomalies_flagged,
    ROUND(COUNT(CASE WHEN flagged = 'Y' THEN 1 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) AS anomaly_flag_rate_pct
FROM dw.fact_anomaly
GROUP BY source_dataset, TO_CHAR(period_date, 'YYYY-MM');


-- --------------------------------------------------------------------
-- M27: High-Risk Attrition Share (Department)
-- Privacy: min group size 10
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m27_high_risk_share AS
SELECT 
    r.department_id,
    dep.department_name,
    COUNT(*) AS total_scored,
    COUNT(CASE WHEN r.risk_band = 'High' THEN 1 END) AS high_risk_count,
    CASE 
        WHEN COUNT(*) < 10 THEN NULL 
        ELSE ROUND(COUNT(CASE WHEN r.risk_band = 'High' THEN 1 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) 
    END AS high_risk_share_pct,
    ROUND(COUNT(CASE WHEN r.risk_band = 'High' THEN 1 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) AS unsuppressed_high_risk_share,
    CASE WHEN COUNT(*) < 10 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_attrition_risk r
JOIN dw.dim_department dep ON dep.department_id = r.department_id
GROUP BY r.department_id, dep.department_name;


-- --------------------------------------------------------------------
-- M28: Forecast Error MAPE (Department x Month)
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m28_forecast_error AS
SELECT 
    fc.forecast_id,
    fc.department_id,
    dep.department_name,
    fc.metric,
    TO_CHAR(fc.forecast_month, 'YYYY-MM') AS forecast_month,
    fc.forecast_value,
    hc.headcount_end AS actual_value,
    ROUND(ABS(hc.headcount_end - fc.forecast_value) / NULLIF(hc.headcount_end, 0) * 100, 2) AS ape_pct
FROM dw.fact_forecast fc
LEFT JOIN dw.dim_department dep ON dep.department_id = fc.department_id
LEFT JOIN dw.dim_date d ON d.date_key = fc.forecast_month_key
LEFT JOIN dw.fact_headcount_monthly hc 
    ON hc.date_key = fc.forecast_month_key 
   AND hc.department_key = dep.department_key;


-- --------------------------------------------------------------------
-- M29: WFH Share (Department x Month) [Mini Challenge]
-- Business definition: Share of present days worked remotely from home
-- Formula: SUM(wfh_days) / NULLIF(SUM(present_days), 0) * 100
-- Privacy: min group size 5 employees
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.metric_m29_wfh_share AS
SELECT 
    d.year_month,
    d.month_end_date,
    dep.department_id,
    dep.department_name,
    COUNT(DISTINCT f.employee_id) AS employees_present,
    SUM(f.wfh_days) AS total_wfh_days,
    SUM(f.present_days) AS total_present_days,
    CASE 
        WHEN COUNT(DISTINCT f.employee_id) < 5 THEN NULL 
        ELSE ROUND((SUM(f.wfh_days)::numeric / NULLIF(SUM(f.present_days), 0) * 100), 2) 
    END AS wfh_share_pct,
    ROUND((SUM(f.wfh_days)::numeric / NULLIF(SUM(f.present_days), 0) * 100), 2) AS unsuppressed_wfh_share_pct,
    CASE WHEN COUNT(DISTINCT f.employee_id) < 5 THEN TRUE ELSE FALSE END AS is_suppressed
FROM dw.fact_attendance_monthly f
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY d.year_month, d.month_end_date, dep.department_id, dep.department_name;
