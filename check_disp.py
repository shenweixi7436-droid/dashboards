import sys, re
sys.stdout.reconfigure(encoding='utf-8')

html = open(r'C:\Users\shenw\github-dashboards\陈列稽核看板.html', 'r', encoding='utf-8').read()

# 找 renderAuditStoreDetail 和 renderIssueStoreDetail 函数
for func_name in ['renderAuditStoreDetail', 'renderIssueStoreDetail', 'openDetail', 'renderProvinceAuditProgress', 'renderProvinceRateDetail']:
    pos = html.find(func_name)
    if pos > 0:
        # 找到函数体
        brace_start = html.find('{', pos)
        brace_count = 0; i = brace_start
        while i < len(html):
            if html[i] == '{': brace_count += 1
            elif html[i] == '}':
                brace_count -= 1
                if brace_count == 0: break
            i += 1
        print(f"\n=== {func_name} ({pos}) ===")
        print(html[pos:i+1])
