-- Chart: M13 Attendance Rate Trend with 3-Month Rolling Average
-- Grain: Month
WITH monthly AS (
    SELECT 
        d.year_month,
        d.month_end_date,
        SUM(f.present_days) AS present,
        SUM(f.half_days_unpaid) AS half_unpaid,
        SUM(f.scheduled_days) AS scheduled,
        ROUND((SUM(f.present_days) + 0.5 * SUM(f.half_days_unpaid)) / SUM(f.scheduled_days) * 100, 2) AS attendance_rate_pct
    FROM dw.fact_attendance_monthly f
    JOIN dw.dim_date d ON d.date_key = f.date_key
    GROUP BY d.year_month, d.month_end_date
)
SELECT 
    year_month,
    month_end_date,
    attendance_rate_pct,
    ROUND(AVG(attendance_rate_pct) OVER (ORDER BY year_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS rolling_3m_avg_pct
FROM monthly
ORDER BY year_month;
