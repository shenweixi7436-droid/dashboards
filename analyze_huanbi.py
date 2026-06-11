import json, sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd

excel_path = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'

with open(r'C:\Users\shenw\github-dashboards\zd_original.json', 'r', encoding='utf-8') as f:
    zd = json.load(f)

# Check huanbi for reg_detail across months for 浙江
for m in ['1月','2月','3月','4月','5月','6月']:
    for r in zd[m]['全部']['reg_detail']:
        if r['name'] == '浙江':
            print(f"{m} 浙江: audit={r['audit']}, rate={r['rate']}, huanbi={r['huanbi']}")
            break

# Also check 广东
print()
for m in ['1月','2月','3月','4月','5月','6月']:
    for r in zd[m]['全部']['reg_detail']:
        if r['name'] == '广东':
            print(f"{m} 广东: audit={r['audit']}, rate={r['rate']}, huanbi={r['huanbi']}")
            break

# And 全年
for r in zd['全年']['全部']['reg_detail']:
    if r['name'] in ['浙江', '广东', '贵州']:
        print(f"全年 {r['name']}: audit={r['audit']}, rate={r['rate']}, huanbi={r['huanbi']}")

# It seems huanbi=0 everywhere in reg_detail! This is a BLANK placeholder.
# The JS probably calculates huanbi dynamically. Let me check:
# 广东 1月 audit=26, 2月 would have different audit, so huanbi = (current-prior)/prior*100
# But if ZD has huanbi=0 for ALL entries, it means the ZD data doesn't include this computation

# Let me also check province_progress format - what are invest, target, audit?
print("\n=== province_progress detailed ===")
pp = zd['1月']['全部']['province_progress']
print(f"Count: {len(pp)}")
for item in pp:
    print(f"  {item}")

# And for 全年:
print("\n=== province_progress 全年 ===")
pp_all = zd['全年']['全部']['province_progress']
print(f"Count: {len(pp_all)}")
for item in pp_all[:5]:
    print(f"  {item}")

# Check issue_rank format more carefully
print("\n=== issue_rank detailed for 6月/全部 ===")
print(zd['6月']['全部']['issue_rank'])
# v = count of 不合格+虚假 for that province
# pct = v / total issues * 100

# Check issue_details for 6月/全部
print("\n=== issue_details 6月/全部 ===")
ids = zd['6月']['全部']['issue_details']
print(f"Count: {len(ids)}")
for item in ids[:5]:
    print(f"  {item}")

# Check issue_details format for 合格/不合格/虚假/有待改进/待定
# In the audit data, 最终结果 has: 合格, 不合格, 虚假
# issue_details should have 不合格+虚假 entries
# audit_details should have ALL entries (合格 + others)

# Let me verify 6月 issue_details count vs raw data
df_audit = pd.read_excel(excel_path, sheet_name='稽核明细-汇总')
dm6 = df_audit[df_audit['稽核月份'] == '6月']
issue_6 = dm6[dm6['最终结果'].isin(['不合格', '虚假'])]
print(f"\n6月 raw issues (不合格+虚假): {len(issue_6)}")
print(f"6月 ZD issue_details count: {len(ids)}")
