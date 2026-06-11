import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

EXCEL = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'
df_audit = pd.read_excel(EXCEL, sheet_name='稽核明细-汇总')
df_plan = pd.read_excel(EXCEL, sheet_name='计划明细-汇总')

print('=== 稽核明细 列名 ===')
print(list(df_audit.columns))
print('\n前3行:')
print(df_audit.head(3).to_string())

print('\n=== 计划明细 列名 ===')
print(list(df_plan.columns))
print('\n前3行:')
print(df_plan.head(3).to_string())

# 确认稽核结果列值
print('\n稽核结果唯一值:', df_audit['稽核结果'].unique())
# 确认是否为稽核目标列值
print('是否为稽核目标唯一值:', df_plan['是否为稽核目标'].unique())
# 1月投入费用门店数(是)
m1_plan = df_plan[df_plan['月份'] == '1月']
invest_yes = len(m1_plan[m1_plan['是否为稽核目标'] == '是'])
print('\n1月 是否为稽核目标=是:', invest_yes, '行')
# 1月稽核数
m1_audit = df_audit[df_audit['稽核月份'] == '1月']
print('1月 稽核数:', len(m1_audit), '行')
# 1月完成率
rate = len(m1_audit) / (invest_yes * 0.2) * 100
print('1月 完成率:', round(rate, 1), '%')
# 1月合格率
qual = len(m1_audit[m1_audit['稽核结果'] == '合格'])
print('1月 合格数:', qual, '合格率:', round(qual/len(m1_audit)*100, 1), '%')
