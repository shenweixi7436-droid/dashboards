# -*- coding: utf-8 -*-
"""
市场稽核部重点工作看板 - 数据生成脚本
从 Excel 数据源计算 ZD JSON 数据，嵌入原 HTML 模板生成完整看板。
"""

import json
import math
import re
import sys
import warnings
from datetime import datetime
from collections import defaultdict

import numpy as np
import pandas as pd

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return super().default(obj)

warnings.filterwarnings('ignore')

# ============ 路径配置 ============
EXCEL_PATH = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'
HTML_TEMPLATE_PATH = r'C:\Users\shenw\Documents\New project\市场稽核部重点工作看板-06101350.html'
OUTPUT_PATH = r'C:\Users\shenw\github-dashboards\index.html'

# ============ 省区→战区映射（来自计划明细数据，唯一权威来源）============
ZONE_MAP = {
    '云南': '区域经营部', '川渝藏': '区域经营部', '广西': '区域经营部',
    '浙江': '区域经营部', '湖南': '区域经营部', '苏北': '区域经营部',
    '苏南': '区域经营部', '陕甘青宁新': '区域经营部',
    '山东': '山东战区',
    '河北': '华北战区', '北京': '华北战区', '天津': '华北战区',
    '广东': '华南战区', '福建': '华南战区', '贵州': '华南战区',
    '内蒙古': '东北战区', '辽宁': '东北战区', '黑龙江': '东北战区', '吉林': '东北战区',
    '安徽': '华中战区', '山西': '华中战区', '河南': '华中战区', '湖北': '华中战区', '江西': '华中战区',
}

# 战区→省份列表（从 ZONE_MAP 反向生成）
ZONES = ['区域经营部', '山东战区', '华北战区', '华南战区', '东北战区', '华中战区']
ZONE_PROVINCES = defaultdict(list)
for prov, zone in ZONE_MAP.items():
    ZONE_PROVINCES[zone].append(prov)
for z in ZONES:
    ZONE_PROVINCES[z].sort()

# 稽核明细中拆分的省区名称 → 合并后的名称
PROV_MERGE = {
    '宁夏': '陕甘青宁新', '陕西': '陕甘青宁新', '甘肃': '陕甘青宁新',
    '青海': '陕甘青宁新', '新疆': '陕甘青宁新',
    '四川': '川渝藏', '重庆': '川渝藏', '西藏': '川渝藏',
}

MONTHS = ['1月', '2月', '3月', '4月', '5月', '6月']

def load_data():
    """加载 Excel 数据"""
    print("加载 Excel 数据...")
    df_audit = pd.read_excel(EXCEL_PATH, sheet_name='稽核明细-汇总')
    df_plan = pd.read_excel(EXCEL_PATH, sheet_name='计划明细-汇总')
    df_summary = pd.read_excel(EXCEL_PATH, sheet_name='各战区稽核进汇总')
    
    # 标准化省区名称（稽核明细使用拆分名称）
    df_audit['省份'] = df_audit['省区清洗-按最新'].map(lambda x: PROV_MERGE.get(x, x))
    # 为每条稽核记录分配战区
    df_audit['战区'] = df_audit['省份'].map(ZONE_MAP)
    
    print(f"  稽核明细: {len(df_audit)} 行")
    print(f"  计划明细: {len(df_plan)} 行")
    print(f"  汇总表: {len(df_summary)} 行")
    
    return df_audit, df_plan, df_summary

def get_all_provinces():
    """获取所有省区列表（来自计划明细）"""
    return sorted(ZONE_MAP.keys())

def compute_province_stats(df_audit, df_plan, month=None):
    """
    计算每个省区的统计数据。
    month=None 表示全年汇总。
    返回 dict: province_name -> {plan, invest, audit, qual, unqual, fake, rate}
    """
    provinces = get_all_provinces()
    stats = {}
    
    # 筛选数据
    audit_filter = df_audit
    plan_filter = df_plan
    if month:
        audit_filter = df_audit[df_audit['稽核月份'] == month]
        plan_filter = df_plan[df_plan['月份'] == month]
    
    for prov in provinces:
        # 计划数据
        plan_rows = plan_filter[plan_filter['省区清洗-按最新'] == prov]
        plan_cnt = len(plan_rows)
        invest_cnt = (plan_rows['是否为稽核目标'] == '是').sum()
        
        # 稽核数据
        audit_rows = audit_filter[audit_filter['省份'] == prov]
        audit_cnt = len(audit_rows)
        qual_cnt = int((audit_rows['最终结果'] == '合格').sum())
        unqual_cnt = int((audit_rows['最终结果'] == '不合格').sum())
        fake_cnt = int((audit_rows['最终结果'] == '虚假').sum())
        rate = round(qual_cnt / audit_cnt * 100, 1) if audit_cnt > 0 else 0.0
        
        stats[prov] = {
            'plan': plan_cnt,
            'invest': invest_cnt,
            'audit': audit_cnt,
            'qual': qual_cnt,
            'unqual': unqual_cnt,
            'fake': fake_cnt,
            'rate': rate,
        }
    
    return stats

