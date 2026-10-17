-- Chart: Leave Requests by Start Day of Week
-- Tests for weekend-adjacent leave patterns (e.g. Monday and Friday concentrations)
SELECT 
    d.day_of_week,
    COUNT(*) AS total_requests,
    ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 1) AS request_pct,
    ROUND(SUM(f.days), 1) AS total_leave_days,
    ROUND(AVG(f.days), 2) AS avg_duration_days
FROM dw.fact_leave f
JOIN dw.dim_date d ON d.date_key = f.start_date_key
GROUP BY d.day_of_week
ORDER BY 
    CASE d.day_of_week 
        WHEN 'Monday' THEN 1 
        WHEN 'Tuesday' THEN 2 
        WHEN 'Wednesday' THEN 3 
        WHEN 'Thursday' THEN 4 
        WHEN 'Friday' THEN 5 
        WHEN 'Saturday' THEN 6 
        WHEN 'Sunday' THEN 7 
    END;
