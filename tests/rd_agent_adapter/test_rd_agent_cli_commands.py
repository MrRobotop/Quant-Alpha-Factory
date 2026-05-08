"""CLI tests for RD-Agent commands."""

from __future__ import annotations

from typer.testing import CliRunner

from src.cli import app


def test_rdagent_health_dry_run() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["rdagent", "health", "--dry-run"])

    assert result.exit_code == 0
    assert "RD-Agent dry-run." in result.output
    assert "rdagent health_check" in result.output


def test_rdagent_run_dry_run() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["rdagent", "run", "--mode", "fin_factor", "--loop-n", "1", "--dry-run"],
    )

    assert result.exit_code == 0
    assert "rdagent fin_factor --loop_n 1" in result.output


def test_rdagent_run_invalid_mode_fails_cleanly() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["rdagent", "run", "--mode", "bad_mode"])

    assert result.exit_code == 1
    assert "Unsupported RD-Agent mode: bad_mode" in result.output
