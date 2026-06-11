import json, sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd

excel_path = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'

with open(r'C:\Users\shenw\github-dashboards\zd_original.json', 'r', encoding='utf-8') as f:
    zd = json.load(f)

# Understand reg_detail for 全部/1月
print("=== ZD 全部/1月 reg_detail ===")
for r in zd['1月']['全部']['reg_detail']:
    print(f"  {r}")

# Now compute from Excel for 1月/全部
df_audit = pd.read_excel(excel_path, sheet_name='稽核明细-汇总')
df_plan = pd.read_excel(excel_path, sheet_name='计划明细-汇总')

# Province-zone mapping from plan data (definitive)
zone_map = {
    '云南': '区域经营部', '川渝藏': '区域经营部', '广西': '区域经营部',
    '浙江': '区域经营部', '湖南': '区域经营部', '苏北': '区域经营部',
    '苏南': '区域经营部', '陕甘青宁新': '区域经营部',
    '山东': '山东战区',
    '河北': '华北战区', '北京': '华北战区', '天津': '华北战区',
    '广东': '华南战区', '福建': '华南战区', '贵州': '华南战区',
    '内蒙古': '东北战区', '辽宁': '东北战区', '黑龙江': '东北战区', '吉林': '东北战区',
    '安徽': '华中战区', '山西': '华中战区', '河南': '华中战区', '湖北': '华中战区', '江西': '华中战区',
}

# Audit data province mapping (audit uses split names, map to plan's merged names)
prov_merge = {
    '宁夏': '陕甘青宁新', '陕西': '陕甘青宁新', '甘肃': '陕甘青宁新',
    '青海': '陕甘青宁新', '新疆': '陕甘青宁新',
    '四川': '川渝藏', '重庆': '川渝藏', '西藏': '川渝藏',
}

df_audit['省份'] = df_audit['省区清洗-按最新'].map(lambda x: prov_merge.get(x, x))

# For 1月, compute per-province stats for 全部
df_1 = df_audit[df_audit['稽核月份'] == '1月']
df_1_plan = df_plan[df_plan['月份'] == '1月']

print("\n=== Computed 1月/全部 per-province ===")
all_provinces = set(df_1['省份'].unique()) | set(df_1_plan['省区清洗-按最新'].unique())
for prov in sorted(all_provinces):
    audit_rows = df_1[df_1['省份'] == prov]
    plan_rows = df_1_plan[df_1_plan['省区清洗-按最新'] == prov]
    plan_cnt = len(plan_rows)
    audit_cnt = len(audit_rows)
    qual_cnt = (audit_rows['最终结果'] == '合格').sum()
    unqual_cnt = (audit_rows['最终结果'] == '不合格').sum()
    fake_cnt = (audit_rows['最终结果'] == '虚假').sum()
    rate = round(qual_cnt / audit_cnt * 100, 1) if audit_cnt > 0 else 0
    if audit_cnt > 0 or plan_cnt > 0:
        print(f"  {prov}: plan={plan_cnt}, audit={audit_cnt}, qual={qual_cnt}, unqual={unqual_cnt}, fake={fake_cnt}, rate={rate}")

# Now let's check ZD's progress_items calculation
print("\n=== ZD 1月/全部 progress_items ===")
for r in zd['1月']['全部']['progress_items']:
    print(f"  {r}")

# ZD says 1月 pct=67.8, plan_q=1710, audit_cnt=232, display_plan=1805
# pct = audit/target? 232/1710 = 13.6% NO
# pct = audit/plan? 232/1805 = 12.9% NO
# Wait... ZD progress is zone-specific. Let me look at 全部:
# For 全部, let me check: is pct = audit/target*100? 232/1710*100 = 13.6%
# But ZD says 67.8%
# 
# Let's check: is this using the summary sheet data?
# summary sheet for 1月: 稽核完成率 values:
# 东北: 0.925926, 山东: ?, 华北: ?, 华南: ?, 区域经营部: ?, 华中: ?

df_summary = pd.read_excel(excel_path, sheet_name='各战区稽核进汇总')
s_1 = df_summary[df_summary['月份'] == '1月']
print("\n=== Summary sheet 1月 ===")
print(s_1.to_string())

# Hmm, the ZD progress_current for 1月/全部 says pct=67.8
# Let me check if it's average of zone completion rates
# Or maybe it's using the 年度合计 row?
# Annual: 稽核完成率 = 0.737814 ≈ 73.8%

# Wait - let me re-examine. ZD's "全部" might not be sum of all zones.
# Let me look at the actual numbers:
# ZD 1月/全部: kpi_monthly=[1805, 232, 2, 99.1]
# plan=1805, audit=232, anomalous=2, rate=99.1
# That matches what I computed from raw data (232 audits, 230 qualified, 2 unqualified)

# But progress_items are different - they show per-month progress
# ZD 1月/全部: progress_items[0] = {m:"1月", pct:67.8, plan_q:1710, audit_cnt:232, display_plan:1805}
# 67.8% = ? 
# 232/342 = 67.8! Where does 342 come from?
# 342 = 投入费用门店数 for 1月? 
# From summary: all zones 1月 投入费用 = 108+108+173+173+173... no wait

# Let me look at the summary sheet more carefully
# 东北战区 1月: 陈列计划数=115, 投入费用门店数=108, 稽核完成率=0.925926
# Wait, but the summary has each zone listed twice? No...

# Actually wait - from earlier analysis, the summary sums to 464 for 1月 (double of 232)
# So the summary sheet data is problematic. 

# Let me try a different approach: 
# pct=67.8, audit=232
# 232/67.8 * 100 = 342.2 → so target=342?
# display_plan=1805 (total plans), plan_q=1710 (target plans = 是=稽核目标)
# progress_current shows: pct=28.2, plan_q=1845, audit_cnt=104, display_plan=2084
# 104/28.2 * 100 = 369 → doesn't match plan_q=1845

# Maybe pct = audit_cnt / plan_q * 100?
# 232/1710 * 100 = 13.6 NO
# 
# Hmm wait, the "progress" in the task says "progress = audit / target * 100"
# But that gives 232/1710=13.6%, not 67.8

# Let me re-read ZD's progress_current for 6月/全部:
print("\n=== ZD 6月/全部 progress_current ===")
print(zd['6月']['全部']['progress_current'])
# ZD says: pct=28.2, plan_q=1845, audit_cnt=104, display_plan=2084

# 104/1845*100 = 5.6% ≠ 28.2%
# But 104/369 * 100 = 28.2%
# Where does 369 come from?

# Hmm, maybe it's using the 各战区稽核进汇总 data?
# For 6月, the summary says 投入费用门店数=3690 for 年度合计, but 6月 for 区域经营部 is ?

# Wait - let me check if this is per-ZONE
# For 区域经营部 1月:
print("\n=== ZD 1月/区域经营部 progress ===")
for r in zd['1月']['区域经营部'].get('progress_items', [])[:1]:
    print(f"  {r}")
print("progress_current:", zd['1月']['区域经营部'].get('progress_current'))
