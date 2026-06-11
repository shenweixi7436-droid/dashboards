import json, sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd

excel_path = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'

with open(r'C:\Users\shenw\github-dashboards\zd_original.json', 'r', encoding='utf-8') as f:
    zd = json.load(f)

# Check trend_points for monthly views (daily data)
print("=== ZD 1月/全部 trend_points ===")
tp1 = zd['1月']['全部']['trend_points']
print(f"Length: {len(tp1)}")
print(f"First: {tp1[:5]}")
print(f"Last: {tp1[-5:]}")
print(f"Title: {zd['1月']['全部']['trend_title']}")

print("\n=== ZD 全年/全部 trend_points ===")
tp_all = zd['全年']['全部']['trend_points']
print(f"Length: {len(tp_all)}")
print(f"Data: {tp_all}")
print(f"Title: {zd['全年']['全部']['trend_title']}")

# Check trend_points for zone-specific views
print("\n=== ZD 1月/区域经营部 trend_points ===")
tp_zone = zd['1月']['区域经营部']['trend_points']
print(f"Length: {len(tp_zone)}")
print(f"First: {tp_zone[:5]}")
print(f"Title: {zd['1月']['区域经营部']['trend_title']}")

# Check audit_details and issue_details for a zone
print("\n=== ZD 1月/全部 audit_details count ===")
print(f"Count: {len(zd['1月']['全部']['audit_details'])}")
print(f"First 3: {zd['1月']['全部']['audit_details'][:3]}")
print(f"Last 3: {zd['1月']['全部']['audit_details'][-3:]}")

print("\n=== ZD 1月/全部 issue_details count ===")
print(f"Count: {len(zd['1月']['全部']['issue_details'])}")
print(f"First 3: {zd['1月']['全部']['issue_details'][:3]}")

print("\n=== ZD 1月/全部 issue_rank ===")
print(zd['1月']['全部']['issue_rank'])

# For 全年, audit_details are ALL audits across all months
print("\n=== ZD 全年/全部 audit_details count ===")
print(f"Count: {len(zd['全年']['全部']['audit_details'])}")
print(f"First 3: {zd['全年']['全部']['audit_details'][:3]}")

# Check kpi_huanbi for 2月
print("\n=== ZD 2月/全部 kpi_huanbi ===")
print(zd['2月']['全部']['kpi_huanbi'])
# Should be环比 1月: 
# plan: (1551-1805)/1805 = -14.1%
# audit: (103-232)/232 = -55.6%
# anomalous: (7-2)/2 = 250%? No... 
# ZD kpi_huanbi = [环比计划, 环比稽核, 环比异常, 环比合格率]

# Let me compute: 
# plan huanbi: (1551-1805)/1805*100 = -14.1% → -14.1
# audit huanbi: (103-232)/232*100 = -55.6% → -55.6
# anomaly huanbi: (7-2)/2*100 = 250 → but ZD says ?
print(f"2月 huanbi plan: {round((1551-1805)/1805*100,1)}")
print(f"2月 huanbi audit: {round((103-232)/232*100,1)}")
print(f"2月 huanbi anomaly: {round((7-2)/2*100,1)}")
print(f"2月 huanbi rate: {round((96/103 - 230/232)*100,1)}")

# Check ZD:
hb2 = zd['2月']['全部']['kpi_huanbi']
print(f"ZD 2月 huanbi: {hb2}")

# Check ZD 3月 huanbi
hb3 = zd['3月']['全部']['kpi_huanbi']
print(f"ZD 3月 huanbi: {hb3}")
print(f"Computed: plan={round((1935-1551)/1551*100,1)}, audit={round((298-103)/103*100,1)}, anomaly={round((77-7)/7*100,1)}, rate={round((221/298-96/103)*100,1)}")

# Check how huanbi is displayed (up/down) in the original ZD
# For reg_detail, huanbi is per-province month-over-month
# Let's check 2月/全部 reg_detail for 浙江:
print("\n=== ZD 2月/全部 reg_detail 浙江 ===")
for r in zd['2月']['全部']['reg_detail']:
    if r['name'] == '浙江':
        print(r)
        break
