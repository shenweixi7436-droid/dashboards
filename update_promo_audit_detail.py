from pathlib import Path
import json
from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parent
SOURCE = Path("C:/Users/shenw/Desktop/\u65b0\u5efa\u6587\u4ef6\u5939/\u5e02\u573a\u7a3d\u6838\u90e8\u91cd\u70b9\u5de5\u4f5c.xlsx")
OUT = ROOT / "assets" / "data" / "promo-audit-detail.js"
SHEET = "\u63a8\u5e7f\u4fc3\u9500\u7a3d\u6838"
COLS = [2, 3, 4, 6, 14]
FALLBACK_HEADERS = ["省份", "市区", "城市经理", "活动门店名称", "稽核结果"]


def norm(value):
    if value is None:
        return ""
    return str(value).strip()


def result_label(value):
    text = norm(value)
    return "合格" if text == "是" else "不合格"


wb = load_workbook(SOURCE, data_only=True, read_only=True)
ws = wb[SHEET]

headers = []
for fallback, col in zip(FALLBACK_HEADERS, COLS):
    headers.append(norm(ws.cell(3, col).value) or fallback)

rows = []
for row_idx in range(4, ws.max_row + 1):
    values = [norm(ws.cell(row_idx, col).value) for col in COLS]
    if not any(values):
        continue
    rows.append(
        {
            "row": row_idx,
            "values": values,
            "result": result_label(values[-1]),
        }
    )

total = len(rows)
qualified = sum(1 for row in rows if row["result"] == "合格")
unqualified = total - qualified

payload = {
    "month": 6,
    "source": "市场稽核部重点工作.xlsx / 推广促销稽核",
    "headers": headers,
    "total": total,
    "qualified": qualified,
    "unqualified": unqualified,
    "rows": rows,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    "window.PROMO_AUDIT_DETAIL = "
    + json.dumps(payload, ensure_ascii=False, indent=2)
    + ";\n",
    encoding="utf-8",
)
print(f"已生成: {OUT}")
print(f"稽核条数: {total}, 合格: {qualified}, 不合格: {unqualified}")
