-- target: dw.fact_headcount_monthly
-- key: date_key, department_key
-- mirror: true
-- Derived from dim_employee history, so it always agrees with the dimension.
-- An employee counts in the department of the version that is valid on the day.
--   headcount_start / headcount_end: people on the last day of the previous month / this month
--   hires: first version starts in the month        exits: exit_date falls in the month
--   transfers_in / transfers_out: a version with change_reason 'Transfer' starts in the month
WITH months AS (
    SELECT d.date_key, d.month_start_date AS ms, d.month_end_date AS me
    FROM dw.dim_date d
    WHERE d.is_month_end
      AND d.month_end_date <= (SELECT max(dd.month_end_date)
                               FROM dw.fact_payroll p JOIN dw.dim_date dd ON dd.date_key = p.date_key)
),
slots AS (
    SELECT m.date_key, m.ms, m.me, dep.department_key
    FROM months m CROSS JOIN dw.dim_department dep
),
v AS (
    SELECT e.*,
           lag(e.department_key) OVER (PARTITION BY e.employee_id ORDER BY e.valid_from) AS prev_department_key,
           e.valid_from = min(e.valid_from) OVER (PARTITION BY e.employee_id)             AS is_first_version
    FROM dw.dim_employee e
),
headcount_end AS (
    SELECT m.date_key, v.department_key, count(*) AS n
    FROM months m JOIN v ON v.valid_from <= m.me AND v.valid_to >= m.me AND v.hire_date <= m.me
                        AND (v.exit_date IS NULL OR v.exit_date > m.me)
    GROUP BY 1, 2
),
headcount_start AS (
    SELECT m.date_key, v.department_key, count(*) AS n
    FROM months m JOIN v ON v.valid_from <= m.ms - 1 AND v.valid_to >= m.ms - 1 AND v.hire_date <= m.ms - 1
                        AND (v.exit_date IS NULL OR v.exit_date > m.ms - 1)
    GROUP BY 1, 2
),
hires AS (
    SELECT m.date_key, v.department_key, count(*) AS n
    FROM months m JOIN v ON v.is_first_version AND v.hire_date BETWEEN m.ms AND m.me
    GROUP BY 1, 2
),
exits AS (
    SELECT m.date_key, v.department_key, count(*) AS n, count(*) FILTER (WHERE v.employment_status = 'Resigned') AS voluntary
    FROM months m JOIN v ON v.exit_date BETWEEN m.ms AND m.me AND v.valid_from <= v.exit_date AND v.valid_to >= v.exit_date
    GROUP BY 1, 2
),
transfers_in AS (
    SELECT m.date_key, v.department_key, count(*) AS n
    FROM months m JOIN v ON v.change_reason = 'Transfer' AND v.valid_from BETWEEN m.ms AND m.me
    GROUP BY 1, 2
),
transfers_out AS (
    SELECT m.date_key, v.prev_department_key AS department_key, count(*) AS n
    FROM months m JOIN v ON v.change_reason = 'Transfer' AND v.valid_from BETWEEN m.ms AND m.me
    GROUP BY 1, 2
)
SELECT s.date_key, s.department_key,
       COALESCE(hs.n, 0)::integer AS headcount_start,
       COALESCE(h.n, 0)::integer  AS hires,
       COALESCE(x.n, 0)::integer  AS exits,
       COALESCE(x.voluntary, 0)::integer AS voluntary_exits,
       COALESCE(ti.n, 0)::integer AS transfers_in,
       COALESCE(tout.n, 0)::integer AS transfers_out,
       COALESCE(he.n, 0)::integer AS headcount_end,
       CASE WHEN COALESCE(hs.n, 0) = 0 THEN 0 ELSE round(100.0 * COALESCE(x.n, 0) / hs.n, 2) END AS attrition_rate_monthly_pct
FROM slots s
LEFT JOIN headcount_start hs ON hs.date_key = s.date_key AND hs.department_key = s.department_key
LEFT JOIN headcount_end   he ON he.date_key = s.date_key AND he.department_key = s.department_key
LEFT JOIN hires           h  ON h.date_key  = s.date_key AND h.department_key  = s.department_key
LEFT JOIN exits           x  ON x.date_key  = s.date_key AND x.department_key  = s.department_key
LEFT JOIN transfers_in    ti ON ti.date_key = s.date_key AND ti.department_key = s.department_key
LEFT JOIN transfers_out   tout ON tout.date_key = s.date_key AND tout.department_key = s.department_key
