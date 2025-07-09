import os
import json
import pandas as pd

# Change working directory to the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Identify Excel file (first .xlsx in directory)
files = os.listdir(script_dir)
xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]
if not xlsx_files:
    raise FileNotFoundError(f"No .xlsx file found in {script_dir}")
excel_path = os.path.join(script_dir, xlsx_files[0])
print(f"Using Excel file: {xlsx_files[0]}")

# Read sheets into pandas DataFrames
xls = pd.ExcelFile(excel_path)
if 'Materials' not in xls.sheet_names or 'Composition' not in xls.sheet_names:
    raise ValueError("Workbook must contain 'Materials' and 'Composition' sheets.")
materials_df = xls.parse('Materials')
composition_df = xls.parse('Composition')

# Build composition mapping: material name -> composition string
composition_data = {}
for col in materials_df.columns:
    if col not in composition_df.columns:
        continue
    material_series = materials_df[col].astype(str).str.strip()
    comp_series = composition_df[col].astype(str).str.strip()
    for name, comp in zip(material_series, comp_series):
        if name and name.lower() != 'nan' and comp and comp.lower() != 'nan':
            composition_data[name] = comp

# Write JSON output
output_file = os.path.join(script_dir, 'compositionData.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(composition_data, f, ensure_ascii=False, indent=2)

print(f"Generated '{output_file}' with {len(composition_data)} material entries.")
