"""Tests for controlled Qlib qrun execution."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src.qlib_integration.runner import (
    QlibRunError,
    QlibRunRequest,
    build_qrun_command,
    run_qlib_experiment,
)

BASELINE_CONFIG = Path("configs/qlib/baseline_lightgbm_alpha158.yaml")


def test_build_qrun_command() -> None:
    request = QlibRunRequest(config_path=BASELINE_CONFIG, qrun_executable="qrun")

    assert build_qrun_command(request) == ("qrun", str(BASELINE_CONFIG))


def test_dry_run_validates_config_and_does_not_execute(monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        calls.append(args[0])
        return subprocess.CompletedProcess(args[0], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_qlib_experiment(QlibRunRequest(config_path=BASELINE_CONFIG), dry_run=True)

    assert result.dry_run
    assert result.return_code is None
    assert calls == []


def test_execute_preserves_stdout_and_stderr_logs(tmp_path, monkeypatch) -> None:
    artifact_dir = tmp_path / "logs"

    def fake_run(command, check, capture_output, text):  # noqa: ANN001
        assert check is False
        assert capture_output is True
        assert text is True
        return subprocess.CompletedProcess(command, returncode=0, stdout="stdout", stderr="stderr")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_qlib_experiment(
        QlibRunRequest(config_path=BASELINE_CONFIG, artifact_dir=artifact_dir),
        dry_run=False,
    )

    assert result.return_code == 0
    assert (artifact_dir / "qrun_stdout.log").read_text(encoding="utf-8") == "stdout"
    assert (artifact_dir / "qrun_stderr.log").read_text(encoding="utf-8") == "stderr"


def test_subprocess_failure_preserves_logs_and_raises(tmp_path, monkeypatch) -> None:
    artifact_dir = tmp_path / "logs"

    def fake_run(command, check, capture_output, text):  # noqa: ANN001
        return subprocess.CompletedProcess(command, returncode=2, stdout="out", stderr="err")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(QlibRunError, match="return code 2"):
        run_qlib_experiment(
            QlibRunRequest(config_path=BASELINE_CONFIG, artifact_dir=artifact_dir),
            dry_run=False,
        )

    assert (artifact_dir / "qrun_stdout.log").read_text(encoding="utf-8") == "out"
    assert (artifact_dir / "qrun_stderr.log").read_text(encoding="utf-8") == "err"


def test_invalid_config_blocks_qrun(tmp_path, monkeypatch) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("task: {}\n", encoding="utf-8")
    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        calls.append(args[0])
        return subprocess.CompletedProcess(args[0], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(QlibRunError, match="invalid config"):
        run_qlib_experiment(QlibRunRequest(config_path=path), dry_run=False)

    assert calls == []

