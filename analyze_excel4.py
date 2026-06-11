import json, sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd

excel_path = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'

df_audit = pd.read_excel(excel_path, sheet_name='稽核明细-汇总')
df_plan = pd.read_excel(excel_path, sheet_name='计划明细-汇总')

# Zone-province mapping from audit data
print("=== Zone-Province mapping (稽核明细) ===")
zone_prov = df_audit.groupby('战区清洗')['省区清洗-按最新'].unique()
for zone, provs in zone_prov.items():
    print(f"  {zone}: {sorted(provs.tolist())}")

# Zone-province mapping from plan data
print("\n=== Zone-Province mapping (计划明细) ===")
zone_prov2 = df_plan.groupby('战区清洗')['省区清洗-按最新'].unique()
for zone, provs in zone_prov2.items():
    print(f"  {zone}: {sorted(provs.tolist())}")

# Verify against original ZD (from 1月 data)
# 区域经营部: 浙江, 湖南, 苏南, 广西, 陕甘青宁新
# 山东战区: 山东
# 华北战区: 河北, 北京, 天津
# 华南战区: 广东, 贵州, 福建
# 东北战区: 辽宁, 黑龙江, 内蒙古, 吉林
# 华中战区: 山西

# But Excel shows 华中战区 has more provinces. Let's check 6月 audit data:
print("\n=== 6月 Audit Zone-Province ===")
df_6 = df_audit[df_audit['稽核月份'] == '6月']
zone_prov6 = df_6.groupby('战区清洗')['省区清洗-按最新'].unique()
for zone, provs in zone_prov6.items():
    print(f"  {zone}: {sorted(provs.tolist())}")

# In original ZD 6月:
# 区域经营部: 苏南, 湖南, 浙江, 河南, 北京, 广西, 陕甘青宁新
# 华中战区: 山西, 湖北, 安徽, 河南, 云南, 川渝藏, 江西
# 华北战区: 河北, 天津, 北京 (北京 appears in BOTH 区域经营部 and 华北?)

# Wait - looking at the original ZD more carefully, the provinces listed in reg_detail 
# are the ones that have data for that specific month/zone combo.
# The mapping from data is:
# The 战区清洗 column already tells us which zone each province belongs to

# But in original ZD, some provinces appear under different zones in different months
# Let's check 河南:
print("\n=== 河南 in audit data ===")
df_henan = df_audit[df_audit['省区清洗-按最新'] == '河南']
print(df_henan[['稽核月份', '战区清洗']].value_counts().sort_index())

# Check 北京 in different months
print("\n=== 北京 in audit data ===")
df_bj = df_audit[df_audit['省区清洗-按最新'] == '北京']
print(df_bj[['稽核月份', '战区清洗']].value_counts().sort_index())

# The province mapping changes per month! That means the zone is attached to each record, 
# not a fixed mapping. The ZD's reg_detail per zone should just filter by 战区清洗 for that month.

# Let me verify plan data for each zone+month
print("\n=== 计划 counts by zone+month ===")
plan_counts = df_plan.groupby(['战区清洗', '月份']).size().unstack(fill_value=0)
print(plan_counts.to_string())

# Now compare to original ZD month_rows for 全部 (which sums across zones)
print("\n=== 计划 total per month ===")
for m in ['1月','2月','3月','4月','5月','6月']:
    cnt = len(df_plan[df_plan['月份'] == m])
    print(f"  {m}: {cnt}")
# ZD month_rows: 1月 p=1805, 2月 p=1551, 3月 p=1935, 4月 p=2190, 5月 p=2394, 6月 p=2084
# These match! ✓

# Check 稽核 target (是否为稽核目标)
print("\n=== 计划 是否为稽核目标 by month ===")
for m in ['1月','2月','3月','4月','5月','6月']:
    dm = df_plan[df_plan['月份'] == m]
    yes = (dm['是否为稽核目标'] == '是').sum()
    no = (dm['是否为稽核目标'] == '否').sum()
    print(f"  {m}: 是={yes}, 否={no}")

# Compare to ZD 1月/全部 target_items: 是=1710, 否=95
# Check 1月:
dm1 = df_plan[df_plan['月份'] == '1月']
yes1 = (dm1['是否为稽核目标'] == '是').sum()
no1 = (dm1['是否为稽核目标'] == '否').sum()
print(f"\n1月 plan target: 是={yes1}, 否={no1}")
# ZD says 是=1710, 否=95
# 1710+95 = 1805, yes1+no1 should = 1805
print(f"Total: {yes1+no1}")

# Check 核查日期 column for trend_points (daily data)
print("\n=== 核查日期 unique for 1月 ===")
df_1 = df_audit[df_audit['稽核月份'] == '1月']
dates = df_1['核查日期'].dropna()
print(f"Non-null dates: {len(dates)}")
print(f"Sample dates: {dates.head(10).tolist()}")
