import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

EXCEL = r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx'
df = pd.read_excel(EXCEL, sheet_name='稽核明细-汇总')

print('各稽核结果数量:')
print(df['稽核结果'].value_counts(dropna=False))
print('\n"有待改进"的行数:', len(df[df['稽核结果'] == '有待改进']))
