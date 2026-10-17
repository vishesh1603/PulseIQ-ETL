# PulseIQ Visual Style Guide (Task 3)

This style guide establishes the visual and typographical standards for all PulseIQ analytics dashboards (Tasks 3 through 20). Following a consistent visual standard builds trust with HR leaders, executives, and department managers, and ensures that charts are accessible to everyone, including people with color vision deficiencies.

---

## 1. Color Palette: Okabe-Ito (Color-Blind Safe)

We use the scientifically validated **Okabe-Ito** palette. This palette is distinguishable by individuals with all common types of color blindness (deuteranopia, protanopia, tritanopia), while also printing cleanly in black-and-white.

### Palette Codes & Roles

| Swatch Name | Hex Code | Semantic Role | Usage Guidance |
|-------------|----------|---------------|----------------|
| **Blue** | `#0072B2` | **Primary Brand & Highlight** | Primary focus series, selected state, key trend line |
| **Orange** | `#E69F00` | Secondary Series / Alert | Comparison series, warning badges, voluntary exits |
| **Bluish Green** | `#009E73` | Positive Trend / Success | Joiners / hires, high attendance, targets met |
| **Sky Blue** | `#56B4E9` | Light Accent | Secondary bars, informational accents, WFH share |
| **Vermilion** | `#D55E00` | Critical / Attention | Exits / leavers, high attrition, anomalies, risk |
| **Reddish Purple**| `#CC79A7` | Tertiary Series | Overtime, special leave types, distinct departments |
| **Yellow** | `#F0E442` | Highlight Accent | Outlier dots, threshold callouts, warnings |

### Neutral Colors (Text & Canvas)

| Neutral Role | Hex Code | Usage |
|--------------|----------|-------|
| **Dark Text** | `#1E293B` | Main headers, chart titles, axis labels, KPI values (contrast ratio > 10:1) |
| **Muted Text** | `#64748B` | Subtitles, takeaway sentences, footnote caveats, axis units |
| **Border / Rule** | `#E2E8F0` | Card borders, table dividers, subtle gridlines |
| **Card Surface** | `#FFFFFF` | KPI card backgrounds, chart card canvas |
| **App Background**| `#F8FAFC` | Dashboard canvas background (cool off-white) |
| **Neutral Context Bar**| `#94A3B8` | Non-focused categories in bar charts when highlighting one department |

### The "One Highlight + Grey" Rule
When presenting categorical comparisons (e.g., comparing 11 departments):
- **Do not** use 11 rainbow colors. Doing so creates visual fatigue and rainbow noise.
- **Do** color only the focal department with `#0072B2` (or the top performer) and render all other departments in soft slate grey (`#94A3B8`).
- Never rely on color as the sole conveyor of information: always pair color with clear labels, numbers, or sorting order.

---

## 2. Typography

We select one modern, highly readable font family with universal system fallbacks:

```css
font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

### Hierarchy & Scale

| Element | Size | Weight | Line Height | Color |
|---------|------|--------|-------------|-------|
| **Dashboard Header** | 22px | Bold (700) | 28px | `#1E293B` |
| **Section Header** | 18px | Semi-Bold (600) | 24px | `#1E293B` |
| **Chart Title** | 15px | Semi-Bold (600) | 20px | `#1E293B` |
| **Takeaway Sentence** | 13px | Medium (500) | 18px | `#475569` |
| **KPI Headline Value** | 28px | Bold (700) | 34px | `#0072B2` or `#1E293B` |
| **KPI Label / Context** | 12px | Regular (400) | 16px | `#64748B` |
| **Body / Table Text** | 13px | Regular (400) | 18px | `#1E293B` |
| **Axis Label / Ticks** | 11px | Regular (400) | 14px | `#64748B` |

---

## 3. Number & Date Formatting

Consistent formatting eliminates ambiguity for business users and aligns directly with the metric dictionary (`docs/metric_dictionary.md`).

| Data Type | Rule | Correct Example | Incorrect Example |
|-----------|------|-----------------|-------------------|
| **Headcount & People** | Integer with thousands commas | `441`, `1,234` | `441.0`, `1234` |
| **Percentages** | Exactly one decimal place + `%` | `0.7%`, `12.5%` | `0.7042%`, `.7%` |
| **Currency (Payroll/INR)**| Rupee sign `₹` in Lakhs (`L`) or Crores (`Cr`)| `₹52.74 L`, `₹5.34 Cr` | `52740110`, `$5.3M` |
| **Days / Hours** | One decimal place when fractional | `21.5 days`, `40.0 hrs` | `21.5333`, `21 days 4 hrs` |
| **Calendar Months** | Three-letter month abbreviation + 4-digit year | `Apr 2025`, `Sep 2026` | `04/2025`, `2025-04` (in UI text) |
| **Specific Dates** | Day, 3-letter month, 4-digit year | `30 Sep 2026` | `09/30/2026`, `2026-09-30` |

---

## 4. The Golden Rule: Title + One-Line Takeaway

Every chart card must communicate its core conclusion immediately. A reader should never have to decipher raw axes to understand the message.

### Format Standard
1. **Title**: Uses the metric dictionary code and official name (e.g., `M01 Headcount Trend (2020 - 2026)`).
2. **Takeaway Sentence**: Exactly one sentence placed directly underneath the title.
   - Must be formulated from **real warehouse numbers** (never guessed or invented).
   - Answers: *What happened, by how much, and what does it mean?*

### Examples
- **M01 Headcount Trend**:
  > **M01 Headcount Trend (Monthly)**  
  > *Total headcount grew from 380 in April 2025 to 441 in September 2026 (+16.1%), driven primarily by Engineering hiring.*

- **M01 Department Distribution**:
  > **M01 Headcount by Department (Sep 2026)**  
  > *Engineering represents the largest single function at 167 employees (37.9% of company total), followed by Support (59) and Data & AI (52).*

- **Tenure Bands**:
  > **Active Employees by Tenure Band**  
  > *Over half the organization (50.6%) has joined within the last 3 years, with 97 employees having under 1 year of tenure.*

---

## 5. Summary Checklist for Dashboard Builders
- [ ] Is Okabe-Ito color palette used?
- [ ] Is color never the only visual differentiator?
- [ ] Are headings set in `Inter` / system sans-serif?
- [ ] Are currency figures displayed with `₹` in Lakhs or Crores?
- [ ] Does every chart have an official metric name title and an empirical one-line takeaway sentence?
