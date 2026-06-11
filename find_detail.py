import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\shenw\github-dashboards\陈列稽核看板-0611-0951.html', 'r', encoding='utf-8') as f:
    content = f.read()
# 找 Card2 详情弹窗 - openDetail(2) 或 detail-2
idx = content.find('detail-2')
if idx < 0:
    idx = content.find('openDetail(2)')
print(content[max(0,idx-100):idx+300])
