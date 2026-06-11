import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\shenw\Documents\New project\市场稽核部重点工作看板-06101350.html', 'r', encoding='utf-8') as f:
    content = f.read()

zd_start = content.find('var ZD =')
zd_end = content.find('</script>', zd_start)

print(f"ZD starts at char: {zd_start}")
print(f"ZD </script> at char: {zd_end}")

# Show chars around ZD
print(f"\n--- 100 chars before ZD ---")
print(content[zd_start-100:zd_start])

print(f"\n--- 200 chars after ZD </script> ---")
print(content[zd_end:zd_end+200])

# Parse ZD
zd_json_start = content.find('{', zd_start)
brace_count = 0
i = zd_json_start
while i < len(content):
    if content[i] == '{':
        brace_count += 1
    elif content[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            break
    i += 1

zd_text = content[zd_json_start:i+1]
zd = json.loads(zd_text)

print(f"\nMonths: {list(zd.keys())}")

# Province mapping from 1月
first_month = '1月'
if first_month in zd:
    print(f"\nZones for {first_month}: {list(zd[first_month].keys())}")
    for zone_name, zone_data in zd[first_month].items():
        if zone_name != '全部' and 'reg_detail' in zone_data:
            provs = [r['name'] for r in zone_data['reg_detail']]
            print(f"  {zone_name}: {provs}")

# Also from 全年
if '全年' in zd:
    print(f"\nZones for 全年: {list(zd['全年'].keys())}")
    for zone_name, zone_data in zd['全年'].items():
        if zone_name != '全部' and 'reg_detail' in zone_data:
            provs = [r['name'] for r in zone_data['reg_detail']]
            print(f"  {zone_name}: {provs}")

# Show structure of a single zone entry
print(f"\n--- Sample zone data keys ({first_month}/全部) ---")
all_data = zd[first_month]['全部']
print(f"Keys: {list(all_data.keys())}")

# Show sample of reg_detail
print(f"\nSample reg_detail:")
for r in all_data.get('reg_detail', [])[:3]:
    print(f"  {r}")

print(f"\nSample month_rows:")
for r in all_data.get('month_rows', [])[:3]:
    print(f"  {r}")

print(f"\nSample trend_points:")
for r in all_data.get('trend_points', [])[:5]:
    print(f"  {r}")

print(f"\nSample progress_items:")
for r in all_data.get('progress_items', [])[:3]:
    print(f"  {r}")

print(f"\nprogress_current: {all_data.get('progress_current')}")

print(f"\nSample result_items: {all_data.get('result_items')}")

print(f"\nSample target_items: {all_data.get('target_items')}")

print(f"\nSample audit_details:")
for r in all_data.get('audit_details', [])[:3]:
    print(f"  {r}")

print(f"\nSample issue_details:")
for r in all_data.get('issue_details', [])[:3]:
    print(f"  {r}")

print(f"\nSample issue_rank:")
for r in all_data.get('issue_rank', [])[:5]:
    print(f"  {r}")

print(f"\nSample province_progress:")
for r in all_data.get('province_progress', [])[:3]:
    print(f"  {r}")

# Save the ZD data for reference
with open(r'C:\Users\shenw\github-dashboards\zd_original.json', 'w', encoding='utf-8') as f:
    json.dump(zd, f, ensure_ascii=False, indent=2)
print(f"\nSaved ZD to zd_original.json")
