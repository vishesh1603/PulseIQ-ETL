-- Chart: M02 & M03 Joiners vs. Leavers by Month (2025 – 2026)
-- Monthly hiring inflow compared against leavers outflow.
SELECT
    d.year_month,
    d.full_date AS month_end,
    SUM(h.hires) AS joiners,
    SUM(h.exits) AS leavers,
    SUM(h.hires) - SUM(h.exits) AS net_addition
FROM dw.fact_headcount_monthly h
JOIN dw.dim_date d ON d.date_key = h.date_key
WHERE d.year >= 2025
GROUP BY d.year_month, d.full_date
ORDER BY d.full_date;
