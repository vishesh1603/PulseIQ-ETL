-- Chart: Active Workforce by Tenure Band (September 2026)
-- Tenure breakdown of active employees.
SELECT
    CASE
        WHEN tenure_years < 1 THEN 'Under 1 yr'
        WHEN tenure_years < 3 THEN '1-3 yrs'
        WHEN tenure_years < 5 THEN '3-5 yrs'
        WHEN tenure_years < 10 THEN '5-10 yrs'
        ELSE '10+ yrs'
    END AS tenure_band,
    COUNT(DISTINCT employee_id) AS employee_count,
    ROUND((COUNT(DISTINCT employee_id)::numeric / 441) * 100, 1) AS share_pct
FROM dw.dim_employee
WHERE is_current = TRUE AND is_active = TRUE
GROUP BY 1, CASE
        WHEN tenure_years < 1 THEN 1
        WHEN tenure_years < 3 THEN 2
        WHEN tenure_years < 5 THEN 3
        WHEN tenure_years < 10 THEN 4
        ELSE 5
    END
ORDER BY MIN(tenure_years);
