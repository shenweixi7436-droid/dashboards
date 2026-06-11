import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\shenw\github-dashboards\陈列稽核看板-0611-0951.html', 'r', encoding='utf-8') as f:
    content = f.read()
# 从 switchMonth 开始
idx = content.find('function switchMonth')
section = content[idx:idx+5000]
# 搜索 kpi
import re
matches = [(m.start(), section[m.start():m.start()+100]) for m in re.finditer(r'kpi\d', section)]
for pos, snippet in matches:
    print(f"pos={pos}: {snippet}")
    print("---")
