import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

EXCEL = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'
df = pd.read_excel(EXCEL, sheet_name='稽核明细-汇总')

# F列 = index 5
print('F列（index 5）列名:', df.columns[5])
print('唯一值:', df.iloc[:, 5].unique())
print('各值数量:')
print(df.iloc[:, 5].value_counts(dropna=False))

# 对比: 稽核结果列（index 30）vs 最终结果列（index 5）的区别
print('\n最终结果 列值统计:')
print(df['最终结果'].value_counts(dropna=False))
print('\n两者是否相同:', df['最终结果'].equals(df.iloc[:, 5]))
