# -*- coding: utf-8 -*-
"""
市场稽核部重点工作看板 - 数据生成脚本 v2(性能优化版)
从 Excel 数据源计算 ZD JSON 数据,嵌入原 HTML 模板生成完整看板。
"""

import json, math, re, sys, warnings
from datetime import datetime
from collections import defaultdict

import numpy as np
import pandas as pd

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)): return int(obj)
        if isinstance(obj, (np.floating,)): return float(obj)
        if isinstance(obj, (np.ndarray,)): return obj.tolist()
        return super().default(obj)

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

# ============ 路径配置 ============
EXCEL_AUDIT = 'C:\\Users\\shenw\\Desktop\\\u770b\u677f\\\u7a3d\u6838\u4e0e\u8ba1\u5212\u660e\u7ec6-2026\u5e74\u5e74\u5ea6.xlsx'
EXCEL_WORK = 'C:\\Users\\shenw\\Desktop\\\u770b\u677f\\\u5e02\u573a\u7a3d\u6838\u90e8\u91cd\u70b9\u5de5\u4f5c.xlsx'
PROJECT_DIR = r'C:\Users\shenw\Documents\New project\github-dashboards'
HTML_TEMPLATE_MAIN = PROJECT_DIR + r'\index.html'
HTML_TEMPLATE_DISP = PROJECT_DIR + r'\display-audit-dashboard.html'
OUTPUT_MAIN = PROJECT_DIR + r'\index.html'
OUTPUT_DISP = PROJECT_DIR + r'\display-audit-dashboard.html'

# 省区→战区映射
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
ZONE_PROVINCES = defaultdict(list)
for p, z in sorted(ZONE_MAP.items()):
    if p not in ZONE_PROVINCES[z]:
        ZONE_PROVINCES[z].append(p)
# 计划明细中的省区名称(可能和稽核明细不同)
PLAN_PROVINCES = sorted(ZONE_MAP.keys())

# 稽核明细中拆分省区→合并名称
PROV_MERGE = {
    '宁夏': '陕甘青宁新', '陕西': '陕甘青宁新', '甘肃': '陕甘青宁新',
    '青海': '陕甘青宁新', '新疆': '陕甘青宁新',
    '四川': '川渝藏', '重庆': '川渝藏', '西藏': '川渝藏',
    '苏北': '苏北', '苏南': '苏南',  # 计划明细中苏北属于山东战区,但稽核明细中按实际
}

MONTHS = ['1月', '2月', '3月', '4月', '5月', '6月']


def apply_data_cache_buster(html, build_tag):
    pattern = r'(assets/data/[^"\']+\.js)(\?v=[^"\']+)?'
    return re.sub(pattern, lambda m: m.group(1) + '?v=' + build_tag, html)


def load_data():
    print("加载 Excel 数据...")
    df_audit = pd.read_excel(EXCEL_AUDIT, sheet_name='稽核明细-汇总')
    df_plan = pd.read_excel(EXCEL_AUDIT, sheet_name='计划明细-汇总')

    # 推广促销稽核
    df_promo = pd.read_excel(EXCEL_WORK, sheet_name='推广促销稽核', header=2)
    # 线上审批流程稽核
    df_approval = pd.read_excel(EXCEL_WORK, sheet_name='线上审批流程稽核明细', header=1)
    # 智能设备台账
    df_device = pd.read_excel(EXCEL_WORK, sheet_name='智能设备台账汇总', header=2)

    # 标准化稽核明细
    df_audit['省份'] = df_audit['省区清洗-按最新'].map(lambda x: PROV_MERGE.get(x, x) if pd.notna(x) else x)
    df_audit['战区'] = df_audit['省份'].map(ZONE_MAP)
    # 最终结果即为F列，直接使用，无需从稽核结果填充

    print(f"  稽核明细: {len(df_audit)} 行")
    print(f"  计划明细: {len(df_plan)} 行")
    print(f"  推广促销: {len(df_promo)} 行")
    print(f"  线上审批: {len(df_approval)} 行")
    print(f"  设备台账: {len(df_device)} 行")

    return df_audit, df_plan, df_promo, df_approval, df_device


