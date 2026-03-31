import sys
from pathlib import Path


BASE = Path(__file__).resolve().parents[2]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from openclaw.mcp_server import MCPServer


def test_mcp_initialize_and_tools_call():
    server = MCPServer()

    init_resp = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        }
    )
    assert init_resp is not None
    assert init_resp["result"]["serverInfo"]["name"] == "openclaw-agent"

    list_resp = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    assert list_resp is not None
    tool_names = [tool["name"] for tool in list_resp["result"]["tools"]]
    assert "openclaw_agent_diagnose" in tool_names
    assert "openclaw_diagnose" in tool_names

    call_resp = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "openclaw_agent_diagnose",
                "arguments": {
                    "config_path": str(BASE / "examples" / "openclaw.config.json"),
                    "incident": {
                        "title": "worker timeout",
                        "namespace": "default",
                        "service": "worker",
                        "symptoms": ["timeout"],
                        "time_window_minutes": 30,
                        "suspect_pod": "worker-99x",
                    },
                },
            },
        }
    )
    assert call_resp is not None
    result = call_resp["result"]
    assert result["isError"] is False
    assert result["structuredContent"]["meta"]["engine"] == "openclaw"
    assert result["structuredContent"]["meta"]["server"] == "openclaw-agent"
    assert result["structuredContent"]["meta"]["tool"] == "openclaw_agent_diagnose"


def test_mcp_legacy_tool_name_still_available():
    server = MCPServer()
    call_resp = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "openclaw_diagnose",
                "arguments": {
                    "config_path": str(BASE / "examples" / "openclaw.config.json"),
                    "incident": {
                        "title": "worker timeout",
                        "namespace": "default",
                    },
                },
            },
        }
    )
    assert call_resp is not None
    assert call_resp["result"]["isError"] is False
    assert call_resp["result"]["structuredContent"]["meta"]["tool"] == "openclaw_agent_diagnose"
