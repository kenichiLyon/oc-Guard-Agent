import json
import os
import sys


BASE = os.path.dirname(os.path.dirname(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from openclaw.config import load_config, load_incident
from openclaw.diagnosis import diagnose


def test_openclaw_diagnosis_has_five_layers():
    cfg = load_config(os.path.join(BASE, "examples", "openclaw.config.json"))
    inc = load_incident(file_path=os.path.join(BASE, "examples", "incidents", "pod_crashloop.json"))
    out = diagnose(inc, cfg)
    assert out["meta"]["engine"] == "openclaw"
    assert len(out["layers"]) == 5
    assert out["layers"][0]["layer"] == "现象"
    assert out["layers"][-1]["layer"] == "变更"
    assert isinstance(out["recommendations"], list) and len(out["recommendations"]) >= 2
    json.dumps(out, ensure_ascii=False)
