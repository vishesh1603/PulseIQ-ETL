-- target: dw.fact_leave
-- key: leave_request_id
-- stage: stg_fact_leave
-- mirror: true
-- Four dates, one date dimension: each join below plays a different role.
-- The department comes from the employee version valid at the start date.
SELECT s.leave_request_id, s.employee_id, s.employee_key, e.department_key, lt.leave_type_key,
       s.start_date_key, s.end_date_key, ad.date_key AS applied_date_key, dd.date_key AS decided_date_key,
       s.days, s.calendar_days::integer AS calendar_days, s.status, s.approver_id, s.reason
FROM stg_fact_leave s
JOIN dw.dim_employee e      ON e.employee_key = s.employee_key
JOIN dw.dim_leave_type lt   ON lt.leave_type_code = s.leave_type_code
JOIN dw.dim_date sd         ON sd.date_key = s.start_date_key
JOIN dw.dim_date ed         ON ed.date_key = s.end_date_key
JOIN dw.dim_date ad         ON ad.full_date = s.applied_on
LEFT JOIN dw.dim_date dd    ON dd.full_date = s.decided_on
