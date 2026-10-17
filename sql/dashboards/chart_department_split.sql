-- Chart: M01 Department Split (Latest Month: September 2026)
-- Distribution of workforce across business departments.
SELECT
    dep.department_name,
    h.headcount_end,
    ROUND((h.headcount_end::numeric / SUM(h.headcount_end) OVER ()) * 100, 1) AS share_pct
FROM dw.fact_headcount_monthly h
JOIN dw.dim_department dep ON dep.department_key = h.department_key
JOIN dw.dim_date d ON d.date_key = h.date_key
WHERE d.year_month = '2026-09'
ORDER BY h.headcount_end DESC;
