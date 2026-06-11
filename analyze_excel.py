import json, sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd

excel_path = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'

# Read all sheets
xls = pd.ExcelFile(excel_path)
print(f"Sheet names: {xls.sheet_names}")

# Sheet 1: 稽核明细-汇总
df_audit = pd.read_excel(excel_path, sheet_name='稽核明细-汇总')
print(f"\n=== 稽核明细-汇总 ===")
print(f"Shape: {df_audit.shape}")
print(f"Columns: {list(df_audit.columns)}")
print(f"\nFirst 3 rows:")
print(df_audit.head(3).to_string())

print(f"\nUnique 战区清洗(战区): {df_audit['战区清洗(战区)'].unique().tolist()}")
print(f"Unique 省区清洗-按最新(省区): {df_audit['省区清洗-按最新(省区)'].unique().tolist()}")
print(f"Unique 稽核月份: {sorted(df_audit['稽核月份'].unique().tolist())}")
print(f"Unique 稽核结果: {df_audit['稽核结果'].unique().tolist()}")
print(f"Unique 是否为稽核目标: {df_audit['是否为稽核目标'].unique().tolist()}")

# Sheet 2: 计划明细-汇总
df_plan = pd.read_excel(excel_path, sheet_name='计划明细-汇总')
print(f"\n=== 计划明细-汇总 ===")
print(f"Shape: {df_plan.shape}")
print(f"Columns: {list(df_plan.columns)}")
print(f"\nFirst 3 rows:")
print(df_plan.head(3).to_string())
print(f"\nUnique 月份: {sorted(df_plan['月份'].unique().tolist())}")

# Sheet 3: 各战区稽核进汇总
df_summary = pd.read_excel(excel_path, sheet_name='各战区稽核进汇总')
print(f"\n=== 各战区稽核进汇总 ===")
print(f"Shape: {df_summary.shape}")
print(f"Columns: {list(df_summary.columns)}")
print(f"\nAll rows:")
print(df_summary.to_string())
