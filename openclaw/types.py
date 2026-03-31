from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass
class Incident:
    title: str
    namespace: str = "default"
    service: str = ""
    symptoms: List[str] = field(default_factory=list)
    time_window_minutes: int = 30
    suspect_pod: str = ""


@dataclass
class Evidence:
    source: str
    summary: str
    data: Any


@dataclass
class LayerResult:
    layer: str
    findings: List[str] = field(default_factory=list)
    evidences: List[Evidence] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer,
            "findings": self.findings,
            "evidences": [asdict(x) for x in self.evidences],
        }
