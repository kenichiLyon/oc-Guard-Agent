import json
import subprocess
import urllib.parse
import urllib.request
from typing import Any, Dict, List


class ToolClients:
    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.cfg = cfg
        self.mock_mode = bool(cfg.get("mock_mode", False))
        self.mock = cfg.get("mock", {}) if isinstance(cfg.get("mock"), dict) else {}

    def _http_get(self, base_url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        query = urllib.parse.urlencode(params)
        url = f"{base_url}?{query}" if query else base_url
        req = urllib.request.Request(url=url, method="GET")
        with urllib.request.urlopen(req, timeout=int(self.cfg.get("http_timeout_sec", 10))) as resp:
            text = resp.read().decode("utf-8")
            try:
                return {"ok": True, "data": json.loads(text)}
            except Exception:
                return {"ok": True, "data": text}

    def _run(self, cmd: List[str]) -> Dict[str, Any]:
        try:
            p = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=int(self.cfg.get("command_timeout_sec", 15)),
                check=False,
                encoding="utf-8",
                errors="replace",
            )
            return {"ok": p.returncode == 0, "code": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
        except Exception as e:
            return {"ok": False, "code": -1, "stdout": "", "stderr": f"{type(e).__name__}: {e}"}

    def kubectl(self, args: List[str]) -> Dict[str, Any]:
        key = " ".join(args)
        if self.mock_mode:
            data = (self.mock.get("kubectl", {}) if isinstance(self.mock.get("kubectl"), dict) else {}).get(key, "")
            return {"ok": True, "code": 0, "stdout": str(data), "stderr": ""}
        cmd = [str(self.cfg.get("kubectl_bin", "kubectl"))] + args
        return self._run(cmd)

    def log_ql(self, query: str, namespace: str = "", service: str = "", minutes: int = 30) -> Dict[str, Any]:
        if self.mock_mode:
            m = self.mock.get("log_ql", {}) if isinstance(self.mock.get("log_ql"), dict) else {}
            return {"ok": True, "data": m.get(query) or m.get("default", "")}
        endpoint = str(self.cfg.get("log_ql_endpoint", "")).strip()
        if not endpoint:
            return {"ok": False, "error": "log_ql_endpoint 未配置"}
        return self._http_get(endpoint, {"query": query, "namespace": namespace, "service": service, "minutes": minutes})

    def promql(self, query: str) -> Dict[str, Any]:
        if self.mock_mode:
            m = self.mock.get("promql", {}) if isinstance(self.mock.get("promql"), dict) else {}
            return {"ok": True, "data": m.get(query) or m.get("default", {})}
        endpoint = str(self.cfg.get("promql_endpoint", "")).strip()
        if not endpoint:
            return {"ok": False, "error": "promql_endpoint 未配置"}
        return self._http_get(endpoint, {"query": query})

    def trace_analyzer(self, service: str, minutes: int = 30) -> Dict[str, Any]:
        if self.mock_mode:
            m = self.mock.get("trace_analyzer", {}) if isinstance(self.mock.get("trace_analyzer"), dict) else {}
            return {"ok": True, "data": m.get(service) or m.get("default", {})}
        endpoint = str(self.cfg.get("trace_endpoint", "")).strip()
        if not endpoint:
            return {"ok": False, "error": "trace_endpoint 未配置"}
        return self._http_get(endpoint, {"service": service, "minutes": minutes})

    def runbook_search(self, keywords: List[str]) -> Dict[str, Any]:
        key = " ".join([x for x in keywords if x])
        if self.mock_mode:
            m = self.mock.get("runbook_search", {}) if isinstance(self.mock.get("runbook_search"), dict) else {}
            return {"ok": True, "data": m.get(key) or m.get("default", [])}
        endpoint = str(self.cfg.get("runbook_endpoint", "")).strip()
        if not endpoint:
            return {"ok": False, "error": "runbook_endpoint 未配置"}
        return self._http_get(endpoint, {"keywords": key})
