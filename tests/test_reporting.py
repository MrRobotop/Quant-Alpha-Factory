"""Tests for research reporting."""

from __future__ import annotations

import sys

import pandas as pd
import pytest
from typer.testing import CliRunner

from src.cli import app
from src.experiments.manifest import create_experiment_manifest
from src.experiments.schema import DateSplit, TransactionCostAssumptions
from src.experiments.store import ExperimentStore
from src.reporting.markdown import build_experiment_report, write_experiment_report
from src.reporting.plots import save_equity_curve_plot


def test_build_report_includes_manifest_metadata_and_limitations(tmp_path) -> None:
    manifest = create_experiment_manifest(
        experiment_id="exp-report",
        status="succeeded",
        config_path="configs/qlib/baseline_lightgbm_alpha158.yaml",
        data_source_path="data/sample/prices.csv",
        seed=42,
        universe="sample",
        benchmark="SPY",
        date_split=DateSplit(
            train_start="2024-01-01",
            train_end="2024-06-30",
            valid_start="2024-07-01",
            valid_end="2024-09-30",
            test_start="2024-10-01",
            test_end="2024-12-31",
        ),
        transaction_cost=TransactionCostAssumptions(open_cost=0.0005, close_cost=0.0015),
        metrics={"net_return": 0.01, "turnover": 0.2},
        artifact_paths={"metrics": tmp_path / "metrics.json"},
        command=["qrun", "config.yaml"],
    )

    report = build_experiment_report(manifest)

    assert "# Experiment Report: exp-report" in report
    assert "Universe: sample" in report
    assert "Benchmark: SPY" in report
    assert "net_return" in report
    assert "turnover" in report
    assert "Open Cost" in report
    assert "Limitations" in report
    assert "no performance values are inferred or fabricated" in report


def test_build_report_marks_missing_metrics_not_available() -> None:
    manifest = create_experiment_manifest(
        experiment_id="exp-missing",
        status="failed",
        failure_reason="qrun failed",
    )

    report = build_experiment_report(manifest)

    assert "Metrics: not available" in report
    assert "Transaction costs: not available" in report
    assert "Failure Reason: qrun failed" in report


def test_write_experiment_report(tmp_path) -> None:
    manifest = create_experiment_manifest(experiment_id="exp-write", status="succeeded")

    path = write_experiment_report(manifest, tmp_path)

    assert path == tmp_path / "exp-write.md"
    assert path.exists()
    assert "exp-write" in path.read_text(encoding="utf-8")


def test_report_cli_builds_markdown(tmp_path) -> None:
    store = ExperimentStore(tmp_path / "experiments")
    store.save(create_experiment_manifest(experiment_id="exp-cli", status="succeeded"))
    output_dir = tmp_path / "reports"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "report",
            "build",
            "--experiment-id",
            "exp-cli",
            "--store",
            str(tmp_path / "experiments"),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Report written:" in result.output
    assert (output_dir / "exp-cli.md").exists()


def test_report_cli_missing_experiment_fails(tmp_path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "report",
            "build",
            "--experiment-id",
            "missing",
            "--store",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "Experiment not found: missing" in result.output


def test_plotting_missing_dependency_raises(monkeypatch, tmp_path) -> None:
    monkeypatch.setitem(sys.modules, "matplotlib", None)

    with pytest.raises(RuntimeError, match="Plotting requires"):
        save_equity_curve_plot(pd.Series([1.0, 1.1]), tmp_path / "plot.png")

