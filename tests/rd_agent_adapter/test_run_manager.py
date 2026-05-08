"""Tests for safe RD-Agent execution manager."""

from __future__ import annotations

import subprocess

import pytest

from src.experiments.store import ExperimentStore
from src.rd_agent_adapter.commands import RDAgentCommandConfig
from src.rd_agent_adapter.run_manager import RDAgentRunError, RDAgentRunRequest, run_rdagent


def test_dry_run_does_not_execute(monkeypatch, tmp_path) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        calls.append(args[0])
        return subprocess.CompletedProcess(args[0], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_rdagent(
        RDAgentRunRequest(
            command_config=RDAgentCommandConfig(mode="fin_factor", loop_n=1),
            artifact_dir=tmp_path / "logs",
            experiment_store=tmp_path / "experiments",
        ),
        dry_run=True,
    )

    assert result.dry_run
    assert result.return_code is None
    assert calls == []


def test_execute_success_writes_logs_and_manifest(monkeypatch, tmp_path) -> None:
    def fake_run(command, check, capture_output, text):  # noqa: ANN001
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, returncode=1, stdout="", stderr="")
        assert command[0].endswith("rdagent")
        assert command[1:] == ("fin_factor", "--loop_n", "1")
        assert check is False
        assert capture_output is True
        assert text is True
        return subprocess.CompletedProcess(command, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    store_root = tmp_path / "experiments"

    result = run_rdagent(
        RDAgentRunRequest(
            command_config=RDAgentCommandConfig(mode="fin_factor", loop_n=1),
            artifact_dir=tmp_path / "logs",
            experiment_store=store_root,
        ),
        dry_run=False,
    )

    assert result.return_code == 0
    assert result.manifest is not None
    assert result.manifest.status == "succeeded"
    assert (tmp_path / "logs" / "rdagent_stdout.log").read_text(encoding="utf-8") == "ok"
    assert ExperimentStore(store_root).get(result.manifest.experiment_id) == result.manifest


def test_execute_failure_records_failed_manifest(monkeypatch, tmp_path) -> None:
    def fake_run(command, check, capture_output, text):  # noqa: ANN001
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, returncode=1, stdout="", stderr="")
        return subprocess.CompletedProcess(command, returncode=2, stdout="out", stderr="bad")

    monkeypatch.setattr(subprocess, "run", fake_run)
    store_root = tmp_path / "experiments"

    with pytest.raises(RDAgentRunError, match="return code 2"):
        run_rdagent(
            RDAgentRunRequest(
                command_config=RDAgentCommandConfig(mode="fin_model"),
                artifact_dir=tmp_path / "logs",
                experiment_store=store_root,
            ),
            dry_run=False,
        )

    manifests = ExperimentStore(store_root).list()
    assert len(manifests) == 1
    assert manifests[0].status == "failed"
    assert manifests[0].failure_reason == "bad"