def precompute_all(df_audit, df_plan):
    """
    一次性预计算所有 (月份, 战区, 省区) 的统计数据,避免重复扫描。
    返回缓存字典。
    """
    print("预计算统计数据...")
    cache = {}

    # 稽核明细预处理:添加月份标记列
    all_months = MONTHS + [None]  # None = 全年

    # 省区级稽核统计:(月份, 省份) -> {audit, qual, unqual, fake}
    audit_prov = {}
    for m in all_months:
        sub = df_audit if m is None else df_audit[df_audit['稽核月份'] == m]
        grouped = sub.groupby('省份')
        for prov, grp in grouped:
            if prov not in audit_prov:
                audit_prov[prov] = {}
            audit_prov[prov][m] = {
                'audit': len(grp),
                'qual': int((grp['最终结果'] == '合格').sum()),
                'unqual': int((grp['最终结果'] == '不合格').sum()),
                'fake': int((grp['最终结果'] == '虚假').sum()),
            }

    # 省区级计划统计:(月份, 省份) -> {plan, invest}
    plan_prov = {}
    for m in all_months:
        sub = df_plan if m is None else df_plan[df_plan['月份'] == m]
        grouped = sub.groupby('省区清洗-按最新')
        for prov, grp in grouped:
            if prov not in plan_prov:
                plan_prov[prov] = {}
            plan_prov[prov][m] = {
                'plan': len(grp),
                'invest': int((grp['是否为稽核目标'] == '是').sum()),
            }

    # 战区级汇总:(月份, 战区) -> {plan, invest, audit, qual, unqual, fake, anomaly, rate}
    for m in all_months:
        for zone in ZONES + ['全部']:
            key = (m, zone)
            provinces = ZONE_PROVINCES[zone] if zone != '全部' else list(ZONE_MAP.keys())
            plan_t = 0; invest_t = 0; audit_t = 0; qual_t = 0; unqual_t = 0; fake_t = 0
            for prov in provinces:
                ps = plan_prov.get(prov, {}).get(m, {'plan': 0, 'invest': 0})
                plan_t += ps['plan']
                invest_t += ps['invest']
                # 注意:稽核明细中的省区是标准化后的,需要匹配
                a_s = audit_prov.get(prov, {}).get(m, {'audit': 0, 'qual': 0, 'unqual': 0, 'fake': 0})
                audit_t += a_s['audit']
                qual_t += a_s['qual']
                unqual_t += a_s['unqual']
                fake_t += a_s['fake']
            anomaly = unqual_t + fake_t
            rate = round(qual_t / audit_t * 100, 1) if audit_t > 0 else 100.0
            completion_rate = round(audit_t / (invest_t * 0.2) * 100, 1) if invest_t > 0 else 0.0
            cache[key] = {
                'plan': plan_t, 'invest': invest_t, 'audit': audit_t,
                'qual': qual_t, 'unqual': unqual_t, 'fake': fake_t,
                'anomaly': anomaly, 'rate': rate, 'completion_rate': completion_rate,
            }

    # 每日稽核趋势:(月份, 战区) -> [{label, value}, ...]
    for m in MONTHS:
        sub = df_audit[df_audit['稽核月份'] == m]
        dates = pd.to_datetime(sub['核查日期'].dropna())
        daily = dates.dt.day.value_counts()
        month_num = int(m.replace('月', ''))
        days = [31, 28, 31, 30, 31, 30][month_num - 1]
        points = [{'label': f'{d}日', 'value': int(daily.get(d, 0))} for d in range(1, days + 1)]
        cache[('trend', m, '全部')] = points

        for zone in ZONES:
            z_sub = sub[sub['战区'] == zone]
            z_dates = pd.to_datetime(z_sub['核查日期'].dropna())
            z_daily = z_dates.dt.day.value_counts()
            z_points = [{'label': f'{d}日', 'value': int(z_daily.get(d, 0))} for d in range(1, days + 1)]
            cache[('trend', m, zone)] = z_points

    # 全年月度趋势
    cache[('trend_monthly', '全部')] = [{'label': m, 'value': cache[(m, '全部')]['audit']} for m in MONTHS]
    for zone in ZONES:
        cache[('trend_monthly', zone)] = [{'label': m, 'value': cache[(m, zone)]['audit']} for m in MONTHS]

    # 省区级详情:(月份, 省份) -> {plan, invest, audit, qual, unqual, fake, rate}
    for prov in list(ZONE_MAP.keys()):
        for m in all_months:
            ps = plan_prov.get(prov, {}).get(m, {'plan': 0, 'invest': 0})
            a_s = audit_prov.get(prov, {}).get(m, {'audit': 0, 'qual': 0, 'unqual': 0, 'fake': 0})
            a = a_s['audit']
            rate = round(a_s['qual'] / a * 100, 1) if a > 0 else 100.0
            cache[('prov', m, prov)] = {
                'plan': ps['plan'], 'invest': ps['invest'],
                'audit': a, 'qual': a_s['qual'], 'unqual': a_s['unqual'],
                'fake': a_s['fake'], 'rate': rate,
            }

    print("  预计算完成")
    return cache


