"""Serve the annual report builder and its local template/image libraries."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import struct
import threading
import urllib.error
import urllib.request
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlsplit


ROOT = Path(__file__).resolve().parent
IMAGE_LIBRARY_ROOT = Path(r"C:\Users\shenw\Desktop\看板\150ppi")
TEMPLATE_LIBRARY_ROOT = Path(r"C:\Users\shenw\Desktop\HTML预设文件合集")
DEFAULT_MODEL = "gpt-6-astra"
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
MAX_REQUEST_BYTES = 256 * 1024
MAX_MESSAGE_CHARS = 4_000

LAYOUT_FAMILIES = {
    "8-bit-orbit.html": "asymmetric",
    "新建 文本文档 (2).HTML": "data-wall",
    "新建 文本文档.html": "editorial",
    "capsule.html": "cards-grid",
    "cobalt-grid.html": "asymmetric",
    "daisy-days.html": "cards-grid",
    "editorial-forest.html": "editorial",
    "pin-and-paper.html": "chart-focus",
    "pink-script.html.html": "two-column",
    "playful.html": "cards-grid",
    "retro-windows.html": "data-wall",
    "retro-zine.html": "asymmetric",
    "sakura-chroma.html": "two-column",
    "signal-gold.html": "chart-focus",
    "soft-editorial.html": "editorial",
    "stencil-tablet.html": "data-wall",
    "vellum-navy.html": "two-column",
}

LAYOUT_LABELS = {
    "asymmetric": "非对称网格",
    "data-wall": "数据墙",
    "editorial": "杂志分栏",
    "cards-grid": "卡片矩阵",
    "chart-focus": "主图优先",
    "two-column": "双栏叙事",
}

ALLOWED_ACTIONS = [
    "set-page-field",
    "set-chart-view",
    "set-chart-config",
    "set-element-style",
    "add-page",
    "duplicate-page",
    "delete-selected-element",
    "reset-layout",
    "undo",
    "redo",
]

OPERATION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ALLOWED_ACTIONS},
        "target": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "field": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "property": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "value": {
            "anyOf": [
                {"type": "string"},
                {"type": "number"},
                {"type": "boolean"},
                {"type": "null"},
            ]
        },
        "module": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "chartId": {"anyOf": [{"type": "string"}, {"type": "null"}]},
    },
    "required": [
        "action",
        "target",
        "field",
        "property",
        "value",
        "module",
        "chartId",
    ],
    "additionalProperties": False,
}

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "operations": {
            "type": "array",
            "items": OPERATION_SCHEMA,
            "maxItems": 20,
        },
        "response": {"type": "string"},
    },
    "required": ["operations", "response"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """
你是皇家小虎年度汇报编辑器的操作规划助手。你的唯一职责是把用户的中文修改要求转换为受控操作。

必须遵守：
1. 只能使用输出结构允许的 action，绝不输出代码、HTML、JavaScript、命令或解释性字段。
2. 只修改用户明确要求的内容；信息不足时返回空 operations，并在 response 中说明需要补充什么。
3. 同一请求可以返回多个操作，但最多 20 个。
4. target 仅使用 primary-chart、secondary-chart、selected、all-kpis；不适用时填 null。
5. module 仅使用 display、approval、store；不适用时填 null。
6. 页面字段 field 仅使用 title、summary、analysisTitle、analysisLead、recommendation。
7. 图表 property 仅使用 visual、metric、sort、topN、showLabels、showLegend、primaryColor、secondaryColor、xAxisTitle、yAxisTitle。
8. visual 值仅使用 auto、combo、bar、line、rank；metric 仅使用 value、rate；sort 仅使用 source、value-desc、value-asc、rate-desc、rate-asc。
9. 组件样式 property 仅使用 fontSize、color、background、textAlign、fontFamily。
10. chartId 必须从当前上下文的 chartOptions 中选择。颜色必须是 #RRGGBB。
11. 删除操作仅在用户明确要求删除时使用。不要推测或创造不存在的数据。

