from __future__ import annotations

import json
from pathlib import Path

from slo_burn_rate.cli import main


def write_samples(path: Path, errors: int) -> None:
    path.write_text(
        "timestamp,total,errors\n"
        f"2026-01-01T11:56:00Z,1000,{errors}\n"
        f"2026-01-01T12:00:00Z,1000,{errors}\n",
        encoding="utf-8",
    )


def test_cli_renders_json(tmp_path: Path, capsys) -> None:
    path = tmp_path / "samples.csv"
    write_samples(path, errors=0)

    exit_code = main([str(path), "--format", "json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["availability"] == 1
    assert payload["firing_alert_count"] == 0


def test_cli_can_fail_pipeline_on_alert(tmp_path: Path) -> None:
    path = tmp_path / "samples.csv"
    write_samples(path, errors=100)

    assert main([str(path), "--fail-on-alert"]) == 2


def test_cli_returns_error_for_invalid_input(tmp_path: Path, capsys) -> None:
    path = tmp_path / "samples.csv"
    path.write_text("bad\n", encoding="utf-8")

    assert main([str(path)]) == 1
    assert "error:" in capsys.readouterr().err


def test_cli_renders_markdown(tmp_path: Path, capsys) -> None:
    path = tmp_path / "samples.csv"
    write_samples(path, errors=0)

    assert main([str(path), "--format", "markdown"]) == 0
    assert "# SLO burn-rate report" in capsys.readouterr().out
