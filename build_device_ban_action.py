import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
SOURCE = Path(r"C:\Users\shenw\Desktop\看板\市场稽核部重点工作.xlsx")
OUTPUT = ROOT / "assets" / "data" / "device-ban-action.js"


def clean(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def integer(value):
    return int(round(number(value)))


def summarize(frame):
    rows = []
    for _, source in frame.iterrows():
        processing_days = integer(source["处理时间"])
        progress = clean(source["最新进展"]) or "未回复"
        rows.append(
            {
                "platform": clean(source["平台"]) or "未注明",
                "location": clean(source["设备所在省市"]) or "未注明",
                "deviceType": clean(source["设备名称"]) or "未注明",
                "count": integer(source["设备台数"]),
                "processingDays": processing_days,
                "processingAge": f">= {processing_days}天" if processing_days >= 0 else "待补充",
                "progress": progress,
                "result": clean(source["跟进结果"]) or "待补充",
            }
        )

    def grouped(column):
        values = frame.groupby(column, dropna=False)["设备台数"].sum().sort_values(ascending=False)
        return [{"name": clean(name) or "未注明", "count": integer(value)} for name, value in values.items()]

    status = frame["最新进展"].map(lambda value: clean(value) or "未回复")
    status_counts = status.to_frame("status").join(frame["设备台数"]).groupby("status")["设备台数"].sum().sort_values(ascending=False)
    platform_counts = frame.groupby("平台")["设备台数"].sum().sort_values(ascending=False)
    return {
        "total": integer(frame["设备台数"].sum()),
        "platform": clean(platform_counts.index[0]) if len(platform_counts) else "--",
        "removed": integer(frame.loc[status == "已下架", "设备台数"].sum()),
        "noReply": integer(frame.loc[status == "未回复", "设备台数"].sum()),
        "reported": integer(frame.loc[status == "已向平台举报", "设备台数"].sum()),
        "merchantInfo": integer(frame.loc[status == "商家信息获取中", "设备台数"].sum()),
        "followUp": integer(frame.loc[status == "当地业务跟进中", "设备台数"].sum()),
        "statuses": [{"name": clean(name), "count": integer(value)} for name, value in status_counts.items()],
        "locations": grouped("设备所在省市"),
        "details": [row for row in rows if row["progress"] != "已下架"],
    }


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source workbook not found: {SOURCE}")
    frame = pd.read_excel(SOURCE, sheet_name="禁网行动", header=1)
    frame["设备台数"] = pd.to_numeric(frame["设备台数"], errors="coerce").fillna(0)
    frame = frame.loc[frame["设备台数"] > 0].copy()
    current = summarize(frame)
    data = {"8月": current, "全年": current}
    payload = "window.DEVICE_BAN_ACTION_BY_MONTH = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    payload += "window.DEVICE_BAN_ACTION = window.DEVICE_BAN_ACTION_BY_MONTH[window.MAIN_SELECTED_MONTH || '8月'] || window.DEVICE_BAN_ACTION_BY_MONTH['全年'];\n"
    OUTPUT.write_text(payload, encoding="utf-8")
    print(f"wrote {OUTPUT} with {len(frame)} rows, {integer(frame['设备台数'].sum())} devices")


if __name__ == "__main__":
    main()
