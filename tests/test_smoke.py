"""Smoke tests for the initial repository scaffold."""

from __future__ import annotations

import importlib


def test_core_packages_import() -> None:
    modules = [
        "src",
        "src.cli",
        "src.data",
        "src.integrations",
        "src.qlib_integration",
        "src.rd_agent_adapter",
        "src.factors",
        "src.strategies",
        "src.backtest",
        "src.experiments",
        "src.validation",
        "src.reporting",
        "api.main",
        "dashboard.app",
    ]

    for module_name in modules:
        importlib.import_module(module_name)


def test_version_is_defined() -> None:
    package = importlib.import_module("src")

    assert package.__version__ == "0.1.0"


def test_cli_status_reflects_current_capabilities() -> None:
    from typer.testing import CliRunner

    from src.cli import app

    result = CliRunner().invoke(app, ["status"])

    assert result.exit_code == 0
    assert "synthetic demo" in result.output
    assert "not implemented yet" not in result.output
