"""
Generate DDL and loading scripts for all additional tables from PulseIQ_Star_Schema_Dataset.xlsx
"""
import pandas as pd

excel_path = r'c:\Users\DELL\Downloads\pulseiq-etl1\data\raw\PulseIQ_Star_Schema_Dataset.xlsx'
xl = pd.ExcelFile(excel_path)

new_sheets = [
    'dim_location',
    'dim_account',
    'dim_client',
    'dim_vendor',
    'dim_team',
    'dim_sprint',
    'fact_ledger',
    'fact_invoice',
    'fact_invoice_payment',
    'fact_expense',
    'fact_task',
    'fact_attrition_risk',
    'fact_forecast',
    'budget_payroll_dept_month',
    'kpi_targets',
]

for s in new_sheets:
    df = pd.read_excel(xl, s, nrows=2)
    print(f"\n-- {s}")
    cols_def = []
    for c in df.columns:
        dt = df[c].dtype
        col_type = 'TEXT'
        if 'int' in str(dt):
            col_type = 'BIGINT' if 'id' in c or 'amount' in c or 'key' in c else 'INTEGER'
        elif 'float' in str(dt):
            col_type = 'NUMERIC(14,2)' if ('amount' in c or 'cost' in c or 'pay' in c or 'debit' in c or 'credit' in c or 'balance' in c or 'subtotal' in c or 'gst' in c) else 'NUMERIC(10,4)'
        elif 'datetime' in str(dt):
            col_type = 'TIMESTAMP'
        cols_def.append(f"    {c} {col_type}")
    print(f"CREATE TABLE IF NOT EXISTS dw.{s} (\n" + ",\n".join(cols_def) + "\n);")
