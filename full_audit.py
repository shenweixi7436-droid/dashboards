import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import json

EXCEL = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'
df_audit = pd.read_excel(EXCEL, sheet_name='稽核明细-汇总')
df_plan = pd.read_excel(EXCEL, sheet_name='计划明细-汇总')

print('=== 基础数据 ===')
print(f'稽核明细总行数: {len(df_audit)}')
print(f'计划明细总行数: {len(df_plan)}')
print(f'稽核月份唯一值: {sorted(df_audit["稽核月份"].dropna().unique())}')
print(f'计划月份唯一值: {sorted(df_plan["月份"].dropna().unique())}')

# F列（最终结果）统计
print('\n=== F列（最终结果）统计 ===')
print(df_audit['最终结果'].value_counts(dropna=False))

# 逐月统计
print('\n=== 逐月详细统计 ===')
for m in ['1月','2月','3月','4月','5月','6月']:
    a = df_audit[df_audit['稽核月份'] == m]
    p = df_plan[df_plan['月份'] == m]
    invest_yes = len(p[p['是否为稽核目标'] == '是'])
    total_plan = len(p)
    
    qual = len(a[a['最终结果'] == '合格'])
    unqual = len(a[a['最终结果'] == '不合格'])
    fake = len(a[a['最终结果'] == '虚假'])
    anomaly = unqual + fake
    total_audit = len(a)
    rate = round(qual / total_audit * 100, 1) if total_audit > 0 else 0.0
    completion = round(total_audit / (invest_yes * 0.2) * 100, 1) if invest_yes > 0 else 0.0
    
    print(f'{m}: 计划总数={total_plan}, 投入费用门店={invest_yes}, '
          f'稽核数={total_audit}, 合格={qual}, 不合格={unqual}, 虚假={fake}, '
          f'异常={anomaly}, 合格率={rate}%, 完成率={completion}%')

# 全年
invest_all = len(df_plan[df_plan['是否为稽核目标'] == '是'])
plan_all = len(df_plan)
qual_all = len(df_audit[df_audit['最终结果'] == '合格'])
unqual_all = len(df_audit[df_audit['最终结果'] == '不合格'])
fake_all = len(df_audit[df_audit['最终结果'] == '虚假'])
audit_all = len(df_audit)
rate_all = round(qual_all / audit_all * 100, 1)
completion_all = round(audit_all / (invest_all * 0.2) * 100, 1)
print(f'全年: 计划总数={plan_all}, 投入费用门店={invest_all}, '
      f'稽核数={audit_all}, 合格={qual_all}, 不合格={unqual_all}, 虚假={fake_all}, '
      f'异常={unqual_all+fake_all}, 合格率={rate_all}%, 完成率={completion_all}%')
