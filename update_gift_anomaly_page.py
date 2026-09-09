# -*- coding: utf-8 -*-
"""update_gift_anomaly_page.py — 线下活动与样品申请异常解读看板 原位数据更新器

数据源：C:/Users/shenw/Desktop/看板/费用分析-样品及活动.xlsx
  - sheet 线下活动试吃品申请单   → 活动Tab（副标题/KPI/金额&数量偏离表/图表/风险结论/筛选按钮）
  - sheet 线下样品申请单         → 样品Tab（KPI/SAMPLE_DATA/风险结论/筛选按钮）
  - sheet 线下活动执行费用核销单 → 核销Tab（VERIFY_DATA/风险结论/筛选按钮）

更新方式：对现有 HTML 做标记区块原位替换（首次运行自动打标记），不重建页面，
         保留字体、Tab、横幅删除等一切非数据改动。双写仓库部署位与 WorkBuddy 工作副本。

计算口径与 tmp/gen_data.py、tmp/gen_verify_data.py 保持一致（已验证还原）。
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

XLSX = Path(r"C:/Users/shenw/Desktop/看板/费用分析-样品及活动.xlsx")
REPO_PAGE = Path(r"C:/Users/shenw/Documents/New project/github-dashboards/assets/pages/线下活动与样品申请异常解读看板.html")
WB_PAGE = Path(r"C:/Users/shenw/WorkBuddy/2026-08-25-13-53-45/线下活动与样品申请异常解读看板.html")
BACKUP_DIR = Path(r"C:/Users/shenw/Documents/New project/github-dashboards/backups")

NA, AM, QT = "商品明细:商品名称", "商品明细:预估金额(元)", "商品明细:数量（单位：袋）"

# ============================================================
# 活动侧
# ============================================================

def load_activity(xlsx):
    df = pd.read_excel(xlsx, sheet_name="线下活动试吃品申请单", header=0)
    df = df[~df["标题"].astype(str).str.contains("经销商大会", na=False)].copy()

    def clean_name(n):
        if pd.isna(n):
            return ""
        n = str(n).strip()
        n = n.replace("皇家小虎", "").replace("小虎", "").replace("商用", "")
        return n[:14]

    rows = []
    for sid, g in df.groupby("流水号", sort=False):
        g2 = g.sort_values(AM, ascending=False, kind="mergesort")
        top = []
        for _, r in g2.head(3).iterrows():
            amt = r[AM]
            top.append(f"{clean_name(r[NA])}{'0元' if pd.isna(amt) else f'{amt:.0f}元'}")
        sausage_rows = g[g[NA].astype(str).str.contains("烤肠", na=False)]
        rows.append({
            "月份": int(g["月份"].iloc[0]),
            "流水号": str(sid).replace("XXHDSCPSQD-2026", "").replace("XXHDSCPSQD-", ""),
            "标题": str(g["标题"].iloc[0]),
            "申请时间": str(g["申请时间"].iloc[0])[:10],
            "产品数": len(g),
            "总金额": round(float(g[AM].sum()), 2),
            "含烤肠": len(sausage_rows) > 0,
            "主要构成": " · ".join(top),
        })
    return pd.DataFrame(rows)


def badge_of(prod, amt):
    if prod >= 20:
        return "大而全"
    if prod >= 10:
        return "多品项展会型" if amt >= 500 else "低金额多品项"
    return "多品项"


def month_span(months):
    if not months:
        return ""
    a, b = min(months), max(months)
    return f"{a}~{b}月" if a != b else f"{a}月"


def build_activity(agg):
    months = sorted(agg["月份"].unique().tolist())
    med_amt = {m: float(agg[agg["月份"] == m]["总金额"].median()) for m in months}
    med_qty = {m: float(agg[agg["月份"] == m]["产品数"].median()) for m in months}
    agg = agg.copy()
    agg["med_amt"] = agg["月份"].map(med_amt)
    agg["med_qty"] = agg["月份"].map(med_qty)
    agg["amt_dev"] = agg["总金额"] - agg["med_amt"]
    agg["amt_pct"] = (agg["amt_dev"] / agg["med_amt"] * 100).round(1)
    agg["qty_dev"] = agg["产品数"] - agg["med_qty"]
    agg["qty_pct"] = (agg["qty_dev"] / agg["med_qty"] * 100).round(1)

    amt_rows = agg[agg["amt_pct"].abs() >= 10].copy().sort_values(
        ["月份", "amt_pct"], ascending=[True, False])
    qty_rows = agg[agg["qty_dev"].abs() >= 1].copy().sort_values(
        ["月份", "qty_pct"], ascending=[True, False])
    qty_rows["badge"] = qty_rows.apply(
        lambda r: badge_of(int(r["产品数"]), float(r["总金额"])), axis=1)

    stats = {}
    for m in months:
        sub = agg[agg["月份"] == m]
        stats[m] = {
            "total": len(sub),
            "amt_n": len(amt_rows[amt_rows["月份"] == m]),
            "qty_n": len(qty_rows[qty_rows["月份"] == m]),
            "both_n": len(sub[(sub["amt_pct"].abs() >= 10) & (sub["qty_dev"].abs() >= 1)]),
            "big_n": len(sub[sub["amt_pct"].abs() >= 1000]),
            "prod20_n": len(sub[sub["产品数"] >= 20]),
            "sausage_n": len(sub[sub["含烤肠"] & (sub["总金额"] >= 2000)]),
            "lowprice_n": len(sub[(sub["产品数"] >= 10) & (sub["总金额"] < 500)]),
            "med_amt": med_amt[m], "med_qty": med_qty[m],
            "max_amt_pct": float(sub["amt_pct"].max()) if len(sub) else 0,
            "max_qty_dev": float(sub["qty_dev"].max()) if len(sub) else 0,
        }
    year = {
        "total": len(agg), "amt_sum": float(agg["总金额"].sum()),
        "amt_n": len(amt_rows), "qty_n": len(qty_rows),
        "both_n": len(agg[(agg["amt_pct"].abs() >= 10) & (agg["qty_dev"].abs() >= 1)]),
        "big_n": len(agg[agg["amt_pct"].abs() >= 1000]),
        "sausage_n": len(agg[agg["含烤肠"] & (agg["总金额"] >= 2000)]),
        "lowprice_n": len(agg[(agg["产品数"] >= 10) & (agg["总金额"] < 500)]),
        "prod20_n": len(agg[agg["产品数"] >= 20]),
    }
    return months, med_amt, med_qty, amt_rows, qty_rows, stats, year


def esc_attr(s):
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def act_amt_row_html(dfr, idx):
    cls = "" if idx < 3 else "hidden-row"
    m = int(dfr["月份"])
    dev = float(dfr["amt_dev"]); pct = float(dfr["amt_pct"])
    dev_s = f"+{dev:.1f}" if dev >= 0 else f"{dev:.1f}"
    pct_s = f"+{pct:.1f}%" if pct >= 0 else f"{pct:.1f}%"
    return (f'<tr class="{cls}" data-month="{m}">\n<td>{m}月</td>\n'
            f'<td>{dfr["med_amt"]:.1f}</td>\n'
            f'<td><span class="serial-link" data-title="{esc_attr(dfr["标题"])}">{dfr["流水号"]}</span></td>\n'
            f'<td>{dfr["申请时间"]}</td>\n<td>{int(dfr["产品数"])}</td>\n'
            f'<td><strong>{dfr["总金额"]:.1f}</strong></td>\n'
            f'<td class="red-text">{dev_s}</td>\n<td class="red-text">{pct_s}</td>\n'
            f'<td>{dfr["主要构成"]}</td>\n</tr>')


def act_qty_row_html(dfr, idx):
    cls = "" if idx < 3 else "hidden-row"
    m = int(dfr["月份"]); dev = int(dfr["qty_dev"]); pct = float(dfr["qty_pct"])
    dev_s = f"+{dev}" if dev >= 0 else f"{dev}"
    pct_s = f"+{pct:.1f}%" if pct >= 0 else f"{pct:.1f}%"
    return (f'<tr class="{cls}" data-month="{m}">\n<td>{m}月</td>\n'
            f'<td>{int(dfr["med_qty"])}</td>\n'
            f'<td><span class="serial-link" data-title="{esc_attr(dfr["标题"])}">{dfr["流水号"]}</span></td>\n'
            f'<td>{dfr["申请时间"]}</td>\n<td><strong>{int(dfr["产品数"])}</strong></td>\n'
            f'<td>{dfr["总金额"]:.1f}</td>\n'
            f'<td class="red-text">{dev_s}</td>\n<td class="red-text">{pct_s}</td>\n'
            f'<td><span class="badge badge-orange">{dfr["badge"]}</span></td>\n</tr>')


def act_kpi_grid_html(months, stats, year):
    h = ['<div class="kpi-card" data-months="all"><div class="kpi-value">'
         f'{year["total"]}</div><div class="kpi-label">总活动场次</div></div>',
         '<div class="kpi-card" data-months="all"><div class="kpi-value">'
         f'{year["amt_sum"]/10000:.1f}万</div><div class="kpi-label">申请总金额(元)</div></div>',
         '<div class="kpi-card" data-months="all"><div class="kpi-value">'
         f'{year["amt_n"]}</div><div class="kpi-label">金额异常场数</div></div>',
         '<div class="kpi-card" data-months="all"><div class="kpi-value">'
         f'{year["qty_n"]}</div><div class="kpi-label">数量异常场数</div></div>',
         '<div class="kpi-card" data-months="all"><div class="kpi-value">'
         f'{year["both_n"]}</div><div class="kpi-label">双维度命中</div></div>',
         '<div class="kpi-card" data-months="all"><div class="kpi-value">'
         f'{year["big_n"]}</div><div class="kpi-label">超大额(≥10倍)</div></div>']
    for m in months:
        s = stats[m]
        for val, label in (
            (s["amt_n"], f"{m}月金额异常"), (s["qty_n"], f"{m}月数量异常"),
            (s["both_n"], f"{m}月双维度命中"), (s["big_n"], f"{m}月超大额"),
            (s["prod20_n"], f"{m}月超大量"), (s["sausage_n"], f"{m}月烤肠批量")):
            h.append(f'<div class="kpi-card" data-months="{m}" style="display:none;">'
                     f'<div class="kpi-value">{val}</div><div class="kpi-label">{label}</div></div>')
    return "\n  ".join(h)


def act_risk_html(months, stats, year):
    pats = []
    if year["sausage_n"]:
        pats.append(f'烤肠批量采购（≥2,000元）累计{year["sausage_n"]}场，贯穿{month_span([m for m in months if stats[m]["sausage_n"]])}')
    if year["big_n"]:
        pats.append(f'超大额申请（偏离≥10倍）累计{year["big_n"]}场')
    if year["lowprice_n"]:
        pats.append(f'低金额多品项（≥10品且&lt;500元）累计{year["lowprice_n"]}场，集中于{month_span([m for m in months if stats[m]["lowprice_n"]])}')
    if year["prod20_n"]:
        pats.append(f'超大量选品（≥20个产品）累计{year["prod20_n"]}场')

    h = ['<div id="annualRisk" class="risk-box">',
         f'<p><strong>年度风险总览：</strong>剔除经销商大会后共{year["total"]}场活动，'
         f'{year["amt_n"]}场金额偏离≥10%、{year["qty_n"]}场数量偏离≥10%，其中{year["both_n"]}场双维度命中。</p>',
         f'<p><strong>核心异常模式：</strong>{"；".join(pats)}。</p>',
         '<p><strong>总体建议：</strong>① 对500G烤肠设置单场数量上限（如≤200袋），超量走供货/采购流程；'
         '② 推广标准试吃套装，减少随意拼单；③ 对单场金额&gt;5,000元或产品数&gt;15个的活动触发二级复核；'
         '④ 清理重复规格SKU，统一产品命名规范。</p>', '</div>', '']
    for m in months:
        s = stats[m]
        mp = []
        if s["big_n"]:
            mp.append(f'超大额申请（偏离≥10倍）{s["big_n"]}场')
        if s["sausage_n"]:
            mp.append(f'烤肠批量采购（≥2,000元）{s["sausage_n"]}场')
        if s["prod20_n"]:
            mp.append(f'超大量选品（≥20个产品）{s["prod20_n"]}场')
        if s["lowprice_n"]:
            mp.append(f'低金额多品项（≥10品且&lt;500元）{s["lowprice_n"]}场')
        sug = []
        if s["sausage_n"]:
            sug.append("烤肠批量采购频发，建议对500G烤肠设置单场≤200袋上限")
        if s["big_n"]:
            sug.append("超大额申请存在，建议核实是否为常规备货而非单场试吃")
        if s["both_n"] >= 10:
            sug.append("双维度异常较多，建议优先复核命中金额+数量的活动")
        if s["lowprice_n"]:
            sug.append("低金额多品项活动增多，建议核查是否仅申请1~2袋/品")
        if s["prod20_n"]:
            sug.append("超大量活动存在，建议核查品项数与场次匹配性")
        if not sug:
            sug.append("本月申请相对平稳，建议保持常规审核节奏")
        h += [f'<div id="risk2026-{m:02d}" class="month-risk-section" data-month="{m}">', '',
              '<div class="risk-box">', '',
              f'<p><strong>{m}月风险总览：</strong>总{s["total"]}场金额异常、{s["qty_n"]}场数量异常',
              f'，其中{s["both_n"]}场双维度命中',
              '。</p>',
              f'<p><strong>主要异常模式：</strong>{"；".join(mp) if mp else "本月无明显集中异常模式"}。</p>',
              f'<p><strong>建议动作：</strong>{"；".join(sug)}。</p>',
              '</div>', '</div>', '']
    # 区间尾部需还原原文件的 3 个收尾 </div>：.section 收尾 + 内层包装 + #activityTab 自身
    h += ["</div>", "", "</div>", "", "</div>"]
    return "\n".join(h)

def load_sample(xlsx):
    df2 = pd.read_excel(xlsx, sheet_name="线下样品申请单", header=0)
    df2 = df2[~df2["标题"].astype(str).str.contains("经销商大会", na=False)].copy()
    df2 = df2[df2["审批状态"] != "已废弃"].copy()
    df2["申请人"] = df2["辅助列"].astype(str).str.split("/").str[-1].fillna("")
    df2["省区"] = df2["辅助列"].astype(str).str.split("/").str[0].fillna("")
    # pandas 3.0 起 astype(str) 保留 NaN，需显式兜底，避免 json 写出字面 NaN
    df2["申请人"] = df2["申请人"].fillna("")
    df2["省区"] = df2["省区"].fillna("")

    def build_compose(g):
        parts = []
        for _, row in g.sort_values(AM, ascending=False).head(3).iterrows():
            name = str(row[NA])[:24]
            qty, amt = row[QT], row[AM]
            try:
                qty_s = f"{int(qty)}袋"
            except Exception:
                qty_s = "?袋"
            try:
                amt_s = f"{amt:.0f}元"
            except Exception:
                amt_s = f"{amt}元"
            parts.append(f"{name}{qty_s}{amt_s}")
        return " · ".join(parts)

    records = []
    for sid, g in df2.groupby("流水号", sort=False):
        records.append({
            "月份": int(g["月份"].iloc[0]), "流水号": sid,
            "申请人": g["申请人"].iloc[0], "省区": g["省区"].iloc[0],
            "标题": str(g["标题"].iloc[0]), "申请时间": str(g["申请时间"].iloc[0]),
            "产品数": len(g), "总金额": round(float(g[AM].sum()), 2),
            "总数量": round(float(g[QT].sum()), 1), "主要构成": build_compose(g),
        })
    return pd.DataFrame(records)


def build_sample(agg2):
    months = sorted(agg2["月份"].unique().tolist())
    med_a2 = {m: float(agg2[agg2["月份"] == m]["总金额"].median()) for m in months}
    med_q2 = {m: float(agg2[agg2["月份"] == m]["产品数"].median()) for m in months}
    agg2 = agg2.copy()
    agg2["金额_当月中位数"] = agg2["月份"].map(med_a2)
    agg2["金额_偏离额"] = agg2["总金额"] - agg2["金额_当月中位数"]
    agg2["金额_偏离%"] = (agg2["金额_偏离额"] / agg2["金额_当月中位数"] * 100).round(1)
    agg2["数量_当月中位数"] = agg2["月份"].map(med_q2)
    agg2["数量_偏离量"] = agg2["产品数"] - agg2["数量_当月中位数"]
    agg2["数量_偏离%"] = (agg2["数量_偏离量"] / agg2["数量_当月中位数"] * 100).round(1)
    amt2 = agg2[agg2["金额_偏离%"] >= 10].sort_values(["月份", "金额_偏离%"], ascending=[True, False])
    qty2 = agg2[agg2["数量_偏离%"] >= 10].sort_values(["月份", "数量_偏离%"], ascending=[True, False])
    both2 = agg2[(agg2["金额_偏离%"] >= 10) & (agg2["数量_偏离%"] >= 10)]
    agg2["_sausage"] = agg2["主要构成"].astype(str).str.contains("烤肠", na=False) & (agg2["总金额"] >= 1000)

    amt_records = [{
        "month": int(r["月份"]), "流水号": r["流水号"], "标题": r["标题"],
        "申请人": r["申请人"], "省区": r["省区"], "申请时间": str(r["申请时间"]),
        "产品数": int(r["产品数"]), "总金额": float(r["总金额"]), "总数量": float(r["总数量"]),
        "中位数": float(r["金额_当月中位数"]), "偏离额": float(r["金额_偏离额"]),
        "偏离%": float(r["金额_偏离%"]), "主要构成": r["主要构成"]} for _, r in amt2.iterrows()]
    qty_records = [{
        "month": int(r["月份"]), "流水号": r["流水号"], "标题": r["标题"],
        "申请人": r["申请人"], "省区": r["省区"], "申请时间": str(r["申请时间"]),
        "产品数": int(r["产品数"]), "总金额": float(r["总金额"]), "总数量": float(r["总数量"]),
        "中位数": int(r["数量_当月中位数"]), "偏离量": float(r["数量_偏离量"]),
        "偏离%": float(r["数量_偏离%"]), "主要构成": r["主要构成"]} for _, r in qty2.iterrows()]

    month_stats = []
    for m in months:
        sm = agg2[agg2["月份"] == m]
        month_stats.append({
            "month": m, "total": len(sm),
            "amt_abnormal": len(amt2[amt2["月份"] == m]),
            "qty_abnormal": len(qty2[qty2["月份"] == m]),
            "both": len(both2[both2["月份"] == m]),
            "large_amt": len(sm[sm["总金额"] >= 1000]),
            "large_qty": len(sm[sm["总数量"] >= 50]),
            "sausage": int(sm["_sausage"].sum()),
            "median_amt": float(med_a2[m]), "median_qty": float(med_q2[m]),
            "total_amt": float(sm["总金额"].sum()), "total_qty": float(sm["总数量"].sum())})

    data = {
        "total_orders": len(agg2), "total_amt_abnormal": len(amt2),
        "total_qty_abnormal": len(qty2), "total_both": len(both2),
        "year_median_amt": float(agg2["总金额"].median()),
        "year_median_qty": float(agg2["产品数"].median()),
        "large_amt_total": len(agg2[agg2["总金额"] >= 1000]),
        "large_qty_total": len(agg2[agg2["总数量"] >= 50]),
        "sausage_total": int(agg2["_sausage"].sum()),
        "month_stats": month_stats, "amt_records": amt_records, "qty_records": qty_records,
    }
    return data, month_stats


def sample_kpi_grid_html(month_stats):
    y_total = sum(ms["total"] for ms in month_stats)
    y_amt = sum(ms["amt_abnormal"] for ms in month_stats)
    y_qty = sum(ms["qty_abnormal"] for ms in month_stats)
    y_both = sum(ms["both"] for ms in month_stats)
    y_lamt = sum(ms["large_amt"] for ms in month_stats)
    y_lqty = sum(ms["large_qty"] for ms in month_stats)
    y_sau = sum(ms["sausage"] for ms in month_stats)
    h = [f'<div class="kpi-card" data-months="all">\n    <div class="kpi-value">{v}</div>\n    <div class="kpi-label">{l}</div>\n  </div>'
         for v, l in ((y_total, "总申请单数"), (y_amt, "金额异常单数"), (y_qty, "数量异常单数"),
                      (y_both, "双维度命中"), (y_lamt, "大额单数"), (y_lqty, "大量单数"), (y_sau, "烤肠批量"))]
    for ms in month_stats:
        m = ms["month"]
        for val, label in ((ms["total"], f"{m}月总单数"), (ms["amt_abnormal"], f"{m}月金额异常"),
                           (ms["qty_abnormal"], f"{m}月数量异常"), (ms["both"], f"{m}月双维度命中"),
                           (ms["large_amt"], f"{m}月大额"), (ms["large_qty"], f"{m}月大量"),
                           (ms["sausage"], f"{m}月烤肠批量")):
            h.append(f'  <div class="kpi-card" data-months="{m}" style="display:none;">\n'
                     f'    <div class="kpi-value">{val}</div>\n'
                     f'    <div class="kpi-label">{label}</div>\n  </div>')
    return "\n  ".join(h)


def sample_risk_html(data, month_stats):
    y_sau = sum(ms["sausage"] for ms in month_stats)
    y_lamt = sum(ms["large_amt"] for ms in month_stats)
    y_lqty = sum(ms["large_qty"] for ms in month_stats)
    sau_span = month_span([ms["month"] for ms in month_stats if ms["sausage"]])
    lqty_span = month_span([ms["month"] for ms in month_stats if ms["large_qty"]])
    h = ['<div id="sampleAnnualRisk" class="risk-box">',
         f'<p><strong>年度风险总览：</strong>剔除经销商大会及已废弃后共 {data["total_orders"]} 场申请，'
         f'{data["total_amt_abnormal"]} 场金额偏离≥10%、{data["total_qty_abnormal"]} 场数量偏离≥10%，'
         f'其中{data["total_both"]}场双维度命中。</p>',
         f'<p><strong>核心异常模式：</strong>烤肠批量送样（≥1000元）累计{y_sau}场，贯穿{sau_span}；'
         f'超大额送样（≥1000元）累计{y_lamt}场；大量送样（≥50袋）累计{y_lqty}场，覆盖{lqty_span}。</p>',
         '<p><strong>总体建议：</strong>① 对单次样品申请金额≥1000元或总数量≥50袋的触发二级复核；'
         '② 同一申请人/同一客户单月多次送样需明确申请原因；'
         '③ 烤肠类批量送样应核实是否为终端客户试吃而非囤货；'
         '④ 清理重复规格SKU，统一产品命名规范。</p>', '</div>', '']
    for ms in month_stats:
        m = ms["month"]
        pats = []
        if ms["large_amt"] >= 5:
            pats.append(f'大额送样（≥1000元）{ms["large_amt"]}场')
        if ms["large_qty"] >= 10:
            pats.append(f'大量送样（≥50袋）{ms["large_qty"]}场')
        if ms["sausage"] >= 3:
            pats.append(f'烤肠批量送样（≥1000元）{ms["sausage"]}场')
        if not pats:
            pats.append("以小额、多频次送样为主")
        sug = []
        if ms["both"] >= 50:
            sug.append("双维度异常较多，建议优先复核命中金额+数量的申请单")
        if ms["large_amt"] >= 5:
            sug.append("大额送样集中，建议核实样品用途与客户转化路径")
        if ms["sausage"] >= 3:
            sug.append("烤肠批量送样存在，需确认是否为终端客户试吃而非囤货")
        if ms["large_qty"] >= 10:
            sug.append("大量送样（≥50袋）较多，应警惕样品转化为库存的风险")
        if not sug:
            sug.append("本月申请相对平稳，建议保持常规审核节奏")
        h += [f'<div id="sampleRisk{m:02d}" class="month-risk-section" data-month="{m}" style="display:none;">',
              '<div class="risk-box">',
              f'<p><strong>{m}月风险总览：</strong>共{ms["total"]}场，金额异常{ms["amt_abnormal"]}场、'
              f'数量异常{ms["qty_abnormal"]}场，其中{ms["both"]}场双维度命中。</p>',
              f'<p><strong>主要异常模式：</strong>{"；".join(pats)}。</p>',
              f'<p><strong>建议动作：</strong>{"；".join(sug)}。</p>',
              '</div>', '</div>', '']
    h.append("</div>")
    return "\n".join(h)


# ============================================================
# 核销侧
# ============================================================

FEE_SHORT = {
    "活动执行费用.活动执行外包人员费用": "外包人员费用",
    "活动执行费用.活动试吃样品": "活动试吃样品",
    "活动执行费用.活动物流运费": "活动物流运费",
    "活动执行费用.场地使用费用": "场地使用费用",
    "一次性活动物料制作&搭建费用": "物料制作&搭建",
    "活动执行费用.其它活动费用": "其它活动费用",
}
CN = "合计费用:费用金额"
CO = "合计费用:费用金额:总合计"
CV = "合计费用:费用项目"
XW = "活动执行费用.活动执行外包人员费用:工资金额"
ZS = "活动执行费用.活动执行外包人员费用:实际销售额"


def build_verify(xlsx):
    df = pd.read_excel(xlsx, sheet_name="线下活动执行费用核销单", header=0)
    df["报销月份"] = pd.to_datetime(df["报销日期"]).dt.month
    fee_order = list(FEE_SHORT.keys())

    summary = []
    details = []
    for sid, g in df.groupby("流水号", sort=False):
        gp = g[g[XW].notna()]
        n_ppl = len(gp)
        sales = round(float(g[ZS].dropna().sum()), 1)
        total_amt = round(float(g[CO].dropna().iloc[0]), 1) if g[CO].notna().any() else 0.0
        fee_rate = round(total_amt / sales * 100, 1) if sales > 0 else None
        wage_sum = round(float(gp[XW].sum()), 1)
        fee_map = {}
        for cvv, sub in g.groupby(CV):
            fee_map[str(cvv)] = round(float(sub[CN].sum()), 1)
        summary.append({
            "月份": int(g["报销月份"].iloc[0]), "流水号": sid, "标题": str(g["标题"].iloc[0]),
            "报销日期": str(g["报销日期"].iloc[0])[:10], "合计金额": total_amt,
            "活动销售额": sales, "活动费比": fee_rate, "人数": n_ppl, "工资合计": wage_sum,
            "费用拆解": {FEE_SHORT.get(k, k): v for k, v in fee_map.items()},
        })
        for cvv in fee_order:
            sub = g[g[CV] == cvv]
            if len(sub) == 0:
                continue
            details.append({
                "月份": int(g["报销月份"].iloc[0]), "流水号": sid, "标题": str(g["标题"].iloc[0]),
                "费用项目": FEE_SHORT[cvv], "费用金额": round(float(sub[CN].sum()), 1),
                "合计金额": total_amt,
            })

    summary_df = pd.DataFrame(summary)
    month_stats = []
    for m in sorted(summary_df["月份"].unique()):
        sub = summary_df[summary_df["月份"] == m]
        m_sales = round(float(sub["活动销售额"].sum()), 1)
        month_stats.append({
            "month": int(m), "count": len(sub),
            "total_amt": round(float(sub["合计金额"].sum()), 1),
            "sales_sum": m_sales,
            "fee_rate": round(float(sub["合计金额"].sum()) / m_sales * 100, 1) if m_sales > 0 else None,
            "wage_sum": round(float(sub["工资合计"].sum()), 1),
            "ppl_cnt": int(sub["人数"].sum()),
            "fee_breakdown": {short: round(float(sum(r["费用拆解"].get(short, 0)
                                 for r in sub.to_dict("records"))), 1)
                              for short in FEE_SHORT.values()},
        })
    total_amt_all = round(float(summary_df["合计金额"].sum()), 1)
    sales_all = round(float(summary_df["活动销售额"].sum()), 1)
    data = {
        "kpi": {
            "count": len(summary), "total_amt": total_amt_all, "sales_sum": sales_all,
            "fee_rate": round(total_amt_all / sales_all * 100, 1) if sales_all > 0 else None,
            "wage_sum": round(float(summary_df["工资合计"].sum()), 1),
            "ppl_cnt": int(summary_df["人数"].sum()),
            "avg_per_order": round(float(summary_df["合计金额"].mean()), 1),
        },
        "month_stats": month_stats,
        "fee_totals": {FEE_SHORT[cvv]: round(float(df[df[CV] == cvv][CN].sum()), 1) for cvv in fee_order},
        "summary": summary, "details": details,
    }
    return data


def verify_risk_html(data):
    k = data["kpi"]
    summary_df = pd.DataFrame(data["summary"])
    fr = summary_df["活动费比"].dropna()
    med_fr = round(float(fr.median()), 1) if len(fr) else None
    n30 = int((fr >= 30).sum())
    top3 = summary_df.dropna(subset=["活动费比"]).sort_values("活动费比", ascending=False).head(3)
    top3_s = "；".join(
        f'{str(r["流水号"]).split("-")[-1]}（费比{r["活动费比"]}%，核销{r["合计金额"]:,.1f}/销售{r["活动销售额"]:,.1f}）'
        for _, r in top3.iterrows())
    n_nosales = int((summary_df["活动销售额"] <= 0).sum())
    n_noppl = int((summary_df["人数"] == 0).sum())
    fee_s = "、".join(f"{name} {amt:,.1f}元" for name, amt in data["fee_totals"].items())
    month_txt = month_span(sorted({ms["month"] for ms in data["month_stats"]}))
    h = ['<div id="verifyRiskAnnual" class="risk-box">',
         f'<p><strong>年度风险总览：</strong>共 {k["count"]} 单核销签呈（报销日期均在 {month_txt}），'
         f'核销总金额 {k["total_amt"]:,.1f} 元，活动销售额合计 {k["sales_sum"]:,.1f} 元，'
         f'<strong>整体活动费比 {k["fee_rate"]}%</strong>，人员 {k["ppl_cnt"]} 人次，'
         f'平均单笔核销 {k["avg_per_order"]:,.1f} 元。</p>',
         f'<p><strong>核心关注点：</strong>① 费比中位数 {med_fr}%，费比≥30% 的签呈 {n30} 单，'
         f'费比Top3：{top3_s}；② {n_nosales} 单无销售额（销售额为0或空），费比无法计算，'
         f'需核实销售数据是否漏报；③ {n_noppl} 单无外包人员明细（人数为空）；'
         f'④ 费用构成：{fee_s}。</p>',
         '<p><strong>总体建议：</strong>① 汇总表默认按活动费比降序展示前20，优先复核高费比签呈的'
         '费用真实性与销售额匹配性（费比=合计金额/活动销售额×100%）；② 无销售额的签呈应先回补销售数据，'
         '再纳入费比考核；③ 外包人员费用为最大成本项，建议抽查人员台账与执行真实性。</p>',
         '</div>', '']
    for ms in data["month_stats"]:
        sub = summary_df[summary_df["月份"] == ms["month"]]
        fr_m = sub["活动费比"].dropna()
        n30_m = int((fr_m >= 30).sum())
        n_nosales_m = int((sub["活动销售额"] <= 0).sum())
        n_noppl_m = int((sub["人数"] == 0).sum())
        fee_m = "、".join(f"{name} {amt:,.1f}元" for name, amt in ms["fee_breakdown"].items()
                          if amt)
        rate_s = f'{ms["fee_rate"]}%' if ms["fee_rate"] is not None else "--"
        h += [f'<div id="verifyRisk{ms["month"]:02d}" class="month-risk-section" data-month="{ms["month"]}" style="display:none;">',
              '<div class="risk-box">',
              f'<p><strong>{ms["month"]}月风险总览：</strong>共{ms["count"]}单，核销金额 {ms["total_amt"]:,.1f} 元，'
              f'活动销售额 {ms["sales_sum"]:,.1f} 元，活动费比 {rate_s}，人员 {ms["ppl_cnt"]} 人次。</p>',
              f'<p><strong>主要关注点：</strong>{n30_m} 单费比≥30%；{n_nosales_m} 单无销售额；'
              f'{n_noppl_m} 单无人员明细；费用构成：{fee_m}。</p>',
              '</div>', '</div>', '']
    h.append("</div>")
    return "\n".join(h)


# ============================================================
# HTML 补丁引擎
# ============================================================

def must_find1(html, needle, ctx=""):
    n = html.count(needle)
    if n != 1:
        raise SystemExit(f"ERROR: 锚点出现 {n} 次(应为1): {needle[:60]} {ctx}")
    return html.index(needle)


def patch_between(html, start_anchor, end_anchor, new_block, name,
                  keep_end=True, start_offset=0):
    """替换 [start_anchor(+offset), end_anchor) 区间为 new_block。
    keep_end=True 时 end_anchor 保留在结果尾部之外（不包含在替换区）。"""
    i = must_find1(html, start_anchor, name)
    j = must_find1(html[i:], end_anchor, name + "/end") + i
    s = i + start_offset
    return html[:s] + new_block + html[j:]


def replace_data_line(html, var_name, new_json, name):
    """只替换单行数据声明 `const VAR = ...;`，绝不触碰其后任何代码行。

    2026-09-09 事故：原实现 re.sub(r"const VAR = .*?;\\n</script>", ..., flags=re.S)
    会跨行懒惰吞到同一 <script> 块内最后一个 ";\\n</script>"（核销渲染函数的初始化
    调用行），把 VERIFY_DATA 与 </script> 之间的 setVerifyMonth/renderVerifyKpi/
    renderVerifySummary/renderVerifyAmtChart 等整段函数一并删除，导致核销Tab空白。
    现改为行级替换：声明行以分号结尾，则仅替换该行，函数块原样保留。
    """
    anchor = f"const {var_name} = "
    i = must_find1(html, anchor, name)
    j = html.index("\n", i)
    line = html[i:j]
    if not line.rstrip().endswith(";"):
        raise SystemExit(f"ERROR: {name} 声明行未以分号结尾: {line[:80]}")
    new_line = f"{anchor}{json.dumps(new_json, ensure_ascii=False)};"
    return html[:i] + new_line + html[j:]


def replace_kpi_grid(html, grid_id, new_cards):
    open_tag = f'<div class="kpi-grid" id="{grid_id}">\n'
    i = must_find1(html, open_tag, grid_id)
    # kpi-grid 的收尾是开标签后第一个顶格 "\n</div>"（卡片段尾的 </div> 均带缩进或同行）。
    # 不能用远处地标 + rindex：样品 Tab 的地标(第3节注释)跨过了第1、2节，
    # rindex 会命中第2节的 section 收尾，导致整块明细被误删（2026-09-09 事故）。
    close = html.index("\n</div>", i)
    new = f'<div class="kpi-grid" id="{grid_id}">\n  {new_cards}\n</div>'
    return html[:i] + new + html[close + len("\n</div>"):]


def replace_filter_bar(tab_slice_start, tab_slice_end, html, months):
    """在指定 Tab 区间内替换月份筛选栏（保留 all 按钮）。返回新 html。"""
    i = html.index(tab_slice_start)
    j = html.index(tab_slice_end, i)
    seg = html[i:j]
    btns = '\n  '.join(f'<button class="filter-btn" data-month="{m}">{m}月</button>' for m in months)
    new_bar = ('<div class="filter-bar">\n'
               '  <button class="filter-btn active" data-month="all">年度汇总</button>\n'
               f'  {btns}\n'
               '</div>')
    pat = re.compile(r'<div class="filter-bar">.*?</div>', re.S)
    if not pat.search(seg):
        raise SystemExit(f"ERROR: 未找到筛选栏 @ {tab_slice_start}")
    seg2 = pat.sub(new_bar, seg, count=1)
    return html[:i] + seg2 + html[j:]


def div_balance_ok(html):
    return html.count("<div") == html.count("</div>")


# ============================================================
# 主流程
# ============================================================

def main():
    if not XLSX.exists():
        print(f"ERROR: source not found: {XLSX}")
        sys.exit(1)
    print(f"读取 {XLSX}")
    html = REPO_PAGE.read_text(encoding="utf-8")
    if not div_balance_ok(html):
        raise SystemExit("ERROR: 原文件 div 不平衡，终止")

    m_sub_old = re.search(r"<p>剔除经销商大会后 \| (\d+)场活动", html)
    old_total = m_sub_old.group(1) if m_sub_old else "?"
    print(f"[旧] 活动Tab 副标题总场次 = {old_total}")

    # ---------- 计算 ----------
    print("计算活动侧...")
    agg = load_activity(XLSX)
    months, med_amt, med_qty, amt_rows, qty_rows, stats, year = build_activity(agg)
    amt_html = "\n\n".join(act_amt_row_html(r, i) for i, (_, r) in enumerate(amt_rows.iterrows()))
    qty_html = "\n\n".join(act_qty_row_html(r, i) for i, (_, r) in enumerate(qty_rows.iterrows()))
    charts_block = (
        f'const monthLabels = {json.dumps([f"{m}月" for m in months], ensure_ascii=False)};\n'
        f'const amtMedData = {[round(stats[m]["med_amt"], 1) for m in months]};\n'
        f'const amtMaxDevData = {[stats[m]["max_amt_pct"] for m in months]};\n'
        f'const qtyMedData = {[int(stats[m]["med_qty"]) for m in months]};\n'
        f'const qtyMaxDevData = {[stats[m]["max_qty_dev"] for m in months]};\n')

    print("计算样品侧...")
    sagg = load_sample(XLSX)
    sdata, smonth_stats = build_sample(sagg)

    print("计算核销侧...")
    vdata = build_verify(XLSX)

    # ---------- 打补丁 ----------
    print("开始原位替换...")
    # 1) 副标题
    html = re.sub(r"<p>剔除经销商大会后 \| \d+场活动[^<]*</p>",
                  f'<p>剔除经销商大会后 | {year["total"]}场活动 | 偏离中位数≥10%标记为异常 | 默认显示Top3，点击展开查看全部</p>',
                  html, count=1)
    # 2) 活动 KPI
    html = replace_kpi_grid(html, "kpiGrid", act_kpi_grid_html(months, stats, year))
    # 3) 活动金额偏离表 tbody
    i_amt = must_find1(html, '<table id="amtTable">')
    tb_open = html.index("<tbody>", i_amt) + len("<tbody>")
    j_qty = must_find1(html, '<table id="qtyTable">')
    tb_close = html.rindex("</tbody>", i_amt, j_qty)
    html = html[:tb_open] + "\n\n" + amt_html + "\n" + html[tb_close:]
    # 4) 活动数量偏离表 tbody
    i_qty2 = must_find1(html, '<table id="qtyTable">')
    tb_open2 = html.index("<tbody>", i_qty2) + len("<tbody>")
    j_risk = must_find1(html, '<div id="annualRisk"')
    tb_close2 = html.rindex("</tbody>", i_qty2, j_risk)
    html = html[:tb_open2] + "\n\n" + qty_html + "\n" + html[tb_close2:]
    # 5) 活动风险结论区（含 .section 收尾 </div>）
    new_risk = act_risk_html(months, stats, year)
    html = patch_between(html, '<div id="annualRisk"', '<div id="sampleTab"', new_risk, "act-risk")
    # 6) 活动图表常量
    html = patch_between(html, "const monthLabels = ", "let currentMonth",
                         charts_block + "\n", "act-charts")
    # 7) 样品 KPI
    html = replace_kpi_grid(html, "sampleKpiGrid", sample_kpi_grid_html(smonth_stats))
    # 8) 样品筛选栏
    html = replace_filter_bar('<div id="sampleTab"', '<div id="verifyTab"',
                              html, [ms["month"] for ms in smonth_stats])
    # 9) 样品风险结论区
    html = patch_between(html, '<div id="sampleAnnualRisk"', '</div><!-- end sampleTab -->',
                         sample_risk_html(sdata, smonth_stats), "sample-risk")
    # 10) SAMPLE_DATA JSON（单行替换，保留其后脚本）
    html = replace_data_line(html, "SAMPLE_DATA", sdata, "SAMPLE_DATA")
    # 11) 核销筛选栏
    html = replace_filter_bar('<div id="verifyTab"', "</div><!-- end verifyTab -->",
                              html, [ms["month"] for ms in vdata["month_stats"]])
    # 12) VERIFY_DATA JSON（单行替换，保留其后渲染函数，勿用 re.S 通配）
    html = replace_data_line(html, "VERIFY_DATA", vdata, "VERIFY_DATA")
    # 13) 核销风险结论区
    html = patch_between(html, '<div id="verifyRiskAnnual"', '</div><!-- end verifyTab -->',
                         verify_risk_html(vdata), "verify-risk")

    if not div_balance_ok(html):
        raise SystemExit("ERROR: 更新后 div 不平衡，放弃写入")

    # 结构守卫：关键区块与 section 容器数量必须与更新前一致，防止误删
    orig = REPO_PAGE.read_text(encoding="utf-8")
    for key in ('id="amtTable"', 'id="qtyTable"', 'id="annualRisk"',
                'id="sampleAmtTable"', 'id="sampleQtyTable"', 'id="sampleAnnualRisk"',
                'id="verifySummaryTable"', 'id="verifyRiskAnnual"',
                'id="kpiGrid"', 'id="sampleKpiGrid"', 'id="verifyKpiGrid"'):
        if key not in html:
            raise SystemExit(f"ERROR: 更新后丢失关键区块 {key}，放弃写入")
    if html.count('class="section"') != orig.count('class="section"'):
        raise SystemExit("ERROR: section 容器数量变化，疑似误删区块，放弃写入")

    # ---------- 双写 ----------
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for target in (REPO_PAGE, WB_PAGE):
        if target.exists():
            shutil.copy2(target, BACKUP_DIR / f"{target.stem}.bak-auto-{stamp}{target.suffix}")
    REPO_PAGE.write_text(html, encoding="utf-8", newline="")
    WB_PAGE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_PAGE, WB_PAGE)

    print("\n===== 更新完成 =====")
    print(f'活动：{year["total"]}场 / 金额异常{year["amt_n"]} / 数量异常{year["qty_n"]} / 双维{year["both_n"]} / 月份{months}')
    print(f'样品：{sdata["total_orders"]}单 / 金额异常{sdata["total_amt_abnormal"]} / 数量异常{sdata["total_qty_abnormal"]}')
    vk = vdata["kpi"]
    print(f'核销：{vk["count"]}单 / 总额{vk["total_amt"]:,.1f} / 费比{vk["fee_rate"]}% / 月份{[ms["month"] for ms in vdata["month_stats"]]}')
    print(f"旧→新 活动总场次: {old_total} → {year['total']}")
    print(f"已写入:\n  {REPO_PAGE}\n  {WB_PAGE}")
    print(f"备份: {BACKUP_DIR}/*.bak-auto-{stamp}.*")


if __name__ == "__main__":
    main()