def compute_zone_summary(df_audit, df_plan, zone_name, month=None):
    """计算单个战区的汇总数据"""
    provinces = ZONE_PROVINCES[zone_name]
    
    audit_filter = df_audit
    plan_filter = df_plan
    if month:
        audit_filter = df_audit[df_audit['稽核月份'] == month]
        plan_filter = df_plan[df_plan['月份'] == month]
    
    zone_audit = audit_filter[audit_filter['战区'] == zone_name]
    
    # 计划数 = 该战区省份的计划行数总和
    plan_total = 0
    invest_total = 0
    for prov in provinces:
        plan_rows = plan_filter[plan_filter['省区清洗-按最新'] == prov]
        plan_total += len(plan_rows)
        invest_total += (plan_rows['是否为稽核目标'] == '是').sum()
    
    audit_total = len(zone_audit)
    qual_total = int((zone_audit['最终结果'] == '合格').sum())
    unqual_total = int((zone_audit['最终结果'] == '不合格').sum())
    fake_total = int((zone_audit['最终结果'] == '虚假').sum())
    anomaly = unqual_total + fake_total
    rate = round(qual_total / audit_total * 100, 1) if audit_total > 0 else 0.0
    
    return {
        'plan': plan_total,
        'invest': int(invest_total),
        'audit': audit_total,
        'qual': qual_total,
        'unqual': unqual_total,
        'fake': fake_total,
        'anomaly': anomaly,
        'rate': rate,
    }

def compute_huanbi(current, previous):
    """计算环比（百分比变化）"""
    if previous == 0:
        return 0.0
    return round((current - previous) / previous * 100, 1)

def compute_rate_huanbi(current_rate, prev_rate):
    """计算合格率环比"""
    if prev_rate == 0:
        return 0.0
    return round((current_rate - prev_rate) / prev_rate * 100, 1)

def compute_trend_points(df_audit, month, zone_name='全部'):
    """计算每日稽核数量趋势"""
    audit_filter = df_audit[df_audit['稽核月份'] == month]
    if zone_name != '全部':
        audit_filter = audit_filter[audit_filter['战区'] == zone_name]
    
    # 从核查日期提取日
    dates = pd.to_datetime(audit_filter['核查日期'].dropna())
    daily = dates.dt.day.value_counts()
    
    # 确定月份天数（简化：1-6月）
    month_num = int(month.replace('月', ''))
    days_in_month = [31, 28, 31, 30, 31, 30][month_num - 1]
    
    points = []
    for d in range(1, days_in_month + 1):
        points.append({
            'label': f'{d}日',
            'value': int(daily.get(d, 0))
        })
    
    return points

def compute_monthly_trend(df_audit):
    """计算每月稽核数量趋势（全年视图）"""
    points = []
    for m in MONTHS:
        dm = df_audit[df_audit['稽核月份'] == m]
        points.append({
            'label': m,
            'value': len(dm)
        })
    return points

