import pandas as pd
excel_path = r'c:\Users\DELL\Downloads\pulseiq-etl1\data\raw\PulseIQ_Star_Schema_Dataset.xlsx'
df = pd.read_excel(excel_path, 'metric_dictionary')
for idx, r in df.iterrows():
    print(f"{r['metric_id']} | {r['metric_name']} | {r['source_table']} | {r['grain']} | {r['minimum_group_size']} | {r['formula']}")
