"""CLI tests for experiment store commands."""

from __future__ import annotations

from typer.testing import CliRunner

from src.cli import app
from src.experiments.manifest import create_experiment_manifest
from src.experiments.store import ExperimentStore


def test_experiments_list_empty_store(tmp_path) -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["experiments", "list", "--store", str(tmp_path)])

    assert result.exit_code == 0
    assert "No experiments found." in result.output


def test_experiments_list_show_and_leaderboard(tmp_path) -> None:
    store = ExperimentStore(tmp_path)
    store.save(
        create_experiment_manifest(
            experiment_id="exp-a",
            status="succeeded",
            benchmark="SPY",
            universe="sample",
            metrics={"net_return": 0.02},
        )
    )
    store.save(
        create_experiment_manifest(
            experiment_id="exp-b",
            status="failed",
            failure_reason="qrun failed",
            metrics={},
        )
    )
    runner = CliRunner()

    list_result = runner.invoke(app, ["experiments", "list", "--store", str(tmp_path)])
    show_result = runner.invoke(
        app,
        ["experiments", "show", "--store", str(tmp_path), "--experiment-id", "exp-a"],
    )
    leaderboard_result = runner.invoke(
        app,
        ["experiments", "leaderboard", "--store", str(tmp_path), "--metric", "net_return"],
    )

    assert list_result.exit_code == 0
    assert "exp-a" in list_result.output
    assert "exp-b" in list_result.output
    assert show_result.exit_code == 0
    assert '"experiment_id": "exp-a"' in show_result.output
    assert leaderboard_result.exit_code == 0
    assert "exp-a\tsucceeded\tnet_return\t0.02\tSPY\tsample" in leaderboard_result.output
    assert "exp-b\tfailed\tnet_return\tNA" in leaderboard_result.output


def test_experiments_show_missing_experiment_fails(tmp_path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["experiments", "show", "--store", str(tmp_path), "--experiment-id", "missing"],
    )

    assert result.exit_code == 1
    assert "Experiment not found: missing" in result.output

