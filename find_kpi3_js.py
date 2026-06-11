import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\shenw\github-dashboards\陈列稽核看板-0611-0951.html', 'r', encoding='utf-8') as f:
    content = f.read()
# 找JS中 kpi3.textContent
idx = content.find("kpi3.textContent")
if idx < 0:
    idx = content.find("kpi3")
    # search from JS section
    idx = content.find("kpi3", idx+100)
print(content[max(0,idx-200):idx+100])
