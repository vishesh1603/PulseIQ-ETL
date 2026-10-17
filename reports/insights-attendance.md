# Executive Insight Note: Attendance Dynamics & AI Behavioral Anomalies

**Author**: PulseIQ Analytics Team  
**Dataset Cut-off**: 30 September 2026  
**Audience**: Chief Human Resources Officer (CHRO), VP of People Operations, Department Heads  
**Scope**: 18-month longitudinal analysis (April 2025 – September 2026), 7,339 attendance records, 3,441 leave requests, and 221 AI-flagged attendance anomalies.

---

## Executive Summary

Across the 18-month reporting window, PulseIQ maintained an overall healthy monthly attendance rate oscillating between **92.89%** and **95.51%** (September 2026 benchmark: **95.19%**). However, aggregate averages mask significant seasonal volatility, departmental attendance friction, and behavioral anomaly clusters detected by the machine learning isolation forest models.

This briefing outlines three empirical findings derived directly from PostgreSQL warehouse truth, evaluates the operational implications, provides concrete HR recommendations, and transparently details data caveats.

---

## 1. Key Empirical Findings

### Finding 1: Seasonal Engagement Trajectory & Summer Attendance Dips
- **Empirical Baseline**: Company-wide attendance peaked in **July 2025 (95.51%)**, **September 2025 (95.48%)**, and **September 2026 (95.19%)**.
- **Seasonal Trough**: A recurring annual engagement dip occurs during May:
  - May 2025 attendance dropped to **93.46%** (a 1.12% drop from April 2025).
  - May 2026 attendance reached the 18-month nadir at **92.89%** (down 1.55% from March 2026).
- **Trailing Moving Average**: A 3-month trailing moving average (`AVG(attendance_rate) OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`) effectively smooths monthly variance, demonstrating that underlying organizational attendance recovered from its summer low of **93.20%** (June 2026) to **94.51%** by September 2026.
- **Operational Reality**: The May drop corresponds with school holidays, annual family travel, and festival leave requests. While expected, the unmanaged overlap of leaves during this window created delivery strain in customer-facing departments.

---

### Finding 2: Leave Dynamics & End-of-Week Concentration
- **Leave Volume**: Employees took **7,999.0 total leave days** across **3,441 approved/processed requests**.
- **Leave Type Mix**:
  1. *Earned (Privilege) Leave*: **1,266 requests / 2,613.0 days (32.7%)** — primary vehicle for planned vacations.
  2. *Casual Leave*: **1,082 requests / 2,226.0 days (27.8%)** — short-term personal leaves.
  3. *Sick Leave*: **933 requests / 1,962.0 days (24.5%)** — unplanned medical absences.
  4. *Maternity Leave*: **7 requests / 910.0 days (11.4%)** — long-duration statutory leaves (average 130.0 days per leave).
  5. *Loss of Pay (Unpaid)*: **61 requests / 135.0 days (1.7%)** — unauthorized or exhausted quota leaves.
- **Weekday Concentration**: All 3,441 leave requests started on standard business weekdays (zero recorded weekend starts). However, start dates skew towards the end of the work week:
  - **Friday**: **720 requests (20.9%)**, **1,746.0 days** (highest volume of leave starts).
  - **Thursday**: **714 requests (20.7%)**, **1,751.0 days**.
  - **Wednesday**: **686 requests (19.9%)**, **1,652.0 days**.
  - **Tuesday**: **672 requests (19.5%)**, **1,372.0 days**.
  - **Monday**: **649 requests (18.9%)**, **1,478.0 days**.
- **Insight**: Employees disproportionately initiate time off on Thursday and Friday to bridge into weekends (41.6% of all leave starts), causing end-of-week coverage gaps in operational units.

---

### Finding 3: AI Anomaly Clusters & Departmental Vulnerability
- **Total Anomaly Scope**: The isolation forest anomaly model flagged **221 attendance records** across **159 distinct employees** (averaging 12.3 anomalies per month). All records carried an explicit `flagged = 'Y'` signal.
- **Taxonomy of Reasons**:
  1. `PATTERN_SHIFT`: **125 flags (56.6%)** | Mean Anomaly Score: **0.661** (Range: 0.566 – 0.882). Sudden disruptions to established check-in and attendance rhythms.
  2. `NO_ATTENDANCE`: **50 flags (22.6%)** | Mean Anomaly Score: **0.887** (Range: 0.833 – 1.000). Entire months with zero physical or remote presence recorded.
  3. `LONG_UNPAID_ABSENCE`: **43 flags (19.5%)** | Mean Anomaly Score: **0.818** (Range: 0.673 – 0.925). Extended leave without pay without prior statutory leave status.
  4. `FREQUENT_LATE`: **3 flags (1.4%)** | Mean Anomaly Score: **0.600** (Range: 0.577 – 0.627). Chronic late logins.
