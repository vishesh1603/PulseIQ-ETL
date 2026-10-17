-- PulseIQ analytics warehouse: star schema in schema "dw".
-- Safe to run many times (everything is IF NOT EXISTS / CREATE OR REPLACE).
-- The ETL runs this file at the start of every load, and Docker runs it on first start.

CREATE SCHEMA IF NOT EXISTS dw;
CREATE EXTENSION IF NOT EXISTS btree_gist;   -- lets the database refuse overlapping employee history

-- ============================ DIMENSIONS ============================

CREATE TABLE IF NOT EXISTS dw.dim_date (
    date_key            integer  PRIMARY KEY,           -- 20250430
    full_date           date     NOT NULL UNIQUE,
    year                smallint NOT NULL,
    quarter             smallint NOT NULL,
    month_number        smallint NOT NULL,
    month_name          text     NOT NULL,
    year_month          text     NOT NULL,              -- '2025-04'
    week_of_year        smallint NOT NULL,
    day_of_week         text     NOT NULL,
    is_weekend          boolean  NOT NULL,
    is_holiday          boolean  NOT NULL,
    is_working_day      boolean  NOT NULL,
    financial_year      text     NOT NULL,              -- 'FY2025-26' (April to March)
    fiscal_quarter      text     NOT NULL,
    fiscal_month_number smallint NOT NULL,
    is_month_end        boolean  NOT NULL,
    month_start_date    date     NOT NULL,
    month_end_date      date     NOT NULL
);
COMMENT ON TABLE dw.dim_date IS 'One row per calendar day. Facts at month grain point at the month-end day.';

CREATE TABLE IF NOT EXISTS dw.dim_department (
    department_key  integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   -- surrogate key
    department_id   text    NOT NULL UNIQUE,                            -- business key
    department_name text    NOT NULL,
    cost_center     text    NOT NULL,
    description     text,
    is_leadership   boolean NOT NULL
);
COMMENT ON TABLE dw.dim_department IS 'One row per department. Type 1: a changed name overwrites the old one.';

CREATE TABLE IF NOT EXISTS dw.dim_role (
    role_key             integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_id              text    NOT NULL UNIQUE,
    department_key       integer NOT NULL REFERENCES dw.dim_department (department_key),
    role_title           text    NOT NULL,
    role_level           smallint NOT NULL,
    grade                text,
    band_min_annual      numeric(14,2) NOT NULL,
    band_mid_annual      numeric(14,2) NOT NULL,
    band_max_annual      numeric(14,2) NOT NULL,
    overtime_eligible    boolean NOT NULL,
    band_reference_year  smallint,
    CHECK (band_min_annual <= band_mid_annual AND band_mid_annual <= band_max_annual)
);
COMMENT ON TABLE dw.dim_role IS 'One row per role. Type 1.';

CREATE TABLE IF NOT EXISTS dw.dim_leave_type (
    leave_type_key          integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    leave_type_code         text    NOT NULL UNIQUE,
    leave_type_name         text    NOT NULL,
    pay_type                text    NOT NULL,
    annual_quota_days       numeric(6,2),
    prorated_for_joiners    boolean,
    carry_forward_allowed   boolean,
    max_carry_forward_days  numeric(6,2),
    policy_note             text
);
COMMENT ON TABLE dw.dim_leave_type IS 'One row per leave type. Type 1.';

