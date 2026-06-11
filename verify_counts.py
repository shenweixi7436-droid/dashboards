import json, sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd

excel_path = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'

with open(r'C:\Users\shenw\github-dashboards\zd_original.json', 'r', encoding='utf-8') as f:
    zd = json.load(f)

df_audit = pd.read_excel(excel_path, sheet_name='稽核明细-汇总')

# Count audits per month from raw data
print("=== Raw audit counts per month ===")
for m in ['1月','2月','3月','4月','5月','6月']:
    dm = df_audit[df_audit['稽核月份'] == m]
    qual = (dm['最终结果'] == '合格').sum()
    unqual = (dm['最终结果'] == '不合格').sum()
    fake = (dm['最终结果'] == '虚假').sum()
    print(f"  {m}: total={len(dm)}, 合格={qual}, 不合格={unqual}, 虚假={fake}")

# Summary says:
# 1月: 稽核=232, 合格=230, 不合格=2, 虚假=0
# 2月: 稽核=103, 合格=96, 不合格=7, 虚假=0
# But ZD month_rows says:
# 2月: p=1551, a=103, q=96, rs=93.2

# Let me check raw 2月:
dm2 = df_audit[df_audit['稽核月份'] == '2月']
print(f"\n2月 detail: total={len(dm2)}")
print(dm2['最终结果'].value_counts(dropna=False))

# ZD 2月 kpi_monthly=[1551, 103, 7, 93.2]
# 不合格+虚假 = 7, but raw has 不合格=7 虚假=0 → 7 ✓
# rate = 96/103 = 93.2% ✓

# Now check 3月:
dm3 = df_audit[df_audit['稽核月份'] == '3月']
print(f"\n3月 detail: total={len(dm3)}")
print(dm3['最终结果'].value_counts(dropna=False))
# ZD 3月: a=298, q=221, 不合格+虚假=75+2=77? But ZD says kpi_monthly[2]=?
# Let me check:
print("\nZD 3月/全部 kpi_monthly:", zd['3月']['全部']['kpi_monthly'])

# 4月:
dm4 = df_audit[df_audit['稽核月份'] == '4月']
print(f"\n4月 detail: total={len(dm4)}")
print(dm4['最终结果'].value_counts(dropna=False))
print("ZD 4月/全部 kpi_monthly:", zd['4月']['全部']['kpi_monthly'])

# 5月:
dm5 = df_audit[df_audit['稽核月份'] == '5月']
print(f"\n5月 detail: total={len(dm5)}")
print(dm5['最终结果'].value_counts(dropna=False))
print("ZD 5月/全部 kpi_monthly:", zd['5月']['全部']['kpi_monthly'])

# 6月:
dm6 = df_audit[df_audit['稽核月份'] == '6月']
print(f"\n6月 detail: total={len(dm6)}")
print(dm6['最终结果'].value_counts(dropna=False))
print("ZD 6月/全部 kpi_monthly:", zd['6月']['全部']['kpi_monthly'])

# Check per-zone 2月 raw data
print("\n=== 2月 per-zone raw ===")
for _, row in dm2.groupby('战区清洗'):
    zone_rows = dm2[dm2['战区清洗'] == _]
    qual = (zone_rows['最终结果'] == '合格').sum()
    unqual = (zone_rows['最终结果'] == '不合格').sum()
    print(f"  {_}: total={len(zone_rows)}, 合格={qual}, 不合格={unqual}")

# Summary says 2月: 东北=21, 山东=42, 华北=23, 华中=0, 华南=0, 区域经营部=17 = 103
# But raw data might differ
