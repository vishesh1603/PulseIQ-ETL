-- Q2. How many people did each department have on the last day of each month?
SELECT d.year_month,
       dep.department_name,
       h.headcount_end
FROM dw.fact_headcount_monthly h
JOIN dw.dim_date d         ON d.date_key = h.date_key
JOIN dw.dim_department dep ON dep.department_key = h.department_key
ORDER BY d.year_month, dep.department_name;
