# PulseIQ Dashboard Design Notes (Tasks 3 & 18)

This document records the visual layout prompts, AI design exploration, and self-critique modifications in accordance with Section 6 and Section 8 (Tasks 3 & 18) of the Data Analyst Guide.

---

## 1. Initial AI Design Prompt

The following prompt was used to explore responsive layouts and component hierarchies:

> "Design a responsive executive HR workforce analytics dashboard layout with a top global header, 4 primary KPI cards at the top displaying the most important number first (Headcount, Monthly Joiners, Monthly Leavers, Monthly Attrition Rate), followed by a grid of analytical charts: monthly headcount trend line, department distribution horizontal bar chart, employee tenure bands, role mix bar chart, and monthly hires vs exits. Include a collapsible left-hand filter panel with department selector and date-range slider. Ensure the design collapses into a clean, legible single column on mobile devices and adheres strictly to color-blind safe palettes."

---

## 2. Review Against Section 6 Rules

The layout prototype in `docs/dashboard_layout.html` was evaluated against the Section 6 style rules:

1. **Color Palette**:
   - Palette standard: Navy `#1F3864`, Blue `#2E75B6`, Orange `#C55A11`, Green `#548235`, Grey `#7F7F7F`.
   - Accessible pairing: Blue and Orange used for positive vs negative signaling (e.g. Joiners vs Leavers). Red and Green are never used alone.
   - Contrast check: All text meets WCAG AA standards (contrast ratio >= 4.5:1 against surfaces).
2. **Typography**:
   - Primary: `Inter`, with universal system fallbacks (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`).
3. **Number Formats**:
   - Headcount & integer counts: `1,234`
   - Currency: Indian Lakhs/Crores format (`₹ 52.74 L`, `₹ 5.55 Cr`).
   - Percentages: Exactly one decimal place (`0.7%`, `95.2%`).
4. **Mandatory Takeaways**:
   - Every single chart contains a formal metric code title (e.g. `M01 Headcount Trend`) and an empirical one-line takeaway sentence computed directly from PostgreSQL warehouse queries.

---

## 3. Changes Made Following Critique

As documented in `docs/design_review.md`, the following 5 weaknesses were identified and rectified:
- **Noise Elimination**: Avoided rainbow color schemes by applying the "One Highlight Color + Neutral Grey" rule.
- **Horizontal Bar Orientation**: Role titles and department names rotated to horizontal bars to eliminate label truncation on smaller viewports.
- **Redundant Signal Encoding**: Added explicit directional arrows (`▲`, `▼`) and textual labels alongside colors so that information is never communicated by color alone.
- **Mobile Grid Collapse**: Implemented CSS media queries (`@media (max-width: 768px)`) collapsing cards and filters into an ergonomic single-column vertical stack.
- **Zero Hallucinated Metrics**: All placeholder values in wireframes and dashboard descriptions were cross-verified against real warehouse figures (e.g. Headcount = `441`, Joiners = `17`, Leavers = `3`, Attrition = `0.70%`).
