# PulseIQ ETL and warehouse (Tasks 1 and 2)

Pandas pipeline that reads the PulseIQ star-schema workbook, cleans it, validates it with pandera, writes clean files, rejected rows, repaired values and a run log, and loads a PostgreSQL star-schema warehouse.

```
docker compose run --rm etl
```

## Quick start

```bash
cp .env.example .env
# put PulseIQ_Star_Schema_Dataset.xlsx in data/raw/   (or: python scripts/download_sheets.py)
docker compose build
docker compose run --rm etl                 # clean the data and load the warehouse
docker compose exec warehouse psql -U pulseiq -d pulseiq -c "\dt dw.*"   # list the warehouse tables
docker compose run --rm etl pytest -q       # run the tests (they wipe and rebuild schema dw, so run the ETL again afterwards)
```

Without Docker: `pip install -r requirements.txt`, then `set PYTHONPATH=src` and `python -m pulseiq_etl` on Windows (`PYTHONPATH=src python -m pulseiq_etl` on Linux or Mac). Leave `WAREHOUSE_DSN` empty to skip the warehouse.

No workbook yet? `python scripts/make_sample_data.py --out data/raw` writes a small sample with planted defects, one CSV per table.

## Inputs and outputs

The pipeline reads `<table>.csv` or a sheet called `<table>` from any `.xlsx` in `data/raw/`. Eight tables are processed:

| Table | Role | Notes |
|-------|------|-------|
| dim_employee | Employee master | One row per version of an employee (SCD Type 2) |
| fact_payroll | Salary and payroll | One row per employee per month, 33 columns. Salary components are in here, so there is no separate salary file |
| fact_attendance_monthly | Attendance | Monthly summary per employee, not daily |
| fact_leave | Leave requests | One row per request |
| dim_department, dim_role, dim_leave_type | Reference data | Used to check the facts, and loaded into the warehouse |
| dim_date | Calendar | One row per day, with financial year and working-day flags |

Clean files go to `data/clean/<table>.parquet`. Per table, `data/rejected/` gets `<table>_rejected.csv` and `<table>_repaired.csv` (header only when empty). The reconciliation sheet is read if present and never loaded.

Other sheets in the workbook (ledger, invoices, tasks, AI feeds) are outside Task 1. To add one, add a `Spec` in `config.py`, a transform function, and a schema in `validate.py`.

## Layout

```
src/pulseiq_etl/
  config.py       table definitions (column kinds, required columns, keys), settings
  extract.py      read CSV or workbook sheets as text, log row counts
  transform.py    types, duplicates, rules, repairs, helper columns
  validate.py     pandera schemas, fails loudly
  load.py         atomic writes of clean, rejected and repaired files
  run_log.py      logs/run_log.jsonl and logs/last_run.json
  pipeline.py     runs the steps in order, checks payroll totals
scripts/          make_sample_data.py, download_sheets.py
tests/            sample-data tests, plus a real-workbook test (set PULSEIQ_WORKBOOK)
docs/metric_dictionary.md
```

## What each step does

1. Extract. Reads every table as text, snake_cases headers, keeps only the columns in the table definition (extra columns are logged and ignored), and logs row counts. A missing table or required column stops the run with a message naming it.
2. Transform. Trims and upper-cases codes, collapses spaces, title-cases categories, reads dates and numbers (currency symbols and commas allowed), and applies the rules in the next sections. Helper columns:
   - dim_employee: `hire_year`, `hire_month`, `tenure_days`, `tenure_years`, `is_active`
   - fact_payroll and fact_attendance_monthly: `year`, `month`, `month_start`
   - fact_leave: `start_year`, `start_month`, `calendar_days`
3. Validate. Pandera schemas run on the cleaned tables: types, non-negative amounts, allowed categories, unique keys, arithmetic (net = gross - deductions, gross = parts, cost = gross + employer contributions), one current version per employee, version history without gaps or overlaps, and hire/exit dates in order. All failures are collected and printed together, then the run stops with exit code 1 and nothing is written to `data/clean/`.
4. Check totals. If the workbook has `reconciliation_answer_key`, monthly employees paid, gross, net and employer cost are compared with it. The result goes to the run log. With `RECONCILE_STRICT=true` a mismatch fails the run.
5. Load. Clean tables are written to temp files and swapped in together, sorted by their natural key, so a failed run leaves the previous output intact.

## Three outcomes for a bad row

Reject, repair, or warn. The rule is: repair only when the data itself proves the fix. Otherwise reject.