CREATE TABLE IF NOT EXISTS dw.dim_employee (
    employee_key       bigint  PRIMARY KEY,          -- one key per VERSION of an employee
    employee_id        text    NOT NULL,             -- business key, repeats across versions
    full_name          text    NOT NULL,
    gender             text    NOT NULL,
    date_of_birth      date    NOT NULL,
    hire_date          date    NOT NULL,
    exit_date          date,
    employment_status  text    NOT NULL,
    employment_type    text    NOT NULL,
    department_key     integer NOT NULL REFERENCES dw.dim_department (department_key),
    role_key           integer NOT NULL REFERENCES dw.dim_role (role_key),
    role_title         text    NOT NULL,
    job_level          smallint NOT NULL,
    manager_id         text,
    work_location      text    NOT NULL,
    work_mode          text    NOT NULL,
    highest_education  text    NOT NULL,
    valid_from         date    NOT NULL,
    valid_to           date    NOT NULL,             -- 9999-12-31 while the version is open
    is_current         boolean NOT NULL,
    change_reason      text    NOT NULL,
    hire_year          smallint,
    hire_month         smallint,
    tenure_days        integer,
    tenure_years       numeric(6,2),
    is_active          boolean,
    CONSTRAINT uq_dim_employee_version  UNIQUE (employee_id, valid_from),
    CONSTRAINT ck_dim_employee_validity CHECK (valid_to >= valid_from),
    -- The same employee can never have two versions that cover the same day.
    CONSTRAINT ex_dim_employee_no_overlap EXCLUDE USING gist
        (employee_id WITH =, daterange(valid_from, valid_to, '[]') WITH &&)
        DEFERRABLE INITIALLY DEFERRED
);
COMMENT ON TABLE dw.dim_employee IS 'Type 2 history: one row per employee per version (valid_from..valid_to). Facts point at the version that was valid in their month.';

-- ============================== FACTS ==============================

CREATE TABLE IF NOT EXISTS dw.fact_payroll (
    employee_id          text    NOT NULL,                                    -- degenerate dimension, part of the grain
    date_key             integer NOT NULL REFERENCES dw.dim_date (date_key),  -- last day of the pay month
    payroll_item_id      text    NOT NULL UNIQUE,
    run_id               text    NOT NULL,
    employee_key         bigint  NOT NULL REFERENCES dw.dim_employee (employee_key),
    department_key       integer NOT NULL REFERENCES dw.dim_department (department_key),
    role_key             integer NOT NULL REFERENCES dw.dim_role (role_key),
    variable_pay_type    text    NOT NULL,
    payable_days         numeric(6,2) NOT NULL,
    lop_days             numeric(6,2) NOT NULL,
    overtime_hours_paid  numeric(8,2) NOT NULL,
    monthly_fixed_gross  numeric(14,2) NOT NULL,
    basic                numeric(14,2) NOT NULL,
    hra                  numeric(14,2) NOT NULL,
    conveyance           numeric(14,2) NOT NULL,
    medical              numeric(14,2) NOT NULL,
    special_allowance    numeric(14,2) NOT NULL,
    earned_fixed_pay     numeric(14,2) NOT NULL,
    overtime_pay         numeric(14,2) NOT NULL,
    variable_pay         numeric(14,2) NOT NULL,
    gross_pay            numeric(14,2) NOT NULL,
    pf_employee          numeric(14,2) NOT NULL,
    esi_employee         numeric(14,2) NOT NULL,
    professional_tax     numeric(14,2) NOT NULL,
    tds                  numeric(14,2) NOT NULL,
    other_deductions     numeric(14,2) NOT NULL,
    total_deductions     numeric(14,2) NOT NULL,
    net_pay              numeric(14,2) NOT NULL,
    pf_employer          numeric(14,2) NOT NULL,
    esi_employer         numeric(14,2) NOT NULL,
    employer_cost        numeric(14,2) NOT NULL,
    headcount_flag       smallint NOT NULL,
    PRIMARY KEY (employee_id, date_key),
    CHECK (gross_pay >= 0 AND net_pay >= 0 AND employer_cost >= 0)
);
COMMENT ON TABLE dw.fact_payroll IS 'Grain: one row per employee per pay month.';

