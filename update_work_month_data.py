from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import json
import re

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parent
SOURCE = Path("C:/Users/shenw/Desktop/看板/市场稽核部重点工作.xlsx")
DATA_DIR = ROOT / "assets" / "data"

PROMO_AUDIT_SHEET = "推广促销稽核"
PROMO_PLAN_SHEET = "推广促销计划"
APPROVAL_SHEET = "线上审批流程稽核明细"
DEVICE_SHEET = "智能设备台账汇总"
MARKET_ORDER_CASE_SHEET = "市场秩序治理-窜货案件数"
MARKET_ORDER_CUSTOMER_SHEET = "市场秩序治理-涉及客户明细"


def norm(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return str(value).strip()


def number(value) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def as_rate(value) -> float:
    if value in (None, ""):
        return 0.0
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    return v if v <= 1 else v / 100


def month_label(value) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, datetime):
        return f"{value.month}月"
    text = str(value).strip()
    m = re.search(r"(\d{1,2})\s*月", text)
    if m:
        return f"{int(m.group(1))}月"
    try:
        dt = datetime.fromisoformat(text[:10])
        return f"{dt.month}月"
    except ValueError:
        pass
    if text.isdigit() and 1 <= int(text) <= 12:
        return f"{int(text)}月"
    return ""


def month_key(month: str) -> int:
    m = re.search(r"\d+", str(month))
    return int(m.group(0)) if m else 99


def result_label(value) -> str:
    text = norm(value)
    return "合格" if text in {"是", "合格"} else "不合格"


def derive_month(row_values, preferred_indexes):
    for idx in preferred_indexes:
        if idx < len(row_values):
            month = month_label(row_values[idx])
            if month:
                return month
    return ""


def read_headers(ws, row, cols, fallback):
    headers = []
    for col, fb in zip(cols, fallback):
        headers.append(norm(ws.cell(row, col).value) or fb)
    return headers


def build_promo_plan(ws):
    rows_by_month = defaultdict(dict)
    months = set()
    max_col = ws.max_column
    month_starts = [col for col in range(1, max_col + 1) if norm(ws.cell(1, col).value).startswith("月份")]
    for start_col in month_starts:
        for row in range(2, ws.max_row + 1):
            raw = [ws.cell(row, start_col + offset).value for offset in range(7)]
            month = month_label(raw[0])
            province = norm(raw[2])
            target = number(raw[4])
            if not month or not province:
                continue
            months.add(month)
            rows_by_month[month][province] = rows_by_month[month].get(province, 0) + target
    return rows_by_month, months


def build_promo(wb):
    ws_audit = wb[PROMO_AUDIT_SHEET]
    ws_plan = wb[PROMO_PLAN_SHEET]
    plan_by_month, plan_months = build_promo_plan(ws_plan)

    detail_cols = [2, 3, 4, 6, 14]
    headers = read_headers(
        ws_audit,
        3,
        detail_cols,
        ["省份", "市区", "城市经理", "活动门店名称", "稽核结果"],
    )
    rows_by_month = defaultdict(list)
    audit_by_month_province = defaultdict(Counter)
    totals_by_month = defaultdict(lambda: {"total": 0, "qualified": 0, "unqualified": 0})
    months = set(plan_months)

    for row_idx, raw_row in enumerate(ws_audit.iter_rows(min_row=4, values_only=True), 4):
        values = [norm(raw_row[col - 1] if len(raw_row) >= col else "") for col in detail_cols]
        result = norm(raw_row[13] if len(raw_row) >= 14 else "")
        if not any(values) and not result:
            continue
        # 推广促销稽核按表内月份归属；没有月份的行不归入任何月份，
        # 避免切换到其他月份时被当前系统月份误带出数据。
        month = derive_month(raw_row, [0, 11, 8])
        if not month:
            continue
        months.add(month)
        province = values[0]
        if province:
            audit_by_month_province[month][province] += 1
        label = result_label(result)
        totals_by_month[month]["total"] += 1
        if label == "合格":
            totals_by_month[month]["qualified"] += 1
        else:
            totals_by_month[month]["unqualified"] += 1
        rows_by_month[month].append({"row": row_idx, "values": values, "result": label})

    plan_payload = {}
    detail_payload = {}
    for month in sorted(months, key=month_key):
        provinces = sorted(set(plan_by_month.get(month, {})) | set(audit_by_month_province.get(month, {})))
        rows = []
        for province in provinces:
            rows.append({
                "province": province,
                "plan": int(plan_by_month.get(month, {}).get(province, 0)),
                "audit": int(audit_by_month_province.get(month, {}).get(province, 0)),
            })
        plan_total = sum(r["plan"] for r in rows)
        audit_total = sum(r["audit"] for r in rows)
        plan_payload[month] = {
            "month": month,
            "planTotal": plan_total,
            "auditTotal": audit_total,
            "progress": round(audit_total / plan_total * 100, 1) if plan_total else 0,
            "rows": rows,
        }
        total = totals_by_month[month]["total"]
        detail_payload[month] = {
            "month": month_key(month),
            "source": "市场稽核部重点工作.xlsx / 推广促销稽核",
            "headers": headers,
            "total": total,
            "qualified": totals_by_month[month]["qualified"],
            "unqualified": totals_by_month[month]["unqualified"],
            "rows": rows_by_month.get(month, []),
        }
    return plan_payload, detail_payload, months


