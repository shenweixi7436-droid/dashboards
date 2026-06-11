import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\shenw\github-dashboards\陈列稽核看板-0611-0951.html', 'r', encoding='utf-8') as f:
    content = f.read()
# 找 <div class="kr" 后面一点
idx = content.find('class="kr"')
snippet = content[idx:idx+500]
print(snippet)
