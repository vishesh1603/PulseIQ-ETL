# PulseIQ End-to-End System & Architecture Flow

This document maps the complete data flow, architectural boundaries, and component interactions across the 20-task PulseIQ HR Analytics project, with focus on Tasks 1 through 4.

```
                      +---------------------------------------+
                      |   PulseIQ_Star_Schema_Dataset.xlsx   |
                      |            (data/raw/)                |
                      +-------------------+-------------------+
                                          |
                                          v  [Task 1: Pandas + Pandera]
                      +---------------------------------------+
                      |         ETL Pipeline Service          |
                      | - extract.py    (read text / sheets)  |
                      | - transform.py  (clean, types, dates) |
                      | - validate.py   (pandera schemas)     |
                      | - load.py       (atomic Parquet swap) |
                      | - run_log.py    (last_run.json)       |
                      +-------+-----------------------+-------+
                              |                       |
               Valid rows     |                       | Rejected / Repaired
                              v                       v
               +----------------------+      +----------------------+
               |    data/clean/*.     |      |   data/rejected/*.   |
               |       parquet        |      |         csv          |
               +----------+-----------+      +----------------------+
                          |
                          v  [Task 2: PostgreSQL Warehouse]
               +----------------------------------------------+
               |     PostgreSQL 16 Star-Schema Warehouse      |
               |                Schema: "dw"                  |
               |                                              |
               |  Dimensions:                                 |
               |  - dim_date (2020..2026, calendar day)       |
               |  - dim_department (surrogate key, Type 1)    |
               |  - dim_role (surrogate key, Type 1)          |
               |  - dim_leave_type (surrogate key, Type 1)    |
               |  - dim_employee (Type 2 SCD history)         |
               |                                              |
               |  Facts:                                      |
               |  - fact_payroll (grain: employee x month)    |
               |  - fact_attendance_monthly (employee x month)|
               |  - fact_leave (grain: leave request)         |
               |  - fact_headcount_monthly (dept x month)     |
               |                                              |
               |  Reporting Views:                            |
               |  - v_payroll, v_attendance, v_headcount,     |
               |    v_leave                                   |
               +----------------------+-----------------------+
                                      |
                  Read-Only Role      | (Host :5433 / Internal :5432)
                  "superset_ro"       |
                                      v  [Task 3 & 4: BI & Analytics]
               +----------------------------------------------+
               |           Apache Superset Service            |
               |               (localhost:8088)               |
               |                                              |
               |  - Custom Docker image with psycopg2         |
               |  - Connected via read-only user              |
               |  - Datasets defined once via SQL             |
               |                                              |
               |  Dashboards:                                 |
               |  - Task 3: Headcount & Departments           |
               |    (M01 Headcount, M02 Joiners, M03 Leavers, |
               |     M04 Attrition, Trends, Splits)           |
               |  - Task 4: Attendance & Leave Trends         |
               |    (M13 Attendance Rate, M14 Late Rate,      |
               |     Leave by type/weekday, AI Anomaly Flags) |
               +----------------------------------------------+
```

---

## 1. Data Ingestion & ETL Flow (Task 1)
- **Input**: `data/raw/PulseIQ_Star_Schema_Dataset.xlsx` (or CSV tables).
- **Execution**: Run via `docker compose run --rm etl` or `python -m pulseiq_etl`.
- **Extraction**: Reads source data as string representations, normalizes column names (`snake_case`), and logs incoming row counts.
- **Transformation**:
  - Cleans whitespace, standardizes categories to Title Case, parses numeric money/quantities.
  - Generates helper columns: `tenure_days`, `tenure_years`, `is_active`, `hire_year`, `hire_month`, `month_start`.
  - Date reconciliation against business cut-off (default: `2026-09-30`).
- **Data Quality & Validation**:
  - Enforced via Pandera schemas in `src/pulseiq_etl/validate.py`.
  - Violations are either cleanly rejected into `data/rejected/*_rejected.csv` with explicit audit codes (`exit_before_hire`, `conflicting_duplicate`, arithmetic errors) or repaired if a verifiable ground-truth key exists (`*_repaired.csv`).
- **Load**: Atomic swap of validated DataFrames into `data/clean/*.parquet`.

---

## 2. Warehouse Ingestion Flow (Task 2)
- **Engine**: PostgreSQL 16 (`pulseiq` database, schema `dw`).
- **Initialization**: `sql/001_schema.sql` establishes tables, domain constraints, exclusion constraints (preventing overlapping Type 2 employee validity dates), and index sets.
- **ETL Loader**: `src/pulseiq_etl/warehouse.py` manages transactional copy into staging, executing `sql/load/*.sql` in dependency order:
  1. Dimensions: `10_dim_date.sql` -> `11_dim_department.sql` -> `12_dim_role.sql` -> `13_dim_leave_type.sql` -> `14_dim_employee.sql`
  2. Fact Tables: `20_fact_payroll.sql` -> `21_fact_attendance_monthly.sql` -> `22_fact_leave.sql`
  3. Derived Fact: `30_fact_headcount_monthly.sql` (synthesizes department start, hires, exits, transfers, and month-end headcount directly from employee history).
- **Idempotency**: All operations leverage upserts (`ON CONFLICT ... DO UPDATE`) and differential mirrors, guaranteeing zero side-effects on re-runs.

---

## 3. Visual Standard & BI Serving Flow (Task 3)
- **Style Foundation**: Color-blind safe Okabe-Ito palette, systematic typography, Indian number formatting (lakhs/crores), and mandatory takeaway headlines for every chart.
- **Security Boundary**: A dedicated PostgreSQL role (`superset_ro`) granted `USAGE ON SCHEMA dw` and `SELECT` only on tables/views.
- **Service Deployment**:
  - Apache Superset container linked in `docker-compose.yml`.
  - Custom build incorporating `psycopg2-binary`.
  - Automated init script: database migrations (`superset db upgrade`), admin user registration, role provisioning, and warehouse connection setup.
- **Dataset Layer**: Centralized SQL views in `sql/dashboards/` mapped into Superset datasets.
- **Dashboard Assembly**:
  - Executive KPI Row: M01 Headcount, M02 Hires (Joiners), M03 Exits (Leavers), M04 Attrition Rate.
  - Breakdown Visuals: Headcount timeline (line), Department distribution (horizontal bar), Tenure distribution (<1y to 10+y), Role mix, Monthly Joiners vs. Leavers.
  - Interactive Slicers: Department selector, Date-range filter.
- **Export & Version Control**: Dashboards exported as versioned YAML definitions under `dashboards/` for automated reproduction via `superset import-dashboards`.

---

## 4. Attendance Trends & Anomaly Pipeline Flow (Task 4)
- **Metric Expansion**: M13 Attendance Rate, M14 Late Arrival Rate, M15 Leave Without Pay Days.
- **Temporal Analysis**:
  - Time-series monthly rate trends with rolling 3-month and 6-month smoothing.
  - Day-of-week leave patterns (from `fact_leave` joined to `dim_date`).
  - Cross-department comparisons identifying engagement high-water and low-water marks.
- **AI/ML Anomaly Integration**:
  - Ingestion of `fact_anomaly` (Isolation Forest anomaly scores & reason codes for monthly attendance).
  - Visualization of flagged periods on attendance trend lines to highlight high-risk outlier periods (e.g. `NO_ATTENDANCE`, `PATTERN_SHIFT`).
- **Synthesis**: 1-page executive analytical finding note (`docs/attendance_insights.md`) explaining observed trends, seasonality, data caveats, and actionable HR recommendations.
