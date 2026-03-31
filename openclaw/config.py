import json
import os
from typing import Any, Dict


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _default_config_path() -> str:
    packaged = os.path.join(os.path.dirname(os.path.abspath(__file__)), "default_config.json")
    if os.path.exists(packaged):
        return packaged
    return os.path.join(_project_root(), "examples", "openclaw.config.json")


def load_config(config_path: str = "") -> Dict[str, Any]:
    path = config_path.strip() or os.getenv("OPENCLAW_CONFIG", "").strip()
    if not path:
        path = _default_config_path()
    if not os.path.exists(path):
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("配置文件必须是 JSON 对象")
    return data


def load_incident(file_path: str = "", json_text: str = "") -> Dict[str, Any]:
    if json_text.strip():
        data = json.loads(json_text)
    elif file_path.strip():
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        raise ValueError("需提供 incident 文件或 JSON 文本")
    if not isinstance(data, dict):
        raise ValueError("incident 必须是 JSON 对象")
    return data
