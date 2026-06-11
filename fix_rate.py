import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\shenw\github-dashboards\generate_v2.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

old = "            ps_sum['rate'] = round(ps_sum['qual'] / ps_sum['audit'] * 100, 1) if ps_sum['audit'] > 0 else 0.0\n"
new = "            ps_sum['invest'] = sum(cache.get(('prov', mm, prov), {}).get('invest', 0) for mm in MONTHS)\n            ps_sum['rate'] = round(ps_sum['audit'] / ps_sum['invest'] * 100, 1) if ps_sum['invest'] > 0 else 0.0\n"

out = []
for line in lines:
    if line == old:
        out.append(new)
    else:
        out.append(line)

with open(r'C:\Users\shenw\github-dashboards\generate_v2.py', 'w', encoding='utf-8') as f:
    f.writelines(out)

print(f'Replaced {lines.count(old)} occurrences')
