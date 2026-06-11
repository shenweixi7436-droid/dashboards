import sys
sys.stdout.reconfigure(encoding='utf-8')
html = open(r'C:\Users\shenw\github-dashboards\index.html', 'r', encoding='utf-8').read()

zd_pos = html.find('var ZD =')
print(f'var ZD position: {zd_pos}')
print(f'File size: {len(html)}')
print(f'Has refreshAll: {"refreshAll" in html}')
print(f'Has openDetail: {"openDetail" in html}')
print(f'Has renderDetail: {"renderDetail" in html}')
print(f'Has ECharts: {"echarts" in html}')

# Check what's right after var ZD
after_zd = html[zd_pos:zd_pos+200]
print(f'\nAfter var ZD: {repr(after_zd[:200])}')

# Check what's at the end
print(f'\nLast 200 chars: {repr(html[-200:])}')
