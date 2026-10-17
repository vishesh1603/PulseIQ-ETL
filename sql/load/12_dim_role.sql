-- target: dw.dim_role
-- key: role_id
-- stage: stg_dim_role
SELECT r.role_id, d.department_key, r.role_title, r.level::smallint AS role_level, r.grade,
       r.band_min_annual, r.band_mid_annual, r.band_max_annual,
       r.overtime_eligible = 'Y' AS overtime_eligible, r.band_reference_year::smallint AS band_reference_year
FROM stg_dim_role r
JOIN dw.dim_department d ON d.department_id = r.department_id
