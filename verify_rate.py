import sys, json
sys.stdout.reconfigure(encoding='utf-8')
html = open(r'C:\Users\shenw\github-dashboards\重点工作看板.html', 'r', encoding='utf-8').read()
zd_pos = html.find('var ZD =')
zd_start = html.find('{', zd_pos)
bc = 0; i = zd_start
while i < len(html):
    if html[i] == '{': bc += 1
    elif html[i] == '}': bc -= 1
    if bc == 0: break
    i += 1
zd = json.loads(html[zd_start:i+1])

for m in ['1月','6月','全年']:
    d = zd[m]['全部']
    km = d['kpi_monthly']
    print(m + '/全部: plan=' + str(km[0]) + ', audit=' + str(km[1]) + ', anomaly=' + str(km[2]) + ', rate=' + str(km[3]))
    if d['top5']:
        for t in d['top5'][:3]:
            print('  top5: ' + t['n'] + ' audit=' + str(t['v']) + ' rate=' + str(t['pct']))
    # reg_detail 抽样
    for r in d['reg_detail'][:3]:
        print('  reg: ' + r['n'] + ' rate=' + str(r.get('rate','?')) + ' huanbi=' + str(r.get('huanbi','?')))