def build_zone_data_cached(cache, zone_name, month):
    """从缓存构建单个 zone + month 的 ZD 数据"""

    provinces = ZONE_PROVINCES[zone_name] if zone_name != '全部' else list(ZONE_MAP.keys())
    all_provinces = list(ZONE_MAP.keys())

    # Zone summary
    if month is None or month == "全年":
        # 全年:汇总各月数据
        ps = [cache.get((m, zone_name), cache.get((m, '全部'), {})) for m in MONTHS]
        zs = {
            'plan': sum(s.get('plan', 0) for s in ps),
            'invest': sum(s.get('invest', 0) for s in ps),
            'audit': sum(s.get('audit', 0) for s in ps),
            'qual': sum(s.get('qual', 0) for s in ps),
            'unqual': sum(s.get('unqual', 0) for s in ps),
            'fake': sum(s.get('fake', 0) for s in ps),
        }
        zs['anomaly'] = zs['unqual'] + zs['fake']
        zs['rate'] = round(zs['qual'] / zs['audit'] * 100, 1) if zs['audit'] > 0 else 100.0
    else:
        zs = cache.get((month, zone_name), cache.get((month, '全部')))
        if zs is None:
            zs = {'plan': 0, 'invest': 0, 'audit': 0, 'qual': 0, 'unqual': 0, 'fake': 0, 'anomaly': 0, 'rate': 100.0}

    # KPI
    kpi_monthly = [zs['plan'], zs['audit'], zs['anomaly'], zs['rate']]

    # KPI huanbi
    if month and month in MONTHS:
        m_idx = MONTHS.index(month)
        if m_idx > 0:
            prev = cache.get((MONTHS[m_idx - 1], zone_name), cache.get((MONTHS[m_idx - 1], '全部')))
            if prev:
                def hb(c, p): return round((c - p) / p * 100, 1) if p != 0 else 0.0
                kpi_huanbi = [
                    hb(zs['plan'], prev['plan']),
                    hb(zs['audit'], prev['audit']),
                    hb(zs['anomaly'], prev['anomaly']),
                    hb(zs['rate'], prev['rate']),
                ]
            else:
                kpi_huanbi = [0, 0, 0, 0]
        else:
            kpi_huanbi = [0, 0, 0, 0]
    else:
        kpi_huanbi = [0, 0, 0, 0]

    # Top5 稽核数
    prov_list = []
    for prov in provinces:
        if month is None or month == "全年":
            # 全年:汇总各省各月数据
            ps_sum = {'audit': 0, 'qual': 0, 'unqual': 0, 'fake': 0}
            for mm in MONTHS:
                ps_m = cache.get(('prov', mm, prov), {})
                for k in ps_sum: ps_sum[k] += ps_m.get(k, 0)
            ps_sum['rate'] = round(ps_sum['qual'] / ps_sum['audit'] * 100, 1) if ps_sum['audit'] > 0 else 100.0
            ps = ps_sum
        else:
            ps = cache.get(('prov', month, prov), {})
        if ps.get('audit', 0) > 0:
            prov_list.append({'n': prov, 'v': ps['audit'], 'pct': ps['rate']})
    prov_list.sort(key=lambda x: x['v'], reverse=True)
    top5 = prov_list[:5]

    # Rate_top5 最低合格率TOP5(升序)
    rate_list = [{'n': p['n'], 'v': f"{p['pct']}", 'bw': int(p['pct'])} for p in prov_list]
    rate_list.sort(key=lambda x: x['bw'])
    rate_top5 = rate_list[:5]

    # Month rows
    month_rows = []
    for m in MONTHS:
        ms = cache[(m, zone_name)] if zone_name != '全部' else cache[(m, '全部')]
        month_rows.append({
            'm': m, 'p': ms['plan'], 'a': ms['audit'],
            'q': ms['qual'], 'rs': f"{ms['rate']}"
        })

    # Trend points
    if month and month in MONTHS:
        trend_points = cache.get(('trend', month, zone_name), cache.get(('trend', month, '全部'), []))
        trend_title = f"{month}每日稽核数量"
    else:
        trend_points = cache.get(('trend_monthly', zone_name), cache.get(('trend_monthly', '全部'), []))
        trend_title = "每月稽核数量"

    # Result items
    result_items = [
        {'n': '合格', 'v': zs['qual'], 'c': '#fcc900'},
        {'n': '不合格', 'v': zs['unqual'], 'c': '#703a1e'},
        {'n': '虚假', 'v': zs['fake'], 'c': '#ec5f74'},
    ]

    # Progress items
    progress_items = []
    for m in MONTHS:
        ps_list = [cache.get(('prov', m, p), {'plan': 0, 'invest': 0, 'audit': 0}) for p in provinces]
        m_plan = sum(s['plan'] for s in ps_list)
        m_invest = sum(s['invest'] for s in ps_list)
        m_audit = sum(s['audit'] for s in ps_list)
        m_pct = round(m_audit / (m_invest * 0.2) * 100, 1) if m_invest > 0 else 0.0
        progress_items.append({
            'm': m, 'pct': m_pct, 'plan_q': m_invest,
            'audit_cnt': m_audit, 'display_plan': m_plan,
        })

    if month and month in MONTHS:
        progress_current = progress_items[MONTHS.index(month)].copy()
        progress_current['m'] = month
    else:
        tp = sum(pi['display_plan'] for pi in progress_items)
        ti = sum(pi['plan_q'] for pi in progress_items)
        ta = sum(pi['audit_cnt'] for pi in progress_items)
        progress_current = {
            'm': '全年', 'pct': round(ta / (ti * 0.2) * 100, 1) if ti > 0 else 0.0,
            'plan_q': ti, 'audit_cnt': ta, 'display_plan': tp,
        }

    # Target items
    prov_targets = []
    for prov in provinces:
        if month is None or month == "全年":
            inv_sum = sum(cache.get(('prov', mm, prov), {}).get('invest', 0) for mm in MONTHS)
            plan_sum = sum(cache.get(('prov', mm, prov), {}).get('plan', 0) for mm in MONTHS)
            prov_targets.append({'invest': inv_sum, 'plan': plan_sum})
        else:
            prov_targets.append(cache.get(('prov', month, prov), {'plan': 0, 'invest': 0}))
    ty = sum(s['invest'] for s in prov_targets)
    tn = sum(s['plan'] - s['invest'] for s in prov_targets)
    target_items = [{'n': '是', 'v': ty, 'c': '#703a1e'}, {'n': '否', 'v': tn, 'c': '#fcc900'}]

    # Reg detail
    reg_detail = []
    for prov in provinces:
        if month is None or month == "全年":
            ps_sum = {'audit': 0, 'qual': 0, 'unqual': 0, 'fake': 0, 'invest': 0}
            for mm in MONTHS:
                ps_m = cache.get(('prov', mm, prov), {})
                for k in ps_sum: ps_sum[k] += ps_m.get(k, 0)
            ps_sum['rate'] = round(ps_sum['qual'] / ps_sum['audit'] * 100, 1) if ps_sum['audit'] > 0 else 100.0
            ps = ps_sum
        else:
            ps = cache.get(('prov', month, prov), {})
        a = ps.get('audit', 0); r = ps.get('rate', 0)
        st = 'normal' if r >= 80 else ('warn' if r >= 60 else 'bad')
        reg_detail.append({
            'name': prov, 'plan': ps.get('invest', 0), 'audit': a,
            'qual': ps.get('qual', 0), 'rate': r, 'huanbi': 0, 'status': st,
        })

    # Province progress
    pp = []
    for prov in provinces:
        if month is None or month == "全年":
            ps_sum = {'invest': 0, 'audit': 0}
            for mm in MONTHS:
                ps_m = cache.get(('prov', mm, prov), {})
                ps_sum['invest'] += ps_m.get('invest', 0)
                ps_sum['audit'] += ps_m.get('audit', 0)
            ps = ps_sum
        else:
            ps = cache.get(('prov', month, prov), {})
        inv = ps.get('invest', 0); tgt = math.ceil(inv / 5) if inv > 0 else 0
        aud = ps.get('audit', 0); prog = round(aud / tgt * 100, 1) if tgt > 0 else 0.0
        pp.append({'name': prov, 'zone': ZONE_MAP.get(prov, ''), 'invest': inv, 'target': tgt, 'audit': aud, 'progress': prog})
    pp.sort(key=lambda x: x['progress'], reverse=True)

    # Issue rank
    issue_rank = []
    for prov in provinces:
        if month is None or month == "全年":
            uv = 0; fv = 0
            for mm in MONTHS:
                ps_m = cache.get(('prov', mm, prov), {})
                uv += ps_m.get('unqual', 0)
                fv += ps_m.get('fake', 0)
            total = uv + fv
        else:
            ps = cache.get(('prov', month, prov), {})
            total = ps.get('unqual', 0) + ps.get('fake', 0)
        if total > 0:
            issue_rank.append({'n': prov, 'v': total})
    issue_rank.sort(key=lambda x: x['v'], reverse=True)

    # 收集稽核数为0的省区（合格率按100%计算）
    zero_audit_provs = []
    for prov in provinces:
        if month is None or month == "全年":
            pa = sum(cache.get(('prov', mm, prov), {}).get('audit', 0) for mm in MONTHS)
        else:
            pa = cache.get(('prov', month, prov), {}).get('audit', 0)
        if pa == 0:
            zero_audit_provs.append(prov)

    return {
        'kpi_monthly': kpi_monthly, 'kpi_huanbi': kpi_huanbi,
        'top5': top5, 'rate_top5': rate_top5, 'month_rows': month_rows,
        'trend_points': trend_points, 'trend_title': trend_title,
        'result_items': result_items, 'progress_items': progress_items,
        'progress_current': progress_current, 'target_items': target_items,
        'reg_detail': reg_detail, 'province_progress': pp,
        'issue_rank': issue_rank, 'zero_audit_provs': zero_audit_provs,
        # audit_details 和 issue_details 在外层按需填充
    }


