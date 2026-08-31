from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE_DIR = Path(r"C:\Users\shenw\Desktop\看板\物料小组看板")
OUTPUT_DIR = REPO_DIR / "material-dashboard"
DATA_DIR = OUTPUT_DIR / "assets" / "data"
FONT_DIR = OUTPUT_DIR / "assets" / "fonts"
MAIN_OUTPUT_DIR = REPO_DIR / "material-main-dashboard"
FREIGHT_OUTPUT_DIR = REPO_DIR / "material-freight-dashboard"

ASSIGNMENTS = ("DATA", "INV", "ORD", "SUPPLIER_PAYMENTS", "SUPPLIER_DETAIL")
P6_DATA_FILES = (
    "province_outbound_data.js",
    "province_material_data.js",
    "device_outbound_data.js",
)


def sha256_short(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def write_hashed(directory: Path, stem: str, suffix: str, data: bytes) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    digest = sha256_short(data)
    filename = f"{stem}.{digest}{suffix}"
    target = directory / filename
    target.write_bytes(data)
    return filename


def remove_old_hashed_files(directory: Path, stems: set[str], keep: set[str]) -> None:
    if not directory.exists():
        return
    for path in directory.iterdir():
        if not path.is_file() or path.name in keep:
            continue
        if any(path.name.startswith(f"{stem}.") for stem in stems):
            path.unlink()


def extract_assignment(html: str, name: str) -> str:
    match = re.search(rf"^const\s+{re.escape(name)}=(.*);\s*$", html, flags=re.MULTILINE)
    if not match:
        raise RuntimeError(f"未在 HTML 中找到数据变量 {name}")
    return match.group(1)


def replace_assignment(html: str, name: str, replacement: str) -> str:
    updated, count = re.subn(
        rf"^const\s+{re.escape(name)}=.*;\s*$",
        replacement,
        html,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise RuntimeError(f"替换数据变量 {name} 失败")
    return updated


def find_font(stem: str) -> Path:
    matches = sorted(FONT_DIR.glob(f"{stem}.*.woff2"))
    if not matches:
        raise RuntimeError(
            f"缺少 WOFF2 字体：{stem}。请先运行 convert_material_fonts.py 生成字体。"
        )
    return matches[-1]


def build_service_worker(asset_urls: list[str], version: str, cache_prefix: str) -> str:
    precache = ["./", "./index.html", *[f"./{url}" for url in asset_urls]]
    return f"""const CACHE_NAME = '{cache_prefix}-{version}';
const PRECACHE_URLS = {json.dumps(precache, ensure_ascii=False, indent=2)};

self.addEventListener('install', event => {{
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS)));
  self.skipWaiting();
}});

self.addEventListener('activate', event => {{
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(key => key.startsWith('{cache_prefix}-') && key !== CACHE_NAME)
        .map(key => caches.delete(key))
    ))
  );
  self.clients.claim();
}});

self.addEventListener('fetch', event => {{
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.endsWith('/') || url.pathname.endsWith('/index.html')) {{
    event.respondWith(
      fetch(event.request).then(response => {{
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
        return response;
      }}).catch(() => caches.match(event.request))
    );
    return;
  }}

  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {{
      const copy = response.clone();
      caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
      return response;
    }}))
  );
}});
"""


def service_worker_registration() -> str:
    return """<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('./sw.js').catch(function (error) {
      console.warn('离线缓存注册失败', error);
    });
  });
}
</script>
"""


def replace_font_faces(html: str, gotham_url: str, yuan_url: str) -> str:
    font_block = (
        f"@font-face{{font-family:'GOTHAMRND-BOLD';src:url('{gotham_url}') format('woff2');font-display:swap}}\n"
        f"@font-face{{font-family:'HKYuan-W7';src:url('{yuan_url}') format('woff2');font-display:swap}}"
    )
    html, count = re.subn(
        r"@font-face\{font-family:'GOTHAMRND-BOLD'.*?\}\s*"
        r"@font-face\{font-family:'HKYuan-W7'.*?\}\s*"
        r"@font-face\{font-family:'HKYuan-W8'.*?\}\s*"
        r"@font-face\{font-family:'HKYuan-W9'.*?\}",
        font_block,
        html,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise RuntimeError("字体声明替换失败")
    return html.replace("'HKYuan-W8'", "'HKYuan-W7'").replace("'HKYuan-W9'", "'HKYuan-W7'")


def hash_data_files(source_dir: Path, output_dir: Path, filenames: tuple[str, ...]) -> dict[str, str]:
    data_dir = output_dir / "assets" / "data"
    names: dict[str, str] = {}
    stems: set[str] = set()
    for filename in filenames:
        source = source_dir / filename
        if not source.exists():
            raise FileNotFoundError(f"缺少看板数据文件：{source}")
        stem = Path(filename).stem
        stems.add(stem)
        names[filename] = write_hashed(data_dir, stem, ".js", source.read_bytes())
    remove_old_hashed_files(data_dir, stems, set(names.values()))
    return names


def finish_static_dashboard(
    output_dir: Path,
    html: str,
    asset_urls: list[str],
    cache_prefix: str,
    source_dir: Path,
    files: dict[str, object],
    readme: str,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_html = html.encode("utf-8")
    (output_dir / "index.html").write_bytes(output_html)
    version_seed = "\n".join([sha256_short(output_html), *asset_urls]).encode("utf-8")
    version = sha256_short(version_seed)
    (output_dir / "sw.js").write_text(
        build_service_worker(asset_urls, version, cache_prefix), encoding="utf-8", newline="\n"
    )
    manifest = {
        "version": version,
        "builtAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": str(source_dir),
        "files": {"html": "index.html", **files},
    }
    (output_dir / "build-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "README.md").write_text(readme.strip() + "\n", encoding="utf-8")
    return {"version": version, "htmlBytes": len(output_html), "output": str(output_dir)}


def build_main_dashboard(source_dir: Path, gotham: Path, yuan: Path) -> dict[str, object]:
    source_html = source_dir / "主看版.html"
    if not source_html.exists():
        raise FileNotFoundError(source_html)
    data_files = (
        "material_freight_dashboard_data.js",
        "material_development_gantt_data.js",
        "inventory_outbound_data.js",
        "device_weekly_outbound_data.js",
        "material_weekly_outbound_data.js",
        "material_inventory_data.js",
    )
    names = hash_data_files(source_dir, MAIN_OUTPUT_DIR, data_files)
    html = source_html.read_text(encoding="utf-8")
    for original, hashed in names.items():
        old = f'<script src="{original}"></script>'
        new = f'<script src="assets/data/{hashed}"></script>'
        if old not in html:
            raise RuntimeError(f"主看版缺少资源引用：{old}")
        html = html.replace(old, new, 1)
    html = replace_font_faces(
        html,
        f"../material-dashboard/assets/fonts/{gotham.name}",
        f"../material-dashboard/assets/fonts/{yuan.name}",
    )
    html = html.replace('href="运费看板.html?month=5%E6%9C%88"', 'href="../material-freight-dashboard/?month=5%E6%9C%88"')
    html = html.replace('href="物料进销存看板.html"', 'href="../material-dashboard/"')
    html = html.replace("freightLink.href='运费看板.html?month='", "freightLink.href='../material-freight-dashboard/?month='")
    html = html.replace("</body>", service_worker_registration() + "</body>", 1)
    assets = [f"assets/data/{names[name]}" for name in data_files] + [
        f"../material-dashboard/assets/fonts/{gotham.name}",
        f"../material-dashboard/assets/fonts/{yuan.name}",
    ]
    return finish_static_dashboard(
        MAIN_OUTPUT_DIR,
        html,
        assets,
        "material-main-dashboard",
        source_dir,
        {"data": assets[: len(data_files)], "fonts": assets[len(data_files) :]},
        """# 物料综合主看板

访问地址：`https://dash.weishenghjxh.xyz/material-main-dashboard/`

由仓库根目录的 `一键更新物料看板.bat` 生成。更新时不要手工编辑本目录中的哈希文件。""",
    )


def build_freight_dashboard(source_dir: Path) -> dict[str, object]:
    source_html = source_dir / "运费看板.html"
    if not source_html.exists():
        raise FileNotFoundError(source_html)
    data_files = (
        "material_freight_dashboard_data.js",
        "material_freight_order_details.js",
        "material_freight_material_details.js",
        "material_freight_calculator_data.js",
    )
    names = hash_data_files(source_dir, FREIGHT_OUTPUT_DIR, data_files)
    html = source_html.read_text(encoding="utf-8")
    for original, hashed in names.items():
        old = f'<script src="{original}"></script>'
        new = f'<script src="assets/data/{hashed}"></script>'
        if old not in html:
            raise RuntimeError(f"运费看板缺少资源引用：{old}")
        html = html.replace(old, new, 1)
    nav_css = ".material-nav{display:flex;gap:8px}.material-nav a{display:inline-flex;align-items:center;padding:7px 10px;border:1px solid #e2e8f0;border-radius:8px;color:var(--t2);background:#fff;text-decoration:none;font-size:12px;font-weight:600}.material-nav a:hover{border-color:var(--acc);color:var(--acc)}"
    html = html.replace("</style>", nav_css + "\n</style>", 1)
    nav = '<nav class="material-nav" aria-label="物料看板导航"><a href="../material-main-dashboard/">综合主看板</a><a href="../material-dashboard/">进销存看板</a></nav>'
    html = html.replace('  <div class="upload-area">', f"  {nav}\n  <div class=\"upload-area\">", 1)
    html = html.replace("</body>", service_worker_registration() + "</body>", 1)
    assets = [f"assets/data/{names[name]}" for name in data_files]
    return finish_static_dashboard(
        FREIGHT_OUTPUT_DIR,
        html,
        assets,
        "material-freight-dashboard",
        source_dir,
        {"data": assets},
        """# 物料运费看板

访问地址：`https://dash.weishenghjxh.xyz/material-freight-dashboard/`

由仓库根目录的 `一键更新物料看板.bat` 生成。更新时不要手工编辑本目录中的哈希文件。""",
    )


def build(source_dir: Path, run_source_update: bool) -> dict[str, object]:
    source_html = source_dir / "物料进销存看板.html"
    source_update = REPO_DIR / "update_material_dashboard_sources.py"
    if not source_html.exists():
        raise FileNotFoundError(f"找不到源看板：{source_html}")

    if run_source_update:
        if not source_update.exists():
            raise FileNotFoundError(f"找不到源数据更新程序：{source_update}")
        print("[1/4] 从 Excel 重新生成物料看板数据...")
        subprocess.run(
            [sys.executable, str(source_update), "--source-dir", str(source_dir)],
            cwd=REPO_DIR,
            check=True,
        )
    else:
        print("[1/4] 跳过 Excel 数据生成，使用现有源看板。")

    print("[2/4] 拆分 HTML 与数据资源...")
    html = source_html.read_text(encoding="utf-8")
    values = {name: extract_assignment(html, name) for name in ASSIGNMENTS}

    core_lines = [
        f"window.DATA={values['DATA']};",
        f"window.INV={values['INV']};",
        f"window.SUPPLIER_PAYMENTS={values['SUPPLIER_PAYMENTS']};",
        f"window.SUPPLIER_DETAIL={values['SUPPLIER_DETAIL']};",
    ]
    core_bytes = ("\n".join(core_lines) + "\n").encode("utf-8")
    core_name = write_hashed(DATA_DIR, "core", ".js", core_bytes)

    orders_bytes = values["ORD"].encode("utf-8")
    orders_gzip = gzip.compress(orders_bytes, compresslevel=9, mtime=0)
    orders_name = write_hashed(DATA_DIR, "orders", ".json.gz", orders_gzip)

    p6_names: dict[str, str] = {}
    for filename in P6_DATA_FILES:
        source = source_dir / filename
        if not source.exists():
            raise FileNotFoundError(f"缺少省份分析数据文件：{source}")
        stem = Path(filename).stem.replace("_data", "")
        p6_names[filename] = write_hashed(DATA_DIR, stem, ".js", source.read_bytes())

    keep_data = {core_name, orders_name, *p6_names.values()}
    remove_old_hashed_files(
        DATA_DIR,
        {"core", "orders", "province_outbound", "province_material", "device_outbound"},
        keep_data,
    )

    html = replace_assignment(html, "DATA", "const DATA=window.DATA;")
    html = replace_assignment(html, "INV", "const INV=window.INV;")
    html = replace_assignment(html, "ORD", "let ORD=[];")
    html = replace_assignment(html, "SUPPLIER_PAYMENTS", "const SUPPLIER_PAYMENTS=window.SUPPLIER_PAYMENTS;")
    html = replace_assignment(html, "SUPPLIER_DETAIL", "const SUPPLIER_DETAIL=window.SUPPLIER_DETAIL;")

    script_replacements = {
        '<script src="province_outbound_data.js"></script>': f'<script src="assets/data/{p6_names["province_outbound_data.js"]}"></script>',
        '<script src="province_material_data.js"></script>': f'<script src="assets/data/{p6_names["province_material_data.js"]}"></script>',
        '<script src="device_outbound_data.js"></script>': f'<script src="assets/data/{p6_names["device_outbound_data.js"]}"></script>\n<script src="assets/data/{core_name}"></script>',
    }
    for old, new in script_replacements.items():
        if old not in html:
            raise RuntimeError(f"HTML 中缺少资源引用：{old}")
        html = html.replace(old, new, 1)

    print("[3/4] 应用精简 WOFF2 字体与按需数据加载...")
    gotham = find_font("gotham-rounded-bold")
    yuan = find_font("hk-yuan-w7")
    html = replace_font_faces(
        html,
        f"assets/fonts/{gotham.name}",
        f"assets/fonts/{yuan.name}",
    )

    loader = f"""
const ORDER_DATA_URL='assets/data/{orders_name}';
let orderDataPromise=null;
function ensureOrderData() {{
  if (ORD.length) return Promise.resolve(ORD);
  if (!orderDataPromise) {{
    document.body.classList.add('loading-order-data');
    orderDataPromise=fetch(ORDER_DATA_URL, {{cache:'force-cache'}})
      .then(function(response) {{
        if (!response.ok) throw new Error('出入库明细加载失败：'+response.status);
        if (!response.body || typeof DecompressionStream === 'undefined') {{
          throw new Error('当前浏览器版本过低，不支持压缩数据解包');
        }}
        const stream=response.body.pipeThrough(new DecompressionStream('gzip'));
        return new Response(stream).json();
      }})
      .then(function(rows) {{ ORD=rows; return ORD; }})
      .finally(function() {{ document.body.classList.remove('loading-order-data'); }});
  }}
  return orderDataPromise;
}}
"""
    marker = "// ── PAGE SWITCH ──"
    if marker not in html:
        raise RuntimeError("找不到页面切换代码标记")
    html = html.replace(marker, loader + "\n" + marker, 1)

    old_switch = """function switchPage(id, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  el.classList.add('active');
  setTimeout(() => { Object.values(charts).forEach(c => c.resize()); renderPage(id); }, 50);
}"""
    new_switch = """function switchPage(id, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  el.classList.add('active');
  setTimeout(() => {
    Object.values(charts).forEach(c => c.resize());
    const needsOrders = id === 'p1' || id === 'p4' || id === 'p5';
    const ready = needsOrders ? ensureOrderData() : Promise.resolve();
    ready.then(() => renderPage(id)).catch(error => {
      console.error(error);
      alert('出入库明细加载失败，请刷新页面后重试。');
    });
  }, 50);
}"""
    if old_switch not in html:
        raise RuntimeError("页面切换函数结构已变化，无法加入按需加载")
    html = html.replace(old_switch, new_switch, 1)
    html = html.replace(
        '<div class="nav-item" onclick="window.location.href=\'运费看板.html\'">',
        '<div class="nav-item" onclick="window.location.href=\'../material-freight-dashboard/\'">',
        1,
    )
    freight_nav = '<div class="nav-item" onclick="window.location.href=\'../material-freight-dashboard/\'"><span class="nav-icon">🚚</span>运费看板</div>'
    if freight_nav in html and "../material-main-dashboard/" not in html:
        main_nav = '<div class="nav-item" onclick="window.location.href=\'../material-main-dashboard/\'"><span class="nav-icon">📊</span>综合主看板</div>'
        html = html.replace(freight_nav, main_nav + "\n    " + freight_nav, 1)

    html = html.replace(
        "</style>",
        "body.loading-order-data::after{content:'正在加载出入库明细…';position:fixed;right:20px;bottom:20px;z-index:9999;padding:10px 14px;border-radius:9px;background:#1e3a8a;color:#fff;font-size:12px;box-shadow:0 8px 24px rgba(30,58,138,.24)}\n</style>",
        1,
    )
    html = html.replace("</body>", service_worker_registration() + "</body>", 1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_html = html.encode("utf-8")
    (OUTPUT_DIR / "index.html").write_bytes(output_html)

    # 大体积出入库明细不预缓存；首次进入 P1/P4/P5 后再由 fetch 处理器持久缓存。
    precache_data = keep_data - {orders_name}
    asset_urls = [
        f"assets/data/{name}" for name in sorted(precache_data)
    ] + [
        f"assets/fonts/{gotham.name}",
        f"assets/fonts/{yuan.name}",
    ]
    version_seed = "\n".join([sha256_short(output_html), *asset_urls]).encode("utf-8")
    version = sha256_short(version_seed)
    (OUTPUT_DIR / "sw.js").write_text(
        build_service_worker(asset_urls, version, "material-inventory-dashboard"), encoding="utf-8", newline="\n"
    )
    manifest = {
        "version": version,
        "builtAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": str(source_dir),
        "files": {
            "html": "index.html",
            "core": f"assets/data/{core_name}",
            "orders": f"assets/data/{orders_name}",
            "fonts": [f"assets/fonts/{gotham.name}", f"assets/fonts/{yuan.name}"],
            "province": [f"assets/data/{p6_names[name]}" for name in P6_DATA_FILES],
        },
    }
    (OUTPUT_DIR / "build-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("[4/4] 生成综合主看板与运费看板...")
    main_result = build_main_dashboard(source_dir, gotham, yuan)
    freight_result = build_freight_dashboard(source_dir)
    print("三个 GitHub Pages 看板文件均已生成。")
    return {
        "inventory": {
            "version": version,
            "htmlBytes": len(output_html),
            "ordersRawBytes": len(orders_bytes),
            "ordersGzipBytes": len(orders_gzip),
            "output": str(OUTPUT_DIR),
        },
        "main": main_result,
        "freight": freight_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 GitHub Pages 版物料综合、进销存与运费看板")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path(os.environ.get("MATERIAL_DASHBOARD_SOURCE", DEFAULT_SOURCE_DIR)),
        help="物料小组看板源目录",
    )
    parser.add_argument(
        "--skip-source-update",
        action="store_true",
        help="不读取独立 Excel 源数据，只转换当前 HTML 和 JS",
    )
    args = parser.parse_args()
    result = build(args.source_dir.resolve(), not args.skip_source_update)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n生成失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        raise
