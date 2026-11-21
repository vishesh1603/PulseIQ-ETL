# PulseIQ — Self-Service User Guide

> **Phase 4 — Task 19** | For non-technical business users  
> **Live Production Dashboard**: [https://pulseiq-etl-0801.onrender.com/](https://pulseiq-etl-0801.onrender.com/)  
> Local Development URL: [http://localhost:8501](http://localhost:8501)

---

## Section 1 — Getting Started

### Opening the Dashboard

You can access PulseIQ in two ways:
1. **Live Production Cloud (Instant Access — Zero Setup)**:
   Navigate directly in any web browser to: **[https://pulseiq-etl-0801.onrender.com/](https://pulseiq-etl-0801.onrender.com/)**
2. **Local Machine (via Docker)**:
   Make sure Docker is running, then run:
   ```powershell
   docker compose up -d warehouse
   python -m streamlit run app.py
   ```
   Open: **http://localhost:8501**

The dashboard will load with the **Overview** page showing key headline numbers.

### Navigating Pages

Use the **left sidebar** to switch between pages. There are 12 pages total:

| Page | What it shows |
| :--- | :--- |
| **Overview** | Headline KPIs — headcount, hires, leavers, total payroll |
| **0. About & Lineage** | What every number means and where it comes from |
| **1. Attendance & Leave** | Attendance rate, late arrivals, leave patterns by month |
| **2. Attrition Analytics** | Who is leaving, when, and why (voluntary vs involuntary) |
| **3. Team Productivity** | Engineering sprint velocity, completion rates, cycle time |
| **4. Payroll Reconciliation** | Payroll costs and 18-month reconciliation audit |
| **5. Budget Variance** | Actual vs budget spend by department |
| **6. Profit & Loss** | Revenue, expenses, margin, top vendors |
| **7. Invoices & Cash Flow** | Outstanding invoices, aging buckets, cash in vs out |
| **8. Cross-Department Impact** | How HR outcomes correlate with financial results |
| **9. AI Signals** | Anomaly alerts, attrition risk scores, headcount forecast |
| **10. Executive Scorecard** | Founder's 8 KPIs in one printable page |
| **11. Alert History** | Log of KPI breaches and alert delivery history |

### Light / Dark Mode Toggle

Click the **☀️ / 🌙** toggle in the top-right corner of any page to switch between light and dark mode. Your choice is remembered for the session.

---

## Section 2 — Reading the Executive Scorecard

The **Executive Scorecard** (Page 10) shows the 8 Founder KPIs at a glance. Each KPI has a **traffic-light status**:

| Colour | Meaning |
| :--- | :--- |
| 🟢 **Green** | On target — no action needed |
| 🟡 **Amber** | Within 10% of threshold — monitor closely |
| 🔴 **Red** | Breached threshold — needs attention |

### The 8 Founder KPIs Explained

| KPI | Plain English | Target | Why It Matters |
| :--- | :--- | :--- | :--- |
| **Total Headcount** | How many people are employed right now | ≥ 420 | Signals growth or contraction |
| **12M Attrition Rate** | Out of every 100 employees, how many left in the past year | ≤ 12% | High attrition is expensive — costs ~1× salary to replace |
| **Attendance Rate** | Out of scheduled work days, what % were people present | ≥ 90% | Low attendance predicts low morale and productivity |
| **Gross Pay Total** | Total earnings paid out before tax | — | Tracks the company's largest expense |
| **Operating Margin** | What % of revenue is left after all costs | ≥ 10% | Below 10% means the business is barely profitable |
| **Revenue (Monthly)** | Total income booked in the accounts this month | ≥ ₹7.5 Cr | The top line — are we growing? |
| **DSO (Days to Collect)** | On average, how many days does it take to get paid | ≤ 60 days | >60 days means cash is stuck in invoices |
| **Task Completion Rate** | What % of planned engineering work gets done | ≥ 70% | Low delivery rate signals resource or planning issues |

---

## Section 3 — Drilling Down from the Scorecard

The scorecard is a summary. When a KPI turns amber or red, click through to the detail page to find out why.

### Example: Attrition is Red

1. The scorecard shows **12M Attrition Rate = 15.2% 🔴** (target: ≤12%).
2. Navigate to **Page 2 — Attrition Analytics**.
3. Use the **Department filter** in the sidebar to narrow down: which department is driving the spike?
4. Check the **Tenure at Exit** chart: are leavers mostly < 1-year employees? That points to onboarding issues.
5. Look at the **CortexHR Risk Bands**: departments with more "High Risk" employees need immediate manager attention.
6. Cross-reference with **Page 1 — Attendance**: a dip in attendance often precedes attrition by 2–3 months.

### Example: Operating Margin is Amber

1. The scorecard shows **Operating Margin = 11.2% 🟡** (target: ≥12%).
2. Navigate to **Page 6 — Profit & Loss**.
3. Check the **Top 10 Vendors** table — are any vendor costs unusually high?
4. Look at the **P&L table**: which expense category grew this month?
5. Cross to **Page 5 — Budget Variance**: which department is overspending its budget?

---

## Section 4 — Understanding AI Signals (Page 9)

The AI Signals page uses machine-learning models to flag unusual patterns before they become problems.

### Anomaly Alerts

- **What it is:** Rows in payroll, attendance, or financial data that look statistically unusual compared to history.
- **Money at Risk:** Each anomaly is tagged with an estimated financial exposure. Sort by "Money at Risk" to prioritise investigation.
- **Confidence Score:** A number between 0 and 1. Above 0.7 = likely real anomaly. Below 0.5 = investigate but don't panic.
- **Action:** Click on a flagged record to see the raw values. Compare to the same employee/department in prior months.

### Attrition Risk Bands

Employees are scored by the CortexHR model into three risk bands:

| Band | Meaning | Suggested Action |
| :--- | :--- | :--- |
| 🔴 **High** | >70% probability of leaving within 90 days | Manager 1-on-1, compensation review |
| 🟡 **Medium** | 40–70% probability | Stay-interview, development plan |
| 🟢 **Low** | <40% probability | Standard engagement |

> **Privacy note:** Groups with fewer than 10 employees show `—` (suppressed) instead of a risk score. This protects individual privacy.

### Headcount Forecast

The forecast shows expected headcount 3 months ahead with an **80% confidence interval**:
- The **line** = most likely headcount.
- The **shaded band** = the range that the actual number will land in 8 times out of 10.
- A **narrowing band** means the model is confident. A **widening band** means higher uncertainty (e.g., after a restructure).

---

## Section 5 — Frequently Asked Questions

**Q: Why doesn't my revenue number match what I see in my invoice report?**

Revenue in PulseIQ (M16) is sourced from the **general ledger** (account codes 4001–4004), not from the invoice register. The ledger is the system of record after payment is received. Invoices may be issued but not yet posted to the ledger. For outstanding invoices, see **Page 7 — Cash Flow** (M21: Overdue Receivables).

---

**Q: What is DQ-04 / account hierarchy?**

The company's chart of accounts has two types: **group accounts** (headings) and **detail accounts** (actual postings). PulseIQ only sums detail accounts in revenue and expense metrics. This prevents double-counting — if we included both a "Total Payroll" group account AND its children (Basic Pay, Overtime, etc.), the total would be twice the actual cost. See `docs/metric_lineage_catalog.md` for the full rule.

---

**Q: Why does a department show `—` instead of a number?**

This is **privacy suppression**. When a department has fewer than 5 employees (or 10 for sensitive metrics like attrition), the value is replaced with `—` to prevent identifying any individual employee's data. This is by design and complies with the minimum group size rule.

---

**Q: Why are 4 payroll rows marked as "quarantined"?**

During data loading, 4 rows (PI-X0001 to PI-X0004) failed data quality checks (negative gross pay, impossible dates). These rows are stored in `data/rejected/` with the reason code attached. They are **excluded** from all metrics. This is intentional — the reconciliation has been verified to ₹0.00 without them.

---

**Q: How fresh is the data?**

The ETL pipeline runs automatically every day at 02:00 AM. You can see the last run timestamp on **Page 0 — About & Lineage** in the Pipeline Health panel. If the pipeline has not run in the last 24 hours, the status will show a warning on the Alert History page.

---

**Q: How do I get alerts when a KPI goes red?**

By default, alerts are written to `logs/alerts.log`. To receive Slack or email alerts, ask your administrator to set `ALERT_CHANNEL=webhook` and `ALERT_WEBHOOK_URL=<your Slack webhook URL>` in the `.env` file and restart the scheduler.

---

**Q: Can I export the charts?**

Yes. Hover over any Plotly chart and click the **camera icon** (📷) in the top-right corner to download it as a PNG. For the Executive Scorecard, use `Ctrl+P` (or `Cmd+P` on Mac) to print or save as PDF — the page is formatted for A4.

---

*PulseIQ Phase 4 — Self-Service Guide | Version 4.0 | November 2026*
