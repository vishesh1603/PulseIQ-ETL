# PulseIQ Project Changelog & Activity Log

All notable changes, architectural decisions, and milestone completions across the PulseIQ project are documented in this log.

---

## [Tasks 1 & 2 Completed Baseline] - 2026-10-16
### Added
- **ETL Pipeline**: Packaged Pandas + Pandera pipeline (`src/pulseiq_etl/`) reading raw star-schema data, applying business cleaning rules, and exporting clean Parquet files to `data/clean/`.
- **Data Quality & Rejection Handling**: Bad records cleanly isolated into `data/rejected/` with descriptive reasons (e.g., `exit_before_hire`, conflicting duplicates).
- **PostgreSQL Star Schema**: Initialized warehouse schema `dw` with 5 dimensions (`dim_date`, `dim_department`, `dim_role`, `dim_leave_type`, `dim_employee` Type 2 SCD) and 4 fact tables (`fact_payroll`, `fact_attendance_monthly`, `fact_leave`, `fact_headcount_monthly`).
- **Upsert Loaders**: Transactional idempotency implemented across all `sql/load/*.sql` routines with zero duplication on repeated execution.
- **Reporting Views**: Created `dw.v_payroll`, `dw.v_attendance`, `dw.v_headcount`, and `dw.v_leave`.
- **Baseline Documentation**: Established `docs/metric_dictionary.md`, `docs/warehouse_design.md`, and `docs/warehouse_questions.md`.

---

## [Task 3: Dashboard Design & Demographics Dashboard] - 2026-10-17
### Added
- **Step 1 - Visual Style Guide**: Authored `docs/style_guide.md` specifying the Okabe-Ito color-blind safe palette (`#0072B2`, `#E69F00`, `#009E73`, `#56B4E9`, `#D55E00`, `#CC79A7`, `#F0E442`), typography system with Inter and universal system fallbacks, strict Indian currency (Lakhs/Crores) and headcount number formatting, and the mandatory "Title + Empirical One-Line Takeaway" rule.
- **Step 2 - Dashboard Layout Wireframe**: Built responsive HTML layout prototype in `docs/dashboard_layout.html` with sticky header, 4 KPI cards placing the primary metric first (`M01 Headcount`), side filter panel with department and date range, charts grid (line trend, horizontal department split, tenure bands, role mix, grouped joiners vs leavers), and media queries for mobile single-column stacking.
- **Step 3 - Critical Design Review**: Authored `docs/design_review.md` auditing the layout against the checklist: confirmed primary metric placement, optimal horizontal bar selections for long text, accessibility via redundant text and directional arrows alongside Okabe-Ito colors, responsive single-column mobile flow, and 100% empirical verification of all card placeholders against the PostgreSQL warehouse.
- **Step 4 - Superset Deployment & Least-Privilege Role**: Added pinned Apache Superset service (`apache/superset:3.1.3`) to `docker-compose.yml` with custom Dockerfile installing `psycopg2-binary`. Configured `superset/superset_config.py` with secret key encryption and persistent application volume. Automated database migration and admin user creation via `superset/docker-init.sh`. Created read-only role `superset_ro` restricted to `SELECT` on schema `dw` via `sql/002_superset_ro.sql`, tested and verified that write/drop operations are denied, confirmed Superset health at `http://localhost:8088/health`, and verified live query execution over PostgreSQL warehouse.
- **Step 8 - Dashboard Export & Re-import**: Exported dashboard definitions to `dashboards/dashboard_export.zip` and unzipped full YAML configuration bundle into `dashboards/`. Verified round-trip re-import via `superset import-dashboards` and documented instructions in `README.md`.

---

## [Task 4: Attendance Trends Analysis & Anomaly Integration] - 2026-10-17
### Added
- **AI Anomaly Schema & Ingestion**:
  - Authored `sql/003_fact_anomaly.sql` defining `dw.fact_anomaly` (table, indexes, foreign keys) and reporting view `dw.v_attendance_anomaly`.
  - Built idempotent ingestion script `scripts/load_fact_anomaly.py` extracting 405 anomaly records from `data/raw/PulseIQ_Star_Schema_Dataset.xlsx` (221 attendance feature anomalies, 184 payroll feature anomalies).
  - Executed idempotent warehouse load (`dw.fact_anomaly`: 405 rows inserted, 0 loss, verified `superset_ro` select access).
