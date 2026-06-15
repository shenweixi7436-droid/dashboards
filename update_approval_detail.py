from datetime import datetime
from pathlib import Path
import json
from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parent
SOURCE = Path("C:/Users/shenw/Desktop/\u65b0\u5efa\u6587\u4ef6\u5939/\u5e02\u573a\u7a3d\u6838\u90e8\u91cd\u70b9\u5de5\u4f5c.xlsx")
OUT = ROOT / "assets" / "data" / "approval-detail.js"
SHEET = "\u7ebf\u4e0a\u5ba1\u6279\u6d41\u7a0b\u7a3d\u6838\u660e\u7ec6"
DETAIL_COLS = [2, 4, 5, 6, 7, 8, 10]
RESULT_COL = 9
HEADER_ROW = 2
DATA_START_ROW = 3
FALLBACK_HEADERS = ["流程发起时间", "费用类型", "签呈号", "省区", "客户名称", "发起人", "问题类型"]


def norm(value):
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return str(value).strip()


wb = load_workbook(SOURCE, data_only=True, read_only=True)
ws = wb[SHEET]

headers = []
for fallback, col in zip(FALLBACK_HEADERS, DETAIL_COLS):
    headers.append(norm(ws.cell(HEADER_ROW, col).value) or fallback)

total = 0
qualified = 0
unqualified = 0
rows = []
needed_cols = sorted(set(DETAIL_COLS + [RESULT_COL]))
max_needed_col = max(needed_cols)

for row_idx, raw_row in enumerate(ws.iter_rows(min_row=DATA_START_ROW, max_col=max_needed_col, values_only=True), DATA_START_ROW):
    detail_values = [norm(raw_row[col - 1] if len(raw_row) >= col else "") for col in DETAIL_COLS]
    result = norm(raw_row[RESULT_COL - 1] if len(raw_row) >= RESULT_COL else "")
    if not any(detail_values) and not result:
        continue

    total += 1
    is_ok = result == "是"
    if is_ok:
        qualified += 1
    else:
        unqualified += 1
        rows.append(
            {
                "row": row_idx,
                "values": detail_values,
                "result": "不合格",
            }
        )

payload = {
    "month": 6,
    "source": "市场稽核部重点工作.xlsx / 线上审批流程稽核明细",
    "headers": headers,
    "total": total,
    "qualified": qualified,
    "unqualified": unqualified,
    "rows": rows,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    "window.APPROVAL_DETAIL = "
    + json.dumps(payload, ensure_ascii=False, indent=2)
    + ";\n",
    encoding="utf-8",
)
print(f"已生成: {OUT}")
print(f"总审核流程数: {total}, 合格: {qualified}, 不合格: {unqualified}")
