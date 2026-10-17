# Questions the warehouse must answer

Written first, because they decide which tables exist. Each question names the fact and the dimensions it needs.

| # | Question a leader asks | Fact | Dimensions | Query |
|---|------------------------|------|------------|-------|
| 1 | What did each department cost per month? | fact_payroll | dim_date, dim_department | `sql/queries/q1_cost_by_department_month.sql` |
| 2 | How many people does each department have, month by month? | fact_headcount_monthly | dim_date, dim_department | `q2_headcount_by_department_month.sql` |
| 3 | What was attendance each month? | fact_attendance_monthly | dim_date | `q3_attendance_rate_by_month.sql` |
| 4 | Which roles cost the most? | fact_payroll | dim_date, dim_role | `q4_cost_by_role_month.sql` |
| 5 | What share of people left each month? | fact_headcount_monthly | dim_date, dim_department | column `attrition_rate_monthly_pct` |
| 6 | How much leave was taken, by type and department? | fact_leave | dim_leave_type, dim_department, dim_date | view `dw.v_leave` |
| 7 | Where did people move between departments, and what did that do to each department's headcount? | fact_headcount_monthly | dim_date, dim_department | columns `transfers_in`, `transfers_out` |
| 8 | What did one person cost in each department they worked in? | fact_payroll | dim_employee (history), dim_department, dim_date | see "Department moves" in `warehouse_design.md` |
| 9 | Which invoices are overdue or overpaid? | fact_invoice | dim_client, dim_date | Not in Task 1 data, so not loaded yet. Add a Spec in `config.py`, a load file in `sql/load/`, and a table in `001_schema.sql`. |