def build_zone_data(df_audit, df_plan, zone_name, month=None, prev_month_data=None, all_prov_stats=None, all_zone_summaries=None):
    """构建单个 zone + month 的 ZD 数据"""
    
    if all_prov_stats is None:
        all_prov_stats = compute_province_stats(df_audit, df_plan, month)
    
    if all_zone_summaries is None:
        all_zone_summaries = {}
        for z in ZONES:
            all_zone_summaries[z] = compute_zone_summary(df_audit, df_plan, z, month)
    
    if zone_name == '全部':
        # 全部 = 所有战区汇总
        zone_summary = {
            'plan': sum(s['plan'] for s in all_zone_summaries.values()),
            'invest': sum(s['invest'] for s in all_zone_summaries.values()),
            'audit': sum(s['audit'] for s in all_zone_summaries.values()),
            'qual': sum(s['qual'] for s in all_zone_summaries.values()),
            'unqual': sum(s['unqual'] for s in all_zone_summaries.values()),
            'fake': sum(s['fake'] for s in all_zone_summaries.values()),
        }
        zone_summary['anomaly'] = zone_summary['unqual'] + zone_summary['fake']
        zone_summary['rate'] = round(zone_summary['qual'] / zone_summary['audit'] * 100, 1) if zone_summary['audit'] > 0 else 0.0
        provinces = get_all_provinces()
    else:
        zone_summary = all_zone_summaries[zone_name]
        provinces = ZONE_PROVINCES[zone_name]
    
    # KPI
    kpi_monthly = [
        zone_summary['plan'],
        zone_summary['audit'],
        zone_summary['anomaly'],
        zone_summary['rate'],
    ]
    
    # KPI 环比
    if prev_month_data and month:
        prev_summary = prev_month_data
        kpi_huanbi = [
            compute_huanbi(zone_summary['plan'], prev_summary['plan']),
            compute_huanbi(zone_summary['audit'], prev_summary['audit']),
            compute_huanbi(zone_summary['anomaly'], prev_summary['anomaly']),
            compute_rate_huanbi(zone_summary['rate'], prev_summary['rate']),
        ]
    else:
        kpi_huanbi = [0.0, 0.0, 0.0, 0.0]
    
    # Top5 稽核数（降序）
    prov_list = []
    for prov in provinces:
        st = all_prov_stats[prov]
        if st['audit'] > 0:
            prov_list.append({'n': prov, 'v': st['audit'], 'pct': st['rate']})
    prov_list.sort(key=lambda x: x['v'], reverse=True)
    top5 = prov_list[:5]
    
    # Rate_top5 合格率最低TOP5（升序，仅包含有稽核数据的省区）
    rate_list = [{'n': p['n'], 'v': f"{p['pct']}", 'bw': int(p['pct'])} for p in prov_list]
    rate_list.sort(key=lambda x: x['bw'])
    rate_top5 = rate_list[:5]
    
    # Month rows（仅 全部 视图）
    if zone_name == '全部':
        month_rows = []
        for m in MONTHS:
            m_stats = compute_zone_summary(df_audit, df_plan, None, m)
            m_all = {
                'plan': sum(compute_zone_summary(df_audit, df_plan, z, m)['plan'] for z in ZONES),
                'audit': sum(compute_zone_summary(df_audit, df_plan, z, m)['audit'] for z in ZONES),
                'qual': sum(compute_zone_summary(df_audit, df_plan, z, m)['qual'] for z in ZONES),
            }
            if zone_name == '全部':
                for z in ZONES:
                    zs = compute_zone_summary(df_audit, df_plan, z, m)
                    m_all = {
                        'plan': sum(compute_zone_summary(df_audit, df_plan, z2, m)['plan'] for z2 in ZONES),
                        'audit': sum(compute_zone_summary(df_audit, df_plan, z2, m)['audit'] for z2 in ZONES),
                        'qual': sum(compute_zone_summary(df_audit, df_plan, z2, m)['qual'] for z2 in ZONES),
                    }
                    break  # 只需要算一次
            m_rate = round(m_all['qual'] / m_all['audit'] * 100, 1) if m_all['audit'] > 0 else 0.0
            month_rows.append({
                'm': m,
                'p': m_all['plan'],
                'a': m_all['audit'],
                'q': m_all['qual'],
                'rs': f"{m_rate}"
            })
    else:
        month_rows = []
        for m in MONTHS:
            zs = compute_zone_summary(df_audit, df_plan, zone_name, m)
            m_rate = round(zs['qual'] / zs['audit'] * 100, 1) if zs['audit'] > 0 else 0.0
            month_rows.append({
                'm': m,
                'p': zs['plan'],
                'a': zs['audit'],
                'q': zs['qual'],
                'rs': f"{m_rate}"
            })
    
    # Trend points
    if month and month != '全年':
        trend_points = compute_trend_points(df_audit, month, zone_name)
        trend_title = f"{month}每日稽核数量"
    else:
        if zone_name == '全部':
            trend_points = compute_monthly_trend(df_audit)
            trend_title = "每月稽核数量"
        else:
            trend_points = []
            for m in MONTHS:
                zs = compute_zone_summary(df_audit, df_plan, zone_name, m)
                trend_points.append({'label': m, 'value': zs['audit']})
            trend_title = "每月稽核数量"
    
    # Result items
    result_items = [
        {'n': '合格', 'v': zone_summary['qual'], 'c': '#fcc900'},
        {'n': '不合格', 'v': zone_summary['unqual'], 'c': '#703a1e'},
        {'n': '虚假', 'v': zone_summary['fake'], 'c': '#ec5f74'},
    ]
    
    # Progress items（需要投入费用门店数）
    if zone_name == '全部':
        progress_items = []
        for m in MONTHS:
            m_prov_stats = compute_province_stats(df_audit, df_plan, m)
            m_plan = sum(m_prov_stats[p]['plan'] for p in get_all_provinces())
            m_invest = sum(m_prov_stats[p]['invest'] for p in get_all_provinces())
            m_audit = sum(m_prov_stats[p]['audit'] for p in get_all_provinces())
            m_pct = round(m_audit / m_invest * 100, 1) if m_invest > 0 else 0.0
            progress_items.append({
                'm': m,
                'pct': m_pct,
                'plan_q': m_invest,
                'audit_cnt': m_audit,
                'display_plan': m_plan,
            })
        # progress_current = 最后一个月
        progress_current = progress_items[-1].copy()
        # 如果指定了月份，用那个月
        if month and month in MONTHS:
            idx = MONTHS.index(month)
            progress_current = progress_items[idx].copy()
            progress_current['m'] = month
        elif month == '全年':
            total_plan = sum(pi['display_plan'] for pi in progress_items)
            total_invest = sum(pi['plan_q'] for pi in progress_items)
            total_audit = sum(pi['audit_cnt'] for pi in progress_items)
            total_pct = round(total_audit / total_invest * 100, 1) if total_invest > 0 else 0.0
            progress_current = {
                'm': '全年',
                'pct': total_pct,
                'plan_q': total_invest,
                'audit_cnt': total_audit,
                'display_plan': total_plan,
            }
    else:
        progress_items = []
        for m in MONTHS:
            m_zone_prov_stats = {}
            for prov in ZONE_PROVINCES[zone_name]:
                m_all_stats = compute_province_stats(df_audit, df_plan, m)
                m_zone_prov_stats[prov] = m_all_stats[prov]
            m_plan = sum(m_zone_prov_stats[p]['plan'] for p in ZONE_PROVINCES[zone_name])
            m_invest = sum(m_zone_prov_stats[p]['invest'] for p in ZONE_PROVINCES[zone_name])
            m_audit = sum(m_zone_prov_stats[p]['audit'] for p in ZONE_PROVINCES[zone_name])
            m_pct = round(m_audit / m_invest * 100, 1) if m_invest > 0 else 0.0
            progress_items.append({
                'm': m,
                'pct': m_pct,
                'plan_q': m_invest,
                'audit_cnt': m_audit,
                'display_plan': m_plan,
            })
        if month and month in MONTHS:
            idx = MONTHS.index(month)
            progress_current = progress_items[idx].copy()
            progress_current['m'] = month
        elif month == '全年':
            total_plan = sum(pi['display_plan'] for pi in progress_items)
            total_invest = sum(pi['plan_q'] for pi in progress_items)
            total_audit = sum(pi['audit_cnt'] for pi in progress_items)
            total_pct = round(total_audit / total_invest * 100, 1) if total_invest > 0 else 0.0
            progress_current = {
                'm': '全年',
                'pct': total_pct,
                'plan_q': total_invest,
                'audit_cnt': total_audit,
                'display_plan': total_plan,
            }
        else:
            progress_current = progress_items[-1].copy()
    
    # Target items（是否为稽核目标分布）
    target_yes = sum(all_prov_stats[p]['invest'] for p in provinces)
    target_no = sum(all_prov_stats[p]['plan'] - all_prov_stats[p]['invest'] for p in provinces)
    target_items = [
        {'n': '是', 'v': target_yes, 'c': '#703a1e'},
        {'n': '否', 'v': target_no, 'c': '#fcc900'},
    ]
    
    # Reg detail（每个省区详情）
    reg_detail = []
    for prov in provinces:
        st = all_prov_stats[prov]
        if st['audit'] > 0 and st['rate'] >= 80:
            status = 'normal'
        elif st['audit'] > 0 and st['rate'] >= 60:
            status = 'warn'
        else:
            status = 'bad'
        
        reg_detail.append({
            'name': prov,
            'plan': st['invest'],  # 投入费用门店数
            'audit': st['audit'],
            'qual': st['qual'],
            'rate': st['rate'],
            'huanbi': 0,  # JS 会动态计算
            'status': status,
        })
    
    # Province progress（投入、目标、稽核、完成率）
    province_progress = []
    for prov in provinces:
        st = all_prov_stats[prov]
        invest = st['invest']
        target = math.ceil(invest / 5) if invest > 0 else 0
        progress = round(st['audit'] / target * 100, 1) if target > 0 else 0.0
        province_progress.append({
            'name': prov,
            'zone': ZONE_MAP[prov],
            'invest': invest,
            'target': target,
            'audit': st['audit'],
            'progress': progress,
        })
    province_progress.sort(key=lambda x: x['progress'], reverse=True)
    
    # Audit details（全部稽核记录）
    audit_filter = df_audit
    if month and month != '全年':
        audit_filter = df_audit[df_audit['稽核月份'] == month]
    
    if zone_name != '全部':
        audit_filter = audit_filter[audit_filter['战区'] == zone_name]
    
    audit_details = []
    for _, row in audit_filter.iterrows():
        result = row['最终结果']
        if pd.isna(result):
            result = '待定'
        audit_details.append({
            'zone': row.get('战区', ZONE_MAP.get(row['省份'], '')),
            'province': row['省份'],
            'month': row['稽核月份'],
            'store': str(row.get('经销商名称（全称）', '') or ''),
            'executor': str(row.get('执行人（大区/城市经理）', '') or ''),
            'result': result,
        })
    
    # Issue details（不合格+虚假记录）
    issue_filter = audit_filter[audit_filter['最终结果'].isin(['不合格', '虚假'])]
    issue_details = []
    for _, row in issue_filter.iterrows():
        issue_details.append({
            'zone': row.get('战区', ZONE_MAP.get(row['省份'], '')),
            'province': row['省份'],
            'month': row['稽核月份'],
            'store': str(row.get('经销商名称（全称）', '') or ''),
            'executor': str(row.get('执行人（大区/城市经理）', '') or ''),
            'result': row['最终结果'],
        })
    
    # Issue rank（不合格+虚假按省区排名，降序）
    issue_counts = issue_filter.groupby('省份').size()
    total_issues = len(issue_filter)
    issue_rank = []
    for prov_name, count in issue_counts.items():
        pct = round(count / total_issues * 100, 1) if total_issues > 0 else 0.0
        issue_rank.append({'n': prov_name, 'v': int(count), 'pct': pct})
    issue_rank.sort(key=lambda x: x['v'], reverse=True)
    
    return {
        'kpi_monthly': kpi_monthly,
        'kpi_huanbi': kpi_huanbi,
        'top5': top5,
        'rate_top5': rate_top5,
        'month_rows': month_rows,
        'trend_points': trend_points,
        'trend_title': trend_title,
        'result_items': result_items,
        'progress_items': progress_items,
        'progress_current': progress_current,
        'target_items': target_items,
        'reg_detail': reg_detail,
        'province_progress': province_progress,
        'audit_details': audit_details,
        'issue_details': issue_details,
        'issue_rank': issue_rank,
    }

