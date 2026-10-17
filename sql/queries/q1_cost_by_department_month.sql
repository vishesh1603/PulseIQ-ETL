-- Q1. What did each department cost per month?
SELECT d.year_month,
       dep.department_name,
       count(*)             AS employees_paid,
       sum(f.employer_cost) AS employer_cost
FROM dw.fact_payroll f
JOIN dw.dim_date d         ON d.date_key = f.date_key
JOIN dw.dim_department dep ON dep.department_key = f.department_key
GROUP BY d.year_month, dep.department_name
ORDER BY d.year_month, dep.department_name;