- **Departmental Concentration & Friction**:
  - **Engineering**: **63 anomalies (28.5%)** across 169 employees (**0.37 flags per head**). Driven primarily by flexible remote schedule `PATTERN_SHIFT` flags.
  - **Customer Support**: **48 anomalies (21.7%)** across 59 employees (**0.81 flags per head**). This represents the highest per-capita anomaly concentration in the enterprise.
  - Combined with a September 2026 attendance rate of **92.43%** (second-lowest in the firm), Customer Support experiences pronounced attendance fragility.
- **Peak Anomaly Month**: **July 2026** registered **22 anomalies**, coinciding with post-midyear performance reviews and organizational re-assignments.

---

## 2. Departmental Benchmark Overview (September 2026)

| Department | Headcount | Attendance Rate (M13) | Late Arrival Rate (M14) | Unpaid Leave Days (M15) | AI Anomalies |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Executive Office** | 1 | 100.0% | 0.0% | 0.0 | 0 |
| **Sales** | 47 | 97.5% | 6.6% | 8.5 | 0 |
| **Engineering** | 169 | 96.2% | 7.2% | 28.5 | 3 |
| **Marketing** | 13 | 96.2% | 7.3% | 1.5 | 0 |
| **Operations & IT** | 29 | 96.0% | **10.4%** | 6.0 | 1 |
| **Human Resources** | 20 | 95.8% | 5.8% | 4.5 | 0 |
| **Product & Design** | 26 | 95.3% | 7.3% | 10.5 | 2 |
| **Data & AI** | 52 | 94.4% | 6.9% | 12.5 | 1 |
| **Legal & Compliance** | 11 | 93.3% | 7.0% | 2.5 | 0 |
| **Customer Support** | 59 | **92.4%** | 6.5% | 8.5 | 2 |
| **Finance & Accounts** | 17 | **88.9%** | 8.3% | 2.5 | 1 |
| **Company Total** | **441** | **95.2%** | **7.1%** | **85.5** | **10** |

*Note: In September 2026, Operations & IT logged the highest late arrival rate at 10.4%, while Finance & Accounts registered the lowest overall attendance rate at 88.9%.*

---

## 3. Actionable HR Operations Recommendations

1. **Targeted Operational Intervention in Customer Support**:
   - Establish a bi-weekly attendance health review between People Operations and Customer Support team leads.
   - Investigate the root causes of the **0.81 anomalies per head** concentration (shift burnout, schedule misalignment, or ticketing software logging friction).
2. **Proactive Summer Capacity & Leave Quotas**:
   - Implement an automated leave quota calendar for April–June to cap simultaneous department-level absences at **15%** of team headcount.
   - Introduce early-bird summer leave planning windows in Q1 to eliminate May delivery bottlenecks.
3. **Automated Triage Protocol for `PATTERN_SHIFT` and `NO_ATTENDANCE`**:
   - Mandate that ML-flagged records with an anomaly score $> 0.80$ automatically trigger an HR Business Partner (HRBP) check-in within 5 business days.
   - For `NO_ATTENDANCE` flags (mean score 0.887), reconcile immediately against payroll records to prevent ghost payroll or unrecorded long leaves.
4. **Operations & IT Shift Punctuality Review**:
   - Address the **10.4% late arrival rate** in Operations & IT by reviewing shift start times and flexible arrival buffers for on-call engineers.

---

## 4. Methodology Notes & Transparent Caveats

1. **Grain Distinction**: `fact_attendance_monthly` reports employee attendance aggregated at the monthly grain. While `fact_leave` contains exact request start/end dates, intra-day swipe times and daily clock-in timestamps are not present in the current star schema.
2. **Synthetic Data Artifacts**:
   - In synthetic datasets, weekday distributions can exhibit uniform spreads across Monday–Friday with zero weekend entries.
   - `fact_anomaly` flags represent model outputs from an Isolation Forest algorithm (`iforest-attendance-0.1`). As documented in the metric dictionary ([`M26`](file:///c:/Users/DELL/Downloads/pulseiq-etl1/docs/metric_dictionary.md)), *flags are leads for human inquiry, not conclusive proof of employee misconduct*.
3. **Small Sample Nuance**: Departments with small headcount (e.g., Executive Office $N=1$, Legal & Compliance $N=11$) can swing percentage metrics substantially from a single employee's absence.
