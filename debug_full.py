import sys, json, warnings
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd, numpy as np

EXCEL_AUDIT = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'
df_audit = pd.read_excel(EXCEL_AUDIT, sheet_name='稽核明细-汇总')
df_plan = pd.read_excel(EXCEL_AUDIT, sheet_name='计划明细-汇总')

PROV_MERGE = {
    '宁夏': '陕甘青宁新', '陕西': '陕甘青宁新', '甘肃': '陕甘青宁新',
    '青海': '陕甘青宁新', '新疆': '陕甘青宁新',
    '四川': '川渝藏', '重庆': '川渝藏', '西藏': '川渝藏',
    '苏北': '苏北', '苏南': '苏南',
}

ZONE_MAP = {
    '云南': '区域经营部', '川渝藏': '区域经营部', '广西': '区域经营部',
    '浙江': '区域经营部', '湖南': '区域经营部', '苏北': '区域经营部',
    '苏南': '区域经营部', '陕甘青宁新': '区域经营部', '宁夏': '区域经营部',
    '陕西': '区域经营部', '甘肃': '区域经营部', '青海': '区域经营部', '新疆': '区域经营部',
    '四川': '区域经营部', '重庆': '区域经营部', '西藏': '区域经营部',
    '山东': '山东战区',
    '河北': '华北战区', '北京': '华北战区', '天津': '华北战区',
    '广东': '华南战区', '福建': '华南战区', '贵州': '华南战区',
    '内蒙古': '东北战区', '辽宁': '东北战区', '黑龙江': '东北战区', '吉林': '东北战区',
    '安徽': '华中战区', '山西': '华中战区', '河南': '华中战区', '湖北': '华中战区', '江西': '华中战区',
}
ZONES = ['区域经营部', '山东战区', '华北战区', '华南战区', '东北战区', '华中战区']
MONTHS = ['1月', '2月', '3月', '4月', '5月', '6月']

ZONE_PROVINCES = defaultdict(list)
for p, z in sorted(ZONE_MAP.items()):
    if p not in ZONE_PROVINCES[z]:
        ZONE_PROVINCES[z].append(p)

# 模拟 build_zone_data_cached 的全年逻辑
zone_name = '全部'
provinces = list(ZONE_MAP.keys())

# 模拟预计算
from generate_v2 import precompute_all
cache = precompute_all(df_audit, df_plan)

# 全年zone summary
ps = [cache.get((m, zone_name), cache.get((m, '全部'), {})) for m in MONTHS]
print("全年/全部 各月数据:")
for i, m in enumerate(MONTHS):
    s = ps[i]
    print(f"  {m}: plan={s.get('plan',0)}, invest={s.get('invest',0)}, audit={s.get('audit',0)}, qual={s.get('qual',0)}")

zs = {
    'plan': sum(s.get('plan', 0) for s in ps),
    'invest': sum(s.get('invest', 0) for s in ps),
    'audit': sum(s.get('audit', 0) for s in ps),
    'qual': sum(s.get('qual', 0) for s in ps),
    'unqual': sum(s.get('unqual', 0) for s in ps),
    'fake': sum(s.get('fake', 0) for s in ps),
}
zs['anomaly'] = zs['unqual'] + zs['fake']
zs['rate'] = round(zs['qual'] / zs['audit'] * 100, 1) if zs['audit'] > 0 else 0.0
print(f"\n全年汇总 zs: {zs}")

# top5
prov_list = []
for prov in provinces:
    ps_sum = {'audit': 0, 'qual': 0, 'unqual': 0, 'fake': 0}
    for mm in MONTHS:
        ps_m = cache.get(('prov', mm, prov), {})
        for k in ps_sum:
            ps_sum[k] += ps_m.get(k, 0)
    if ps_sum['audit'] > 0:
        prov_list.append({'n': prov, 'v': ps_sum['audit']})
print(f"\ntop5 prov_list 长度: {len(prov_list)}")
print(f"top5: {sorted(prov_list, key=lambda x:x['v'], reverse=True)[:5]}")
