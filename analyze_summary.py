import json, sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd

excel_path = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'

with open(r'C:\Users\shenw\github-dashboards\zd_original.json', 'r', encoding='utf-8') as f:
    zd = json.load(f)

df_summary = pd.read_excel(excel_path, sheet_name='各战区稽核进汇总')
df_audit = pd.read_excel(excel_path, sheet_name='稽核明细-汇总')
df_plan = pd.read_excel(excel_path, sheet_name='计划明细-汇总')

# Province-zone mapping
prov_merge = {
    '宁夏': '陕甘青宁新', '陕西': '陕甘青宁新', '甘肃': '陕甘青宁新',
    '青海': '陕甘青宁新', '新疆': '陕甘青宁新',
    '四川': '川渝藏', '重庆': '川渝藏', '西藏': '川渝藏',
}
df_audit['省份'] = df_audit['省区清洗-按最新'].map(lambda x: prov_merge.get(x, x))

zone_map_plan = {
    '云南': '区域经营部', '川渝藏': '区域经营部', '广西': '区域经营部',
    '浙江': '区域经营部', '湖南': '区域经营部', '苏北': '区域经营部',
    '苏南': '区域经营部', '陕甘青宁新': '区域经营部',
    '山东': '山东战区',
    '河北': '华北战区', '北京': '华北战区', '天津': '华北战区',
    '广东': '华南战区', '福建': '华南战区', '贵州': '华南战区',
    '内蒙古': '东北战区', '辽宁': '东北战区', '黑龙江': '东北战区', '吉林': '东北战区',
    '安徽': '华中战区', '山西': '华中战区', '河南': '华中战区', '湖北': '华中战区', '江西': '华中战区',
}

# Use summary sheet for zone-level data
# Filter out 年度合计 rows
zones = ['东北战区', '山东战区', '华北战区', '华中战区', '华南战区', '区域经营部']
df_summary_zones = df_summary[df_summary['战区'].isin(zones)]

# Build zone+month lookup from summary
summary_lookup = {}
for _, row in df_summary_zones.iterrows():
    key = (row['战区'], row['月份'])
    summary_lookup[key] = row.to_dict()

# Check ZD progress for a few zone+month combos
print("=== ZD vs Summary for progress_items ===")
for month in ['1月', '6月']:
    print(f"\n--- {month} ---")
    for zone in zones:
        zd_data = zd[month].get(zone, {})
        prog = zd_data.get('progress_current', {})
        if prog:
            skey = (zone, month)
            srow = summary_lookup.get(skey, {})
            s_invest = srow.get('投入费用门店数', '?')
            s_audit = srow.get('稽核数', '?')
            s_rate = srow.get('稽核完成率', '?')
            print(f"  {zone}: ZD pct={prog.get('pct')}, plan_q={prog.get('plan_q')}, audit={prog.get('audit_cnt')} | Summary invest={s_invest}, audit={s_audit}, rate={s_rate}")

# Now let me understand the 全部/progress_items for each month
# In ZD, 全部/progress_items shows all 6 months
# This seems to come from the 年度合计 rows in summary
print("\n=== 年度合计 rows ===")
annual = df_summary[df_summary['战区'] == '年度合计']
print(annual[['月份', '稽核数', '合格数', '不合格数', '虚假数', '陈列计划数', '投入费用门店数', '稽核完成率']].to_string())

# Verify against ZD 1月/全部:
# ZD: pct=67.8, plan_q=1710, audit_cnt=232, display_plan=1805
# Summary 年度合计 1月: 稽核数=232, 陈列计划数=1805, 投入费用门店数=1710, 稽核完成率=0.678363
# 0.678363 * 100 = 67.8 ✓
# So progress_items use 年度合计 row data!

# For 全年:
print("\n=== ZD 全年/全部 progress_current ===")
print(zd['全年']['全部']['progress_current'])
# And check 年度合计 全年合计:
annual_all = df_summary[(df_summary['战区'] == '年度合计') & (df_summary['月份'] == '全年合计')]
print(annual_all.to_string())
