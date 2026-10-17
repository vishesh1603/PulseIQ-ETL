-- target: dw.dim_date
-- key: date_key
-- stage: stg_dim_date
SELECT date_key, date AS full_date, year::smallint, quarter::smallint, month_number::smallint, month_name, year_month,
       week_of_year::smallint, day_of_week, is_weekend = 'Y' AS is_weekend, is_holiday = 'Y' AS is_holiday,
       is_working_day = 'Y' AS is_working_day, financial_year, fiscal_quarter, fiscal_month_number::smallint,
       is_month_end = 'Y' AS is_month_end, month_start_date, month_end_date
FROM stg_dim_date
