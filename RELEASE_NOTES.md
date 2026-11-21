# PulseIQ v1.0.0 — Release Notes & Production Handoff

> **Release Version**: `v1.0.0` (Release Candidate: `v1.0.0-rc1`)  
> **Release Date**: November 2026  
> **Author / Lead**: Vishesh Chaturvedi  
> **Live Production Dashboard**: [https://pulseiq-etl-0801.onrender.com/](https://pulseiq-etl-0801.onrender.com/)  
> **Repository**: [https://github.com/vishesh1603/PulseIQ-ETL](https://github.com/vishesh1603/PulseIQ-ETL)  
> **Git Tags**: `v1.0.0-rc1`, `v1.0.0`, `phase-4`

---

## 1. What is Included in v1.0.0

PulseIQ v1.0.0 is a production-grade, enterprise People & Financial Analytics platform that extracts, cleans, validates, models, and serves workforce, payroll, sprint, and general ledger data.

### 🌟 Core Milestones & Capabilities

#### Phase 1: Data Foundations & Governance (Tasks 1–5)
- **Star Schema Data Warehouse**: PostgreSQL schema `dw` with surrogate keys, dimension tables (`dim_date`, `dim_department`, `dim_role`, `dim_leave_type`), and fact tables (`fact_payroll`, `fact_attendance_monthly`, `fact_leave`).
- **Data Contracts & Quarantine**: Strict Pandera schemas and quarantine pipelines (`data/rejected/`) separating malformed records from clean warehouse feeds.
- **Answer Key Reconciliation**: 18 months of historical payroll reconciled to the exact rupee (0 mismatches).

#### Phase 2: Relational Data Modeling & Advanced Governance (Tasks 6–10)
- **SCD Type 2 Employee Tracking**: Full point-in-time employee tenure, level, and department tracking with effective date ranges (`valid_from`, `valid_to`, `is_current`).
- **Data Quality Check Suite**: 14 automated data quality checks (`scripts/run_all_14_dq_checks.py`) auditing referential integrity, unmapped departments, and negative pay.
- **Machine Learning Anomaly Detection**: Isolation Forest and Z-score models detecting anomalous attendance, overtime surges, and ghost employee pay patterns.

#### Phase 3: Money & Insight Analytics (Tasks 11–15)
- **Profit & Loss Statement**: Governed P&L view excluding group header accounts (`is_group = 'N'`) to eliminate double-counting.
- **Receivables & Cash Flow Aging**: Open receivables categorized into 0–30, 31–60, 61–90, and 90+ days aging buckets with DSO tracking.
- **Cross-Department Impact Model**: Multi-fact grain alignment joining headcount, payroll, attendance, and leave using the aggregate-first pattern.
- **Responsible AI Signals Dashboard**: Confidence intervals, error tracking, and mandatory "AI-generated, for human review" disclosures.
- **Founder 8-KPI Executive Scorecard**: Single-page executive summary traceable exclusively to governed SQL views.

#### Phase 4: Release, Scale & Production Handoff (Tasks 16–20)
- **Automated Monthly Pack Builder**: One-command executive report generator (`python build_report.py --month YYYY-MM`) with cut-off timestamps.
- **Continuous Scheduling**: Daily 02:00 AM daemon (`scripts/scheduler.py`), Windows wrapper (`scripts/run_etl_now.ps1`), and GitHub Actions workflow (`.github/workflows/monthly_report.yml`).
- **Role-Based Access Control (RBAC)**: Principle of least privilege enforced across 3 PostgreSQL roles (`role_hr`, `role_finance`, `role_executive`).
- **Automated KPI Alerting Engine**: 8 business threshold rules with multi-channel dispatch (`log`, `webhook`, `email`).
- **Governed Metric Lineage Catalog**: 29 governed metrics documented with grain, formula, owner, and source facts in `docs/metric_lineage_catalog.md`.
- **Self-Service Explorer with Privacy**: Multi-level drill-down (Company → Dept → Team) with strict k-anonymity suppression (groups < 5 masked).
- **FastAPI Metrics REST API**: Interactive `/docs` providing endpoints for M01, M07, M17, M18, and M20 with end-to-end data lineage.
- **Executive Board Deck**: 10-slide presentation (`reports/PulseIQ_Board_Deck.pdf`) delivering strategic insights across people, cost, cash, and AI.

---

## 2. What is NOT Included (Out of Scope by Design)

1. **Transactional Write-Back**: PulseIQ is an analytical data warehouse (`dw`) and read-only executive intelligence system. It does not write back employee terminations or payroll corrections directly into primary HRIS or ERP source databases.
2. **Multi-Tenant SaaS Partitioning**: Built for enterprise single-organization analytics; multi-company multi-tenant tenant isolation is outside the scope of v1.0.0.

---

## 3. Known Limits & Operational Notes

1. **Render Free Tier Spin-Down**: On Render's free compute tier, web services enter idle sleep after 15 minutes of inactivity. The first visit takes ~30 seconds for cold-start wake-up.
2. **Historical Scope**: Current baseline star schema dataset covers 18 historical months (April 2025 to September 2026).
3. **Database Network Connectivity**: In restricted corporate networks with local DNS refusal on cloud AWS hostnames, `init_cloud_db.py` uses built-in Google DNS-over-HTTPS (DoH) fallback with `hostaddr` injection.

---

## 4. Final Challenge Note: Privacy-Preserving Self-Service Exploration

- **Feature Built**: Minimum group threshold masking (`k = 5`) implemented in `pages/12_Self_Service_Explorer.py`.
- **Branch**: `feature/privacy-drilldown-k5`
- **Rationale**: In analytical dashboards, unrestricted drill-down into 1-to-2 person teams allows bad actors to calculate individual compensation and flight probability. Masking groups with `< 5` members protects employee privacy while preserving department-level analytical utility.

---

## 5. Verification Certification

| Verification Suite | Test Count | Pass Rate | Result |
| :--- | :---: | :---: | :---: |
| **Phase 1 Foundations** | 5 Tests | 100% | **PASS** |
| **Phase 2 Data Quality Suite** | 14 Tests | 100% | **PASS** |
| **Phase 3 Reconciliation Tie-Outs** | 18 Months | 100% | **PASS (0 diff)** |
| **Phase 4 Automated Verification Suite** | 48 Tests | 100% | **PASS** |
| **Governed Metrics REST API** | 5 Endpoints | 100% | **PASS (200 OK)** |
