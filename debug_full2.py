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

df_audit['省份'] = df_audit['省区清洗-按最新'].map(lambda x: PROV_MERGE.get(x, x) if pd.notna(x) else x)
df_audit['战区'] = df_audit['省份'].map(ZONE_MAP)

# 简化预计算
cache = {}

# 战区级
for m in MONTHS:
    a_sub = df_audit[df_audit['稽核月份'] == m]
    p_sub = df_plan[df_plan['月份'] == m]
    
    # 省区级稽核
    audit_prov_m = {}
    for prov, grp in a_sub.groupby('省份'):
        audit_prov_m[prov] = {
            'audit': len(grp), 'qual': int((grp['稽核结果'].fillna('待定') == '合格').sum()),
            'unqual': int((grp['稽核结果'].fillna('待定') == '不合格').sum()),
            'fake': int((grp['稽核结果'].fillna('待定') == '虚假').sum()),
        }
    
    # 省区级计划
    plan_prov_m = {}
    for prov, grp in p_sub.groupby('省区清洗-按最新'):
        plan_prov_m[prov] = {
            'plan': len(grp), 'invest': int((grp['是否为稽核目标'] == '是').sum()),
        }
    
    # 战区级汇总
    for zone in ZONES + ['全部']:
        provinces = ZONE_PROVINCES[zone] if zone != '全部' else list(ZONE_MAP.keys())
        plan_t = 0; invest_t = 0; audit_t = 0; qual_t = 0; unqual_t = 0; fake_t = 0
        for prov in provinces:
            ps = plan_prov_m.get(prov, {'plan': 0, 'invest': 0})
            plan_t += ps['plan']; invest_t += ps['invest']
            a_s = audit_prov_m.get(prov, {'audit': 0, 'qual': 0, 'unqual': 0, 'fake': 0})
            audit_t += a_s['audit']; qual_t += a_s['qual']
            unqual_t += a_s['unqual']; fake_t += a_s['fake']
        anomaly = unqual_t + fake_t
        rate = round(qual_t / audit_t * 100, 1) if audit_t > 0 else 0.0
        cache[(m, zone)] = {
            'plan': plan_t, 'invest': invest_t, 'audit': audit_t,
            'qual': qual_t, 'unqual': unqual_t, 'fake': fake_t,
            'anomaly': anomaly, 'rate': rate,
        }
    
    # 省区级缓存 (用标准化后的省份名)
    for prov, grp in a_sub.groupby('省份'):
        audit_prov_m[prov] = {
            'audit': len(grp), 'qual': int((grp['稽核结果'].fillna('待定') == '合格').sum()),
            'unqual': int((grp['稽核结果'].fillna('待定') == '不合格').sum()),
            'fake': int((grp['稽核结果'].fillna('待定') == '虚假').sum()),
        }
    for prov in list(ZONE_MAP.keys()):
        p_data = plan_prov_m.get(prov, {'plan': 0, 'invest': 0})
        a_data = audit_prov_m.get(prov, {'audit': 0, 'qual': 0, 'unqual': 0, 'fake': 0})
        a = a_data['audit']
        rate = round(a_data['qual'] / a * 100, 1) if a > 0 else 0.0
        cache[('prov', m, prov)] = {
            'plan': p_data['plan'], 'invest': p_data['invest'],
            'audit': a, 'qual': a_data['qual'], 'unqual': a_data['unqual'],
            'fake': a_data['fake'], 'rate': rate,
        }

# 全年zone summary测试
zone_name = '全部'
provinces = list(ZONE_MAP.keys())
ps = [cache.get((m, zone_name), cache.get((m, '全部'), {})) for m in MONTHS]
print("各月数据:")
for i, m in enumerate(MONTHS):
    s = ps[i]
    print(f"  {m}: plan={s.get('plan',0)}, audit={s.get('audit',0)}, qual={s.get('qual',0)}")

zs = {
    'plan': sum(s.get('plan', 0) for s in ps),
    'audit': sum(s.get('audit', 0) for s in ps),
    'qual': sum(s.get('qual', 0) for s in ps),
    'unqual': sum(s.get('unqual', 0) for s in ps),
    'fake': sum(s.get('fake', 0) for s in ps),
}
zs['anomaly'] = zs['unqual'] + zs['fake']
zs['rate'] = round(zs['qual'] / zs['audit'] * 100, 1) if zs['audit'] > 0 else 0.0
print(f"\n全年汇总: {zs}")

# top5
prov_list = []
for prov in provinces:
    ps_sum = {'audit': 0, 'qual': 0}
    for mm in MONTHS:
        ps_m = cache.get(('prov', mm, prov), {})
        ps_sum['audit'] += ps_m.get('audit', 0)
        ps_sum['qual'] += ps_m.get('qual', 0)
    if ps_sum['audit'] > 0:
        prov_list.append({'n': prov, 'v': ps_sum['audit']})
prov_list.sort(key=lambda x: x['v'], reverse=True)
print(f"\ntop5: {prov_list[:5]}")
