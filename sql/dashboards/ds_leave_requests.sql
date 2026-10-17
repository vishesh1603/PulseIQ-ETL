-- Dataset: ds_leave_requests
-- Used for leave distribution by type, weekday patterns, and departmental breakdowns
SELECT 
    f.leave_request_id,
    f.employee_id,
    f.employee_key,
    e.full_name,
    dep.department_id,
    dep.department_name,
    lt.leave_type_code,
    lt.leave_type_name,
    lt.pay_type,
    f.start_date_key,
    f.end_date_key,
    sd.full_date AS start_date,
    ed.full_date AS end_date,
    sd.day_of_week AS start_day_of_week,
    sd.year_month AS start_year_month,
    sd.year AS start_year,
    f.days,
    f.calendar_days,
    f.status,
    f.approver_id,
    f.reason
FROM dw.fact_leave f
JOIN dw.dim_leave_type lt ON lt.leave_type_key = f.leave_type_key
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_employee e ON e.employee_key = f.employee_key
JOIN dw.dim_date sd ON sd.date_key = f.start_date_key
JOIN dw.dim_date ed ON ed.date_key = f.end_date_key;
