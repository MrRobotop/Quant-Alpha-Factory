"""Tests for leakage detection."""

from __future__ import annotations

from datetime import date

from src.validation.leakage import check_factor_expression, check_fit_period_not_test_overlap
from src.validation.splits import DateRange


def test_future_ref_expression_fails() -> None:
    result = check_factor_expression("Ref($close, -1) / $close - 1")

    assert result.status == "fail"
    assert "future_ref_expression" in {issue.code for issue in result.issues}


def test_forward_return_feature_fails() -> None:
    result = check_factor_expression("next_return_5d")

    assert result.status == "fail"
    assert "forward_return_in_feature" in {issue.code for issue in result.issues}


def test_label_usage_fails_unless_explicitly_allowed() -> None:
    result = check_factor_expression("label")
    allowed = check_factor_expression("label", allow_label_definition=True)

    assert result.status == "fail"
    assert "label_leakage" in {issue.code for issue in result.issues}
    assert allowed.status == "pass"


def test_ambiguous_ref_warns() -> None:
    result = check_factor_expression("Ref($close, 1) + $volume")

    assert result.status == "warning"
    assert "ambiguous_ref_expression" in {issue.code for issue in result.issues}


def test_fit_period_overlapping_test_fails() -> None:
    result = check_fit_period_not_test_overlap(
        DateRange(date(2024, 1, 1), date(2024, 10, 1)),
        DateRange(date(2024, 10, 1), date(2024, 12, 31)),
    )

    assert result.status == "fail"
    assert "fit_period_overlaps_test" in {issue.code for issue in result.issues}


def test_fit_period_before_test_passes() -> None:
    result = check_fit_period_not_test_overlap(
        DateRange(date(2024, 1, 1), date(2024, 9, 30)),
        DateRange(date(2024, 10, 1), date(2024, 12, 31)),
    )

    assert result.status == "pass"

