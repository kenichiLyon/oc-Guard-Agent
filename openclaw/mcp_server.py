import json
import sys
from typing import Any, Dict, Optional

from .config import load_config
from .diagnosis import diagnose

SERVER_NAME = "openclaw-agent"
SERVER_VERSION = "0.1.0"
PRIMARY_TOOL_NAME = "openclaw_agent_diagnose"
LEGACY_TOOL_NAME = "openclaw_diagnose"


class MCPServer:
    def __init__(self) -> None:
        self.server_info = {"name": SERVER_NAME, "version": SERVER_VERSION}
        input_schema = {
            "type": "object",
            "properties": {
                "incident": {
                    "type": "object",
                    "description": "故障输入对象",
                    "properties": {
                        "title": {"type": "string"},
                        "namespace": {"type": "string"},
                        "service": {"type": "string"},
                        "symptoms": {"type": "array", "items": {"type": "string"}},
                        "time_window_minutes": {"type": "integer"},
                        "suspect_pod": {"type": "string"},
                    },
                    "required": ["title"],
                },
                "config_path": {"type": "string", "description": "OpenClaw 配置文件路径"},
            },
            "required": ["incident"],
        }
        self.tool_schemas = [
            {
                "name": PRIMARY_TOOL_NAME,
                "description": "openclaw-agent 对 openclaw 五层诊断引擎的 MCP 封装",
                "inputSchema": input_schema,
            },
            {
                "name": LEGACY_TOOL_NAME,
                "description": "兼容旧调用名，等价于 openclaw_agent_diagnose",
                "inputSchema": input_schema,
            },
        ]

    def _success(self, req_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _error(self, req_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = str(request.get("method", ""))
        req_id = request.get("id")
        params = request.get("params", {}) if isinstance(request.get("params"), dict) else {}

        if method == "notifications/initialized":
            return None
        if method == "initialize":
            version = str(params.get("protocolVersion", "2024-11-05"))
            return self._success(
                req_id,
                {
                    "protocolVersion": version,
                    "capabilities": {"tools": {}},
                    "serverInfo": self.server_info,
                },
            )
        if method == "ping":
            return self._success(req_id, {})
        if method == "tools/list":
            return self._success(req_id, {"tools": self.tool_schemas})
        if method == "tools/call":
            name = str(params.get("name", ""))
            arguments = params.get("arguments", {}) if isinstance(params.get("arguments"), dict) else {}
            if name not in {PRIMARY_TOOL_NAME, LEGACY_TOOL_NAME}:
                return self._error(req_id, -32602, f"未知工具: {name}")
            incident = arguments.get("incident")
            if not isinstance(incident, dict):
                return self._error(req_id, -32602, "incident 必须是对象")
            config_path = str(arguments.get("config_path", ""))
            try:
                cfg = load_config(config_path)
                report = diagnose(incident, cfg)
                report["meta"]["server"] = SERVER_NAME
                report["meta"]["tool"] = PRIMARY_TOOL_NAME
            except Exception as e:
                return self._success(
                    req_id,
                    {
                        "content": [{"type": "text", "text": json.dumps({"error": str(e)}, ensure_ascii=False)}],
                        "isError": True,
                    },
                )
            return self._success(
                req_id,
                {
                    "content": [{"type": "text", "text": json.dumps(report, ensure_ascii=False)}],
                    "structuredContent": report,
                    "isError": False,
                },
            )
        return self._error(req_id, -32601, f"未知方法: {method}")


def _read_message() -> Optional[Dict[str, Any]]:
    headers: Dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        text = line.decode("utf-8").strip()
        if ":" in text:
            key, value = text.split(":", 1)
            headers[key.strip().lower()] = value.strip()
    content_length = int(headers.get("content-length", "0"))
    if content_length <= 0:
        return None
    body = sys.stdin.buffer.read(content_length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def _write_message(payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def run_stdio_server() -> None:
    server = MCPServer()
    while True:
        request = _read_message()
        if request is None:
            break
        response = server.handle_request(request)
        if response is not None:
            _write_message(response)
