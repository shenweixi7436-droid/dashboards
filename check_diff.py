import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

EXCEL = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'
df = pd.read_excel(EXCEL, sheet_name='稽核明细-汇总')

# 稽核结果 vs 最终结果 不一致的行
diff = df[df['稽核结果'] != df['最终结果']]
print(f'不一致的行数: {len(diff)}')
if len(diff) > 0:
    print('\n不一致的明细:')
    print(diff[['战区清洗', '省区清洗-按最新', '稽核月份', '稽核结果', '最终结果']].to_string())
