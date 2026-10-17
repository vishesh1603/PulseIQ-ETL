-- Dataset: ds_attendance_monthly
-- Used for attendance rate trends, rolling metrics, and departmental comparisons
SELECT 
    f.attendance_fact_id,
    f.employee_id,
    f.date_key,
    d.full_date AS month_end_date,
    d.year,
    d.month_number,
    d.year_month,
    dep.department_id,
    dep.department_name,
    f.scheduled_days,
    f.present_days,
    f.wfh_days,
    f.half_days_unpaid,
    f.paid_leave_days,
    f.unpaid_absence_days,
    f.late_arrivals,
    f.avg_hours_worked,
    f.overtime_hours,
    f.attendance_rate
FROM dw.fact_attendance_monthly f
JOIN dw.dim_date d ON d.date_key = f.date_key
JOIN dw.dim_department dep ON dep.department_key = f.department_key;
