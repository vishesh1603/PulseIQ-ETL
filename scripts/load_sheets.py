from pathlib import Path
import pandas as pd

FILE_ID = "1pncXUdkKBURmt15HDHMuFBMveTKI8mrI"
URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"

# Resolve the folder from this file's location, so it works from any terminal directory
RAW_DIR = Path(__file__).resolve().parents[1] / "data"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# sheets = pd.read_excel(URL, sheet_name=None, dtype=str, header=None)

# for name, df in sheets.items():
#     df.to_csv(RAW_DIR / f"{name}.csv", index=False, header=False, encoding="utf-8")
#     print(f"{name:32s} {df.shape[0]:>6} rows x {df.shape[1]:>3} cols")

# print(f"\nSaved {len(sheets)} files to {RAW_DIR}")

import urllib.request
urllib.request.urlretrieve(URL, RAW_DIR / "PulseIQ_Star_Schema_Dataset.xlsx")