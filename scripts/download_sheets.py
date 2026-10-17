"""Download the workbook from Google Sheets into data/raw/ (needs 'Anyone with the link' access).

    python scripts/download_sheets.py

The pipeline reads the .xlsx directly, so no CSV conversion is needed.
"""
from pathlib import Path
import urllib.request

FILE_ID = "1pncXUdkKBURmt15HDHMuFBMveTKI8mrI"
URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

target = RAW_DIR / "PulseIQ_Star_Schema_Dataset.xlsx"
urllib.request.urlretrieve(URL, target)
print(f"Saved {target} ({target.stat().st_size // 1024} KB)")
