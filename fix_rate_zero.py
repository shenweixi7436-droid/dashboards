import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\shenw\github-dashboards\generate_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换所有 rate 的 0.0 fallback 为 100.0（仅限 rate 相关的）
content = content.replace(
    "ps_sum['rate'] = round(ps_sum['qual'] / ps_sum['audit'] * 100, 1) if ps_sum['audit'] > 0 else 0.0",
    "ps_sum['rate'] = round(ps_sum['qual'] / ps_sum['audit'] * 100, 1) if ps_sum['audit'] > 0 else 100.0"
)

with open(r'C:\Users\shenw\github-dashboards\generate_v2.py', 'w', encoding='utf-8') as f:
    f.write(content)

# 验证没有残留的 rate ... else 0.0
count = content.count("else 0.0")
print(f'Remaining "else 0.0": {count}')
# 确认 rate ... else 100.0
count2 = content.count("else 100.0")
print(f'"else 100.0" count: {count2}')
