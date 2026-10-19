"""
Load additional dimensions and facts from PulseIQ_Star_Schema_Dataset.xlsx into Postgres schema dw.
Robustly handles types, NaNs, and integers.
"""
import pandas as pd
import psycopg
import numpy as np

EXCEL_PATH = r'c:\Users\DELL\Downloads\pulseiq-etl1\data\raw\PulseIQ_Star_Schema_Dataset.xlsx'
PG_CONN_STR = "postgresql://pulseiq:pulseiq@localhost:5433/pulseiq"

TABLES_TO_LOAD = [
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

def clean_val(v):
    if pd.isna(v) or v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, (pd.Timestamp, np.datetime64)):
        return v.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(v, (np.integer, int)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        # If it's a whole number, keep as float or int depending
        return float(v)
    return str(v).strip()

def load_sheet(conn, sheet_name):
    print(f"Reading sheet: {sheet_name}...")
    df = pd.read_excel(EXCEL_PATH, sheet_name)
    total_rows = len(df)
    
    table_name = f"dw.{sheet_name}"
    cols = list(df.columns)
    col_str = ", ".join(f'"{c}"' for c in cols)
    placeholders = ", ".join(["%s"] * len(cols))
    
    # Process records row by row
    records = []
    for row in df.itertuples(index=False, name=None):
        clean_row = tuple(clean_val(x) for x in row)
        records.append(clean_row)
        
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
        insert_query = f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders});"
        
        # Insert in chunks of 1000
        chunk_size = 1000
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            cur.executemany(insert_query, chunk)
        conn.commit()
        
    print(f"Loaded {total_rows} rows into {table_name} successfully.")

def main():
    print("Connecting to PostgreSQL at localhost:5433...")
    conn = psycopg.connect(PG_CONN_STR)
    for t in TABLES_TO_LOAD:
        load_sheet(conn, t)
    conn.close()
    print("All additional tables loaded successfully!")

if __name__ == '__main__':
    main()