def build_approval(wb):
    ws = wb[APPROVAL_SHEET]
    detail_cols = [2, 4, 5, 6, 7, 8, 10, 11]
    headers = read_headers(
        ws,
        2,
        detail_cols,
        ["流程发起时间", "费用类型", "签呈号", "省区", "客户名称", "发起人", "问题类型", "着装不合格类型"],
    )
    stats = defaultdict(lambda: {"total": 0, "qualified": 0, "unqualified": 0, "issues": Counter(), "dress": Counter(), "province": Counter(), "rows": []})
    months = set()
    for row_idx, raw_row in enumerate(ws.iter_rows(min_row=3, values_only=True), 3):
        values = [norm(raw_row[col - 1] if len(raw_row) >= col else "") for col in detail_cols]
        result = norm(raw_row[8] if len(raw_row) >= 9 else "")
        if not any(values) and not result:
            continue
        # 线上审批流程稽核明细按 B 列拆分月份；无月份的行不归入任何月份。
        month = derive_month(raw_row, [1])
        if not month:
            continue
        months.add(month)
        bucket = stats[month]
        bucket["total"] += 1
        if result == "是":
            bucket["qualified"] += 1
        else:
            bucket["unqualified"] += 1
            issue = values[6]
            dress_issue = values[7] if len(values) > 7 else ""
            province = values[3]
            if issue:
                bucket["issues"][issue] += 1
            if dress_issue:
                bucket["dress"][dress_issue] += 1
            if province:
                bucket["province"][province] += 1
            bucket["rows"].append({"row": row_idx, "values": values, "result": "不合格"})

    pies_payload = {}
    detail_payload = {}
    for month in sorted(months, key=month_key):
        bucket = stats[month]
        total = bucket["total"]
        issues = [{"name": k, "value": v} for k, v in bucket["issues"].most_common(3)]
        dress_issues = [{"name": k, "value": v} for k, v in bucket["dress"].most_common()]
        province_issues = [{"province": k, "value": v} for k, v in bucket["province"].most_common() if v > 0]
        pies_payload[month] = {
            "month": month,
            "total": total,
            "qualified": bucket["qualified"],
            "unqualified": bucket["unqualified"],
            "rate": round(bucket["qualified"] / total * 100, 1) if total else 0,
            "issues": issues,
            "dressIssues": dress_issues,
            "provinceIssues": province_issues,
        }
        detail_payload[month] = {
            "month": month_key(month),
            "source": "市场稽核部重点工作.xlsx / 线上审批流程稽核明细",
            "headers": headers,
            "total": total,
            "qualified": bucket["qualified"],
            "unqualified": bucket["unqualified"],
            "rows": bucket["rows"],
            "dressIssues": dress_issues,
            "provinceIssues": province_issues,
        }
    return pies_payload, detail_payload, months


