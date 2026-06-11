import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\shenw\github-dashboards\zd_original.json', 'r', encoding='utf-8') as f:
    zd = json.load(f)

# rate_top5 details
print("=== rate_top5 samples ===")
for m in ['1月', '3月', '6月']:
    print(f"\n{m}/全部 rate_top5:")
    for r in zd[m]['全部']['rate_top5']:
        print(f"  {r}")

# top5 details
print("\n=== top5 samples ===")
for m in ['1月', '3月', '6月']:
    print(f"\n{m}/全部 top5:")
    for r in zd[m]['全部']['top5']:
        print(f"  {r}")

# Check what rate_top5 looks like when there's 0%合格率
# For 6月, some provinces have 0 audits
print("\n=== 6月/全部 rate_top5 ===")
for r in zd['6月']['全部']['rate_top5']:
    print(f"  {r}")

# rate_top5 has "v" as string "合格率" and "bw" as number value
# top5 has "pct" as number 合格率

# Check kpi_huanbi format - all numbers, 1位小数
print("\n=== kpi_huanbi for all months ===")
for m in ['1月','2月','3月','4月','5月','6月']:
    print(f"{m}: {zd[m]['全部']['kpi_huanbi']}")

# Verify huanbi calculation for 4月:
# 3月: plan=1935, audit=298, anomaly=77, rate=221/298=74.2
# 4月: plan=2190, audit=308, anomaly=47, rate=261/308=84.7
# huanbi_plan = (2190-1935)/1935*100 = 13.2
# huanbi_audit = (308-298)/298*100 = 3.4
# huanbi_anomaly = (47-77)/77*100 = -39.0
# huanbi_rate = (84.7-74.2) = 10.5
print(f"\nComputed 4月 huanbi: plan={round((2190-1935)/1935*100,1)}, audit={round((308-298)/298*100,1)}, anomaly={round((47-77)/77*100,1)}, rate={round(84.7-74.2,1)}")
print(f"ZD 4月 huanbi: {zd['4月']['全部']['kpi_huanbi']}")

# Check for 3月:
# 2月: plan=1551, audit=103, anomaly=7, rate=96/103=93.2
# 3月: plan=1935, audit=298, anomaly=77, rate=221/298=74.2
# anomaly huanbi = (77-7)/7*100 = 1000.0
# ZD says 1000.0 ✓
print(f"\nComputed 3月 huanbi: plan={round((1935-1551)/1551*100,1)}, audit={round((298-103)/103*100,1)}, anomaly={round((77-7)/7*100,1)}, rate={round(74.2-93.2,1)}")
print(f"ZD 3月 huanbi: {zd['3月']['全部']['kpi_huanbi']}")

# Now check: anomaly huanbi when prior month has 0 anomaly
# 1月: anomaly=2, 2月: anomaly=7
# huanbi = (7-2)/2*100 = 250.0 ✓
# When prior anomaly=0: what happens?
# Let me check month where anomaly goes from 0 to non-zero or vice versa
# 4月 anomaly=47, 5月 anomaly=9
# huanbi = (9-47)/47*100 = -80.9
print(f"\nComputed 5月 huanbi anomaly: {round((9-47)/47*100,1)}")
print(f"ZD 5月 huanbi: {zd['5月']['全部']['kpi_huanbi']}")

# Check 5月:
# 4月 rate=84.7, 5月 rate=384/393=97.7
# rate huanbi = 97.7-84.7 = 13.0
print(f"Computed 5月 rate huanbi: {round(97.7-84.7,1)}")

# Hmm but 2月 anomaly huanbi was (7-2)/2*100 = 250.0
# But what if 1月 anomaly was 0? We'd get division by zero
# So anomaly huanbi uses (current - prior) / prior * 100, and when prior=0, what?
