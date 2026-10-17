# Warehouse design (Task 2)

Diagram: `warehouse_schema.svg` (also `.png`, source in `warehouse_schema.dot`). Table SQL: `sql/001_schema.sql`. Load logic: `sql/load/`.

## Grain of every fact

| Fact | One row per... | Natural key | Where it comes from |
|------|----------------|-------------|---------------------|
| fact_payroll | employee per pay month | employee_id, date_key | clean `fact_payroll` |
| fact_attendance_monthly | employee per month | employee_id, date_key | clean `fact_attendance_monthly` |
| fact_leave | leave request | leave_request_id | clean `fact_leave` |
| fact_headcount_monthly | department per month | date_key, department_key | derived inside the warehouse from `dim_employee` |

The task text suggests attendance at one row per employee per day. The data has monthly summaries only, so the grain stays monthly. Daily rows would have to be invented, and a made-up grain is worse than an honest coarse one. If daily attendance arrives later it becomes a new fact, `fact_attendance_daily`, next to this one.

Monthly facts point at the last day of the month (`date_key` = 20250430), so one `dim_date` row serves every monthly fact and `is_month_end` marks them.

## Dimensions and keys

| Dimension | One row per | Surrogate key | Business key | Change handling |
|-----------|-------------|---------------|--------------|-----------------|
| dim_date | calendar day | date_key (yyyymmdd) | full_date | none |
| dim_department | department | department_key (warehouse identity) | department_id | Type 1, overwrite |
| dim_role | role | role_key (warehouse identity) | role_id | Type 1, overwrite |
| dim_leave_type | leave type | leave_type_key (warehouse identity) | leave_type_code | Type 1, overwrite |
| dim_employee | employee **version** | employee_key | employee_id + valid_from | Type 2, history kept |

One choice to know about: for `dim_employee` the warehouse reuses the version key that the source system already assigns, instead of minting its own. It is unique per version and stable between loads, which keeps the upsert simple. The other three dimensions get warehouse-owned keys, and the load files translate business keys into surrogate keys.

## Dimension history (Type 2)

Each row of `dim_employee` is one period of an employee's life: a department, a role, a manager. The columns `valid_from` and `valid_to` say when that version was true, and `valid_to = 9999-12-31` means it is still open. Task 1 stores open versions as blank because pandas cannot hold that date, and the warehouse load puts the convention back.

The database itself enforces clean history:

- `UNIQUE (employee_id, valid_from)`
- `CHECK (valid_to >= valid_from)`
- an exclusion constraint that rejects two versions of the same employee covering the same day (checked at commit, so a load can update an old version and insert the next one in one transaction)

## Department moves: May's cost and July's cost

Question: an employee moves from Sales to Support in June. How should May's and July's cost be reported?

**May's cost stays in Sales and July's cost goes to Support. Nothing is rewritten.** Each payroll row stores the `employee_key` of the version that was valid in its month, plus the `department_key` of that version. When the employee moves, the Sales version is closed (`valid_to` = 31 May) and a new Support version is opened (`valid_from` = 1 June). New payroll rows point at the new version. Old rows keep pointing at the old one. A report that groups by department therefore splits the cost by itself.

If the dimension kept only the current department (Type 1), every past month would silently move to Support, and Sales' history would shrink after the fact. That is the failure Type 2 prevents.

**June, the month of the move, goes to Support in full.** Payroll is attributed to the version valid on the last day of the month. This is a rule, not an accident, and it matches how the source data is built: a pay row carries one department. The alternative is to prorate by days (for a move on 4 Feb, 3 days to the old department and 25 to the new). That needs a day-level split of pay and is a business decision, so it is not done here. Headcount follows the same last-day rule, and `fact_headcount_monthly` also records the move itself in `transfers_out` for Sales and `transfers_in` for Support, so the flow is visible.

A real example from the data: EMP-0194 moved from Data & AI to Product & Design on 4 February 2026. Their January pay row sits under Data & AI and their February row under Product & Design. The query that shows it:

```sql
SELECT d.year_month, dep.department_name, f.employer_cost, e.valid_from, e.valid_to
FROM dw.fact_payroll f
JOIN dw.dim_date d         ON d.date_key = f.date_key
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_employee e     ON e.employee_key = f.employee_key
WHERE f.employee_id = 'EMP-0194' AND d.year_month BETWEEN '2025-12' AND '2026-04'
ORDER BY d.year_month;
```

The sample data has the same story with EMP-0005 (Sales to Support on 1 June 2025), and `test_department_move_splits_cost_by_month` checks it.

## How the load works

`python -m pulseiq_etl` loads the warehouse when `WAREHOUSE_DSN` is set (Compose sets it for you). Steps, all inside one database transaction, so any error leaves the warehouse exactly as it was:

1. Run `sql/001_schema.sql`. It does nothing when the tables already exist.
2. Copy each clean table into a temporary staging table.
3. For each file in `sql/load/`, in filename order (dimensions, then facts, then the derived headcount fact):
   - run its SELECT, which turns business keys into surrogate keys
   - stop with an error if any row was lost in the lookups (a fact pointing at a department, employee version or date that does not exist)
   - delete warehouse rows that are no longer in the feed (facts only, marked `mirror: true`)
   - `INSERT ... ON CONFLICT (key) DO UPDATE`, changing only rows whose values differ
   - check that every feed row now exists in the warehouse
4. Run `ANALYZE`.

Because the key is the natural key of each table, repeating a load inserts, updates and deletes nothing. The run log (`logs/last_run.json`, section `warehouse`) shows inserted, updated, unchanged and deleted per table.

Dimension rows are never deleted. A fact may still point at them, and the database would refuse the delete.

## Indexes

Primary keys and unique constraints already carry indexes. Added on top, each with a reason:

| Index | Why |
|-------|-----|
| fact_payroll (date_key), (department_key, date_key), (employee_key), (role_key, date_key) | month filters, department by month, one person's history, role by month |
| fact_attendance_monthly (date_key), (department_key, date_key), (employee_key) | same pattern |
| fact_leave (employee_id), (employee_key), (department_key, start_date_key), (leave_type_key), (start_date_key) | leave per person, department, type and period |
| fact_headcount_monthly (department_key, date_key) | department trend |
| dim_employee (employee_id), (department_key), (role_key), partial index on current versions | all versions of a person, department and role lookups, "who is here now" |
| dim_date (year_month), partial index on month ends | month filters, month-end lookups |

At about 7,000 payroll rows PostgreSQL may still choose a full table scan, which is fine and fast. The indexes matter as the data grows. To see which a query uses, put `EXPLAIN` in front of it.

## Reporting views

`dw.v_payroll`, `dw.v_attendance`, `dw.v_headcount` and `dw.v_leave` join each fact to its dimensions, so Task 3's dashboards can start from one flat table.

## Things to know

- **Derived headcount.** `fact_headcount_monthly` is built from `dim_employee`, never loaded from a file. It reproduces the workbook's own `fact_headcount_monthly` sheet exactly for all 891 department-month rows. The only difference is one rounding case: an attrition rate of exactly 3.125 is 3.12 in the workbook (Python rounds half to even) and 3.13 in PostgreSQL (rounds half up).
- **Mirroring.** If Task 1 starts rejecting a payroll row that it accepted before, the next load deletes that row from the warehouse. The warehouse always equals the clean files.
- **Not loaded.** Ledger, invoice, expense, task and forecast sheets are outside Tasks 1 and 2.