def build_device(wb, months):
    ws = wb[DEVICE_SHEET]
    device_names = ["保温柜", "烤肠机", "冰柜"]
    items = []
    for index, row in enumerate(range(4, 7)):
        volume = number(ws.cell(row, 14).value)
        rate = as_rate(ws.cell(row, 15).value)
        items.append({"name": device_names[index], "volume": volume, "rate": rate})

    def display(value, is_rate=False):
        value = "" if value is None else value
        if value == "":
            return "-"
        if is_rate and isinstance(value, (int, float)):
            return f"{value * 100:.1f}%"
        if isinstance(value, (int, float)):
            return f"{int(value):,}" if abs(value - int(value)) < 0.00001 else f"{value:.1f}"
        return str(value).strip()

    def read_table(name, header_row, start_row, end_row, start_col=1, end_col=8):
        headers = [display(ws.cell(header_row, col).value) for col in range(start_col, end_col + 1)]
        rows = []
        for row_idx in range(start_row, end_row + 1):
            raw = [ws.cell(row_idx, col).value for col in range(start_col, end_col + 1)]
            if not any(value not in (None, "") for value in raw):
                continue
            rows.append([
                display(value, is_rate=(idx == len(raw) - 1 and isinstance(value, (int, float)) and value <= 1))
                for idx, value in enumerate(raw)
            ])
        return {"name": name, "headers": headers, "rows": rows}

    detail = {
        "month": 6,
        "source": "市场稽核部重点工作.xlsx / 智能设备台账汇总",
        "summary": items,
        "sections": [
            read_table("保温柜", 3, 4, 7, 1, 8),
            read_table("烤肠机", 9, 10, 13, 1, 8),
            read_table("冰柜", 15, 16, 18, 1, 7),
        ],
    }
    status = {
        "source": "市场稽核部重点工作.xlsx / 智能设备台账汇总!M4:O6",
        "items": items,
    }
    return {month: status for month in months}, {month: detail for month in months}


def build_market_order(wb):
    ws_cases = wb[MARKET_ORDER_CASE_SHEET]
    ws_customers = wb[MARKET_ORDER_CUSTOMER_SHEET]
    monthly = defaultdict(lambda: {
        "cases": set(),
        "customers": set(),
        "provinceCases": defaultdict(set),
        "customerRows": defaultdict(int),
        "punish": set(),
        "internal": set(),
        "unverified": set(),
        "others": {},
    })
    months = set()

    def is_2026(value):
        text = norm(value)
        if isinstance(value, datetime):
            return value.year == 2026
        m = re.search(r"20\d{2}", text)
        return bool(m and int(m.group(0)) == 2026)

    for row in ws_cases.iter_rows(min_row=2, values_only=True):
        if not row or not is_2026(row[0] if len(row) > 0 else ""):
            continue
        month = month_label(row[1] if len(row) > 1 else "")
        seq = norm(row[2] if len(row) > 2 else "")
        if not month or not seq:
            continue
        months.add(month)
        bucket = monthly[month]
        bucket["cases"].add(seq)
        province = norm(row[4] if len(row) > 4 else "")
        city = norm(row[5] if len(row) > 5 else "")
        method = norm(row[13] if len(row) > 13 else "")
        if province:
            bucket["provinceCases"][province].add(seq)
        if method in {"营销中心通报处罚", "省区通报处罚"}:
            bucket["punish"].add(seq)
        elif method in {"内部处理", "内部沟通处理"}:
            bucket["internal"].add(seq)
        elif method == "未查实":
            bucket["unverified"].add(seq)
        elif method:
            note = f"窜货{seq}{province}{city}{method}"
            bucket["others"][seq] = note

    for row in ws_customers.iter_rows(min_row=2, values_only=True):
        if not row:
            continue
        month = month_label(row[0] if len(row) > 0 else "")
        customer = norm(row[1] if len(row) > 1 else "")
        if not month or not customer:
            continue
        months.add(month)
        monthly[month]["customers"].add(customer)
        monthly[month]["customerRows"][customer] += 1

    payload = {}
    for month in sorted(months, key=month_key):
        bucket = monthly[month]
        province_rank = sorted(
            ({"name": name, "count": len(seq_set)} for name, seq_set in bucket["provinceCases"].items()),
            key=lambda item: (-item["count"], item["name"])
        )
        customer_rank = sorted(
            ({"name": name, "count": count} for name, count in bucket["customerRows"].items()),
            key=lambda item: (-item["count"], item["name"])
        )
        payload[month] = {
            "month": month,
            "source": "市场稽核部重点工作.xlsx / 市场秩序治理",
            "caseCount": len(bucket["cases"]),
            "customerCount": len(bucket["customers"]),
            "punishCount": len(bucket["punish"]),
            "internalCount": len(bucket["internal"]),
            "unverifiedCount": len(bucket["unverified"]),
            "otherNotes": list(bucket["others"].values()),
            "provinceRank": province_rank,
            "customerRank": customer_rank,
        }
    return payload, months


