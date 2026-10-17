-- Q3. What was the company attendance rate each month?
-- Divide the sums, never average the per-row rates.
SELECT d.year_month,
       round((sum(f.present_days) + 0.5 * sum(f.half_days_unpaid)) / sum(f.scheduled_days), 4) AS attendance_rate
FROM dw.fact_attendance_monthly f
JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY d.year_month
ORDER BY d.year_month;
