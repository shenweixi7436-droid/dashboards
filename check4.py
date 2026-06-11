import sys
sys.stdout.reconfigure(encoding='utf-8')
html = open(r'C:\Users\shenw\github-dashboards\index.html', 'r', encoding='utf-8').read()

# 找标题区域
hd = html.find('class="hd"')
print(f'hd class pos: {hd}')
if hd > 0:
    # 打印 hd 区域的HTML
    end = html.find('</div>', hd + 200)
    print(repr(html[hd-20:end+6]))
