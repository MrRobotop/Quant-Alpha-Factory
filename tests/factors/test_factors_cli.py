"""CLI tests for factor registry commands."""

from __future__ import annotations

from typer.testing import CliRunner

from src.cli import app


def test_factors_list() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["factors", "list"])

    assert result.exit_code == 0
    assert "momentum_20d" in result.output
    assert "risk_adjusted_momentum_20d" in result.output


def test_factors_describe() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["factors", "describe", "--name", "momentum_20d"])

    assert result.exit_code == 0
    assert '"name": "momentum_20d"' in result.output
    assert '"economic_rationale"' in result.output
    assert '"leakage_notes"' in result.output


def test_factors_describe_missing_factor_fails() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["factors", "describe", "--name", "missing"])

    assert result.exit_code == 1
    assert "Factor not found: missing" in result.output

