import sys
sys.stdout.reconfigure(encoding='utf-8')
html = open(r'C:\Users\shenw\github-dashboards\index.html', 'r', encoding='utf-8').read()

# 找所有"陈列稽核"
import re
positions = [m.start() for m in re.finditer('陈列稽核', html)]
print(f'共 {len(positions)} 处')
for i, p in enumerate(positions):
    start = max(0, p - 150)
    end = min(len(html), p + 150)
    print(f'\n--- 第{i+1}处 (pos={p}) ---')
    print(repr(html[start:end]))
