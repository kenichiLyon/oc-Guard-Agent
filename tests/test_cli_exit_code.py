from openclaw.cli import build_report, run


def test_run_returns_zero():
    exit_code = run(
        [
            "--config",
            "examples/openclaw.config.json",
            "--incident-file",
            "examples/incidents/pod_crashloop.json",
            "--format",
            "json",
        ]
    )
    assert exit_code == 0


def test_build_report_still_returns_report():
    report = build_report(
        [
            "--config",
            "examples/openclaw.config.json",
            "--incident-file",
            "examples/incidents/pod_crashloop.json",
            "--format",
            "json",
        ]
    )
    assert report["meta"]["engine"] == "openclaw"
