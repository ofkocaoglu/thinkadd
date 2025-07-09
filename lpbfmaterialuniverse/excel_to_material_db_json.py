import os
import json
import pandas as pd

# Change working directory to script's directory
tool_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(tool_dir)

# Identify the Excel archive file (first .xlsx)
files = os.listdir(tool_dir)
xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]
if not xlsx_files:
    raise FileNotFoundError(f"No .xlsx file found in {tool_dir}")
excel_file = xlsx_files[0]
print(f"Loading Excel file: {excel_file}")

# Read the first sheet into a DataFrame
df = pd.read_excel(excel_file, sheet_name=0, dtype=str)

# Drop entirely empty rows
df = df.dropna(how='all')

# Replace NaNs with None
df = df.where(pd.notnull(df), None)

# Build list of dictionaries (records)
records = df.to_dict(orient='records')

# Output JSON file
output_file = 'materialDatabase.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"Generated '{output_file}' with {len(records)} records.")