**Rejected** rows are copied with their raw values to `<table>_rejected.csv`, with `source_row` (line number in the sheet) and `reject_reason`. A row can have several reasons joined with `;`.

| Reason | Meaning |
|--------|---------|
| missing_X, bad_X | A required value is empty, or cannot be read as the right type |
| exact_duplicate | Same values as an earlier row, apart from the surrogate id. The first copy is kept |
| conflicting_duplicate | Same key, different values. Every copy is rejected because the right one is unknown |
| unknown_employee, unknown_employee_key, employee_key_belongs_to_other_employee | Fact row points at no employee, or at someone else's version |
| department_differs_from_employee_version, role_differs_from_employee_version | Fact row disagrees with the employee version it points to |
| activity_after_exit_month, activity_before_hire | Pay or attendance outside the employee's time with the company |
| exit_before_hire | Employee dates conflict (see below) |
| negative_amount, negative_value | Pay or attendance figure below zero |
| *_differs_from_*, *_mismatch | Arithmetic does not add up |
| end_before_start | Leave dates in the wrong order, and the date keys do not prove which is right |

**Repaired** values go to `<table>_repaired.csv` with old and new value:

- dim_employee: when a version overlaps the next one, it is closed the day before the next starts. This is the fix the workbook's own DQ catalog (DQ-C12) prescribes.
- fact_leave: when start and end dates are swapped and the two `*_date_key` columns agree with the swapped order, the dates are swapped back. The keys are an independent copy of the dates, so they prove the original order.

**Warnings** appear in the run log without blocking a row. Currently: leave requests that were approved or rejected without an approver id.

The run stops if any table rejects more than `MAX_REJECT_PCT` percent of its rows (default 10). A sudden jump usually means a broken export.

## Employee exit date before hire date

Decision: reject the employee's rows, do not guess a fix, and keep the history out of the clean tables until HR corrects the source.

- Dropping without a trace hides the problem, and the person still appears in payroll and attendance.
- Fixing needs a guess. Either date could be wrong, or the two could be swapped, and a wrong guess looks like valid data. Tenure, headcount and attrition would all be off with no sign of it.
- Keeping the row with a flag leaves a bad row in every headcount query unless each query remembers to filter it.

So every version of that employee goes to `dim_employee_rejected.csv` as `exit_before_hire`. Their payroll, attendance and leave rows are rejected as `unknown_employee`, so the clean tables never contain a person who is missing from the employee table. The cost is that their pay drops out of cost totals until the source is fixed. That is why rejects are counted in the run log and capped.

The same reasoning separates this from the swapped leave dates above. There, a second column independently proves the right order. For employee dates, nothing does.

## Other choices worth knowing

- **Open versions.** The workbook marks an open employee version with `valid_to = 9999-12-31`. pandas cannot hold that date, so the clean `valid_to` is blank for open versions. Task 2 can restore the 9999-12-31 convention when it builds the warehouse.
- **Missing values.** `highest_education` blank becomes `Not stated`. `variable_pay_type` blank becomes `None` when `variable_pay` is 0, and a blank with pay above 0 is rejected. Every fill is counted in the run log under `missing_values_filled`. `manager_id`, `exit_date`, `decided_on` and `approver_id` stay blank because blank is meaningful there.
- **Categories.** A new value in a closed list (gender, status, work mode, leave status and so on) stops the run through pandera. A new category usually means the data contract changed, and a person should look at it.
- **Checks not done here.** Payroll against the ledger (DQ-C01) and the other ledger, invoice and task checks need tables that Task 1 does not load. The reconciliation step covers payroll totals meanwhile.

## Repeatable runs

- Output depends only on the input files, `AS_OF_DATE` and the settings. No timestamps or random values go into the data files.
- If `AS_OF_DATE` is empty, the reference date for tenure is the latest period in payroll and attendance (30 Sep 2026 for this workbook), not today's date.
- Outputs are overwritten, never appended. Running twice does no harm.
- Each run records a hash of the inputs and of every output file. If the inputs match the previous successful run, the log records `identical_to_previous_run: true`, or warns if the outputs differ. `tests/test_pipeline.py` checks this.

## Run log

`logs/run_log.jsonl` gets one JSON line per run, and `logs/last_run.json` holds the latest one formatted. Fields: `run_id`, `started_at`, `finished_at`, `duration_seconds`, `status` (SUCCESS or FAILED), `error`, `as_of_date`, `input_files` (name, rows, sha256), and per table `rows_in`, `rows_out`, `rows_rejected`, `rejected_pct`, `reject_reasons`, `values_repaired`, `missing_values_filled`, `warnings`. It also has `reconciliation`, `outputs` (with hashes) and `identical_to_previous_run`. Console output is also saved to `logs/etl.log`.

