import sys, re, json
sys.stdout.reconfigure(encoding='utf-8')
html = open(r'C:\Users\shenw\github-dashboards\index.html', 'r', encoding='utf-8').read()

# 找 var ZD
pos = html.find('var ZD =')
print(f'var ZD position: {pos}')
print(f'Total file size: {len(html)}')

if pos > 0:
    # 读取后面一些内容
    snippet = html[pos:pos+500]
    print(f'\nSnippet after var ZD:')
    print(snippet)
    
    # 检查 JS
    has_refresh = 'refreshAll' in html
    has_detail = 'renderDetail' in html
    print(f'\nHas refreshAll: {has_refresh}')
    print(f'Has renderDetail: {has_detail}')
    
    # 检查末尾
    print(f'\nLast 100 chars: {repr(html[-100:])}')
