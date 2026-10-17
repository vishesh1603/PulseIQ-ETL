-- Chart: AI Anomaly Flags by Month & Reason Code (M26)
-- Grain: Month x Reason Code
SELECT 
    d.year_month,
    d.month_end_date,
    a.reason_code,
    COUNT(*) AS flag_count
FROM dw.fact_anomaly a
JOIN dw.dim_date d ON d.date_key = a.period_key
WHERE a.source_dataset = 'attendance_monthly_features'
GROUP BY d.year_month, d.month_end_date, a.reason_code
ORDER BY d.year_month, flag_count DESC;
