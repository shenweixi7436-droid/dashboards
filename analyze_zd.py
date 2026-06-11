import re

with open(r'C:\Users\shenw\Documents\New project\市场稽核部重点工作看板-06101350.html', 'r', encoding='utf-8') as f:
    content = f.read()

zd_start = content.find('var ZD =')
zd_end = content.find('</script>', zd_start)
js_end = content.find('</script>', zd_end + 1)

print(f"ZD starts at char: {zd_start}")
print(f"ZD </script> at char: {zd_end}")
print(f"JS </script> at char: {js_end}")

# Show the HTML right before ZD
print(f"\n--- 200 chars before ZD start ---")
print(repr(content[zd_start-200:zd_start]))

# Show the HTML right after ZD </script>
print(f"\n--- 300 chars after ZD </script> ---")
print(repr(content[zd_end:zd_end+300]))

# Show what comes after the JS </script> (end of file)
print(f"\n--- Last 500 chars of file ---")
print(repr(content[-500:]))

# Get the first line of ZD to see the structure
first_line_end = content.find('\n', zd_start)
print(f"\n--- First 500 chars of ZD ---")
print(content[zd_start:zd_start+500])

# Extract province names from "全部" zone
import json
# Try to parse the ZD data
zd_json_start = content.find('{', zd_start)
# Find matching brace
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

print(f"\nZD JSON object from {zd_json_start} to {i+1}")
zd_text = content[zd_json_start:i+1]
zd = json.loads(zd_text)

# Show months
print(f"Months: {list(zd.keys())}")
# Show zones for first month
first_month = list(zd.keys())[0]
print(f"Zones for {first_month}: {list(zd[first_month].keys())}")

# Extract province list from reg_detail of "全部" zone
all_zone = zd[first_month].get('全部', {})
if 'reg_detail' in all_zone:
    provinces = [r['name'] for r in all_zone['reg_detail']]
    print(f"Provinces in reg_detail ({first_month}): {provinces}")

# Check which zone each province belongs to
print("\nProvince-zone mapping:")
for month_name in ['1月', '6月', '全年']:
    if month_name not in zd:
        continue
    print(f"\n=== {month_name} ===")
    for zone_name, zone_data in zd[month_name].items():
        if zone_name == '全部':
            continue
        if 'reg_detail' in zone_data:
            provs = [r['name'] for r in zone_data['reg_detail']]
            print(f"  {zone_name}: {provs}")
