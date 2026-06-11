import sys, json
sys.stdout.reconfigure(encoding='utf-8')
html = open(r'C:\Users\shenw\github-dashboards\陈列稽核看板.html', 'r', encoding='utf-8').read()
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
    print(m + '/全部: kpi=' + str(km) + ' invest=' + str(d.get('progress_current',{}).get('plan_q','?')))