CREATE TABLE IF NOT EXISTS dw.fact_attendance_monthly (
    employee_id          text    NOT NULL,
    date_key             integer NOT NULL REFERENCES dw.dim_date (date_key),
    attendance_fact_id   text    NOT NULL UNIQUE,
    employee_key         bigint  NOT NULL REFERENCES dw.dim_employee (employee_key),
    department_key       integer NOT NULL REFERENCES dw.dim_department (department_key),
    scheduled_days       numeric(6,2) NOT NULL,
    present_days         numeric(6,2) NOT NULL,
    wfh_days             numeric(6,2) NOT NULL,
    half_days_unpaid     numeric(6,2) NOT NULL,
    paid_leave_days      numeric(6,2) NOT NULL,
    unpaid_absence_days  numeric(6,2) NOT NULL,
    late_arrivals        numeric(6,2) NOT NULL,
    avg_hours_worked     numeric(6,2) NOT NULL,
    overtime_hours       numeric(8,2) NOT NULL,
    attendance_rate      numeric(6,4) NOT NULL,
    PRIMARY KEY (employee_id, date_key),
    CHECK (present_days <= scheduled_days AND attendance_rate BETWEEN 0 AND 1)
);
COMMENT ON TABLE dw.fact_attendance_monthly IS 'Grain: one row per employee per month (the source has monthly summaries, not daily rows).';

CREATE TABLE IF NOT EXISTS dw.fact_leave (
    leave_request_id   text    PRIMARY KEY,
    employee_id        text    NOT NULL,
    employee_key       bigint  NOT NULL REFERENCES dw.dim_employee (employee_key),   -- version valid at the start date
    department_key     integer NOT NULL REFERENCES dw.dim_department (department_key),
    leave_type_key     integer NOT NULL REFERENCES dw.dim_leave_type (leave_type_key),
    start_date_key     integer NOT NULL REFERENCES dw.dim_date (date_key),            -- role-playing date dimension
    end_date_key       integer NOT NULL REFERENCES dw.dim_date (date_key),
    applied_date_key   integer NOT NULL REFERENCES dw.dim_date (date_key),
    decided_date_key   integer REFERENCES dw.dim_date (date_key),                      -- blank while Pending
    days               numeric(6,2) NOT NULL,                                          -- working days
    calendar_days      integer NOT NULL,
    status             text    NOT NULL,
    approver_id        text,
    reason             text,
    CHECK (days > 0 AND end_date_key >= start_date_key)
);
COMMENT ON TABLE dw.fact_leave IS 'Grain: one row per leave request.';

CREATE TABLE IF NOT EXISTS dw.fact_headcount_monthly (
    date_key                    integer NOT NULL REFERENCES dw.dim_date (date_key),   -- last day of the month
    department_key              integer NOT NULL REFERENCES dw.dim_department (department_key),
    headcount_start             integer NOT NULL,
    hires                       integer NOT NULL,
    exits                       integer NOT NULL,
    voluntary_exits             integer NOT NULL,
    transfers_in                integer NOT NULL,
    transfers_out               integer NOT NULL,
    headcount_end               integer NOT NULL,
    attrition_rate_monthly_pct  numeric(6,2) NOT NULL,
    PRIMARY KEY (date_key, department_key),
    CHECK (headcount_start + hires + transfers_in - exits - transfers_out = headcount_end)
);
COMMENT ON TABLE dw.fact_headcount_monthly IS 'Grain: one row per department per month. Built from dim_employee history, never loaded from a file.';

-- ============================ INDEXES ============================
-- Primary keys and UNIQUE constraints already have indexes. These cover the other join keys and date filters.

CREATE INDEX IF NOT EXISTS ix_dim_employee_employee_id  ON dw.dim_employee (employee_id);        -- all versions of one person
CREATE INDEX IF NOT EXISTS ix_dim_employee_department   ON dw.dim_employee (department_key);
CREATE INDEX IF NOT EXISTS ix_dim_employee_role         ON dw.dim_employee (role_key);
CREATE INDEX IF NOT EXISTS ix_dim_employee_current      ON dw.dim_employee (employee_id) WHERE is_current;
CREATE INDEX IF NOT EXISTS ix_dim_role_department       ON dw.dim_role (department_key);
CREATE INDEX IF NOT EXISTS ix_dim_date_year_month       ON dw.dim_date (year_month);
CREATE INDEX IF NOT EXISTS ix_dim_date_month_end        ON dw.dim_date (month_end_date) WHERE is_month_end;

