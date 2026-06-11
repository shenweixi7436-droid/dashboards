import sys, re, json
sys.stdout.reconfigure(encoding='utf-8')
html = open(r'C:\Users\shenw\github-dashboards\index.html', 'r', encoding='utf-8').read()
print(f'文件大小: {len(html)} 字符')

zd_match = re.search(r'var ZD\s*=\s*(\{.*?\});', html, re.DOTALL)
if zd_match:
    zd = json.loads(zd_match.group(1))
    months = list(zd.keys())
    print(f'月份: {months}')
    jun = zd.get('6月', {}).get('全部', {})
    print(f'6月 kpi_monthly: {jun.get("kpi_monthly")}')
    print(f'6月 top5: {jun.get("top5")}')
    print(f'6月 rate_top5: {jun.get("rate_top5")}')
    print(f'6月 result_items: {jun.get("result_items")}')
    print(f'6月 reg_detail count: {len(jun.get("reg_detail", []))}')
    print(f'6月 trend_points count: {len(jun.get("trend_points", []))}')
    print(f'6月 audit_details count: {len(jun.get("audit_details", []))}')
    print(f'6月 issue_details count: {len(jun.get("issue_details", []))}')
    
    ann = zd.get('全年', {}).get('全部', {})
    print(f'\n全年 kpi_monthly: {ann.get("kpi_monthly")}')
    print(f'全年 reg_detail count: {len(ann.get("reg_detail", []))}')
    print(f'全年 audit_details count: {len(ann.get("audit_details", []))}')
    
    # 检查战区
    jun_zones = list(zd.get('6月', {}).keys())
    print(f'6月战区: {jun_zones}')
else:
    print('ERROR: 没有找到 ZD 数据!')

if 'function refreshAll' in html:
    print('\nOK: JS交互逻辑完整')
if 'echarts' in html.lower():
    print('OK: ECharts 引用完整')
style_match = re.search(r'<style[^>]*>.*?</style>', html, re.DOTALL)
if style_match:
    print(f'OK: CSS完整 ({len(style_match.group(0))} 字符)')
