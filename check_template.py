import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\shenw\github-dashboards\陈列稽核看板.html', 'r', encoding='utf-8') as f:
    content = f.read()

# kpi3 初始值
pos = content.find('id="kpi3"')
print('kpi3:', content[pos:pos+80])

# 进度条
pos2 = content.find('稽核完成率')
print('\nprogress:', content[pos2:pos2+200])

# card1 foot
pos3 = content.find('id="foot0"')
print('\nfoot0:', content[pos3:pos3+80])

# card2 title
pos4 = content.find('各省区合格率')
print('\ncard2 title:', content[pos4-50:pos4+80])

# reg_detail 表头
pos5 = content.find('稽核数</th><th>环比</th><th>合格率')
if pos5 < 0:
    pos5 = content.find('合格率</th>')
print('\ntable header:', content[max(0,pos5-80):pos5+40])
