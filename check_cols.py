import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

df = pd.read_excel(r'C:\Users\shenw\Desktop\新建文件夹\稽核与计划明细-2026年年度.xlsx', sheet_name='稽核明细-汇总')
print("列名:")
for i, col in enumerate(df.columns):
    print(f"  [{i}] {col}")

# 看看有没有"经销商"或"执行人"相关的列
for col in df.columns:
    if any(k in str(col) for k in ['经销商', '执行', '名称', '门店', '店']):
        print(f"\n匹配列: [{col}]")
        print(df[col].head(10).tolist())
