import sys
sys.stdout.reconfigure(encoding='utf-8')
html = open(r'C:\Users\shenw\github-dashboards\index.html', 'r', encoding='utf-8').read()

# 找"陈列稽核"卡片
pos = html.find('陈列稽核')
print(f'位置: {pos}')
if pos > 0:
    start = max(0, pos - 200)
    end = min(len(html), pos + 200)
    print(repr(html[start:end]))
