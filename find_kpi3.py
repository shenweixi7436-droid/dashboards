import sys
sys.stdout.reconfigure(encoding='utf-8')
# 找KPI3在陈列看板中的位置
with open(r'C:\Users\shenw\github-dashboards\陈列稽核看板-0611-0951.html', 'r', encoding='utf-8') as f:
    content = f.read()
idx = content.find('id="kpi3"')
if idx < 0:
    idx = content.find('kpi3')
print(content[max(0,idx-300):idx+150])