## Warehouse (Task 2)

Files: `sql/001_schema.sql` (tables, indexes, views), `sql/load/*.sql` (one load file per table), `src/pulseiq_etl/warehouse.py` (the loader), `sql/queries/` (four sample questions), `docs/`.

- `docs/warehouse_schema.svg` is the diagram, with the grain of every fact table.
- `docs/warehouse_design.md` explains the grains, keys, dimension history, the department-move rule, the upsert design and the indexes.
- `docs/warehouse_questions.md` lists the questions the warehouse is built to answer.

The warehouse is PostgreSQL 16 in the `warehouse` Compose service. From your PC it listens on `localhost:5433` (user and database `pulseiq`, password from `.env`), so you can connect with DBeaver or psql. Run a sample query:

```
docker compose exec -T warehouse psql -U pulseiq -d pulseiq < sql\queries\q1_cost_by_department_month.sql
```

Repeating `docker compose run --rm etl` is safe: the second run reports 0 inserted, 0 updated and 0 deleted for every table in `logs/last_run.json`, section `warehouse`.

`tests/test_warehouse.py` needs the database (Compose provides it). It checks that SQL answers match the clean files, that a repeated load changes nothing, that a renamed department is updated and a vanished payroll row is deleted, that the database refuses overlapping history and orphan facts, and that a department move splits cost by month. With `PULSEIQ_WORKBOOK` set it also checks the warehouse against the workbook's own headcount sheet, reconciliation key and department summary.

## Metric dictionary

See `docs/metric_dictionary.md`.

## Apache Superset Dashboards (Task 3)

Apache Superset runs in Docker at **http://localhost:8088**.
- **Admin Login**: Username `admin`, Password `admin` (configured via `.env`)
- **Warehouse Access**: Connects via least-privilege read-only user `superset_ro` (`sql/002_superset_ro.sql`) restricted to `SELECT` on schema `dw`.
- **Dashboard**: **Headcount & Departments** (`/superset/dashboard/headcount-and-departments/`) featuring 4 top KPI cards (M01 Headcount, M02 Joiners, M03 Leavers, M04 Attrition Rate), monthly headcount trend, department split, tenure bands, role mix, monthly joiners vs leavers, and cross-filters for Department and Date Range.

### Re-importing the dashboard
The dashboard definition is version-controlled in `dashboards/`. To import it into Superset:
```bash
docker compose exec superset superset import-dashboards -p /app/dashboards/dashboard_export.zip -u admin
```
Or to regenerate all datasets, charts, and layout positions from the SQL definitions:
```bash
docker compose exec superset python3 /app/scripts/build_superset_dashboard.py
```

### Exporting dashboards
To export dashboard updates from Superset back into the repo:
```bash
docker compose exec superset superset export-dashboards -f /app/dashboards/dashboard_export.zip
```
On Windows PowerShell, unpack the YAML bundle into `dashboards/`:
```powershell
Expand-Archive -Path dashboards\dashboard_export.zip -DestinationPath dashboards\ -Force
```

### Verifying dashboard KPIs against the warehouse
Execute the automated test suite asserting that every KPI value and takeaway matches database reality:
```bash
docker compose run --rm etl pytest -v tests/test_dashboard_kpis.py
```

## Attendance & Leave Trends Dashboard & AI Anomaly Pipeline (Task 4)

Task 4 extends PulseIQ with machine learning anomaly ingestion (`dw.fact_anomaly`), time-series attendance smoothing, and weekday leave patterns.

- **Dashboard**: **Attendance & Leave Trends** (`/superset/dashboard/attendance-and-leave/`) featuring:
  - 4 Executive KPI cards: M13 Attendance Rate (95.2%), M14 Late Arrival Rate (7.1%), M15 Unpaid Leave Days (85.5 days), and M26 AI Anomaly Flags (10).
  - Monthly attendance rate trajectory with 3-month trailing moving average.
  - Stacked time-series breakdown of AI anomalies by reason code (`PATTERN_SHIFT`, `NO_ATTENDANCE`, `LONG_UNPAID_ABSENCE`, `FREQUENT_LATE`).
  - Total leave days by leave category (Earned Leave 32.7%, Casual Leave 27.8%, Sick Leave 24.5%).
  - Leave start day concentration analysis (Friday 20.9%, Thursday 20.7%, Monday 18.9%).
  - Departmental attendance benchmark ranking for September 2026.
  - Interactive cross-filters for Department, Time Period, and Leave Type.

