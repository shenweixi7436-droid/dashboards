# -*- coding: utf-8 -*-
"""重建 store-business-analysis.html 内嵌的 RAW_DATA 明细快照。

用途：替代已丢失的 build_audit_dashboard.py 中更新鸣忙专项稽核看板页面的部分。
数据源：市场稽核部重点工作.xlsx 的"鸣忙门店专项稽核"sheet。
用法：
    python build_store_audit_dashboard.py            # 更新 RAW_DATA
    python build_store_audit_dashboard.py --check    # 仅校验：与现有快照逐行比对，不写文件
"""
from __future__ import annotations

import json
import posixpath
import re
import sys
import zipfile
from datetime import datetime, date
from pathlib import Path
from xml.etree import ElementTree as ET

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent
SOURCE = Path("C:/Users/shenw/Desktop/看板/市场稽核部重点工作.xlsx")
PAGE = ROOT / "store-business-analysis.html"
SHEET = "鸣忙门店专项稽核"
PHOTO_URL_PREFIX = "门店经营分析_照片"
PHOTO_DIR = ROOT / PHOTO_URL_PREFIX

DISPIMG_RE = re.compile(r'DISPIMG\("([^"]+)"')
CELLIMAGE_NS = {
    "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def text_value(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    # 源表中部分单元格为 UTF-8 字节被按 GBK 解码产生的乱码（如"闄堝垪涓嶈冻鍗婃煖"），
    # 反向修复：先按 GBK 编回字节，再按 UTF-8 解码；失败则保留原文。
    try:
        repaired = text.encode("gbk").decode("utf-8")
        if repaired and "\ufffd" not in repaired:
            return repaired
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return text


def date_value(value) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if value is None:
        return ""
    return str(value)


PROVINCE_ALIASES = {
    "北京": "北京市",
    "上海": "上海市",
    "天津": "天津市",
    "重庆": "重庆市",
    "广西省壮族自治区": "广西壮族自治区",
}


def normalize_province(value) -> str:
    """统一 G 列省份别名，避免同一省/直辖市拆成多个分类。"""
    province = text_value(value).replace(" ", "")
    return PROVINCE_ALIASES.get(province, province)


def build_column_map(ws) -> dict[str, int]:
    """通过表头定位字段，避免源表插入列后整页数据错位。"""
    headers = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
    positions: dict[str, list[int]] = {}
    for column, header in enumerate(headers, start=1):
        name = text_value(header)
        if name:
            positions.setdefault(name, []).append(column)

    required = (
        "年清洗", "月份清洗", "门店名称", "省份", "城市", "区县", "门店地址",
        "陈列SKU数", "陈列冰柜数", "烤肠零售价", "蛋挞皮零售价", "蛋挞液零售价",
        "竞品记录信息", "本次巡店改进项", "巡店日期", "登记时间", "登记人",
        "判定结果", "不合格原因", "冰柜照片是否完整", "备注",
    )
    missing = [name for name in required if name not in positions]
    if missing:
        raise ValueError(f"{SHEET} 缺少必要表头：{', '.join(missing)}")

    # 源表当前含有两个同名“省区”字段；明细筛选沿用最后一个，若未来只保留一个则自然回退。
    regions = positions.get("省区", [])
    if not regions:
        raise ValueError(f"{SHEET} 缺少必要表头：省区")

    def one(name: str) -> int:
        return positions[name][0]

    return {
        "year": one("年清洗"), "month": one("月份清洗"), "store": one("门店名称"),
        "province": one("省份"), "city": one("城市"), "district": one("区县"),
        "address": one("门店地址"), "sku": one("陈列SKU数"),
        "freezer": one("陈列冰柜数"), "sausage": one("烤肠零售价"),
        "shell": one("蛋挞皮零售价"), "liquid": one("蛋挞液零售价"),
        "competitor": one("竞品记录信息"), "improve": one("本次巡店改进项"),
        "region": regions[-1], "date": one("巡店日期"),
        "registered_at": one("登记时间"), "registrar": one("登记人"),
        "result": one("判定结果"), "reason": one("不合格原因"),
        "photo_ok": one("冰柜照片是否完整"), "remark": one("备注"),
    }


def cell(row: tuple, columns: dict[str, int], name: str):
    """按列号安全取值，源表缺少尾部空单元格时返回空。"""
    index = columns[name] - 1
    return row[index] if index < len(row) else None


def export_embedded_photos(photo_ids: set[str], write_files: bool) -> dict[str, str]:
    """将 WPS/Excel DISPIMG 图片导出为看板可直接引用的文件。"""
    if not photo_ids:
        return {}

    with zipfile.ZipFile(SOURCE) as archive:
        image_root = ET.fromstring(archive.read("xl/cellimages.xml"))
        rel_root = ET.fromstring(archive.read("xl/_rels/cellimages.xml.rels"))
        targets = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rel_root.findall(f"{{{REL_NS}}}Relationship")
        }
        photo_map: dict[str, str] = {}
        missing_targets: list[str] = []

        for image in image_root:
            pic = image.find("xdr:pic", CELLIMAGE_NS)
            if pic is None:
                continue
            name_node = pic.find("xdr:nvPicPr/xdr:cNvPr", CELLIMAGE_NS)
            blip = pic.find("xdr:blipFill/a:blip", CELLIMAGE_NS)
            if name_node is None or blip is None:
                continue
            photo_id = name_node.attrib.get("name", "")
            if photo_id not in photo_ids:
                continue
            rel_id = blip.attrib.get(f"{{{CELLIMAGE_NS['r']}}}embed")
            target = targets.get(rel_id or "")
            if not target:
                missing_targets.append(photo_id)
                continue
            archive_name = posixpath.normpath(posixpath.join("xl", target))
            if archive_name not in archive.namelist():
                missing_targets.append(photo_id)
                continue
            suffix = Path(archive_name).suffix.lower() or ".png"
            output_name = f"{photo_id}{suffix}"
            photo_map[photo_id] = f"{PHOTO_URL_PREFIX}/{output_name}"
            if write_files:
                PHOTO_DIR.mkdir(parents=True, exist_ok=True)
                output_path = PHOTO_DIR / output_name
                output_path.write_bytes(archive.read(archive_name))

    if missing_targets:
        print(f"WARNING: {len(missing_targets)} photo IDs could not be exported")
    print(f"embedded photos mapped: {len(photo_map)} (requested: {len(photo_ids)})")
    return photo_map


