import sys
sys.stdout.reconfigure(encoding='utf-8')

# Use full precision for rate calculations
# 2月: 96/103 = 0.932038... 
# 3月: 221/298 = 0.741610...
# 4月: 261/308 = 0.847402...
# 5月: 384/393 = 0.977096...
# 6月: 85/104 = 0.817307...

rates = {
    '1月': 230/232,
    '2月': 96/103,
    '3月': 221/298,
    '4月': 261/308,
    '5月': 384/393,
    '6月': 85/104,
}

for m in ['1月','2月','3月','4月','5月','6月']:
    print(f"{m}: rate={rates[m]:.6f}, pct={rates[m]*100:.4f}")

# huanbi rate:
for i, m in enumerate(['2月','3月','4月','5月','6月']):
    prev_m = ['1月','2月','3月','4月','5月'][i]
    huanbi = (rates[m] - rates[prev_m]) * 100
    print(f"{m} huanbi_rate = ({rates[m]:.6f} - {rates[prev_m]:.6f}) * 100 = {huanbi:.1f}")

# ZD values: 2月=-6.0, 3月=-20.4, 4月=14.2, 5月=15.3, 6月=-16.4
# My computed: 2月=-6.0, 3月=-19.0, 4月=10.5, 5月=13.0, 6月=-16.0
# Still doesn't match exactly for 3月, 4月, 5月

# Wait - let me check if the anomaly count is 不合格+虚假 or something else
# For kpi_monthly[2], the ZD shows:
# 1月: 2 → 不合格=2, 虚假=0 → sum=2 ✓
# 2月: 7 → 不合格=7, 虚假=0 → sum=7 ✓
# 3月: 77 → 不合格=75, 虚假=2 → sum=77 ✓

# But wait - top5 for 3月/全部:
# 安徽 v=154, pct=100.0 - this doesn't match raw data which shows 安徽 3月 audit=154 ✓
# But the pct here is 100.0, meaning 154 are all qualified? Let me check:
# 合格=154? But ZD kpi says 3月 total qualified=221. If 安徽 has 154 qualified, that's a lot.

# Actually top5.pct seems to be the 合格率 for that province, not the percentage of total
# 浙江 1月: v=32, pct=100.0 → 浙江 had 32 audits, 100% qualified → all 32 passed
# This is the province 合格率

# Now back to rate huanbi. Let me check with MORE precision
import math

r1 = 230/232  # 1月
r2 = 96/103   # 2月
r3 = 221/298  # 3月
r4 = 261/308  # 4月
r5 = 384/393  # 5月
r6 = 85/104   # 6月

print(f"\n3月 huanbi = ({r3:.10f} - {r2:.10f}) * 100 = {(r3-r2)*100:.1f}")
print(f"4月 huanbi = ({r4:.10f} - {r3:.10f}) * 100 = {(r4-r3)*100:.1f}")
print(f"5月 huanbi = ({r5:.10f} - {r4:.10f}) * 100 = {(r5-r4)*100:.1f}")
print(f"6月 huanbi = ({r6:.10f} - {r5:.10f}) * 100 = {(r6-r5)*100:.1f}")

# ZD: 3月=-20.4, 4月=14.2, 5月=15.3, 6月=-16.4
# My:    3月=-19.0, 4月=10.5, 5月=13.0, 6月=-16.0

# Hmm, these still don't match. The difference is getting bigger.
# Maybe the rate huanbi uses (合格数/稽核数) for each month differently?
# Or maybe it uses the per-zone summary rates?

# Let me try a completely different approach:
# Maybe rate huanbi = (合格率_this - 合格率_prev), where 合格率 is the displayed value (rounded to 1 decimal)
r1d = round(r1*100, 1)  # 99.1
r2d = round(r2*100, 1)  # 93.2
r3d = round(r3*100, 1)  # 74.2
r4d = round(r4*100, 1)  # 84.7
r5d = round(r5*100, 1)  # 97.7
r6d = round(r6*100, 1)  # 81.7

print(f"\nUsing rounded rates:")
print(f"2月: {r2d} - {r1d} = {r2d - r1d}")
print(f"3月: {r3d} - {r2d} = {r3d - r2d}")
print(f"4月: {r4d} - {r3d} = {r4d - r3d}")
print(f"5月: {r5d} - {r4d} = {r5d - r4d}")
print(f"6月: {r6d} - {r5d} = {r6d - r5d}")
# ZD: -6.0, -20.4, 14.2, 15.3, -16.4
# Rounded diff: -5.9, -19.0, 10.5, 13.0, -16.0
# Still doesn't match!

# Wait - the ZD 6月 kpi_huanbi[-16.4] ≈ my rounded [-16.0]. Let me check with more decimal places:
print(f"\nMore precise:")
print(f"6月 rate diff: {r6d} - {r5d} = {r6d - r5d:.1f}")
# 81.7 - 97.7 = -16.0

# Maybe the ZD uses the actual rate from the summary sheet?
# Summary 6月 合格率 = 85/104 = 0.8173076... 
# But ZD kpi_monthly[3] = 81.7
# So ZD uses round(合格/稽核 * 100, 1) = 81.7

# Hmm... let me try using the summary sheet's exact 合格率:
# From summary (年度合计):
# 1月: 0.991379 → 99.1
# 2月: 0.932039 → 93.2  (wait, raw is 96/103=0.9320388... summary says 0.932039)
# 3月: 0.741611 → 74.2  (raw 221/298=0.7416107... summary says 0.741611)
# So the summary uses the same raw calculation

# Let me try yet another formula: 
# rate_huanbi = (this合格数/this稽核数 - prev合格数/prev稽核数) * 100
# Using the per-zone rates somehow?

# OR maybe rate huanbi isn't a simple difference but percentage change:
# 4月: (84.7-74.2)/74.2*100 = 14.15 → 14.2 ✓✓✓
# 3月: (74.2-93.2)/93.2*100 = -20.39 → -20.4 ✓✓✓
# 5月: (97.7-84.7)/84.7*100 = 15.35 → 15.3 ✓✓✓
# 2月: (93.2-99.1)/99.1*100 = -5.95 → -6.0 ✓✓✓
# 6月: (81.7-97.7)/97.7*100 = -16.37 → -16.4 ✓✓✓

print(f"\n=== PERCENTAGE CHANGE formula ===")
print(f"2月: ({r2d}-{r1d})/{r1d}*100 = {(r2d-r1d)/r1d*100:.1f}")
print(f"3月: ({r3d}-{r2d})/{r2d}*100 = {(r3d-r2d)/r2d*100:.1f}")
print(f"4月: ({r4d}-{r3d})/{r3d}*100 = {(r4d-r3d)/r3d*100:.1f}")
print(f"5月: ({r5d}-{r4d})/{r4d}*100 = {(r5d-r4d)/r4d*100:.1f}")
print(f"6月: ({r6d}-{r5d})/{r5d}*100 = {(r6d-r5d)/r5d*100:.1f}")
print("ZD: -6.0, -20.4, 14.2, 15.3, -16.4")
