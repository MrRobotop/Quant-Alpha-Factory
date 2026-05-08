"""Tests for the synthetic Qlib demo orchestration."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src.data.qlib_converter import QlibConversionResult
from src.experiments.store import ExperimentStore
from src.qlib_integration.demo import QlibDemoError, QlibDemoRequest, run_qlib_synthetic_demo
from src.qlib_integration.runner import QlibRunError, QlibRunResult


def fake_git_run(*args, **kwargs):  # noqa: ANN002, ANN003
    return subprocess.CompletedProcess(args[0], returncode=1, stdout="", stderr="")


def write_config(path: Path) -> None:
    path.write_text(
        "qlib_init:\n"
        "  provider_uri: data/qlib_bin/sample\n"
        "task:\n"
        "  model: {}\n"
        "  dataset:\n"
        "    kwargs:\n"
        "      handler:\n"
        "        kwargs:\n"
        "          fit_start_time: '2024-01-02'\n"
        "          fit_end_time: '2024-06-30'\n"
        "      segments:\n"
        "        train: ['2024-01-02', '2024-06-30']\n"
        "        valid: ['2024-07-01', '2024-09-30']\n"
        "        test: ['2024-10-01', '2024-12-31']\n"
        "  record: []\n"
        "experiment:\n"
        "  seed: 42\n"
        "  universe: sample\n"
        "  benchmark: SPY\n"
        "  transaction_cost:\n"
        "    open_cost: 0.0005\n"
        "    close_cost: 0.0015\n"
        "    min_cost: 5\n",
        encoding="utf-8",
    )


def write_data(path: Path) -> None:
    path.write_text("date,symbol,open,high,low,close,volume\n", encoding="utf-8")


def test_qlib_demo_dry_run_records_manifest(tmp_path, monkeypatch) -> None:
    config = tmp_path / "config.yaml"
    data = tmp_path / "prices.csv"
    write_config(config)
    write_data(data)

    def fake_convert(config, dry_run):  # noqa: ANN001
        return QlibConversionResult(command=("convert",), dry_run=dry_run, return_code=None)

    def fake_qrun(request, dry_run):  # noqa: ANN001
        return QlibRunResult(
            command=("qrun", str(request.config_path)),
            dry_run=dry_run,
            return_code=None,
        )

    monkeypatch.setattr("src.qlib_integration.demo.convert_to_qlib", fake_convert)
    monkeypatch.setattr("src.qlib_integration.demo.run_qlib_experiment", fake_qrun)
    monkeypatch.setattr(subprocess, "run", fake_git_run)

    result = run_qlib_synthetic_demo(
        QlibDemoRequest(
            input_path=data,
            output_dir=tmp_path / "qlib",
            config_path=config,
            experiment_store=tmp_path / "experiments",
            mlruns_dir=tmp_path / "mlruns",
        ),
        dry_run=True,
    )

    assert result.manifest.status == "succeeded"
    assert result.manifest.seed == 42
    assert result.manifest.universe == "sample"
    assert result.manifest.metrics == {}
    assert result.manifest_path.exists()


def test_qlib_demo_execute_parses_mlflow_metrics(tmp_path, monkeypatch) -> None:
    config = tmp_path / "config.yaml"
    data = tmp_path / "prices.csv"
    run_dir = tmp_path / "mlruns" / "1" / "abc"
    metrics_dir = run_dir / "metrics"
    metrics_dir.mkdir(parents=True)
    (run_dir / "meta.yaml").write_text("run\n", encoding="utf-8")
    (metrics_dir / "IC").write_text("1700000000000 0.21 0\n", encoding="utf-8")
    write_config(config)
    write_data(data)

    def fake_convert(config, dry_run):  # noqa: ANN001
        return QlibConversionResult(command=("convert",), dry_run=dry_run, return_code=0)

    def fake_qrun(request, dry_run):  # noqa: ANN001
        return QlibRunResult(
            command=("qrun", str(request.config_path)),
            dry_run=dry_run,
            return_code=0,
            artifact_dir=request.artifact_dir,
        )

    monkeypatch.setattr("src.qlib_integration.demo.convert_to_qlib", fake_convert)
    monkeypatch.setattr("src.qlib_integration.demo.run_qlib_experiment", fake_qrun)
    monkeypatch.setattr(subprocess, "run", fake_git_run)

    result = run_qlib_synthetic_demo(
        QlibDemoRequest(
            input_path=data,
            output_dir=tmp_path / "qlib",
            config_path=config,
            experiment_store=tmp_path / "experiments",
            mlruns_dir=tmp_path / "mlruns",
        ),
        dry_run=False,
    )

    assert result.manifest.status == "succeeded"
    assert result.manifest.metrics["IC"] == 0.21
    assert result.manifest.artifact_paths["mlflow_run_dir"].endswith("abc")


def test_qlib_demo_failure_records_failed_manifest(tmp_path, monkeypatch) -> None:
    config = tmp_path / "config.yaml"
    data = tmp_path / "prices.csv"
    write_config(config)
    write_data(data)

    def fake_convert(config, dry_run):  # noqa: ANN001
        return QlibConversionResult(command=("convert",), dry_run=dry_run, return_code=0)

    def fake_qrun(request, dry_run):  # noqa: ANN001
        raise QlibRunError("qrun failed")

    monkeypatch.setattr("src.qlib_integration.demo.convert_to_qlib", fake_convert)
    monkeypatch.setattr("src.qlib_integration.demo.run_qlib_experiment", fake_qrun)
    monkeypatch.setattr(subprocess, "run", fake_git_run)
    store_root = tmp_path / "experiments"

    with pytest.raises(QlibDemoError, match="Manifest recorded"):
        run_qlib_synthetic_demo(
            QlibDemoRequest(
                input_path=data,
                output_dir=tmp_path / "qlib",
                config_path=config,
                experiment_store=store_root,
                mlruns_dir=tmp_path / "mlruns",
            ),
            dry_run=False,
        )

    manifests = ExperimentStore(store_root).list()
    assert len(manifests) == 1
    assert manifests[0].status == "failed"
    assert "qrun failed" in str(manifests[0].failure_reason)
