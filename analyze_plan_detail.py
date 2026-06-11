import json, sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd

excel_path = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'

with open(r'C:\Users\shenw\github-dashboards\zd_original.json', 'r', encoding='utf-8') as f:
    zd = json.load(f)

df_summary = pd.read_excel(excel_path, sheet_name='各战区稽核进汇总')

# The summary sheet has per-zone per-month data AND per-zone annual AND "年度合计" annual
# But the summary 稽核数 is DOUBLE the actual! Let's verify:
# Annual 合计: 稽核数=1438 ✓ (matches total audit rows)
# But 1月 合计: 稽核数=232 ✓ 
# And 1月 per zone sum: 20+14+20+0+68+110 = 232 ✓
# So per-zone sum = annual 合计 per month ✓
# The issue was earlier when I summed ALL zones for 1月 without filtering by 月份

# Wait, earlier the sum was 464 for 1月, but now I see 20+14+20+0+68+110=232
# Let me re-check...
print("=== Summary 1月 (all rows) ===")
s1 = df_summary[df_summary['月份'] == '1月']
print(s1[['战区', '稽核数']].to_string())
print(f"Sum: {s1['稽核数'].sum()}")

# Ah - I see! The summary has 91 rows - there are 13 months * 7 zones = 91 rows
# Each zone has entries for every month, including months with no data
# The rows I saw earlier (rows 0-9) were 东北战区 for all months
# The doubling was from different zone rows

# OK, so the summary sheet IS correct per zone. Let me verify a specific case:
# 东北战区 1月: 稽核数=20, 但 audit data shows 东北战区 1月 only has 内蒙古(2)+辽宁(10)+黑龙江(8)=20 ✓

# Now let me understand reg_detail.plan: where does it come from?
# For 1月/全部, 浙江 plan=171, but plan data shows 浙江 1月 has 233 rows
# That's because plan_q comes from 投入费用门店数 (是否为稽核目标=是 subset)
df_plan = pd.read_excel(excel_path, sheet_name='计划明细-汇总')
df_plan_1 = df_plan[df_plan['月份'] == '1月']

# 浙江 1月:
zj_plan = df_plan_1[df_plan_1['省区清洗-按最新'] == '浙江']
zj_target_yes = (zj_plan['是否为稽核目标'] == '是').sum()
zj_target_no = (zj_plan['是否为稽核目标'] == '否').sum()
print(f"\n浙江 1月: total={len(zj_plan)}, 是={zj_target_yes}, 否={zj_target_no}")
# ZD says plan=171 for 浙江
# But total plan rows = 233, 是 = ?
# Hmm, so plan is NOT total plan rows either

# Let me check summary sheet for 浙江 - but it doesn't have per-province data
# The summary only has per-zone data

# Maybe plan = 投入费用门店数 per province?
# Let me check: for 区域经营部 1月, 投入费用=626
# 区域经营部 provinces in plan: 浙江(233), 湖南(181), 苏南(202), 广西(58), 陕甘青宁新(15)
# 投入费用(是) for these:
total_invest = 0
for prov in ['浙江', '湖南', '苏南', '广西', '陕甘青宁新']:
    pp = df_plan_1[(df_plan_1['省区清洗-按最新'] == prov) & (df_plan_1['是否为稽核目标'] == '是')]
    cnt = len(pp)
    total_invest += cnt
    print(f"  {prov}: 投入费用={cnt}")

print(f"Total invest: {total_invest}")
# 区域经营部 1月 投入费用门店数 = 626 from summary
# So if total invest matches 626, then reg_detail.plan should use per-province invest

# Check ZD 浙江 plan=171 vs actual 是 for 浙江:
print(f"\n浙江 是 for 1月: {zj_target_yes}")
# If ZD says plan=171 but actual 是={zj_target_yes}, they need to match

# Actually, the plan data counts I see might be affected by the 苏北/苏南/陕甘青宁新 merge
# Let me also check if plan uses 陈列门店数量 instead of row count
zj_plan_display = zj_plan['陈列门店数量'].sum()
print(f"浙江 1月 陈列门店数量 sum: {zj_plan_display}")
