import sys
sys.stdout.reconfigure(encoding='utf-8')

html = open(r'C:\Users\shenw\github-dashboards\陈列稽核看板.html', 'r', encoding='utf-8').read()

after_start = html.find(';', html.find('var ZD ='))
after = html[after_start:]

# 找 refreshAll 函数
pos = after.find('function refreshAll')
if pos < 0:
    pos = after.find('refreshAll=function')
if pos < 0:
    pos = after.find('function refreshAll')

# 找完整函数体
func_start = after.find('{', pos)
bc = 0; i = func_start
while i < len(after):
    if after[i] == '{': bc += 1
    elif after[i] == '}': bc -= 1
    if bc == 0: break
    i += 1

print("=== refreshAll ===")
print(after[pos:i+1])
