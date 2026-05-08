"""Tests for the synthetic end-to-end demo."""

from __future__ import annotations

from typer.testing import CliRunner

from src.cli import app
from src.demo.synthetic import run_synthetic_demo
from src.experiments.store import ExperimentStore


def test_run_synthetic_demo_creates_manifest_report_and_leaderboard(tmp_path) -> None:
    result = run_synthetic_demo(
        experiment_store_root=tmp_path / "experiments",
        report_output_dir=tmp_path / "reports",
    )

    manifest = ExperimentStore(tmp_path / "experiments").get("synthetic-demo")
    report_text = result.report_path.read_text(encoding="utf-8")

    assert result.experiment_id == "synthetic-demo"
    assert result.manifest_path.exists()
    assert result.report_path.exists()
    assert result.validation_summary.startswith("Market data validation valid")
    assert "qlib.scripts.dump_bin" in " ".join(result.qlib_conversion_command)
    assert result.qlib_run_command == ("qrun", "configs/qlib/baseline_lightgbm_alpha158.yaml")
    assert result.rdagent_command == ("rdagent", "fin_factor", "--loop_n", "1")
    assert result.leaderboard_rows == 1
    assert manifest.status == "succeeded"
    assert manifest.universe == "synthetic_sample"
    assert manifest.notes is not None
    assert "Synthetic demo only" in manifest.notes
    assert "net_return" in manifest.metrics
    assert "Synthetic demo only" in report_text
    assert "no performance values are inferred or fabricated" in report_text


def test_synthetic_demo_cli(tmp_path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "demo",
            "synthetic",
            "--store",
            str(tmp_path / "experiments"),
            "--report-dir",
            str(tmp_path / "reports"),
        ],
    )

    assert result.exit_code == 0
    assert "Synthetic demo completed." in result.output
    assert "Experiment ID: synthetic-demo" in result.output
    assert "Qlib conversion dry-run command:" in result.output
    assert "RD-Agent dry-run command:" in result.output
    assert (tmp_path / "experiments" / "synthetic-demo" / "manifest.json").exists()
    assert (tmp_path / "reports" / "synthetic-demo.md").exists()

