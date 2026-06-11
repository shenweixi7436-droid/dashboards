import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\shenw\github-dashboards\generate_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()
old = 'month is None'
new = 'month is None or month == "\u5168\u5e74"'
content = content.replace(old, new)
with open(r'C:\Users\shenw\github-dashboards\generate_v2.py', 'w', encoding='utf-8') as f:
    f.write(content)
count = content.count('month is None or month == ')
print('Replaced count:', count)
