from __future__ import annotations

import hashlib
import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent
SOURCE_FONT_DIR = Path(r"C:\Users\shenw\Desktop\看板\物料小组看板\web_app\static\fonts")
OUTPUT_DIR = REPO_DIR / "material-dashboard" / "assets" / "fonts"


def convert(source: Path, stem: str) -> Path:
    try:
        from fontTools.ttLib import TTFont
    except ImportError as exc:
        raise RuntimeError("缺少 fonttools，请先安装 fonttools 和 brotli") from exc

    font = TTFont(str(source))
    font.flavor = "woff2"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_DIR / f"{stem}.tmp.woff2"
    font.save(str(temporary))
    data = temporary.read_bytes()
    digest = hashlib.sha256(data).hexdigest()[:12]
    target = OUTPUT_DIR / f"{stem}.{digest}.woff2"
    temporary.replace(target)
    for old in OUTPUT_DIR.glob(f"{stem}.*.woff2"):
        if old != target:
            old.unlink()
    return target


def main() -> None:
    sources = {
        "gotham-rounded-bold": SOURCE_FONT_DIR / "GOTHAMRND-BOLD.otf",
        "hk-yuan-w7": SOURCE_FONT_DIR / "华康圆体-W7.ttf",
    }
    for source in sources.values():
        if not source.exists():
            raise FileNotFoundError(source)
    for stem, source in sources.items():
        target = convert(source, stem)
        print(f"{source.name} -> {target.name} ({target.stat().st_size:,} bytes)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"字体转换失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
