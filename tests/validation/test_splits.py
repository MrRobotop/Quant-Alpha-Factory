"""Tests for date split validation."""

from __future__ import annotations

from datetime import date

from src.validation.splits import DateRange, ResearchSplits, validate_date_splits


def make_splits() -> ResearchSplits:
    return ResearchSplits(
        train=DateRange(date(2024, 1, 1), date(2024, 6, 30)),
        valid=DateRange(date(2024, 7, 1), date(2024, 9, 30)),
        test=DateRange(date(2024, 10, 1), date(2024, 12, 31)),
    )


def test_valid_date_splits_pass() -> None:
    result = validate_date_splits(make_splits(), min_days=1)

    assert result.status == "pass"
    assert result.issues == ()


def test_overlapping_train_valid_fails() -> None:
    splits = ResearchSplits(
        train=DateRange(date(2024, 1, 1), date(2024, 7, 1)),
        valid=DateRange(date(2024, 7, 1), date(2024, 9, 30)),
        test=DateRange(date(2024, 10, 1), date(2024, 12, 31)),
    )

    result = validate_date_splits(splits)

    assert result.status == "fail"
    assert "train_valid_overlap" in {issue.code for issue in result.issues}


def test_overlapping_valid_test_fails() -> None:
    splits = ResearchSplits(
        train=DateRange(date(2024, 1, 1), date(2024, 6, 30)),
        valid=DateRange(date(2024, 7, 1), date(2024, 10, 1)),
        test=DateRange(date(2024, 10, 1), date(2024, 12, 31)),
    )

    result = validate_date_splits(splits)

    assert result.status == "fail"
    assert "valid_test_overlap" in {issue.code for issue in result.issues}


def test_start_after_end_fails() -> None:
    splits = ResearchSplits(
        train=DateRange(date(2024, 6, 30), date(2024, 1, 1)),
        valid=DateRange(date(2024, 7, 1), date(2024, 9, 30)),
        test=DateRange(date(2024, 10, 1), date(2024, 12, 31)),
    )

    result = validate_date_splits(splits)

    assert "train_start_after_end" in {issue.code for issue in result.issues}


def test_minimum_segment_length_fails() -> None:
    result = validate_date_splits(make_splits(), min_days=200)

    assert result.status == "fail"
    assert {"train_too_short", "valid_too_short", "test_too_short"} <= {
        issue.code for issue in result.issues
    }

