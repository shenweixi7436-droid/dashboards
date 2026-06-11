import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\shenw\github-dashboards\generate_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 战区级 rate: 改回合格率 qual/audit
content = content.replace(
    'rate = round(audit_t / invest_t * 100, 1) if invest_t > 0 else 0.0',
    'rate = round(qual_t / audit_t * 100, 1) if audit_t > 0 else 0.0'
)

# 2. 省区级 rate: 改回合格率 qual/audit
content = content.replace(
    "rate = round(a / ps['invest'] * 100, 1) if ps['invest'] > 0 else 0.0",
    "rate = round(a_s['qual'] / a * 100, 1) if a > 0 else 0.0"
)

# 3. 全年汇总 zone summary rate: 改回合格率
content = content.replace(
    "zs['rate'] = round(zs['audit'] / zs['invest'] * 100, 1) if zs['invest'] > 0 else 0.0",
    "zs['rate'] = round(zs['qual'] / zs['audit'] * 100, 1) if zs['audit'] > 0 else 0.0"
)

# 4. 全年省区 ps_sum rate (2处): 改回合格率 qual/audit
old_lines = [
    "            ps_sum['invest'] = sum(cache.get(('prov', mm, prov), {}).get('invest', 0) for mm in MONTHS)\n            ps_sum['rate'] = round(ps_sum['audit'] / ps_sum['invest'] * 100, 1) if ps_sum['invest'] > 0 else 0.0\n",
]
new_lines = [
    "            ps_sum['rate'] = round(ps_sum['qual'] / ps_sum['audit'] * 100, 1) if ps_sum['audit'] > 0 else 0.0\n",
]
for old, new in zip(old_lines, new_lines):
    content = content.replace(old, new)

with open(r'C:\Users\shenw\github-dashboards\generate_v2.py', 'w', encoding='utf-8') as f:
    f.write(content)

# verify no audit/invest rate left in precompute
count = content.count('audit_t / invest_t')
print('Remaining audit/invest rate:', count)
count2 = content.count("a / ps['invest']")
print("Remaining a/ps['invest'] rate:", count2)
print('Done')
