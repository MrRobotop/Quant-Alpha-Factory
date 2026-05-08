"""Tests for conservative Qlib artifact parsing."""

from __future__ import annotations

from src.qlib_integration.result_parser import parse_qlib_results


def test_missing_artifact_directory_is_unavailable(tmp_path) -> None:
    result = parse_qlib_results(tmp_path / "missing")

    assert result.status == "unavailable"
    assert result.metrics == {}


def test_no_supported_artifacts_is_unavailable(tmp_path) -> None:
    (tmp_path / "notes.txt").write_text("not metrics", encoding="utf-8")

    result = parse_qlib_results(tmp_path)

    assert result.status == "unavailable"
    assert "No supported Qlib result artifacts" in result.message


def test_parse_json_artifacts(tmp_path) -> None:
    (tmp_path / "metrics.json").write_text('{"ic": 0.01, "rank_ic": 0.02}', encoding="utf-8")
    nested = tmp_path / "recorder"
    nested.mkdir()
    (nested / "portfolio_analysis.json").write_text('{"annualized_return": 0.03}', encoding="utf-8")

    result = parse_qlib_results(tmp_path)

    assert result.status == "available"
    assert result.metrics["metrics"]["ic"] == 0.01
    assert result.metrics["portfolio_analysis"]["annualized_return"] == 0.03
    assert len(result.artifacts) == 2


def test_parse_mlflow_metric_artifacts(tmp_path) -> None:
    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()
    (metrics_dir / "IC").write_text(
        "1700000000000 0.12 0\n1700000001000 0.13 1\n",
        encoding="utf-8",
    )
    (metrics_dir / "1day.excess_return_with_cost.annualized_return").write_text(
        "1700000000000 0.03 0\n",
        encoding="utf-8",
    )

    result = parse_qlib_results(tmp_path)

    assert result.status == "available"
    assert result.metrics["IC"] == 0.13
    assert result.metrics["1day.excess_return_with_cost.annualized_return"] == 0.03
    assert len(result.artifacts) == 2


def test_invalid_json_reports_partial(tmp_path) -> None:
    (tmp_path / "metrics.json").write_text('{"ic": 0.01}', encoding="utf-8")
    (tmp_path / "results.json").write_text("{bad json", encoding="utf-8")

    result = parse_qlib_results(tmp_path)

    assert result.status == "partial"
    assert result.metrics["metrics"]["ic"] == 0.01
    assert "could not be parsed" in result.message
