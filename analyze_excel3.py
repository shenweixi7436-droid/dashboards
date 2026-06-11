import json, sys, warnings
sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd

excel_path = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'

df_audit = pd.read_excel(excel_path, sheet_name='稽核明细-汇总')

# Check relationship between 最终结果 and 稽核结果
print("=== 最终结果 vs 稽核结果 ===")
print(df_audit[['最终结果', '稽核结果']].value_counts(dropna=False))

# What does '有待改进' and '待定' mean? 
# In original ZD: result_items has 合格, 不合格, 虚假
# Let's check how many rows per result
print("\n=== 最终结果 value counts ===")
print(df_audit['最终结果'].value_counts(dropna=False))

print("\n=== 稽核结果 value counts ===")
print(df_audit['稽核结果'].value_counts(dropna=False))

# The ZD only has 合格/不合格/虚假 - no '有待改进' or '待定'
# Let's check what the original ZD's 1月/全部/result_items says
# 合格 230, 不合格 2 → total 232 for 1月/全部
# Let's count:
df_1 = df_audit[df_audit['稽核月份'] == '1月']
print(f"\n1月 total rows: {len(df_1)}")
print("1月 最终结果:")
print(df_1['最终结果'].value_counts(dropna=False))
print("1月 稽核结果:")
print(df_1['稽核结果'].value_counts(dropna=False))

# Wait - the original ZD says 1月/全部 has 232 audits, 230 qualified, 2 unqualified
# Let's check: 230+2 = 232 ✓ but df says len=1438 for all months
# The column used for the "result" is 最终结果 
print(f"\n1月 rows with 最终结果='合格': {(df_1['最终结果']=='合格').sum()}")
print(f"1月 rows with 最终结果='不合格': {(df_1['最终结果']=='不合格').sum()}")
print(f"1月 rows with 最终结果='虚假': {(df_1['最终结果']=='虚假').sum()}")
print(f"1月 rows with 最终结果='有待改进': {(df_1['最终结果']=='有待改进').sum()}")
print(f"1月 rows with 最终结果='待定': {(df_1['最终结果']=='待定').sum()}")

# Check 计划明细 - month and province mapping
df_plan = pd.read_excel(excel_path, sheet_name='计划明细-汇总')
print(f"\n=== 计划明细 省区清洗-按最新 unique ===")
print(df_plan['省区清洗-按最新'].unique().tolist())

print(f"\n=== 计划明细 战区清洗 unique ===")
print(df_plan['战区清洗'].unique().tolist())

# Check counts per month for plan
print(f"\n=== 计划 counts per month ===")
for m in ['1月','2月','3月','4月','5月','6月']:
    cnt = len(df_plan[df_plan['月份'] == m])
    print(f"  {m}: {cnt} rows")

# Check 是否为稽核目标 values
print(f"\n=== 是否为稽核目标 values ===")
print(df_plan['是否为稽核目标'].value_counts(dropna=False))

# Check the 各战区稽核进汇总 for "全部" equivalent (年度合计)
df_summary = pd.read_excel(excel_path, sheet_name='各战区稽核进汇总')
annual = df_summary[df_summary['月份'] == '全年合计']
print(f"\n=== 年度合计 ===")
print(annual.to_string())

# Per month summary for all zones
print(f"\n=== 各战区稽核进 按月汇总 ===")
for m in ['1月','2月','3月','4月','5月','6月']:
    m_data = df_summary[df_summary['月份'] == m]
    total_audit = m_data['稽核数'].sum()
    total_qualified = m_data['合格数'].sum()
    total_unqual = m_data['不合格数'].sum()
    total_fake = m_data['虚假数'].sum()
    total_plan = m_data['陈列计划数'].sum()
    total_invest = m_data['投入费用门店数'].sum()
    print(f"  {m}: 计划={total_plan}, 稽核={total_audit}, 合格={total_qualified}, 不合格={total_unqual}, 虚假={total_fake}, 投入费用={total_invest}")

# Now verify against original ZD
print("\n=== VS Original ZD month_rows ===")
# ZD says: 1月 p=1805 a=232 q=230
# ZD says: 2月 p=1551 a=103 q=96