### Ingesting AI Anomaly Predictions
Load the 405 machine learning anomaly records into PostgreSQL:
```bash
docker compose run --rm etl python scripts/load_fact_anomaly.py
```

### Rebuilding or Importing the Attendance Dashboard
To rebuild the datasets and dashboard programmatically:
```bash
docker compose exec superset python scripts/build_attendance_dashboard.py
```
Or import from the exported ZIP bundle:
```bash
docker compose exec superset superset import-dashboards -p /app/dashboards/attendance_dashboard_export.zip -u admin
```

### Verifying Attendance KPIs against the warehouse
Run the automated test suite verifying all attendance checkpoints and warehouse counts:
```bash
docker compose run --rm etl pytest -v tests/test_attendance_kpis.py
```

### Executive Insight Briefing
Read the 1-page executive analytical brief in `reports/insights-attendance.md` (and `docs/attendance_insights.md`) for empirical findings, operational recommendations, and data caveats.

---

## Handoff Package (Foundation Phase: Phase 1)

In accordance with Section 4 of the *PulseIQ — Data Analyst Guide*, all deliverables are version-controlled in the repository:

| Item | When | Published Location | Content |
|:---|:---|:---|:---|
| **Metric Dictionary** | Task 1–4 (ongoing to Task 17) | [`docs/metric_dictionary.md`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/docs/metric_dictionary.md) | Official metric names, formulas, warehouse SQL, and check values (M01, M04, M07, M09, M13, M14, M15, M26). |
| **Warehouse Schema Diagram** | Task 2 | [`docs/warehouse-schema.md`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/docs/warehouse-schema.md) | Schema design, fact grains in one sentence, SCD Type 2 history, and [SVG diagram](file:///c:/Users/DELL/Downloads/pulseiq-etl1/docs/warehouse_schema.svg). |
| **Visual Style Guide** | Task 3 | [`docs/style_guide.md`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/docs/style_guide.md) | Okabe-Ito color-blind safe palette, typography, Indian number formatting, and title+takeaway rule. |
| **Design Review & Notes** | Task 3 | [`docs/design-notes.md`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/docs/design-notes.md) | Wireframe AI prompt, 6-point self-review, and changes made ([`docs/design_review.md`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/docs/design_review.md)). |
| **Dashboard Exports** | Tasks 3 & 4 | [`dashboards/headcount.zip`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/dashboards/headcount.zip)<br>[`dashboards/attendance_dashboard_export.zip`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/dashboards/attendance_dashboard_export.zip) | Standalone Superset dashboard bundles reproducible via `superset import-dashboards`. |
| **Insight Note** | Task 4 | [`reports/insights-attendance.md`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/reports/insights-attendance.md) | 1-page executive note on attendance seasonality, leave skew, AI anomaly clusters, and HR recommendations. |
| **Phase 1 Review** | Phase 1 Close | [`reports/phase-1-review.md`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/reports/phase-1-review.md) | Phase 1 sign-off report strictly following Section 10 template (Done, In progress, Blockers, Next phase plan). |

---

## Foundation Phase Consolidated Verification

Execute the master verification script to confirm all Task 1–4 check values, warehouse totals, and checkpoints against PostgreSQL:
```bash
docker compose run --rm etl python scripts/verify_foundation_phase.py
```
Or execute the automated pytest suites:
```bash
docker compose run --rm etl pytest -v tests/test_dashboard_kpis.py tests/test_attendance_kpis.py
```

---

## Assumptions

As prescribed by Page 1 & Page 23 of the Data Analyst Guide:
1. **Raw Operational Source**: Workbook 01 (`data/raw/01_LedgerForge_Python_Master_Dataset.xlsx`) is the canonical transactional source. The star-schema workbook (`03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx`) is used as a reference design and ground-truth answer key.
2. **Attendance Grain**: Employee attendance in the source feed is aggregated at the monthly summary grain (`fact_attendance_monthly`), not daily swipes. Daily attendance logs in Workbook 01 (`attendance` sheet) provide 150,155 clock-in events for downstream intra-day modeling.
3. **Data As-Of Date**: Point-in-time metrics and SCD Type 2 current status are evaluated as of `DEMO_TODAY = 2026-09-30`.
4. **Least-Privilege Role**: Apache Superset queries PostgreSQL exclusively via the dedicated read-only role `superset_ro` restricted to `SELECT` on schema `dw`.

