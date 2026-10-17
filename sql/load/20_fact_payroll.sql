-- target: dw.fact_payroll
-- key: employee_id, date_key
-- stage: stg_fact_payroll
-- mirror: true
-- The joins are also existence checks: a payroll row with an unknown date, employee version,
-- department or role is lost by the join, and the loader stops with an error.
SELECT s.employee_id, s.date_key, s.payroll_item_id, s.run_id, s.employee_key, d.department_key, r.role_key,
       s.variable_pay_type, s.payable_days, s.lop_days, s.overtime_hours_paid, s.monthly_fixed_gross, s.basic, s.hra,
       s.conveyance, s.medical, s.special_allowance, s.earned_fixed_pay, s.overtime_pay, s.variable_pay, s.gross_pay,
       s.pf_employee, s.esi_employee, s.professional_tax, s.tds, s.other_deductions, s.total_deductions, s.net_pay,
       s.pf_employer, s.esi_employer, s.employer_cost, s.headcount_flag::smallint AS headcount_flag
FROM stg_fact_payroll s
JOIN dw.dim_date dt        ON dt.date_key = s.date_key
JOIN dw.dim_employee e     ON e.employee_key = s.employee_key
JOIN dw.dim_department d   ON d.department_id = s.department_id
JOIN dw.dim_role r         ON r.role_id = s.role_id