- **Analytical Datasets & SQL Queries (`sql/dashboards/`)**:
  - `ds_attendance_monthly.sql`: Monthly attendance fact joined with `dim_date` and `dim_department`.
  - `ds_leave_requests.sql`: Leave requests fact joined with `dim_leave_type`, `dim_employee`, `dim_department`, and `dim_date`.
  - `ds_attendance_anomalies.sql`: Flat dataset based on `dw.v_attendance_anomaly`.
  - `chart_attendance_kpi_summary.sql`: September 2026 metrics for M13 (95.2%), M14 (7.1%), M15 (85.5 days), and M26 (10 anomaly flags).
  - `chart_attendance_rate_trend.sql`: Monthly attendance rate and 3-month trailing moving average.
  - `chart_attendance_anomalies_trend.sql`: Anomaly volume by month and reason code (`PATTERN_SHIFT`, `NO_ATTENDANCE`, `LONG_UNPAID_ABSENCE`, `FREQUENT_LATE`).
  - `chart_leave_by_weekday.sql`: Day-of-week distribution of leave start dates (Friday: 720 requests, Thursday: 714, Monday: 649).
  - `chart_leave_by_type.sql`: Breakdown of total leave volume across leave categories (Earned Leave 32.7%, Casual Leave 27.8%, Sick Leave 24.5%).
  - `chart_attendance_by_dept.sql`: Department attendance ranking for September 2026.
- **Superset "Attendance & Leave Trends" Dashboard**:
  - Programmatically constructed dashboard `attendance-and-leave` via `scripts/build_attendance_dashboard.py` in Superset.
  - Configured 4 top KPI cards (M13 Attendance Rate, M14 Late Arrival Rate, M15 Unpaid Leave Days, M26 Anomaly Flags) and 5 visuals (Monthly Trend, Anomaly Flags by Reason, Leave by Type, Weekday Distribution, Department Comparison) with Okabe-Ito colors and empirical takeaways.
  - Implemented cross-chart native filters for Department, Time Period, and Leave Type.
  - Exported complete reproducible YAML specification to `dashboards/attendance_and_leave/` and zip bundle `dashboards/attendance_dashboard_export.zip`.
- **Executive Insight Briefing**:
  - Authored 1-page analytical insight report `docs/attendance_insights.md` presenting 3 verified empirical findings (summer May attendance dip, end-of-week leave concentration, Customer Support anomaly cluster of 0.81 flags/head), 4 actionable HR recommendations, and transparent data caveats.
- **Automated KPI Validation Suite**:
  - Created pytest suite `tests/test_attendance_kpis.py` checking Engineering Apr 2025 checkpoint (`0.9509`), Sep 2026 company KPIs, anomaly counts/referential integrity, and weekday leave distributions (5/5 tests passing).
- **Metric Dictionary Expansion**:
  - Updated `docs/metric_dictionary.md` to formally document M13, M14, M15, and M26 with business questions, warehouse SQL, edge cases, and checked values.

---

## [Foundation Phase (Phase 1) Final Sign-off] - 2026-10-17
### Added
- **Workbook Alignment**:
  - Standardized filename `data/raw/01_LedgerForge_Python_Master_Dataset.xlsx` (Workbook 01 raw operational source).
  - Validated that Workbook 03 (`03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx`) is byte-identical to `PulseIQ_Star_Schema_Dataset.xlsx` and serves as the official reference design and answer key.
- **Handoff Package & Deliverables Compliance**:
  - Created `reports/insights-attendance.md` (exact path per Guide Page 4 & 10).
  - Exported `dashboards/headcount.zip` (exact path per Guide Page 10).
  - Authored `docs/design-notes.md` detailing prompt, layout choices, and palette adherence per Guide Page 8 & 10.
  - Authored `docs/warehouse-schema.md` documenting fact grains in one sentence, dimensions, and SCD Type 2 logic.
  - Formulated `reports/phase-1-review.md` following Section 10 template (Done, In Progress, Blocked, Next Phase Plan).
- **Master Verification Suite**:
  - Authored `scripts/verify_foundation_phase.py` asserting all Task 1–4 check values against PostgreSQL:
    - Task 2: PR-2025-04 cost = ₹5,33,63,392.08, PR-2026-09 employees = 444, employee counts = 745 total / 441 active / 1,606 versions.
    - Task 3: Sep 2026 headcount = 441, hires = 17, exits = 3, attrition = 0.70%.
    - Task 4: M13 Engineering Apr 2025 = 0.9509, Sep 2026 Attendance = 95.2%, Late Rate = 7.1%, 405 anomalies with 0 orphans, 3,441 weekday leave requests.
  - Verified 100% pass across all checks.
- **Documentation**:
  - Updated `README.md` with official "Handoff Package" table and "Assumptions" section.


