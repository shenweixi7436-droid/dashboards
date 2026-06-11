import sys
sys.stdout.reconfigure(encoding='utf-8')

html = open(r'C:\Users\shenw\github-dashboards\陈列稽核看板.html', 'r', encoding='utf-8').read()

# 找主要的渲染函数 - 从 after 部分找 render 相关函数
after_start = html.find(';', html.find('var ZD ='))
after = html[after_start:]

# 找所有 function 定义
import re
funcs = re.findall(r'function\s+(\w+)\s*\(', after)
print("JS 函数列表:")
for f in funcs:
    print(f"  {f}")

# 找关键的渲染入口 - updateAll / render / switchMonth 等
for keyword in ['updateAll', 'switchMonth', 'renderMain', 'function updateAll', 'function switchMonth', 'function renderMain', '全年', 'month ==']:
    pos = after.find(keyword)
    if pos > 0:
        snippet = after[max(0,pos-30):pos+200]
        print(f"\n--- 找到 '{keyword}' (pos={pos}) ---")
        print(snippet)
