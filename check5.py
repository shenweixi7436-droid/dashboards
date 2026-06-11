import sys
sys.stdout.reconfigure(encoding='utf-8')
html = open(r'C:\Users\shenw\github-dashboards\index.html', 'r', encoding='utf-8').read()

# 找按钮位置
btn_pos = html.find('陈列稽核看板')
print(f'按钮位置: {btn_pos}')
if btn_pos > 0:
    # 看看周围内容
    start = max(0, btn_pos - 300)
    end = min(len(html), btn_pos + 300)
    print(repr(html[start:end]))