def write_js(path: Path, legacy_name: str, map_name: str, payload_by_month: dict, default_month: str, extra=""):
    payload = payload_by_month.get(default_month) or next(iter(payload_by_month.values()), {})
    text = (
        f"window.{map_name} = "
        + json.dumps(payload_by_month, ensure_ascii=False, indent=2)
        + ";\n"
        + f"window.{legacy_name} = window.{map_name}[window.MAIN_SELECTED_MONTH || {json.dumps(default_month, ensure_ascii=False)}] || "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n"
        + extra
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    wb = load_workbook(SOURCE, data_only=True, read_only=True)
    promo_plan, promo_detail, promo_months = build_promo(wb)
    approval_pies, approval_detail, approval_months = build_approval(wb)
    market_order, market_months = build_market_order(wb)
    all_months = sorted(set(promo_months) | set(approval_months) | set(market_months), key=month_key)
    if not all_months:
        all_months = [month_label(datetime.now())]
    default_month = all_months[-1]
    device_status, device_detail = build_device(wb, all_months)
    month_extra = (
        "window.MAIN_WORK_MONTHS = "
        + json.dumps(all_months, ensure_ascii=False)
        + ";\nwindow.MAIN_DEFAULT_MONTH = "
        + json.dumps(default_month, ensure_ascii=False)
        + ";\n"
    )

    write_js(DATA_DIR / "promo-plan-audit.js", "PROMO_PLAN_AUDIT", "PROMO_PLAN_AUDIT_BY_MONTH", promo_plan, default_month, month_extra)
    write_js(DATA_DIR / "promo-audit-detail.js", "PROMO_AUDIT_DETAIL", "PROMO_AUDIT_DETAIL_BY_MONTH", promo_detail, default_month)
    write_js(DATA_DIR / "approval-pies.js", "APPROVAL_PIES", "APPROVAL_PIES_BY_MONTH", approval_pies, default_month)
    write_js(DATA_DIR / "approval-detail.js", "APPROVAL_DETAIL", "APPROVAL_DETAIL_BY_MONTH", approval_detail, default_month)
    write_js(DATA_DIR / "device-channel-status.js", "DEVICE_CHANNEL_STATUS", "DEVICE_CHANNEL_STATUS_BY_MONTH", device_status, default_month)
    write_js(DATA_DIR / "device-detail.js", "DEVICE_DETAIL", "DEVICE_DETAIL_BY_MONTH", device_detail, default_month)
    write_js(DATA_DIR / "market-order-governance.js", "MARKET_ORDER_GOVERNANCE", "MARKET_ORDER_GOVERNANCE_BY_MONTH", market_order, default_month)

    print(f"Updated month-aware work data: {', '.join(all_months)}; default {default_month}")


if __name__ == "__main__":
    main()
