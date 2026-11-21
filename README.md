# PulseIQ — Enterprise Workforce & HR Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-FF4B4B.svg)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)

PulseIQ is an end-to-end People Analytics platform that extracts, cleans, validates, and models enterprise HR, payroll, attendance, and sprint data into a PostgreSQL Star-Schema Data Warehouse (`dw`), served through an interactive Streamlit executive dashboard.

---

## ⚡ Quick Start: Run the Whole Project in 3 Steps

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (must be running)
- Python 3.11+ installed

---

### Step 1: Start the PostgreSQL Warehouse
Open your terminal in the project folder and start the database container:
```powershell
docker compose up -d warehouse
```
*Verify it is running and healthy on port 5433:*
```powershell
docker compose ps
```

---

### Step 2: Run the ETL Pipeline (Loads & Validates All Data)
Run the pipeline to clean raw files, validate data contracts, quarantine bad rows, and populate schema `dw`:

**Using Docker (Recommended):**
```powershell
docker compose run --rm etl
```
*Or using local Python directly:*
```powershell
pip install -r requirements.txt
python -m pulseiq_etl
```

---

### Step 3: Launch the Streamlit Interactive Dashboard
Start the dashboard application:
```powershell
python -m streamlit run app.py
```
Open your browser and navigate to:
👉 **[http://localhost:8501](http://localhost:8501)**

---

## 🧪 Verification & Automated Testing

Run the automated test suites to verify that all metrics, 18-month financial reconciliations, and data checks pass 100%:

### 1. Verify Phase 3 Deliverables (Tasks 11 to 15)
```powershell
python scripts/verify_phase3_deliverables.py
```
*Checks:*
- [x] **Task 11**: P&L tie-out against `reconciliation_answer_key` (Revenue, Expense, Net Profit match to ₹0.00; DQ-04 audited)
- [x] **Task 12**: Receivables aging buckets sum to exact open receivables (**₹139,394,278.00**) with open status rules
- [x] **Task 13**: 4-Way cross-department join matches `reference_summary_dept_month` across all 198 rows with zero error
- [x] **Task 14**: AI anomaly money-at-risk ranking and 80% confidence intervals for headcount forecasts
- [x] **Task 15**: 8 Headline founder KPIs verified to pull exclusively from `dw.metric_*` views

### 2. Verify Phase 2 Deliverables (Tasks 6 to 10)
```powershell
python scripts/verify_phase2_deliverables.py
```
*Checks:*
- [x] **Task 6**: Attendance rates, working day denominators, 19 holiday annotations
- [x] **Task 7**: Attrition rates (M04/M05), voluntary split (87.7%), AI risk groups
- [x] **Task 8**: Sprint delivery across 16 teams (Sprint 1 T01 & T02 velocity & cycle time)
- [x] **Task 9**: 18-Month payroll reconciliation against `reconciliation_answer_key` (**₹0.00 difference**)
- [x] **Task 10**: Budget variance sign rules & April 2025 hand checks (D00, D01, D02)

### 3. Verify Foundation Phase (Tasks 1 to 5)
```powershell
python scripts/verify_foundation_phase.py
```

### 4. Run Pytest Unit & Warehouse Test Suites
```powershell
pytest -v tests/
```

---

## 📊 Dashboard Pages Overview

The Streamlit app is organized into **12 executive pages** (in `pages/`) plus the main overview:

| Page | File | Key Features & Metrics |
| :--- | :--- | :--- |
| **Overview** | [`app.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/app.py) | Executive headcount, joiners, leavers, salary totals, quick navigation. |
| **0. About & Lineage** | [`pages/0_About_and_Lineage.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/0_About_and_Lineage.py) | **Task 19**: Interactive 29-metric lineage catalog, pipeline health panel, SQL view detail, data flow diagram. |
| **1. Attendance & Leave** | [`pages/1_Attendance_and_Leave.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/1_Attendance_and_Leave.py) | **Task 6**: M13 Attendance Rate, M14 Late Arrivals, 19 Indian holidays marked, monthly heatmap, leave category breakdown. |
| **2. Attrition Analytics** | [`pages/2_Attrition_Analytics.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/2_Attrition_Analytics.py) | **Task 7**: M03–M06 Attrition, voluntary/involuntary, tenure at exit, CortexHR AI risk (groups <10 suppressed). |
| **3. Team Productivity** | [`pages/3_Team_Productivity.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/3_Team_Productivity.py) | **Task 8**: 16 teams, 38 sprints, 28k tasks. M24 Velocity, M22 completion %, M25 cycle time. |
| **4. Payroll Reconciliation** | [`pages/4_Payroll_Cost_and_Reconciliation.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/4_Payroll_Cost_and_Reconciliation.py) | **Task 9**: M07–M10, 18-month reconciliation (**₹0.00 variance**), 4 quarantined rows. |
| **5. Budget Variance** | [`pages/5_Budget_vs_Actual_Variance.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/5_Budget_vs_Actual_Variance.py) | **Task 10**: Actual−Budget sign rule, department overspend ranking, KPI scorecard. |
| **6. Profit & Loss** | [`pages/6_Profit_and_Loss.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/6_Profit_and_Loss.py) | **Task 11**: M16–M18, P&L table, Top 10 vendors, 18-month tie-out with DQ-04 audit. |
| **7. Invoices & Cash Flow** | [`pages/7_Invoices_and_Cash_Flow.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/7_Invoices_and_Cash_Flow.py) | **Task 12**: 4 aging buckets (₹13.93 Cr open), M20 DSO, M21 overdue receivables. |
| **8. Cross-Department Impact** | [`pages/8_Cross_Department_Impact.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/8_Cross_Department_Impact.py) | **Task 13**: 4-way join, 198-row reconciliation against `reference_summary_dept_month`. |
| **9. AI Signals** | [`pages/9_AI_Signals.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/9_AI_Signals.py) | **Task 14**: M26–M28, anomalies ranked by ₹3.14 Cr risk, 80% CI forecast. |
| **10. Executive Scorecard** | [`pages/10_Executive_Scorecard.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/10_Executive_Scorecard.py) | **Task 15**: 8 Founder KPIs, traffic-light status, A4 print layout. |
| **11. Alert History** | [`pages/11_Alert_Log.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/11_Alert_Log.py) | **Task 18**: KPI breach log, severity chart, scheduler heartbeat, re-run button. |

---

## 🗄️ Database Warehouse Architecture

- **Engine**: PostgreSQL 16
- **Host / Port**: `localhost:5433` (Docker container maps host `5433` -> container `5432` to avoid conflicts)
- **Database / User / Password**: `pulseiq` / `pulseiq` / `pulseiq`
- **Schema**: `dw`
- **Core Tables**:
  - `dw.dim_employee`: SCD Type 2 employee history (`valid_from`, `valid_to`, `is_current`)
  - `dw.dim_department`, `dw.dim_role`, `dw.dim_date`
  - `dw.fact_payroll`: 33-column monthly salary facts (4 dirty rows quarantined at ingestion)
  - `dw.fact_attendance_monthly`: Monthly employee attendance, late arrivals, WFH
  - `dw.fact_leave`: Individual leave requests and durations
  - `dw.fact_task`: 28k engineering tasks across 38 sprints and 16 teams
  - `dw.fact_headcount_monthly`, `dw.fact_attrition_risk`
  - `dw.budget_payroll_dept_month`, `dw.kpi_targets`, `dw.reconciliation_answer_key`

---

## 📁 Project Structure

```text
pulseiq-etl1/
├── app.py                                   # Streamlit main landing application
├── pages/                                   # Streamlit multi-page dashboard
│   ├── 1_Attendance_and_Leave.py            # Task 6: Attendance & Leave Trends
│   ├── 2_Attrition_Analytics.py             # Task 7: Attrition & CortexHR AI Risk
│   ├── 3_Team_Productivity.py               # Task 8: Sprint & Task Productivity
│   ├── 4_Payroll_Cost_and_Reconciliation.py # Task 9: Payroll & 18M Reconciliation
│   └── 5_Budget_vs_Actual_Variance.py       # Task 10: Budget Variance & Scorecards
├── src/pulseiq_etl/                         # Core Python ETL package
│   ├── config.py                            # Table schemas and data contracts
│   ├── extract.py                           # Source feed readers
│   ├── transform.py                         # Data cleaning and type enforcement
│   ├── validate.py                          # Pandera contract validation
│   ├── load.py                              # Parquet file writer
│   └── warehouse.py                         # PostgreSQL star-schema loader
├── sql/                                     # DDL and analytical views
│   ├── 001_schema.sql                       # Tables, constraints, and 28 metric views
│   └── load/                                # SQL upsert scripts per table
├── data/                                    # Data directories
│   ├── raw/                                 # Raw source Excel workbooks & CSVs
│   ├── clean/                               # Validated Parquet tables
│   └── rejected/                            # Quarantined rows with reject reasons
├── scripts/                                 # Automation & verification scripts
│   ├── verify_phase2_deliverables.py        # Master Phase 2 automated test suite
│   ├── verify_foundation_phase.py           # Foundation phase test suite
│   └── load_phase2_raw_feeds.py             # Data ingestion helpers
├── reports/                                 # Program evaluation deliverables
│   ├── DataAnalytics_Vishesh_Phase1_Report.pdf
│   └── DataAnalytics_Vishesh_Phase2_Report.pdf
├── docker-compose.yml                       # Docker services (warehouse, etl, dashboard)
└── requirements.txt                         # Python dependencies
```

---

## 🛠️ Management Cheat Sheet

### Core Commands
| Task | Command |
| :--- | :--- |
| **Start database only** | `docker compose up -d warehouse` |
| **Check all services** | `docker compose ps` |
| **Stop all services** | `docker compose stop` |
| **Connect to psql shell** | `docker compose exec warehouse psql -U pulseiq -d pulseiq` |
| **Run Streamlit dashboard** | `python -m streamlit run app.py` |
| **Stop Streamlit** | Press `Ctrl + C` in the terminal |

### Phase 4 — Production Commands
| Task | Command |
| :--- | :--- |
| **Run ETL immediately** | `python scripts/scheduler.py --run-now` |
| **Start daily scheduler** | `docker compose up -d scheduler` |
| **Apply RBAC roles** | `docker compose exec warehouse psql -U pulseiq -d pulseiq -f /app/sql/006_rbac.sql` |
| **Apply DQ log table** | `docker compose exec warehouse psql -U pulseiq -d pulseiq -f /app/sql/007_dq_monitoring.sql` |
| **Apply alert log table** | `docker compose exec warehouse psql -U pulseiq -d pulseiq -f /app/sql/008_alert_log.sql` |
| **Run DQ checks** | `python scripts/run_all_14_dq_checks.py` |
| **Run KPI alert checks** | `python scripts/alerting.py` |
| **Verify Phase 4** | `python scripts/verify_phase4_deliverables.py` |
| **Generate Phase 4 PDF** | `python scripts/generate_phase4_pdf.py` |
| **Connect as HR user** | `psql -U hr_readonly -d pulseiq -h localhost -p 5433` |
| **Connect as Finance user** | `psql -U fin_readonly -d pulseiq -h localhost -p 5433` |
| **Connect as Exec user** | `psql -U exec_readonly -d pulseiq -h localhost -p 5433` |

### Verification Commands (All Phases)
| Phase | Command |
| :--- | :--- |
| **Phase 4** | `python scripts/verify_phase4_deliverables.py` |
| **Phase 3** | `python scripts/verify_phase3_deliverables.py` |
| **Phase 2** | `python scripts/verify_phase2_deliverables.py` |
| **Foundation** | `python scripts/verify_foundation_phase.py` |
| **All pytest** | `pytest -v tests/` |

---

## 📑 Program Submissions & Git Tags

- **Phase 1 Tag**: `git checkout phase-1`  
  *Report*: [`reports/DataAnalytics_Vishesh_Phase1_Report.pdf`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/reports/DataAnalytics_Vishesh_Phase1_Report.pdf)
- **Phase 2 Tag**: `git checkout phase-2`  
  *Report*: [`reports/DataAnalytics_Vishesh_Phase2_Report.pdf`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/reports/DataAnalytics_Vishesh_Phase2_Report.pdf)
- **Phase 3 Tag**: `git checkout phase-3`  
  *Report*: [`reports/DataAnalytics_Vishesh_Phase3_Report.pdf`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/reports/DataAnalytics_Vishesh_Phase3_Report.pdf)
- **Phase 4 Tag**: `git checkout phase-4`  
  *Report*: [`reports/DataAnalytics_Vishesh_Phase4_Report.pdf`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/reports/DataAnalytics_Vishesh_Phase4_Report.pdf)
- **Author**: Vishesh Chaturvedi (`vishesh1603`)
- **Reviewer**: `fobesitech`

---

## 🔐 Phase 4: Security & Production Features

### Role-Based Access Control (RBAC)
Apply with: `psql -U pulseiq -d pulseiq -f sql/006_rbac.sql`

| Role | Login User | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| `role_hr` | `hr_readonly` | `hr_pass_2026` | HR fact tables + metric views M01–M15, M27, M29 |
| `role_finance` | `fin_readonly` | `fin_pass_2026` | Finance tables + metric views M16–M21 |
| `role_executive` | `exec_readonly` | `exec_pass_2026` | All 29 metric views only (no raw tables) |

### KPI Alerting
Configure in `.env` (copy from `.env.example`):
```
ALERT_CHANNEL=log          # log | webhook | email
ALERT_WEBHOOK_URL=         # Slack/Teams webhook URL
```
Manual run: `python scripts/alerting.py`

### Automated Scheduler
```powershell
# Start the daily 02:00 AM scheduler
docker compose up -d scheduler

# Or run ETL immediately
python scripts/scheduler.py --run-now
```
