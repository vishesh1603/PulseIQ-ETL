-- Chart: M01 Headcount Trend (Monthly)
-- Shows the continuous month-end headcount trajectory.
SELECT
    d.year_month,
    d.full_date AS month_end,
    SUM(h.headcount_end) AS headcount
FROM dw.fact_headcount_monthly h
JOIN dw.dim_date d ON d.date_key = h.date_key
GROUP BY d.year_month, d.full_date
ORDER BY d.full_date;
