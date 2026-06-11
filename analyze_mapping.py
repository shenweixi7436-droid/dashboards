import json, sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd

excel_path = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'

# Load original ZD
with open(r'C:\Users\shenw\github-dashboards\zd_original.json', 'r', encoding='utf-8') as f:
    zd_original = json.load(f)

# For each zone in original ZD, compare province list with Excel's 战区清洗 column
for month_name in ['1月', '6月']:
    print(f"\n=== {month_name} ===")
    zd_month = zd_original[month_name]
    
    # Collect all provinces in Excel audit for this month, grouped by zone
    df_audit = pd.read_excel(excel_path, sheet_name='稽核明细-汇总')
    df_m = df_audit[df_audit['稽核月份'] == month_name]
    
    excel_zones = df_m.groupby('战区清洗')['省区清洗-按最新'].apply(lambda x: sorted(set(x.tolist())))
    print(f"Excel audit provinces by zone:")
    for z, ps in excel_zones.items():
        print(f"  {z}: {ps}")
    
    print(f"\nZD provinces by zone:")
    for zone_name, zone_data in zd_month.items():
        if zone_name != '全部' and 'reg_detail' in zone_data:
            provs = [r['name'] for r in zone_data['reg_detail']]
            print(f"  {zone_name}: {provs}")
    
    # Find discrepancies
    print(f"\nDiscrepancies:")
    for zone_name, zone_data in zd_month.items():
        if zone_name == '全部':
            continue
        zd_provs = set(r['name'] for r in zone_data.get('reg_detail', []))
        excel_provs = set()
        if zone_name in excel_zones.index:
            excel_provs = set(excel_zones[zone_name])
        
        only_zd = zd_provs - excel_provs
        only_excel = excel_provs - zd_provs
        
        if only_zd or only_excel:
            print(f"  {zone_name}: only in ZD: {only_zd}, only in Excel: {only_excel}")

# Check the province_progress data for "全年" - this should give us the definitive mapping
print("\n=== 全年 province_progress mapping ===")
pp = zd_original['全年']['全部']['province_progress']
zone_from_pp = {}
for item in pp:
    prov = item['name']
    zone = item['zone']
    if prov not in zone_from_pp:
        zone_from_pp[prov] = zone
    elif zone_from_pp[prov] != zone:
        print(f"  CONFLICT: {prov} → {zone_from_pp[prov]} vs {zone}")
    zone_from_pp[prov] = zone

print("\nFinal province-zone mapping:")
for prov in sorted(zone_from_pp.keys()):
    print(f"  {prov} → {zone_from_pp[prov]}")