CREATE INDEX IF NOT EXISTS ix_fact_payroll_date         ON dw.fact_payroll (date_key);
CREATE INDEX IF NOT EXISTS ix_fact_payroll_department   ON dw.fact_payroll (department_key, date_key);
CREATE INDEX IF NOT EXISTS ix_fact_payroll_employee     ON dw.fact_payroll (employee_key);
CREATE INDEX IF NOT EXISTS ix_fact_payroll_role         ON dw.fact_payroll (role_key, date_key);

CREATE INDEX IF NOT EXISTS ix_fact_attendance_date       ON dw.fact_attendance_monthly (date_key);
CREATE INDEX IF NOT EXISTS ix_fact_attendance_department ON dw.fact_attendance_monthly (department_key, date_key);
CREATE INDEX IF NOT EXISTS ix_fact_attendance_employee   ON dw.fact_attendance_monthly (employee_key);

CREATE INDEX IF NOT EXISTS ix_fact_leave_employee        ON dw.fact_leave (employee_id);
CREATE INDEX IF NOT EXISTS ix_fact_leave_employee_key    ON dw.fact_leave (employee_key);
CREATE INDEX IF NOT EXISTS ix_fact_leave_department      ON dw.fact_leave (department_key, start_date_key);
CREATE INDEX IF NOT EXISTS ix_fact_leave_type            ON dw.fact_leave (leave_type_key);
CREATE INDEX IF NOT EXISTS ix_fact_leave_start           ON dw.fact_leave (start_date_key);

CREATE INDEX IF NOT EXISTS ix_fact_headcount_department  ON dw.fact_headcount_monthly (department_key, date_key);

-- ============================ VIEWS ============================
-- Flat views so a dashboard can start with one table and no joins.

CREATE OR REPLACE VIEW dw.v_payroll AS
SELECT f.*, d.full_date AS month_end, d.year, d.month_number, d.year_month, d.financial_year,
       dep.department_name, r.role_title, e.full_name, e.valid_from AS version_valid_from,
       e.valid_to AS version_valid_to
FROM dw.fact_payroll f
JOIN dw.dim_date d        ON d.date_key = f.date_key
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_role r        ON r.role_key = f.role_key
JOIN dw.dim_employee e    ON e.employee_key = f.employee_key;

CREATE OR REPLACE VIEW dw.v_attendance AS
SELECT f.*, d.full_date AS month_end, d.year, d.month_number, d.year_month, dep.department_name
FROM dw.fact_attendance_monthly f
JOIN dw.dim_date d        ON d.date_key = f.date_key
JOIN dw.dim_department dep ON dep.department_key = f.department_key;

CREATE OR REPLACE VIEW dw.v_headcount AS
SELECT f.*, d.full_date AS month_end, d.year, d.month_number, d.year_month, dep.department_name
FROM dw.fact_headcount_monthly f
JOIN dw.dim_date d        ON d.date_key = f.date_key
JOIN dw.dim_department dep ON dep.department_key = f.department_key;

CREATE OR REPLACE VIEW dw.v_leave AS
SELECT f.*, lt.leave_type_name, lt.pay_type, dep.department_name, sd.full_date AS start_date, ed.full_date AS end_date
FROM dw.fact_leave f
JOIN dw.dim_leave_type lt  ON lt.leave_type_key = f.leave_type_key
JOIN dw.dim_department dep ON dep.department_key = f.department_key
JOIN dw.dim_date sd        ON sd.date_key = f.start_date_key
JOIN dw.dim_date ed        ON ed.date_key = f.end_date_key;
