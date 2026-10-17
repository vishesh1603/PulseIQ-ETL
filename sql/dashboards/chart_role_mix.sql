-- Chart: Active Workforce by Role Mix (Top Roles, September 2026)
-- Shows top job roles across the company.
SELECT
    r.role_title,
    dep.department_name,
    COUNT(DISTINCT e.employee_id) AS employee_count,
    ROUND((COUNT(DISTINCT e.employee_id)::numeric / 441) * 100, 1) AS share_pct
FROM dw.dim_employee e
JOIN dw.dim_role r ON r.role_key = e.role_key
JOIN dw.dim_department dep ON dep.department_key = e.department_key
WHERE e.is_current = TRUE AND e.is_active = TRUE
GROUP BY r.role_title, dep.department_name
ORDER BY employee_count DESC, r.role_title;