def main():
    check_only = "--check" in sys.argv
    wb = load_workbook(SOURCE, data_only=True, read_only=True)
    ws = wb[SHEET]
    columns = build_column_map(ws)
    print("resolved columns: " + ", ".join(f"{name}={column}" for name, column in columns.items()))

    # 先收集备注中的 DISPIMG 标识，再从工作簿压缩包导出真实图片文件。
    photo_ids_needed: set[str] = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        photo_ids_needed.update(
            DISPIMG_RE.findall(text_value(cell(row, columns, "remark")))
        )
    photo_map = export_embedded_photos(photo_ids_needed, write_files=not check_only)

    # 逐行构建（保留 Excel 真实行号作为 rowNum）
    out = []
    for excel_row_idx, row in enumerate(
        ws.iter_rows(min_row=2, values_only=True), start=2
    ):
        if cell(row, columns, "year") in (None, ""):
            continue
        remark = text_value(cell(row, columns, "remark"))
        photo_ids = DISPIMG_RE.findall(remark)
        photo_urls = [photo_map[photo_id] for photo_id in photo_ids if photo_id in photo_map]
        result = text_value(cell(row, columns, "result")) or "未填写"
        reason = text_value(cell(row, columns, "reason"))
        if result == "合格" or reason in ("/", ""):
            # 原生成器口径：合格一律记"无不合格原因"；未填写原因记"未填写原因"
            reason = "无不合格原因" if result == "合格" else "未填写原因"

        def num(v):
            return v if v not in (None, "") else ""

        province = normalize_province(cell(row, columns, "province"))
        # 概览和筛选使用同一份规范化省份，避免自治区等别名被拆为两个柱形分组。
        audit_group = province
        out.append(
            {
                "rowNum": excel_row_idx,
                "yearClean": text_value(cell(row, columns, "year")),
                "monthClean": text_value(cell(row, columns, "month")),
                "auditGroup": audit_group,
                "store": text_value(cell(row, columns, "store")),
                "province": province,
                "city": text_value(cell(row, columns, "city")),
                "district": text_value(cell(row, columns, "district")),
                "address": text_value(cell(row, columns, "address")),
                "sku": num(cell(row, columns, "sku")),
                "freezer": num(cell(row, columns, "freezer")),
                "sausagePrice": num(cell(row, columns, "sausage")),
                "eggTartShellPrice": num(cell(row, columns, "shell")),
                "eggTartLiquidPrice": num(cell(row, columns, "liquid")),
                "competitor": text_value(cell(row, columns, "competitor")),
                "improvement": text_value(cell(row, columns, "improve")),
                "region": text_value(cell(row, columns, "region")),
                "date": date_value(cell(row, columns, "date")),
                "registeredAt": date_value(cell(row, columns, "registered_at")),
                "registrar": text_value(cell(row, columns, "registrar")),
                "result": result,
                "reason": reason,
                "photoComplete": text_value(cell(row, columns, "photo_ok")),
                "remark": remark,
                "photoIds": photo_ids,
                "photoUrls": photo_urls,
                "hasPhoto": bool(photo_urls),
            }
        )

    print(f"built rows from Excel: {len(out)}")

    html = PAGE.read_text(encoding="utf-8")
    m = re.search(r"var RAW_DATA = (\[.*?\]);\s*\n", html, re.S)
    if not m:
        print("ERROR: RAW_DATA block not found in page")
        sys.exit(1)
    existing = json.loads(m.group(1))
    print(f"existing snapshot rows: {len(existing)}")

    if check_only:
        old_by_num = {r["rowNum"]: r for r in existing}
        mismatch = 0
        for i, new in enumerate(out):
            old = old_by_num.get(new["rowNum"])
            if old is None:
                continue
            if old != new:
                mismatch += 1
                if mismatch <= 3:
                    for k in new:
                        if old.get(k) != new[k]:
                            print(
                                f"rowNum={new['rowNum']} field={k}: "
                                f"snapshot={old.get(k)!r} excel={new[k]!r}"
                            )
        common = sum(1 for r in out if r["rowNum"] in old_by_num)
        print(f"compared {common} common rows, mismatches: {mismatch}")
        sys.exit(0 if mismatch == 0 else 2)

    new_json = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    block = f"var RAW_DATA = {new_json};\n"
    html = html[: m.start()] + block + html[m.end():]

    # 同步更新页头"内置数据：N 条"计数
    pill_new = f"内置数据：{len(out):,} 条"
    html, n_pill = re.subn(
        r"内置数据：[\d,]+ 条", pill_new, html, count=1
    )

    PAGE.write_text(html, encoding="utf-8")
    print(f"RAW_DATA updated in {PAGE.name}: {len(out)} rows (source-pill updated: {n_pill})")


if __name__ == "__main__":
    main()
