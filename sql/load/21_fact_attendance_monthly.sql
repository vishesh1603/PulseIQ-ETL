-- target: dw.fact_attendance_monthly
-- key: employee_id, date_key
-- stage: stg_fact_attendance_monthly
-- mirror: true
SELECT s.employee_id, s.date_key, s.attendance_fact_id, s.employee_key, d.department_key,
       s.scheduled_days, s.present_days, s.wfh_days, s.half_days_unpaid, s.paid_leave_days, s.unpaid_absence_days,
       s.late_arrivals, s.avg_hours_worked, s.overtime_hours, s.attendance_rate
FROM stg_fact_attendance_monthly s
JOIN dw.dim_date dt      ON dt.date_key = s.date_key
JOIN dw.dim_employee e   ON e.employee_key = s.employee_key
JOIN dw.dim_department d ON d.department_id = s.department_id