def build_audit_details(df_audit, zone_name, month):
    """构建稽核明细列表"""
    sub = df_audit.copy()
    if month and month in MONTHS:
        sub = sub[sub['稽核月份'] == month]
    if zone_name != '全部':
        sub = sub[sub['战区'] == zone_name]

    details = []
    for _, row in sub.iterrows():
        result = row['最终结果']
        details.append({
            'zone': row.get('战区', ''),
            'province': row['省份'],
            'month': row['稽核月份'],
            'store': str(row.get('经销商名称（全称）', '') or ''),
            'executor': str(row.get('执行人（大区/城市经理）', '') or ''),
            'result': result,
        })
    return details


def build_issue_details(df_audit, zone_name, month):
    """构建不合格/虚假明细"""
    sub = df_audit.copy()
    if month and month in MONTHS:
        sub = sub[sub['稽核月份'] == month]
    if zone_name != '全部':
        sub = sub[sub['战区'] == zone_name]
    sub = sub[sub['最终结果'].isin(['不合格', '虚假'])]

    details = []
    for _, row in sub.iterrows():
        details.append({
            'zone': row.get('战区', ''),
            'province': row['省份'],
            'month': row['稽核月份'],
            'store': str(row.get('经销商名称（全称）', '') or ''),
            'executor': str(row.get('执行人（大区/城市经理）', '') or ''),
            'result': row['最终结果'],
        })
    return details


