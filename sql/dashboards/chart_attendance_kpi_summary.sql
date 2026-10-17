-- Chart: KPI Summary Cards for Attendance & Leave (Latest Month: 2026-09)
-- Metrics: M13 (Attendance Rate), M14 (Late Arrival Rate), M15 (Unpaid Leave Days), M26 (Anomaly Flags)
SELECT 
    '2026-09' AS year_month,
    ROUND((SUM(present_days) + 0.5 * SUM(half_days_unpaid)) / SUM(scheduled_days) * 100, 1) AS attendance_rate_pct,
    ROUND(SUM(late_arrivals)::numeric / SUM(present_days) * 100, 1) AS late_arrival_rate_pct,
    ROUND(SUM(unpaid_absence_days + 0.5 * half_days_unpaid), 1) AS unpaid_leave_days,
    (SELECT COUNT(*) FROM dw.fact_anomaly WHERE period_key = 20260930 AND source_dataset = 'attendance_monthly_features') AS anomaly_count
FROM dw.fact_attendance_monthly
WHERE date_key = 20260930;