def build_zd(df_audit, df_plan):
    """构建完整的 ZD 数据结构"""
    print("构建 ZD 数据...")
    zd = {}
    
    # 缓存月度数据用于环比计算
    month_cache = {}  # (zone_name, month) -> summary for huanbi
    
    # 先计算所有需要的月度汇总
    for zone_name in ['全部'] + ZONES:
        for m in MONTHS:
            if zone_name == '全部':
                s = {
                    'plan': sum(compute_zone_summary(df_audit, df_plan, z, m)['plan'] for z in ZONES),
                    'audit': sum(compute_zone_summary(df_audit, df_plan, z, m)['audit'] for z in ZONES),
                    'qual': sum(compute_zone_summary(df_audit, df_plan, z, m)['qual'] for z in ZONES),
                    'anomaly': sum(compute_zone_summary(df_audit, df_plan, z, m)['anomaly'] for z in ZONES),
                    'rate': 0,
                }
                total_a = s['audit']
                s['rate'] = round(s['qual'] / total_a * 100, 1) if total_a > 0 else 0.0
            else:
                s = compute_zone_summary(df_audit, df_plan, zone_name, m)
            month_cache[(zone_name, m)] = s
    
    # 构建每月数据
    for m in MONTHS:
        zd[m] = {}
        all_zone_names = ['全部'] + ZONES
        
        for zone_name in all_zone_names:
            print(f"  {m} / {zone_name}...")
            
            # 获取该月数据
            all_prov_stats = compute_province_stats(df_audit, df_plan, m)
            
            # 获取上月数据（用于环比）
            m_idx = MONTHS.index(m)
            if m_idx > 0:
                prev_m = MONTHS[m_idx - 1]
                prev_summary = month_cache.get((zone_name, prev_m))
            else:
                prev_summary = None
            
            # 计算环比
            if zone_name == '全部':
                current_summary = month_cache[(zone_name, m)]
            else:
                current_summary = compute_zone_summary(df_audit, df_plan, zone_name, m)
            
            kpi_huanbi = [0.0, 0.0, 0.0, 0.0]
            if prev_summary:
                kpi_huanbi = [
                    compute_huanbi(current_summary['plan'], prev_summary['plan']),
                    compute_huanbi(current_summary['audit'], prev_summary['audit']),
                    compute_huanbi(current_summary['anomaly'], prev_summary['anomaly']),
                    compute_rate_huanbi(current_summary['rate'], prev_summary['rate']),
                ]
            
            # 构建 zone data
            zone_data = build_zone_data(
                df_audit, df_plan, zone_name, month=m,
                prev_month_data=prev_summary,
                all_prov_stats=all_prov_stats,
            )
            
            # 覆盖 kpi_huanbi（因为 build_zone_data 内部的计算方式不同）
            zone_data['kpi_huanbi'] = kpi_huanbi
            
            zd[m][zone_name] = zone_data
    
    # 构建全年数据
    print("  全年 / ...")
    zd['全年'] = {}
    for zone_name in ['全部'] + ZONES:
        print(f"  全年 / {zone_name}...")
        
        all_prov_stats = compute_province_stats(df_audit, df_plan, None)  # 全年
        
        zone_data = build_zone_data(
            df_audit, df_plan, zone_name, month=None,
            prev_month_data=None,
            all_prov_stats=all_prov_stats,
        )
        zone_data['kpi_huanbi'] = [0.0, 0.0, 0.0, 0.0]  # 全年无环比
        
        zd['全年'][zone_name] = zone_data
    
    return zd

