-- target: dw.dim_department
-- key: department_id
-- stage: stg_dim_department
SELECT department_id, department_name, cost_center, description, is_leadership = 'Y' AS is_leadership
FROM stg_dim_department
