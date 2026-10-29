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

### 1. Verify Phase 2 Deliverables (Tasks 6 to 10)
```powershell
python scripts/verify_phase2_deliverables.py
```
*Checks:*
- [x] **Task 6**: Attendance rates, working day denominators, 19 holiday annotations
- [x] **Task 7**: Attrition rates (M04/M05), voluntary split (87.7%), AI risk groups
- [x] **Task 8**: Sprint delivery across 16 teams (Sprint 1 T01 & T02 velocity & cycle time)
- [x] **Task 9**: 18-Month payroll reconciliation against `reconciliation_answer_key` (**₹0.00 difference**)
- [x] **Task 10**: Budget variance sign rules & April 2025 hand checks (D00, D01, D02)

### 2. Verify Foundation Phase (Tasks 1 to 5)
```powershell
python scripts/verify_foundation_phase.py
```

### 3. Run Pytest Unit & Warehouse Test Suites
```powershell
pytest -v tests/
```

---

## 📊 Dashboard Pages Overview

The Streamlit app is organized into 5 dedicated executive pages (in `pages/`):

| Page | File | Key Features & Metrics |
| :--- | :--- | :--- |
| **Overview** | [`app.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/app.py) | Executive headcount, joiners, leavers, salary totals, and quick navigation. |
| **1. Attendance & Leave** | [`pages/1_Attendance_and_Leave.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/1_Attendance_and_Leave.py) | **Task 6**: M13 Attendance Rate, M14 Late Arrivals, 19 Indian holidays marked, monthly attendance heatmap, leave category breakdown. |
| **2. Attrition Analytics** | [`pages/2_Attrition_Analytics.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/2_Attrition_Analytics.py) | **Task 7**: M03 Exits, M04/M05 Attrition, voluntary/involuntary breakdown, tenure at exit distribution, CortexHR AI predictions with group privacy masking (`<10` suppressed). |
| **3. Team Productivity** | [`pages/3_Team_Productivity.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/3_Team_Productivity.py) | **Task 8**: 16 engineering teams, 38 sprints, 28k tasks. M24 Velocity, cycle time, on-time completion %, cancelled/reopened task rules. |
| **4. Payroll Reconciliation** | [`pages/4_Payroll_Cost_and_Reconciliation.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/4_Payroll_Cost_and_Reconciliation.py) | **Task 9**: M07 Gross Pay, M09 Employer Cost, M10 Cost Per Head, official 18-month reconciliation table (**exact match, ₹0.00 variance**), audit trail of 4 quarantined rows (`PI-X0001` to `PI-X0004`). |
| **5. Budget Variance** | [`pages/5_Budget_vs_Actual_Variance.py`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/pages/5_Budget_vs_Actual_Variance.py) | **Task 10**: Cost variance sign rule banner (`Actual - Budget`), department overspend ranking, operational KPI scorecard against `kpi_targets`. |

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

| Task | Command |
| :--- | :--- |
| **Start database only** | `docker compose up -d warehouse` |
| **Check database status** | `docker compose ps` |
| **Stop database** | `docker compose stop warehouse` |
| **Connect to psql shell** | `docker compose exec warehouse psql -U pulseiq -d pulseiq` |
| **Run Streamlit dashboard** | `python -m streamlit run app.py` |
| **Stop Streamlit** | Press `Ctrl + C` in the terminal |
| **Run Phase 2 Verification** | `python scripts/verify_phase2_deliverables.py` |

---

## 📑 Program Submissions & Git Tags

- **Phase 1 Tag**: `git checkout phase-1`  
  *Report*: [`reports/DataAnalytics_Vishesh_Phase1_Report.pdf`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/reports/DataAnalytics_Vishesh_Phase1_Report.pdf)
- **Phase 2 Tag**: `git checkout phase-2`  
  *Report*: [`reports/DataAnalytics_Vishesh_Phase2_Report.pdf`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/reports/DataAnalytics_Vishesh_Phase2_Report.pdf)
- **Author**: Vishesh Chaturvedi (`vishesh1603`)
- **Reviewer**: `fobesitech`
