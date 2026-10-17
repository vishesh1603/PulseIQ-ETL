# PulseIQ Analytics Warehouse Schema (Star Schema)

**Schema**: `dw`  
**Database**: PostgreSQL 16  
**Architecture**: Kimball Star Schema with Slowly Changing Dimensions (SCD Type 2)  
**Visual Diagram**: [warehouse_schema.svg](file:///c:/Users/DELL/Downloads/pulseiq-etl1/docs/warehouse_schema.svg) (source: `warehouse_schema.dot`, PNG render: `warehouse_schema.png`)  
**DDL Definitions**: `sql/001_schema.sql`, `sql/003_fact_anomaly.sql`  
**Upsert Loaders**: `sql/load/*.sql`, `scripts/load_fact_anomaly.py`

---

## 1. Grain of Every Fact Table

In accordance with Section 8 (Task 2) of the Data Analyst Guide, here is the exact grain of each fact table stated in one sentence:

| Fact Table | Grain (One Sentence) | Primary Key / Natural Key | Source |
|:---|:---|:---|:---|
| **`dw.fact_payroll`** | One row per employee per calendar month of payroll execution. | `payroll_item_id` (natural: `employee_id, date_key`) | Workbook 01 / clean `fact_payroll` |
| **`dw.fact_attendance_monthly`** | One row per employee per calendar month summarizing working, present, WFH, leave, and late days. | `attendance_fact_id` (natural: `employee_id, date_key`) | Workbook 01 / clean `fact_attendance_monthly` |
| **`dw.fact_leave`** | One row per employee leave request, capturing duration, type, dates, and approval status. | `leave_request_id` | Workbook 01 / clean `fact_leave` |
| **`dw.fact_headcount_monthly`** | One row per department per calendar month tracking starting headcount, hires, exits, transfers, and month-end headcount. | `(date_key, department_key)` | Synthesized inside warehouse from `dim_employee` history |
| **`dw.fact_anomaly`** | One row per machine learning anomaly scoring result for an employee attendance or payroll period. | `result_id` | Workbook 03 feed / Workbook 02 ML model outputs |

---

## 2. Dimension Tables & Key Architecture

| Dimension Table | Entity Represented | Surrogate Key | Natural / Business Key | SCD Handling |
|:---|:---|:---|:---|:---|
| **`dw.dim_date`** | One row per calendar day (2020 to 2026). | `date_key` (`integer`, e.g. `20250430`) | `full_date` (`date`) | Type 0 (Static Calendar) |
| **`dw.dim_department`** | One row per organizational department. | `department_key` (`integer IDENTITY`) | `department_id` (e.g. `D01`) | Type 1 (Overwrite) |
| **`dw.dim_role`** | One row per job role and salary compensation band. | `role_key` (`integer IDENTITY`) | `role_id` (e.g. `R01`) | Type 1 (Overwrite) |
| **`dw.dim_leave_type`** | One row per company leave category and entitlement rule. | `leave_type_key` (`integer IDENTITY`) | `leave_type_code` (e.g. `CL`, `EL`, `SL`) | Type 1 (Overwrite) |
| **`dw.dim_employee`** | One row per **version** of an employee's employment history. | `employee_key` (`bigint`) | `employee_id` (e.g. `EMP-0001`) + `valid_from` | **Type 2 (History Retained)** |

---

## 3. Slowly Changing Dimension (SCD Type 2) Logic

- In `dw.dim_employee`, each row reflects a contiguous period of an employee's career (department, role, level, manager).
- The validity interval is bounded by `valid_from` and `valid_to`. An open (active) version is marked with `valid_to = '9999-12-31'` and `is_current = true`.
- **Database-Level Integrity Constraints**:
  - `CONSTRAINT uq_dim_employee_version UNIQUE (employee_id, valid_from)`
  - `CONSTRAINT ck_dim_employee_validity CHECK (valid_to >= valid_from)`
  - Exclusion constraint using `btree_gist` extension:
    ```sql
    CONSTRAINT ex_dim_employee_no_overlap EXCLUDE USING gist (
        employee_id WITH =,
        daterange(valid_from, valid_to, '[)') WITH &&
    )
    ```
    This guarantees that PostgreSQL physically rejects overlapping versions for any employee.

---

## 4. Reporting Views for BI Serving

To allow analytics dashboards and Apache Superset to query flattened star-schemas without complex multi-table joins:
- **`dw.v_payroll`**: Enriches `fact_payroll` with `dim_date`, `dim_department`, `dim_role`, and employee version names.
- **`dw.v_attendance`**: Enriches `fact_attendance_monthly` with `dim_date` and `dim_department`.
- **`dw.v_headcount`**: Enriches `fact_headcount_monthly` with `dim_date` and `dim_department`.
- **`dw.v_leave`**: Enriches `fact_leave` with `dim_leave_type`, `dim_department`, and start/end dates.
- **`dw.v_attendance_anomaly`**: Enriches `fact_anomaly` (attendance feature anomalies) with `dim_department`, `dim_employee`, and `fact_attendance_monthly`.