def extract_and_inject_template(html_path, zd_json_str):
    """从模板提取 HTML，注入 ZD 数据，返回完整 HTML"""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    zd_start = content.find('var ZD =')
    zd_json_start = content.find('{', zd_start)
    
    # 找 ZD JSON 结束（匹配花括号）
    brace_count = 0; i = zd_json_start
    while i < len(content):
        if content[i] == '{': brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0: break
        i += 1
    zd_end = i + 1
    
    before = content[:zd_start]
    after = content[zd_end:]
    
    # 修正模板中的字体路径为本地 fonts/ 目录
    before = before.replace("url('assets/fonts/", "url('fonts/")
    
    # 注入零稽核提示div（在 .kr 之前）
    zero_hint_html = '''<div id="zero-hint" style="display:none;margin:0 16px 8px;padding:8px 12px;background:#fff3cd;border-radius:6px;font-size:12px;color:#856404;line-height:1.5;">
      &#9888; <span id="zero-hint-text"></span>
    </div>'''
    if 'id="zero-hint"' not in content:
        before = before.replace('<div class="kr">', zero_hint_html + '\n<div class="kr">', 1)
    
    # 注入JS更新逻辑（在kpi3更新后）
    zero_hint_js = '''
  // 零稽核提示
  (function(){
    var zp = d.zero_audit_provs || [];
    var hint = document.getElementById("zero-hint");
    var hintTxt = document.getElementById("zero-hint-text");
    if(zp.length > 0){
      var names = zp.join("、");
      hintTxt.textContent = names + " 因本月无稽核计划，合格率按100%计算";
      hint.style.display = "block";
    } else {
      hint.style.display = "none";
    }
  })();
'''
    # 在 kpi3.textContent 行之后插入
    if '零稽核提示' not in content:
        after = after.replace(
            'kpi3").textContent=km[3]+"%";',
            'kpi3").textContent=km[3]+"%";' + zero_hint_js,
            1
        )
    
    print(f"  模板前半: {len(before)} 字符, 模板后半: {len(after)} 字符")
    
    return before + 'var ZD = ' + zd_json_str + after


