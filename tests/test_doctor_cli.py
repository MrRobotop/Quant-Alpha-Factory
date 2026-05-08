"""CLI tests for real-execution readiness checks."""

from __future__ import annotations

from typer.testing import CliRunner

from src.cli import app


def test_doctor_reports_readiness_without_strict_exit() -> None:
    result = CliRunner().invoke(app, ["doctor", "--component", "rdagent", "--skip-docker-daemon"])

    assert result.exit_code == 0
    assert "readiness=" in result.output
    assert "llm_credentials" in result.output


def test_doctor_strict_exits_nonzero_when_missing_prerequisites() -> None:
    result = CliRunner().invoke(
        app,
        ["doctor", "--component", "rdagent", "--skip-docker-daemon", "--strict"],
    )

    assert result.exit_code == 1
    assert "readiness=not_ready" in result.output


def test_doctor_can_allow_missing_llm_for_public_preflight() -> None:
    result = CliRunner().invoke(
        app,
        [
            "doctor",
            "--component",
            "rdagent",
            "--skip-docker-daemon",
            "--allow-missing-llm",
            "--strict",
        ],
    )

    assert result.exit_code == 0
    assert "llm_credentials" in result.output
    assert "warn" in result.output


def test_doctor_rejects_unknown_component() -> None:
    result = CliRunner().invoke(app, ["doctor", "--component", "bad"])

    assert result.exit_code == 1
    assert "Unsupported component" in result.output
