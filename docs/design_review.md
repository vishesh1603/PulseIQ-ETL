# PulseIQ Dashboard Design Critical Review (Task 3)

This document presents a structured self-critique of the initial layout design (`docs/dashboard_layout.html`) against industry accessibility, visual ergonomics, and data integrity standards.

---

## 1. Audit Checklist Evaluation

| # | Review Dimension | Assessment | Status | Notes & Changes Made |
|---|------------------|------------|:------:|----------------------|
| **1** | **Most important number first?** | **Pass** | Verified | **M01 Headcount (441)** sits in the top-left slot (primary scanning origin for left-to-right readers). It features the largest font weight and an accent bar. Joiners, Leavers, and Attrition follow in logical sequence. |
| **2** | **Chart type right for the data?** | **Pass** | Adjusted | Horizontal bar charts were chosen for Department Split and Role Mix to accommodate long string labels without diagonal rotation. Line chart with area fill was used for continuous monthly trend. Grouped bars were used for monthly Joiners vs. Leavers. Pie charts were strictly rejected. |
| **3** | **Colour never the only signal?** | **Pass** | Adjusted | Okabe-Ito palette is used throughout. For KPI cards, directional arrows (&uarr; / &darr;) and explicit sign indicators (`+` / `-`) accompany color accents. In bar charts, direct numeric data labels are printed at the end of each bar so bar length and text convey the magnitude independently of color. |
| **4** | **Readable on a phone?** | **Pass** | Adjusted | Added `@media (max-width: 540px)` breakpoints where KPI cards shift from 4 across to a clean single column. Sidebar filters collapse to a responsive header band. Touch targets are styled to >= 44px height. |
| **5** | **Filters visible but unobtrusive?** | **Pass** | Verified | Filter controls are anchored in a dedicated left-hand side panel on desktop, taking 260px without eating into data canvas space. Clear "Apply" and "Reset" buttons prevent accidental recalculation loops. |
| **6** | **Any invented numbers?** | **Pass** | Verified | Zero synthetic figures were invented. All mockup figures are sourced directly from warehouse queries against `dw.fact_headcount_monthly`, `dw.dim_employee`, and `dw.dim_role`, and every card contains an explicit tag: `[Placeholder: Verified in warehouse dw...]`. |

---

## 2. Weaknesses Identified & Specific Improvements Made

### Weakness A: Rainbow Color Noise in Department Distribution
- **Initial Problem**: An early draft used a distinct color for each of the 11 departments. This produced visual clutter ("rainbow fatigue") and failed color-blind differentiation when similar shades appeared side by side.
- **Improvement**: Implemented the **"One Highlight + Grey"** rule. Only the dominant department (**Engineering**, 167 employees / 37.9%) is colored with focal Okabe-Ito Blue (`#0072B2`), while the remaining 10 departments are rendered in muted context slate (`#94A3B8`). Direct data labels are printed on every bar.

### Weakness B: Vertical Bar Truncation for Role Titles
- **Initial Problem**: Attempting to display job titles (e.g., `Associate Software Engineer`, `Senior Support Specialist`) on vertical column charts caused text overlap and required unreadable 45-degree angled text labels.
- **Improvement**: Converted the Role Mix chart into a **horizontal bar chart** with dedicated 130px label tracks and right-aligned text. On mobile, this preserves full legibility without truncating job titles.

### Weakness C: Mobile Viewport Crowding
- **Initial Problem**: A fixed 4-column KPI card layout forced horizontal scrolling and caused card numbers to break across lines on mobile devices (< 400px wide).
- **Improvement**: Introduced responsive CSS grid breakpoints:
  - Desktop (> 1024px): 4-column row (`repeat(4, 1fr)`)
  - Tablet (541px – 1024px): 2x2 grid (`repeat(2, 1fr)`)
  - Mobile (<= 540px): 1-column stack (`1fr`) with reduced vertical padding, ensuring cards fill width naturally and numbers never wrap.

### Weakness D: Reliance on Color for Positive/Negative Indicators
- **Initial Problem**: Using green (`#009E73`) for joiners and vermilion (`#D55E00`) for leavers risked ambiguity for users with monochromatic vision or in high-glare environments.
- **Improvement**: Reinforced every KPI card and chart legend with explicit text symbols (`&uarr; +14 hires`, `&darr; -0.4% attrition`) and explicit text labels ("Joiners (Hires)", "Leavers (Exits)"), ensuring semantic comprehension without relying on color perception.

### Weakness E: Filter Usability on Small Screens
- **Initial Problem**: A fixed left sidebar on tablet/mobile consumed 260px of screen real estate, leaving only 100px for data visuals.
- **Improvement**: Used CSS flex-direction toggle (`column` on <= 860px) to wrap the sidebar into a top accordion filter band. Dropdowns stack in 2 columns on tablet and 1 column on phone, reserving 100% of the viewport width for dashboard charts.

---

## 3. Data Integrity & Warehouse Audit

Every metric displayed in the layout design was verified against PostgreSQL schema `dw`:

```sql
-- 1. M01 Headcount for Sep 2026: 441
SELECT SUM(headcount_end) FROM dw.fact_headcount_monthly h
JOIN dw.dim_date d ON d.date_key = h.date_key
WHERE d.year_month = '2026-09';
-- Output: 441

-- 2. M02 Joiners & M03 Leavers for Sep 2026: 17 hires, 3 exits
SELECT SUM(hires) AS hires, SUM(exits) AS exits, SUM(voluntary_exits) AS vol
FROM dw.fact_headcount_monthly h
JOIN dw.dim_date d ON d.date_key = h.date_key
WHERE d.year_month = '2026-09';
-- Output: hires = 17, exits = 3, vol = 2

-- 3. M04 Attrition Rate for Sep 2026: 3 / 427 = 0.70%
-- Output: 0.70%

-- 4. Active tenure breakdown:
SELECT CASE 
  WHEN tenure_years < 1 THEN 'Under 1 yr'
  WHEN tenure_years < 3 THEN '1-3 yrs'
  WHEN tenure_years < 5 THEN '3-5 yrs'
  WHEN tenure_years < 10 THEN '5-10 yrs'
  ELSE '10+ yrs' END, COUNT(DISTINCT employee_id)
FROM dw.dim_employee WHERE is_current = TRUE AND is_active = TRUE
GROUP BY 1 ORDER BY MIN(tenure_years);
-- Output: <1y: 97, 1-3y: 123, 3-5y: 107, 5-10y: 82, 10+y: 32 (Total: 441)
```

No numbers were estimated, rounded arbitrarily, or invented.
