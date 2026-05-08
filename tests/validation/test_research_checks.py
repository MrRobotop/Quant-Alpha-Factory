"""Tests for combined research checks."""

from __future__ import annotations

import pytest

from src.validation.research_checks import (
    ResearchCheckError,
    extract_feature_expressions,
    run_research_checks,
)


def test_baseline_qlib_config_passes_research_checks() -> None:
    result = run_research_checks("configs/qlib/baseline_lightgbm_alpha158.yaml")

    assert result.status == "pass"
    assert result.issues == ()


def test_overlapping_split_config_fails(tmp_path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
experiment:
  transaction_cost:
    open_cost: 0.001
    close_cost: 0.001
task:
  dataset:
    kwargs:
      handler:
        kwargs:
          fit_start_time: "2024-01-01"
          fit_end_time: "2024-06-30"
      segments:
        train: ["2024-01-01", "2024-07-01"]
        valid: ["2024-07-01", "2024-09-30"]
        test: ["2024-10-01", "2024-12-31"]
""",
        encoding="utf-8",
    )

    result = run_research_checks(path)

    assert result.status == "fail"
    assert "train_valid_overlap" in {issue.code for issue in result.issues}


def test_feature_expression_leakage_fails(tmp_path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
experiment:
  transaction_cost:
    open_cost: 0.001
    close_cost: 0.001
task:
  dataset:
    kwargs:
      handler:
        kwargs:
          fit_start_time: "2024-01-01"
          fit_end_time: "2024-06-30"
          feature_expression: "Ref($close, -1) / $close - 1"
      segments:
        train: ["2024-01-01", "2024-06-30"]
        valid: ["2024-07-01", "2024-09-30"]
        test: ["2024-10-01", "2024-12-31"]
""",
        encoding="utf-8",
    )

    result = run_research_checks(path)

    assert result.status == "fail"
    assert "future_ref_expression" in {issue.code for issue in result.issues}


def test_missing_transaction_cost_fails(tmp_path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
task:
  dataset:
    kwargs:
      segments:
        train: ["2024-01-01", "2024-06-30"]
        valid: ["2024-07-01", "2024-09-30"]
        test: ["2024-10-01", "2024-12-31"]
""",
        encoding="utf-8",
    )

    result = run_research_checks(path)

    assert result.status == "fail"
    assert "missing_transaction_cost" in {issue.code for issue in result.issues}


def test_fit_period_overlapping_test_fails(tmp_path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
experiment:
  transaction_cost:
    open_cost: 0.001
    close_cost: 0.001
task:
  dataset:
    kwargs:
      handler:
        kwargs:
          fit_start_time: "2024-01-01"
          fit_end_time: "2024-10-01"
      segments:
        train: ["2024-01-01", "2024-06-30"]
        valid: ["2024-07-01", "2024-09-30"]
        test: ["2024-10-01", "2024-12-31"]
""",
        encoding="utf-8",
    )

    result = run_research_checks(path)

    assert result.status == "fail"
    assert "fit_period_overlaps_test" in {issue.code for issue in result.issues}


def test_missing_config_fails() -> None:
    with pytest.raises(ResearchCheckError, match="does not exist"):
        run_research_checks("configs/missing.yaml")


def test_extract_feature_expressions() -> None:
    expressions = extract_feature_expressions(
        {"handler": {"feature_expression": "$close / Ref($close, 5) - 1"}}
    )

    assert expressions == ["$close / Ref($close, 5) - 1"]

