"""CLI tests for data validation."""

from __future__ import annotations

from typer.testing import CliRunner

from src.cli import app


def test_data_validate_sample_file_passes() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["data", "validate", "--input", "data/sample/prices.csv"])

    assert result.exit_code == 0
    assert "Market data validation valid" in result.output


def test_data_validate_bad_file_fails(tmp_path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text(
        "date,symbol,open,high,low,close,volume\n"
        "2024-01-02,AAA,10,9,8,10,100\n",
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["data", "validate", "--input", str(path)])

    assert result.exit_code == 1
    assert "invalid_ohlc_relationship" in result.output


def test_data_convert_dry_run_passes() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "data",
            "convert",
            "--input",
            "data/sample/prices.csv",
            "--output",
            "data/qlib_bin/sample",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "Qlib conversion dry-run." in result.output
    assert "qlib.scripts.dump_bin" in result.output


def test_data_convert_bad_file_fails(tmp_path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text(
        "date,symbol,open,high,low,close,volume\n"
        "2024-01-02,AAA,10,9,8,10,100\n",
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["data", "convert", "--input", str(path), "--output", "data/qlib_bin/bad"],
    )

    assert result.exit_code == 1
    assert "Validation failed before Qlib conversion" in result.output


def test_qlib_run_dry_run_passes() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "qlib",
            "run",
            "--config",
            "configs/qlib/baseline_lightgbm_alpha158.yaml",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "Qlib run dry-run." in result.output
    assert "qrun configs/qlib/baseline_lightgbm_alpha158.yaml" in result.output


def test_qlib_run_missing_config_fails() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["qlib", "run", "--config", "configs/qlib/missing.yaml"])

    assert result.exit_code == 1
    assert "invalid config" in result.output


def test_qlib_demo_dry_run_passes() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["qlib", "demo", "--dry-run"])

    assert result.exit_code == 0
    assert "Qlib synthetic demo dry-run." in result.output
    assert "Manifest:" in result.output
