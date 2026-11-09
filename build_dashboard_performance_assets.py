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


def read_assigned_json(path: Path, assignment: str):
    """Read the JSON object that immediately follows a JavaScript assignment."""
    content = path.read_text(encoding="utf-8")
    start = content.find(assignment)
    if start < 0:
        raise ValueError(f"Cannot find {assignment!r} in {path.name}")
    start += len(assignment)
    value, _ = json.JSONDecoder().raw_decode(content[start:].lstrip())
    return value


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
    approval = read_assigned_json(
        DATA_DIR / "approval-detail.js", "window.APPROVAL_DETAIL_BY_MONTH = "
    )
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
