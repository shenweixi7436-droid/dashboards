from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image


SOURCE_HTML = Path(r"C:\Users\shenw\Desktop\看板\看板首页.html")
SOURCE_FONT = Path(r"C:\Users\shenw\Desktop\看板\字体\华康圆体-W9.ttf")
OUTPUT_DIR = Path(r"C:\Users\shenw\Documents\New project\dashboard-home-site")
IMAGE_PATTERN = re.compile(
    r"data:image/(?P<type>png|jpe?g|webp|gif);base64,(?P<data>[A-Za-z0-9+/=]+)",
    re.IGNORECASE,
)

LINKS = {
    "entry-card-a": "https://dash.weishenghjxh.xyz/",
    "entry-card-b": "https://dash.weishenghjxh.xyz/material-main-dashboard/",
    "entry-card-c": "https://dash.weishenghjxh.xyz/device-main-dashboard/",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def prepare_output() -> tuple[Path, Path]:
    image_dir = OUTPUT_DIR / "assets" / "images"
    font_dir = OUTPUT_DIR / "assets" / "fonts"
    for directory in (image_dir, font_dir):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)
    return image_dir, font_dir


def export_images(html: str, image_dir: Path) -> tuple[str, list[dict[str, object]]]:
    import base64

    exported: list[dict[str, object]] = []

    def replace(match: re.Match[str]) -> str:
        raw = base64.b64decode(match.group("data"))
        index = len(exported) + 1
        source_hash = digest(raw)
        filename = f"home-image-{index}-{source_hash}.webp"
        target = image_dir / filename
        with Image.open(BytesIO(raw)) as image:
            image.load()
            width, height = image.size
            has_alpha = image.mode in {"RGBA", "LA"} or (
                image.mode == "P" and "transparency" in image.info
            )
            converted = image.convert("RGBA" if has_alpha else "RGB")
            converted.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            converted.save(
                target,
                "WEBP",
                quality=84,
                method=6,
            )
        exported.append(
            {
                "file": f"assets/images/{filename}",
                "width": width,
                "height": height,
                "publishedWidth": converted.width,
                "publishedHeight": converted.height,
                "sourceBytes": len(raw),
                "publishedBytes": target.stat().st_size,
            }
        )
        return f"assets/images/{filename}"

    return IMAGE_PATTERN.sub(replace, html), exported


def rewrite_links(html: str) -> str:
    links_json = json.dumps(LINKS, ensure_ascii=False, indent=6)
    html, count = re.subn(
        r"const links = \{.*?\n\s*\};",
        "const links = " + links_json + ";",
        html,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise RuntimeError("未找到首页卡片跳转配置")
    return html


def main() -> None:
    if not SOURCE_HTML.is_file():
        raise FileNotFoundError(SOURCE_HTML)
    if not SOURCE_FONT.is_file():
        raise FileNotFoundError(SOURCE_FONT)

    image_dir, font_dir = prepare_output()
    html = SOURCE_HTML.read_text(encoding="utf-8")
    html, images = export_images(html, image_dir)
    html = html.replace(
        './字体/华康圆体-W9.ttf', 'assets/fonts/hk-yuan-w9.ttf'
    )
    html = rewrite_links(html)

    shutil.copy2(SOURCE_FONT, font_dir / "hk-yuan-w9.ttf")
    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8", newline="\n")
    (OUTPUT_DIR / "CNAME").write_text("weishenghjxh.xyz\n", encoding="ascii")
    (OUTPUT_DIR / ".nojekyll").write_text("", encoding="ascii")

    manifest = {
        "name": "市场稽核部&物料/设备数据看板首页",
        "version": digest(html.encode("utf-8")),
        "builtAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": str(SOURCE_HTML),
        "customDomain": "weishenghjxh.xyz",
        "links": LINKS,
        "images": images,
    }
    (OUTPUT_DIR / "build-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (OUTPUT_DIR / "README.md").write_text(
        "# 数据看板首页\n\n由 `publish_dashboard_home.py` 从桌面看板首页生成。\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
