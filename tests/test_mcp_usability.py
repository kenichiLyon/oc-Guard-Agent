from pathlib import Path

from openclaw.config import load_config
from openclaw.mcp_server import MCPServer


BASE = Path(__file__).resolve().parents[1]


def test_load_config_uses_project_default(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg["mock_mode"] is True


def test_mcp_call_without_config_path_uses_default_config(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    server = MCPServer()
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "openclaw_agent_diagnose",
                "arguments": {
                    "incident": {
                        "title": "worker timeout",
                        "namespace": "default",
                        "service": "worker",
                        "symptoms": ["timeout"],
                    }
                },
            },
        }
    )
    assert response is not None
    assert response["result"]["isError"] is False
    assert response["result"]["structuredContent"]["meta"]["engine"] == "openclaw"
    assert response["result"]["structuredContent"]["meta"]["server"] == "openclaw-agent"


def test_project_example_config_exists():
    assert (BASE / "examples" / "openclaw.config.json").exists()
