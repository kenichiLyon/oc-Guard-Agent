import argparse
import json
from typing import Any, Dict

from .config import load_config, load_incident
from .diagnosis import diagnose


def run(argv=None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(prog="openclaw")
    parser.add_argument("--config", type=str, default="", help="OpenClaw 配置文件路径")
    parser.add_argument("--incident-file", type=str, default="", help="故障输入 JSON 文件")
    parser.add_argument("--incident-json", type=str, default="", help="故障输入 JSON 文本")
    parser.add_argument("--format", type=str, default="pretty", choices=["pretty", "json"], help="输出格式")
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    incident = load_incident(file_path=args.incident_file, json_text=args.incident_json)
    report = diagnose(incident, cfg)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return report
