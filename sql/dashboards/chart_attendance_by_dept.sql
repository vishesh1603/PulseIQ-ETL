-- Chart: Department Attendance Rate Comparison (Latest Month: 2026-09)
-- Ranks departments by attendance rate, showing engagement levels and late arrival rate
SELECT 
    d.department_name,
    ROUND((SUM(f.present_days) + 0.5 * SUM(f.half_days_unpaid)) / SUM(f.scheduled_days) * 100, 2) AS attendance_rate_pct,
    ROUND(SUM(f.late_arrivals)::numeric / SUM(f.present_days) * 100, 2) AS late_rate_pct,
    ROUND(SUM(f.unpaid_absence_days + 0.5 * f.half_days_unpaid), 1) AS unpaid_leave_days,
    COUNT(DISTINCT f.employee_id) AS active_employees
FROM dw.fact_attendance_monthly f
JOIN dw.dim_department d ON d.department_key = f.department_key
WHERE f.date_key = 20260930
GROUP BY d.department_name
ORDER BY attendance_rate_pct DESC;
