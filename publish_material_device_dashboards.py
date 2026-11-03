from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent
SOURCE_DIR = Path(r"C:\Users\shenw\Desktop\看板\物料小组看板")
MATERIAL_DIR = REPO_DIR / "material-main-dashboard"
DEVICE_DIR = REPO_DIR / "device-main-dashboard"

GOTHAM_FILE = "gotham-rounded-bold.f6281701cdb9.woff2"
YUAN_FILE = "hk-yuan-w7.a0f4d903956d.woff2"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def rewrite_html(html: str, data_files: tuple[str, ...]) -> str:
    replacements = {
        "../字体/GOTHAMRND-BOLD.otf": f"assets/fonts/{GOTHAM_FILE}",
        "../字体/华康圆体-W7.ttf": f"assets/fonts/{YUAN_FILE}",
        "../字体/华康圆体-W8.ttf": f"assets/fonts/{YUAN_FILE}",
        "../字体/华康圆体-W9.ttf": f"assets/fonts/{YUAN_FILE}",
        "format('opentype')": "format('woff2')",
        "format('truetype')": "format('woff2')",
    }
    for old, new in replacements.items():
        html = html.replace(old, new)
    for filename in data_files:
        old = f'<script src="{filename}"></script>'
        new = f'<script src="assets/data/{filename}"></script>'
        if old not in html:
            raise RuntimeError(f"HTML 缺少数据引用：{old}")
        html = html.replace(old, new, 1)
    registration = """<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('./sw.js').catch(function (error) {
      console.warn('离线缓存注册失败', error);
    });
  });
}
</script>
"""
    if "navigator.serviceWorker.register('./sw.js')" not in html:
        html = html.replace("</body>", registration + "</body>", 1)
    return html


def service_worker(cache_prefix: str, version: str, assets: list[str]) -> str:
    precache = ["./", "./index.html", *[f"./{path}" for path in assets]]
    return f"""const CACHE_NAME = {json.dumps(cache_prefix + '-' + version)};
const CACHE_PREFIX = {json.dumps(cache_prefix + '-')};
const PRECACHE_URLS = {json.dumps(precache, ensure_ascii=False, indent=2)};

self.addEventListener('install', event => {{
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS)));
  self.skipWaiting();
}});

self.addEventListener('activate', event => {{
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
      .map(key => caches.delete(key))
  )));
  self.clients.claim();
}});

self.addEventListener('fetch', event => {{
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  event.respondWith(
    fetch(event.request).then(response => {{
      if (response.ok) {{
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
      }}
      return response;
    }}).catch(() => caches.match(event.request).then(cached =>
      cached || (event.request.mode === 'navigate' ? caches.match('./index.html') : undefined)
    ))
  );
}});
"""


def publish_dashboard(
    *,
    name: str,
    source_html: str,
    output_dir: Path,
    data_files: tuple[str, ...],
    cache_prefix: str,
) -> dict[str, object]:
    source_path = SOURCE_DIR / source_html
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    font_source = MATERIAL_DIR / "assets" / "fonts"
    for font in (GOTHAM_FILE, YUAN_FILE):
        if not (font_source / font).is_file():
            raise FileNotFoundError(font_source / font)

    data_dir = output_dir / "assets" / "data"
    font_dir = output_dir / "assets" / "fonts"
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    font_dir.mkdir(parents=True, exist_ok=True)

    for filename in data_files:
        source = SOURCE_DIR / filename
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, data_dir / filename)
    for font in (GOTHAM_FILE, YUAN_FILE):
        source = font_source / font
        target = font_dir / font
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)

    html = rewrite_html(source_path.read_text(encoding="utf-8"), data_files)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_bytes = html.encode("utf-8")
    (output_dir / "index.html").write_bytes(html_bytes)
    assets = [
        *[f"assets/data/{filename}" for filename in data_files],
        f"assets/fonts/{GOTHAM_FILE}",
        f"assets/fonts/{YUAN_FILE}",
    ]
    version_seed = bytearray(html_bytes)
    for asset in assets:
        version_seed.extend((output_dir / asset).read_bytes())
    version = digest(bytes(version_seed))
    (output_dir / "sw.js").write_text(
        service_worker(cache_prefix, version, assets), encoding="utf-8", newline="\n"
    )
    manifest = {
        "name": name,
        "version": version,
        "builtAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "sourceHtml": str(source_path),
        "sourceWorkbook": str(
            Path(r"C:\Users\shenw\Desktop\物料&设备数据分析\2026年物料及设备出库数据汇总.xlsx")
        ),
        "files": {"html": "index.html", "assets": assets},
    }
    (output_dir / "build-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "README.md").write_text(
        f"# {name}\n\n由 `publish_material_device_dashboards.py` 从本地主看板生成。\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "name": name,
        "output": str(output_dir),
        "version": version,
        "htmlBytes": len(html_bytes),
        "dataBytes": sum((output_dir / "assets" / "data" / item).stat().st_size for item in data_files),
    }


def main() -> None:
    results = [
        publish_dashboard(
            name="营销物料数据主看板",
            source_html="营销物料数据主看板.html",
            output_dir=MATERIAL_DIR,
            data_files=("material_summary_data.js", "material_filter_data.js"),
            cache_prefix="material-main-dashboard",
        ),
        publish_dashboard(
            name="设备数据分析看板",
            source_html="设备主看版.html",
            output_dir=DEVICE_DIR,
            data_files=("device_filter_data.js",),
            cache_prefix="device-main-dashboard",
        ),
    ]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
