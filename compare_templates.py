import sys, re
sys.stdout.reconfigure(encoding='utf-8')

# 读取两个模板
with open(r'C:\Users\shenw\github-dashboards\重点工作看板.html', 'r', encoding='utf-8') as f:
    main_html = f.read()
with open(r'C:\Users\shenw\github-dashboards\陈列稽核看板.html', 'r', encoding='utf-8') as f:
    disp_html = f.read()

# 找 var ZD 之前的部分（CSS+HTML结构）和之后的部分（JS函数）
def split_at_zd(html):
    zd_start = html.find('var ZD =')
    zd_json_start = html.find('{', zd_start)
    brace_count = 0; i = zd_json_start
    while i < len(html):
        if html[i] == '{': brace_count += 1
        elif html[i] == '}':
            brace_count -= 1
            if brace_count == 0: break
        i += 1
    zd_end = i + 1
    return html[:zd_start], html[zd_end:]

main_before, main_after = split_at_zd(main_html)
disp_before, disp_after = split_at_zd(disp_html)

print(f"主看板 before: {len(main_before)} 字符")
print(f"陈列看板 before: {len(disp_before)} 字符")
print(f"主看板 after: {len(main_after)} 字符")
print(f"陈列看板 after: {len(disp_after)} 字符")
print(f"before 是否相同: {main_before == disp_before}")
print(f"after 是否相同: {main_after == disp_after}")

if main_before != disp_before:
    # 找差异
    for i in range(min(len(main_before), len(disp_before))):
        if main_before[i] != disp_before[i]:
            print(f"\nbefore 首次差异位置: {i}")
            print(f"主看板: ...{repr(main_before[max(0,i-50):i+80])}...")
            print(f"陈列看板: ...{repr(disp_before[max(0,i-50):i+80])}...")
            break

if main_after != disp_after:
    for i in range(min(len(main_after), len(disp_after))):
        if main_after[i] != disp_after[i]:
            print(f"\nafter 首次差异位置: {i}")
            print(f"主看板: ...{repr(main_after[max(0,i-50):i+80])}...")
            print(f"陈列看板: ...{repr(disp_after[max(0,i-50):i+80])}...")
            break