response 使用简短中文，说明将执行或无法执行的内容。
""".strip()


class ConfigurationError(RuntimeError):
    pass


class UpstreamError(RuntimeError):
    pass


def json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def png_dimensions(path: Path) -> tuple[int, int]:
    """Read PNG dimensions without loading the full image into memory."""
    try:
        with path.open("rb") as stream:
            header = stream.read(24)
        if header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR":
            return struct.unpack(">II", header[16:24])
    except OSError:
        pass
    return (0, 0)


def image_library() -> list[dict[str, Any]]:
    if not IMAGE_LIBRARY_ROOT.is_dir():
        return []
    assets = []
    for path in sorted(IMAGE_LIBRARY_ROOT.iterdir(), key=lambda item: item.name.casefold()):
        if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        width, height = png_dimensions(path) if path.suffix.lower() == ".png" else (0, 0)
        assets.append(
            {
                "name": path.name,
                "width": width,
                "height": height,
                "url": f"/api/report-assets/image?name={quote(path.name)}",
            }
        )
    return assets


def layout_library() -> list[dict[str, str]]:
    if not TEMPLATE_LIBRARY_ROOT.is_dir():
        return []
    layouts = []
    for path in sorted(TEMPLATE_LIBRARY_ROOT.iterdir(), key=lambda item: item.name.casefold()):
        if not path.is_file() or path.suffix.lower() not in {".html", ".htm"}:
            continue
        family = LAYOUT_FAMILIES.get(path.name, "two-column")
        layouts.append(
            {
                "template": path.name,
                "name": path.stem,
                "layoutId": family,
                "layoutName": LAYOUT_LABELS[family],
            }
        )
    return layouts


def safe_library_file(root: Path, name: str) -> Path | None:
    if not name or Path(name).name != name:
        return None
    candidate = (root / name).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def service_status() -> dict[str, Any]:
    mock = os.environ.get("REPORT_AI_MOCK") == "1"
    configured = mock or bool(os.environ.get("OPENAI_API_KEY", "").strip())
    return {
        "configured": configured,
        "provider": "mock" if mock else ("openai" if configured else "local"),
        "model": os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
    }


def extract_output_text(response: dict[str, Any]) -> str:
    if response.get("status") == "incomplete":
        reason = (response.get("incomplete_details") or {}).get("reason", "unknown")
        raise UpstreamError(f"AI response was incomplete: {reason}")
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "refusal":
                raise UpstreamError(content.get("refusal") or "The model refused the request")
            if content.get("type") == "output_text" and content.get("text"):
                return content["text"]
    raise UpstreamError("The model did not return structured output")


def validate_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise UpstreamError("AI output is not an object")
    operations = value.get("operations")
    response = value.get("response")
    if not isinstance(operations, list) or not isinstance(response, str):
        raise UpstreamError("AI output is missing operations or response")
    cleaned: list[dict[str, Any]] = []
    allowed_keys = {"action", "target", "field", "property", "value", "module", "chartId"}
    for operation in operations[:20]:
        if not isinstance(operation, dict) or operation.get("action") not in ALLOWED_ACTIONS:
            continue
        cleaned.append({key: operation.get(key) for key in allowed_keys})
    return {"operations": cleaned, "response": response[:800]}


def mock_result(payload: dict[str, Any]) -> dict[str, Any]:
    message = str(payload.get("message", ""))
    match = re.search(r"(?:页面)?标题(?:改成|修改为|设置为)\s*[：:]?\s*(.+)$", message)
    if match:
        operation = {
            "action": "set-page-field",
            "target": None,
            "field": "title",
            "property": None,
            "value": match.group(1).strip(),
            "module": None,
            "chartId": None,
        }
        return {"operations": [operation], "response": "模拟 AI 服务已完成标题修改。"}
    return {"operations": [], "response": "模拟 AI 服务已连接，请使用“页面标题改成……”进行联调。"}


def call_openai(payload: dict[str, Any]) -> dict[str, Any]:
    if os.environ.get("REPORT_AI_MOCK") == "1":
        return mock_result(payload)

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ConfigurationError("未配置 OPENAI_API_KEY，当前继续使用本地安全指令模式。")

    user_input = {
        "request": payload.get("message"),
        "current_report_context": payload.get("context", {}),
        "client_operation_schema": payload.get("schema", {}),
    }
    request_body = {
        "model": os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(user_input, ensure_ascii=False, separators=(",", ":")),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "annual_report_operations",
                "strict": True,
                "schema": RESPONSE_SCHEMA,
            }
        },
        "max_output_tokens": 2_500,
        "store": False,
    }
    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json_bytes(request_body),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            upstream = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body).get("error", {}).get("message")
        except json.JSONDecodeError:
            detail = None
        raise UpstreamError(detail or f"OpenAI API returned HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise UpstreamError(f"无法连接 OpenAI API：{error.reason}") from error

    output_text = extract_output_text(upstream)
    try:
        parsed = json.loads(output_text)
    except json.JSONDecodeError as error:
        raise UpstreamError("AI returned invalid JSON") from error
    return validate_result(parsed)


class ReportAIHandler(SimpleHTTPRequestHandler):
    server_version = "ReportAI/1.0"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def list_directory(self, path: str):  # type: ignore[override]
        self.send_error(HTTPStatus.FORBIDDEN, "Directory listing is disabled")
        return None

    def send_json(self, status: int, value: Any) -> None:
        body = json_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/api/report-assets/images":
            self.send_json(HTTPStatus.OK, {"items": image_library(), "root": str(IMAGE_LIBRARY_ROOT)})
            return
        if parsed.path == "/api/report-layouts":
            self.send_json(HTTPStatus.OK, {"items": layout_library(), "root": str(TEMPLATE_LIBRARY_ROOT)})
            return
        if parsed.path == "/api/report-assets/image":
            name = parse_qs(parsed.query).get("name", [""])[0]
            asset = safe_library_file(IMAGE_LIBRARY_ROOT, name)
            if asset is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Image not found")
                return
            content_type = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
            try:
                body = asset.read_bytes()
            except OSError:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Unable to read image")
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/report-ai/status":
            self.send_json(HTTPStatus.OK, service_status())
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] != "/api/report-ai":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self.send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "请求内容过大或为空。"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "请求不是有效的 JSON。"})
            return
        if not isinstance(payload, dict) or not isinstance(payload.get("message"), str):
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "缺少有效的 message。"})
            return
        if len(payload["message"]) > MAX_MESSAGE_CHARS:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "指令过长，请缩短后重试。"})
            return
        try:
            result = call_openai(payload)
        except ConfigurationError as error:
            self.send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(error), "code": "api_key_missing"})
            return
        except UpstreamError as error:
            self.send_json(HTTPStatus.BAD_GATEWAY, {"error": str(error), "code": "upstream_error"})
            return
        except Exception as error:
            self.log_error("Unexpected report AI error: %s", error)
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "AI 服务发生未预期错误。"})
            return
        self.send_json(HTTPStatus.OK, result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the annual report builder with local asset support.")
    parser.add_argument("--host", default=os.environ.get("REPORT_AI_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("REPORT_AI_PORT", "8765")))
    parser.add_argument("--open", action="store_true", help="Open the report builder in the default browser.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    url = f"http://{args.host}:{args.port}/annual-report-builder.html"
    server = ThreadingHTTPServer((args.host, args.port), ReportAIHandler)
    print(f"Annual report builder: {url}")
    print(f"Local layouts: {len(layout_library())}; local images: {len(image_library())}")
    if args.open:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
