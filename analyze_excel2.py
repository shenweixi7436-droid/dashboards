import json, sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd

excel_path = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'

# Sheet 1: 稽核明细-汇总
df_audit = pd.read_excel(excel_path, sheet_name='稽核明细-汇总')
print(f"=== 稽核明细-汇总 ===")
print(f"Shape: {df_audit.shape}")
cols = list(df_audit.columns)
for i, c in enumerate(cols):
    print(f"  [{i}] {c}")

print(f"\nUnique 战区清洗: {df_audit['战区清洗'].unique().tolist()}")
print(f"Unique 省区清洗-按最新: {df_audit['省区清洗-按最新'].unique().tolist()}")
print(f"Unique 稽核月份: {sorted(df_audit['稽核月份'].unique().tolist())}")
print(f"Unique 稽核结果: {df_audit['稽核结果'].unique().tolist()}")

# Check if there's a '是否为稽核目标' column
has_target = [c for c in cols if '目标' in str(c)]
print(f"\nColumns with '目标': {has_target}")
has_finally = [c for c in cols if '最终' in str(c)]
print(f"Columns with '最终': {has_finally}")

# Sheet 2: 计划明细-汇总
df_plan = pd.read_excel(excel_path, sheet_name='计划明细-汇总')
print(f"\n=== 计划明细-汇总 ===")
print(f"Shape: {df_plan.shape}")
cols2 = list(df_plan.columns)
for i, c in enumerate(cols2):
    print(f"  [{i}] {c}")
print(f"\nUnique 月份: {sorted(df_plan['月份'].unique().tolist())}")

has_target2 = [c for c in cols2 if '目标' in str(c)]
print(f"Columns with '目标': {has_target2}")

# Sheet 3: 各战区稽核进汇总
df_summary = pd.read_excel(excel_path, sheet_name='各战区稽核进汇总')
print(f"\n=== 各战区稽核进汇总 ===")
print(f"Shape: {df_summary.shape}")
cols3 = list(df_summary.columns)
for i, c in enumerate(cols3):
    print(f"  [{i}] {c}")
print(f"\nAll data:")
print(df_summary.head(10).to_string())

# Check all unique values
print(f"\nUnique 战区: {df_summary['战区'].unique().tolist()}")
print(f"Unique 月份: {df_summary['月份'].unique().tolist()}")
