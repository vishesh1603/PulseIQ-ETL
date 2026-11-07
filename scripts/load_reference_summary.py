import psycopg
import pandas as pd

excel_path = r'data\raw\03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx'
df = pd.read_excel(excel_path, 'reference_summary_dept_month')

conn = psycopg.connect('dbname=pulseiq user=pulseiq password=pulseiq host=127.0.0.1 port=5433')
conn.autocommit = True
cur = conn.cursor()
cur.execute('TRUNCATE TABLE dw.reference_summary_dept_month CASCADE;')

cols = list(df.columns)
col_str = ', '.join(f'"{c}"' for c in cols)
placeholders = ', '.join(['%s'] * len(cols))
insert_sql = f'INSERT INTO dw.reference_summary_dept_month ({col_str}) VALUES ({placeholders});'

records = []
for row in df.itertuples(index=False, name=None):
    clean_row = tuple(None if pd.isna(x) else x for x in row)
    records.append(clean_row)

cur.executemany(insert_sql, records)
print(f'Inserted {len(records)} rows into dw.reference_summary_dept_month successfully!')
conn.close()
