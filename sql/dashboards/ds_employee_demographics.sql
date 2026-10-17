-- Dataset: Employee Demographics (Active Workforce)
-- Used for: Tenure Bands (Bar) and Role Mix (Bar).
SELECT
    e.employee_id,
    e.full_name,
    dep.department_id,
    dep.department_name,
    r.role_id,
    r.role_title,
    r.role_level,
    e.gender,
    e.work_mode,
    e.work_location,
    e.hire_date,
    e.tenure_years,
    CASE
        WHEN e.tenure_years < 1 THEN 'Under 1 yr'
        WHEN e.tenure_years < 3 THEN '1-3 yrs'
        WHEN e.tenure_years < 5 THEN '3-5 yrs'
        WHEN e.tenure_years < 10 THEN '5-10 yrs'
        ELSE '10+ yrs'
    END AS tenure_band,
    CASE
        WHEN e.tenure_years < 1 THEN 1
        WHEN e.tenure_years < 3 THEN 2
        WHEN e.tenure_years < 5 THEN 3
        WHEN e.tenure_years < 10 THEN 4
        ELSE 5
    END AS tenure_band_order
FROM dw.dim_employee e
JOIN dw.dim_department dep ON dep.department_key = e.department_key
JOIN dw.dim_role r ON r.role_key = e.role_key
WHERE e.is_current = TRUE AND e.is_active = TRUE;