def extract_template(html_path):
    """提取 HTML 模板（ZD 之前的部分和之后的部分）"""
    print("提取 HTML 模板...")
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    zd_start = content.find('var ZD =')
    zd_json_start = content.find('{', zd_start)
    
    # 找到 ZD JSON 的结束位置
    brace_count = 0
    i = zd_json_start
    while i < len(content):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                break
        i += 1
    
    zd_end = i + 1
    # 找到 </script> 结束标签
    script_end = content.find('</script>', zd_end)
    
    # 模板前半部分：从开头到 var ZD = （包含 <script>\n）
    template_before = content[:zd_start]
    # 模板后半部分：从 </script> 到结尾
    template_after = content[script_end:]
    
    print(f"  模板前半部分: {len(template_before)} 字符")
    print(f"  模板后半部分: {len(template_after)} 字符")
    
    return template_before, template_after

def generate_html(zd, template_before, template_after):
    """组装完整 HTML"""
    print("组装 HTML...")
    
    zd_json = json.dumps(zd, ensure_ascii=False, separators=(',', ':'), cls=NpEncoder)
    
    html = template_before + 'var ZD = ' + zd_json + template_after
    
    return html

def main():
    print(f"=== 市场稽核部重点工作看板生成器 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 加载数据
    df_audit, df_plan, df_summary = load_data()
    
    # 构建 ZD
    zd = build_zd(df_audit, df_plan)
    
    # 验证数据
    print("\n=== 数据验证 ===")
    # 对比 1月/全部 数据
    zd_1_all = zd['1月']['全部']
    print(f"1月/全部: plan={zd_1_all['kpi_monthly'][0]}, audit={zd_1_all['kpi_monthly'][1]}, anomaly={zd_1_all['kpi_monthly'][2]}, rate={zd_1_all['kpi_monthly'][3]}")
    # 原始 ZD: [1805, 232, 2, 99.1]
    
    # 提取模板
    template_before, template_after = extract_template(HTML_TEMPLATE_PATH)
    
    # 生成 HTML
    html = generate_html(zd, template_before, template_after)
    
    # 写入输出
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    
    sys.stdout.reconfigure(encoding='utf-8')
    print(f"\n生成完成: {OUTPUT_PATH}")
    print(f"   文件大小: {len(html):,} 字符")

if __name__ == '__main__':
    main()
