from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import openpyxl


DEFAULT_SOURCE = Path(
    r"C:\Users\shenw\Desktop\物料&设备数据分析\2026年物料及设备出库数据汇总.xlsx"
)
DEFAULT_DASHBOARD_DIR = Path(r"C:\Users\shenw\Desktop\看板\物料小组看板")


def clean_text(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    return text or fallback


def clean_number(value: object) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def clean_date(value: object) -> str | None:
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    text = str(value or "").strip()
    for pattern in ("%Y-%m-%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(text[:10] if pattern == "%Y-%m-%d" else text, pattern).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def write_js(path: Path, variable: str, payload: dict, *, pretty: bool = False) -> None:
    options = {"ensure_ascii": False}
    if pretty:
        options["indent"] = 2
    else:
        options["separators"] = (",", ":")
    content = f"window.{variable} = " + json.dumps(payload, **options) + ";\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


def build_material_data(sheet) -> tuple[dict, dict]:
    rows: list[dict] = []
    monthly_amount: dict[int, float] = defaultdict(float)
    monthly_categories: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    monthly_provinces: dict[int, set[str]] = defaultdict(set)
    monthly_cities: dict[int, set[str]] = defaultdict(set)

    for values in sheet.iter_rows(min_row=2, min_col=1, max_col=21, values_only=True):
        row_date = clean_date(values[2])  # C 创建日期清洗
        if not row_date:
            continue
        month = int(row_date[5:7])
        name = clean_text(values[4], "未命名物料")  # E
        amount = round(clean_number(values[5]), 2)  # F
        category = clean_text(values[6], "未分类")  # G
        province = clean_text(values[19], "未标注")  # T
        city = clean_text(values[20], "未标注")  # U
        rows.append(
            {"m": month, "d": row_date, "a": amount, "n": name, "p": province, "c": city, "g": category}
        )
        monthly_amount[month] += amount
        monthly_categories[month][category] += amount
        monthly_provinces[month].add(province)
        monthly_cities[month].add(city)

    months: dict[str, dict] = {}
    for month in range(1, 13):
        amount = monthly_amount.get(month, 0.0)
        previous = monthly_amount.get(month - 1, 0.0) if month > 1 else 0.0
        categories = monthly_categories.get(month, {})
        if categories:
            top_category, top_amount = max(categories.items(), key=lambda item: item[1])
        else:
            top_category, top_amount = "暂无数据", 0.0
        months[str(month)] = {
            "amount": round(amount, 2),
            "amountMom": (amount / previous - 1) if previous else None,
            "topCategory": top_category,
            "topAmount": round(top_amount, 2),
            "topShare": (top_amount / amount) if amount else None,
            "provinceCount": len(monthly_provinces.get(month, set())),
            "cityCount": len(monthly_cities.get(month, set())),
        }

    filter_payload = {
        "year": 2026,
        "sourceFile": DEFAULT_SOURCE.name,
        "sourceSheet": "物料出库明细",
        "sourceColumns": "C创建日期清洗、E物料名称清洗、F金额、G物料分类、T省、U市",
        "rows": rows,
    }
    summary_payload = {
        "year": 2026,
        "sourceFile": DEFAULT_SOURCE.name,
        "sourceSheet": "物料出库明细",
        "months": months,
        "inventory": {
            "amount": None,
            "topCode": "",
            "topAmount": None,
            "topName": "暂无数据",
            "topShare": None,
        },
    }
    return filter_payload, summary_payload


def build_device_data(sheet) -> dict:
    rows: list[dict] = []
    channels: set[str] = set()
    for values in sheet.iter_rows(min_row=2, min_col=1, max_col=14, values_only=True):
        row_date = clean_date(values[10])  # K 下单日期
        if not row_date:
            continue
        channel = clean_text(values[2], "未标注")  # C
        rows.append(
            {
                "d": row_date,
                "a": round(clean_number(values[7]), 2),  # H 总货值
                "q": round(clean_number(values[9]), 2),  # J 数量
                "n": clean_text(values[0], "未命名设备"),  # A
                "b": clean_text(values[1], "未标注"),  # B
                "c": channel,
                "p": clean_text(values[4], "未标注"),  # E
                "g": clean_text(values[13], "未分类"),  # N
            }
        )
        channels.add(channel)
    return {
        "year": 2026,
        "sourceFile": DEFAULT_SOURCE.name,
        "sourceSheet": "设备出库明细",
        "sourceColumns": "A设备名称、B设备品牌、C渠道、E省份、H总货值、J数量、K下单日期、N设备大类",
        "channels": sorted(channels),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="从单一工作簿刷新物料与设备主看板数据")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--dashboard-dir", type=Path, default=DEFAULT_DASHBOARD_DIR)
    args = parser.parse_args()
    source = args.source.resolve()
    dashboard_dir = args.dashboard_dir.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"找不到源数据：{source}")
    for filename in ("营销物料数据主看板.html", "设备主看版.html"):
        if not (dashboard_dir / filename).is_file():
            raise FileNotFoundError(f"找不到主看板：{dashboard_dir / filename}")

    workbook = openpyxl.load_workbook(source, read_only=True, data_only=True)
    required = ("物料出库明细", "设备出库明细")
    missing = [name for name in required if name not in workbook.sheetnames]
    if missing:
        raise KeyError("源数据缺少 sheet：" + "、".join(missing))

    material_filter, material_summary = build_material_data(workbook["物料出库明细"])
    device_filter = build_device_data(workbook["设备出库明细"])
    workbook.close()

    write_js(dashboard_dir / "material_filter_data.js", "MATERIAL_FILTER_DATA", material_filter)
    write_js(dashboard_dir / "material_summary_data.js", "MATERIAL_SUMMARY_DATA", material_summary, pretty=True)
    write_js(dashboard_dir / "device_filter_data.js", "DEVICE_FILTER_DATA", device_filter)
    print(
        json.dumps(
            {
                "source": str(source),
                "materialRows": len(material_filter["rows"]),
                "deviceRows": len(device_filter["rows"]),
                "outputs": [
                    str(dashboard_dir / "material_filter_data.js"),
                    str(dashboard_dir / "material_summary_data.js"),
                    str(dashboard_dir / "device_filter_data.js"),
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
