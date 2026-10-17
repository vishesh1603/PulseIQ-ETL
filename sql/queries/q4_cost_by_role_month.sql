-- Q4. Which roles cost the most each month, and how many people hold them?
SELECT d.year_month,
       r.role_title,
       count(*)             AS employees_paid,
       sum(f.employer_cost) AS employer_cost
FROM dw.fact_payroll f
JOIN dw.dim_date d ON d.date_key = f.date_key
JOIN dw.dim_role r ON r.role_key = f.role_key
GROUP BY d.year_month, r.role_title
ORDER BY d.year_month, employer_cost DESC;
