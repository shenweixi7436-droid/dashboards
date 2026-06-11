import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, re

with open(r'C:\Users\shenw\github-dashboards\重点工作看板.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 验证1: zero-hint div是否存在
assert 'id="zero-hint"' in content, 'zero-hint div missing!'
print('✅ zero-hint div exists')

# 验证2: JS注入
assert 'zero_audit_provs' in content, 'JS injection missing!'
assert 'zero-hint-text' in content, 'zero-hint-text missing!'
print('✅ JS injection exists')

# 验证3: 检查数据中有zero_audit_provs
zd_start = content.find('var ZD =')
zd_json_start = content.find('{', zd_start)
# 只提取前几百个字符看结构
snippet = content[zd_json_start:zd_json_start+200]
print(f'ZD starts: {snippet[:100]}...')

# 提取完整的ZD
brace_count = 0; i = zd_json_start
while i < len(content):
    if content[i] == '{': brace_count += 1
    elif content[i] == '}':
        brace_count -= 1
        if brace_count == 0: break
    i += 1
zd = json.loads(content[zd_json_start:i+1])

# 检查各月各战区的zero_audit_provs
for m in ['1月','2月','3月','4月','5月','6月','全年']:
    for z in ['全部','区域经营部','山东战区','华北战区','华南战区','东北战区','华中战区']:
        zp = zd[m][z].get('zero_audit_provs', [])
        if zp:
            print(f'  {m}/{z}: zero_audit_provs={zp}')
