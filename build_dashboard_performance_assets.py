"""Build compact homepage data assets for the main audit dashboard.

The full data files stay in place for detail dialogs.  This script removes the
row-level payload from the files required by the homepage, then refreshes their
cache version in index.html.  It is intentionally run after every source-data
update so summary data and detail data always come from the same batch.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "assets" / "data"
INDEX_FILE = ROOT / "index.html"


def read_assigned_json(path: Path, *assignments: str):
    """Read JSON from the first compatible JavaScript assignment in a file."""
    content = path.read_text(encoding="utf-8")
    for assignment in assignments:
        start = content.find(assignment)
        if start < 0:
            continue
        start += len(assignment)
        value, _ = json.JSONDecoder().raw_decode(content[start:].lstrip())
        return value
    raise ValueError(f"Cannot find any supported assignment in {path.name}: {assignments!r}")


def write_assignment(path: Path, assignment: str, value) -> None:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"{assignment}{payload};\n", encoding="utf-8")


def build_snapshot_summary(snapshot):
    summary = copy.deepcopy(snapshot)
    for zones in summary.values():
        for zone_data in zones.values():
            zone_data.pop("audit_details", None)
            zone_data.pop("issue_details", None)
    return summary


def build_month_summary(rows, excluded_fields):
    summary = copy.deepcopy(rows)
    for month_data in summary.values():
        for field in excluded_fields:
            month_data.pop(field, None)
    return summary


def normalize_month_map(payload):
    """Support both legacy single-month and current month-map generators."""
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object for month-aware dashboard data")
    if any(re.fullmatch(r"\d+月", str(key)) for key in payload):
        return payload
    month = payload.get("month")
    if month is None:
        raise ValueError("Single-month payload has no month field")
    month_text = str(month).replace("月", "").strip()
    return {f"{month_text}月": payload}


def update_asset_version(version: str) -> None:
    html = INDEX_FILE.read_text(encoding="utf-8")
    replacements = {
        r'(window\.DASHBOARD_ASSET_VERSION\s*=\s*")[^"]*(";)': rf'\g<1>{version}\g<2>',
        r'(assets/data/approval-detail-summary\.js\?v=)[^"<]+': rf'\g<1>{version}',
        r'(assets/data/market-order-governance-summary\.js\?v=)[^"<]+': rf'\g<1>{version}',
        r'(assets/data/dashboard-snapshot-summary\.js\?v=)[^"<]+': rf'\g<1>{version}',
    }
    for pattern, replacement in replacements.items():
        html, count = re.subn(pattern, replacement, html)
        if count != 1:
            raise ValueError(f"Expected one cache-version marker for {pattern}, found {count}")
    INDEX_FILE.write_text(html, encoding="utf-8")


def main() -> None:
    snapshot = read_assigned_json(DATA_DIR / "dashboard-snapshot.js", "var ZD = ")
    approval = normalize_month_map(read_assigned_json(
        DATA_DIR / "approval-detail.js",
        "window.APPROVAL_DETAIL_BY_MONTH = ",
        "window.APPROVAL_DETAIL = ",
    ))
    market = read_assigned_json(
        DATA_DIR / "market-order-governance.js",
        "window.MARKET_ORDER_GOVERNANCE_BY_MONTH = ",
    )

    write_assignment(
        DATA_DIR / "dashboard-snapshot-summary.js",
        "var ZD = ",
        build_snapshot_summary(snapshot),
    )
    write_assignment(
        DATA_DIR / "approval-detail-summary.js",
        "window.APPROVAL_DETAIL_BY_MONTH = ",
        build_month_summary(approval, {"rows"}),
    )
    write_assignment(
        DATA_DIR / "market-order-governance-summary.js",
        "window.MARKET_ORDER_GOVERNANCE_BY_MONTH = ",
        build_month_summary(market, {"caseDetails"}),
    )

    version = datetime.now().strftime("%Y%m%d%H%M%S")
    update_asset_version(version)
    print(f"Built compact homepage assets (version {version}).")


if __name__ == "__main__":
    main()
