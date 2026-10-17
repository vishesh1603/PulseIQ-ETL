-- target: dw.dim_employee
-- key: employee_key
-- stage: stg_dim_employee
-- Each source row is one version of an employee. Open versions have a blank valid_to in the clean
-- files, and get the conventional 9999-12-31 here so date-range joins need no NULL handling.
SELECT s.employee_key, s.employee_id, s.full_name, s.gender, s.date_of_birth, s.hire_date, s.exit_date,
       s.employment_status, s.employment_type, d.department_key, r.role_key, s.role_title, s.job_level::smallint AS job_level,
       s.manager_id, s.work_location, s.work_mode, s.highest_education, s.valid_from,
       COALESCE(s.valid_to, DATE '9999-12-31') AS valid_to, s.is_current = 'Y' AS is_current, s.change_reason,
       s.hire_year::smallint AS hire_year, s.hire_month::smallint AS hire_month, s.tenure_days::integer AS tenure_days,
       s.tenure_years, s.is_active
FROM stg_dim_employee s
JOIN dw.dim_department d ON d.department_id = s.department_id
JOIN dw.dim_role r       ON r.role_id = s.role_id
