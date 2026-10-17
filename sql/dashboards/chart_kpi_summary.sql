-- Query: Latest Month Executive KPIs
-- Returns M01 Headcount, M02 Joiners, M03 Leavers, and M04 Monthly Attrition Rate for September 2026.
WITH latest_period AS (
    SELECT MAX(date_key) AS max_date_key
    FROM dw.fact_headcount_monthly
)
SELECT
    d.year_month,
    d.full_date AS month_end,
    SUM(h.headcount_start) AS headcount_start,
    SUM(h.hires) AS m02_joiners,
    SUM(h.exits) AS m03_leavers,
    SUM(h.voluntary_exits) AS voluntary_leavers,
    SUM(h.headcount_end) AS m01_headcount,
    ROUND((SUM(h.exits)::numeric / NULLIF(SUM(h.headcount_start), 0)) * 100, 2) AS m04_attrition_rate_monthly_pct
FROM dw.fact_headcount_monthly h
JOIN dw.dim_date d ON d.date_key = h.date_key
JOIN latest_period lp ON lp.max_date_key = h.date_key
GROUP BY d.year_month, d.full_date;
