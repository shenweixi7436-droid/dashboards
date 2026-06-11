import json, sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd

excel_path = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'

with open(r'C:\Users\shenw\github-dashboards\zd_original.json', 'r', encoding='utf-8') as f:
    zd = json.load(f)

df_audit = pd.read_excel(excel_path, sheet_name='稽核明细-汇总')

# Check 1月 trend_points (daily data from 核查日期)
dm1 = df_audit[df_audit['稽核月份'] == '1月']
dates = dm1['核查日期'].dropna()
print(f"1月 audit count: {len(dm1)}")
print(f"1月 dates with 核查日期: {len(dates)}")

# Daily distribution
dm1['day'] = pd.to_datetime(dm1['核查日期']).dt.day
daily = dm1.groupby('day').size()
print(f"\n1月 daily audit counts:")
for d in range(1, 32):
    cnt = daily.get(d, 0)
    if cnt > 0:
        print(f"  {d}日: {cnt}")

# Check ZD 1月/全部 trend_points
tp1 = zd['1月']['全部']['trend_points']
nonzero = [p for p in tp1 if p['value'] > 0]
print(f"\nZD 1月 trend_points with value > 0: {len(nonzero)}")
for p in nonzero[:10]:
    print(f"  {p}")

# Check a later month where data might be populated
tp6 = zd['6月']['全部']['trend_points']
nonzero6 = [p for p in tp6 if p['value'] > 0]
print(f"\nZD 6月 trend_points with value > 0: {len(nonzero6)}")
for p in nonzero6[:20]:
    print(f"  {p}")

# Check 核查日期 for 6月
dm6 = df_audit[df_audit['稽核月份'] == '6月']
dm6_dates = dm6['核查日期'].dropna()
print(f"\n6月 audit count: {len(dm6)}")
print(f"6月 dates: {len(dm6_dates)}")

dm6['day'] = pd.to_datetime(dm6['核查日期']).dt.day
daily6 = dm6.groupby('day').size()
print(f"6月 daily counts:")
for d in sorted(daily6.index):
    print(f"  {d}日: {daily6[d]}")

# Now I understand: the trend data in ZD might be computed differently
# The ZD trend_points for 1月/全部 are all 0s which is odd since there ARE audits in 1月
# Maybe the trend_points are the BLANK/SKELETON values and the JS fills them in?
# Or maybe they are filled from a different data source?

# Let me check the JS to understand how trend_points are used
print("\n=== Checking HTML for trend_points usage ===")
with open(r'C:\Users\shenw\Documents\New project\市场稽核部重点工作看板-06101350.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find trend_points references
import re
matches = re.findall(r'trend_points.{0,100}', html)
for m in matches[:20]:
    print(f"  {m}")

# Check huanbi calculation for reg_detail
# ZD 2月/全部 浙江 huanbi=0, but 1月 浙江 had audit=32, 2月=11
# huanbi should be (11-32)/32*100 = -65.6, but ZD says 0
# Maybe huanbi=0 for 1月 (no prior month) and this is zone-specific?
print("\n=== ZD 1月/全部 浙江 ===")
for r in zd['1月']['全部']['reg_detail']:
    if r['name'] == '浙江':
        print(r)
        break

# For ZD 3月 浙江 huanbi:
print("\n=== ZD 3月/全部 浙江 ===")
for r in zd['3月']['全部']['reg_detail']:
    if r['name'] == '浙江':
        print(r)
        break

# Check issue_rank format
print("\n=== ZD 6月/全部 issue_rank ===")
print(zd['6月']['全部']['issue_rank'])

# province_progress format  
print("\n=== ZD 1月/全部 province_progress ===")
print(zd['1月']['全部']['province_progress'][:5])
