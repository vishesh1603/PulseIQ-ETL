-- Chart: Leave Days by Leave Type
-- Shows total volume of paid vs unpaid leaves utilized across the organization
SELECT 
    lt.leave_type_name,
    lt.pay_type,
    COUNT(*) AS total_requests,
    ROUND(SUM(f.days), 1) AS total_leave_days,
    ROUND(SUM(f.days)::numeric / SUM(SUM(f.days)) OVER () * 100, 1) AS days_share_pct
FROM dw.fact_leave f
JOIN dw.dim_leave_type lt ON lt.leave_type_key = f.leave_type_key
GROUP BY lt.leave_type_name, lt.pay_type
ORDER BY total_leave_days DESC;