def sync_top_kpi_placeholders(html, current_data, df_promo, df_approval):
    audit_count = int(current_data.get('audit', 0) or 0)

    promo_total = int(len(df_promo)) if df_promo is not None else 0
    promo_yes = 0
    if df_promo is not None and len(df_promo.columns) >= 14 and promo_total:
        promo_result = df_promo.iloc[:, 13].astype(str).str.strip()
        promo_yes = int((promo_result == '\u662f').sum())
    promo_rate = round((promo_yes / promo_total * 100), 1) if promo_total else 0

    approval_total = int(len(df_approval)) if df_approval is not None else 0
    approval_yes = 0
    if df_approval is not None and len(df_approval.columns) >= 9 and approval_total:
        approval_result = df_approval.iloc[:, 8].astype(str).str.strip()
        approval_yes = int(approval_result.isin(['\u662f', '\u5408\u683c']).sum())
    approval_rate = round((approval_yes / approval_total * 100), 1) if approval_total else 0

    html = re.sub(r'(<div id="kpi0"[^>]*>)[^<]*(</div>)', rf'\g<1>{audit_count}\2', html, count=1)
    html = re.sub(r'(<span id="kpi0Live">)[^<]*(</span>)', rf'\g<1>{audit_count}\2', html, count=1)
    html = re.sub(r'(<span id="promoAuditLive">)[^<]*(</span>)', rf'\g<1>{promo_total}\2', html, count=1)
    html = re.sub(r'(<span id="promoProgressLive"[^>]*>)[^<]*(</span>)', rf'\g<1>{promo_rate:g}%\2', html, count=1)
    html = re.sub(
        r'(<div class="kpi-live-main">)\d+(<span class="kpi-unit">[^<]*</span></div>\s*<div class="kpi-live-sub">[^<]*<span class="kpi-live-rate">)[^<]*(</span></div>)',
        lambda m: m.group(1) + str(approval_total) + m.group(2) + f'{approval_rate:g}%' + m.group(3),
        html,
        count=1,
    )
    return html


