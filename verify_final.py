import sys, json
sys.stdout.reconfigure(encoding='utf-8')

for fname in ['重点工作看板.html', '陈列稽核看板.html']:
    html = open(r'C:\Users\shenw\github-dashboards\\' + fname, 'r', encoding='utf-8').read()
    zd_pos = html.find('var ZD =')
    zd_start = html.find('{', zd_pos)
    bc = 0; i = zd_start
    while i < len(html):
        if html[i] == '{': bc += 1
        elif html[i] == '}': bc -= 1
        if bc == 0: break
        i += 1
    zd = json.loads(html[zd_start:i+1])

    print('=== ' + fname + ' ===')
    for m in ['1月','6月','全年']:
        d = zd[m]['全部']
        km = d['kpi_monthly']
        pc = d.get('progress_current', {})
        print(m + ': kpi=[plan=' + str(km[0]) + ', audit=' + str(km[1]) + ', anomaly=' + str(km[2]) + ', 合格率=' + str(km[3]) + '%]')
        print('    完成率=' + str(pc.get('pct','?')) + '% invest=' + str(pc.get('plan_q','?')))
    print()