def main():
    print(f"=== 市场稽核部重点工作看板生成器 v2 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    build_tag = datetime.now().strftime('%Y%m%d%H%M%S')

    # 加载数据
    df_audit, df_plan, df_promo, df_approval, df_device = load_data()

    # 预计算所有统计数据
    cache = precompute_all(df_audit, df_plan)

    # 验证
    print("\n=== 数据验证 ===")
    c1 = cache[('1月', '全部')]
    print(f"1月/全部: plan={c1['plan']}, audit={c1['audit']}, anomaly={c1['anomaly']}, rate={c1['rate']}")
    c6 = cache[('6月', '全部')]
    print(f"6月/全部: plan={c6['plan']}, audit={c6['audit']}, anomaly={c6['anomaly']}, rate={c6['rate']}")

    # 构建 ZD
    print("\n构建 ZD 数据...")
    zd = {}

    for m in MONTHS + ['全年']:
        zd[m] = {}
        for zone_name in ['全部'] + ZONES:
            print(f"  {m} / {zone_name}...")
            zd[m][zone_name] = build_zone_data_cached(cache, zone_name, m)

    # 填充 audit_details 和 issue_details(仅 '全部' 和各战区)
    print("  填充明细数据...")
    for m in MONTHS + ['全年']:
        for zone_name in ['全部'] + ZONES:
            zd[m][zone_name]['audit_details'] = build_audit_details(df_audit, zone_name, m)
            zd[m][zone_name]['issue_details'] = build_issue_details(df_audit, zone_name, m)

    # 注入模板
    print("\n注入 HTML 模板...")
    zd_json = json.dumps(zd, ensure_ascii=False, separators=(',', ':'), cls=NpEncoder)
    print(f"  ZD JSON: {len(zd_json):,} 字符")

    # 生成主看板
    print("\n--- 生成主看板 ---")
    html_main = extract_and_inject_template(HTML_TEMPLATE_MAIN, zd_json)
    html_main = sync_top_kpi_placeholders(html_main, c6, df_promo, df_approval)
    html_main = apply_data_cache_buster(html_main, build_tag)
    with open(OUTPUT_MAIN, 'w', encoding='utf-8') as f:
        f.write(html_main)
    print(f"  ✅ 主看板: {OUTPUT_MAIN} ({len(html_main):,} 字符)")

    # 生成陈列稽核看板
    print("\n--- 生成陈列稽核看板 ---")
    html_disp = extract_and_inject_template(HTML_TEMPLATE_DISP, zd_json)
    html_disp = apply_data_cache_buster(html_disp, build_tag)
    with open(OUTPUT_DISP, 'w', encoding='utf-8') as f:
        f.write(html_disp)
    print(f"  ✅ 陈列稽核看板: {OUTPUT_DISP} ({len(html_disp):,} 字符)")

    print(f"\n🎉 两个看板均生成完成!")


if __name__ == '__main__':
    main()
