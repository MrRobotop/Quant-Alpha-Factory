"""Tests for canonical market data validation."""

from __future__ import annotations

import pandas as pd

from src.data.validation import validate_market_data


def valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-02"]),
            "symbol": ["AAA", "AAA", "BBB"],
            "open": [100.0, 101.0, 50.0],
            "high": [102.0, 103.0, 51.0],
            "low": [99.0, 100.0, 49.0],
            "close": [101.0, 102.0, 50.5],
            "volume": [1000, 1100, 900],
            "adjusted_close": [101.0, 102.0, 50.5],
        }
    )


def issue_codes(frame: pd.DataFrame) -> set[str]:
    return {issue.code for issue in validate_market_data(frame).issues}


def test_valid_market_data_passes() -> None:
    result = validate_market_data(valid_frame())

    assert result.is_valid
    assert result.errors == ()


def test_missing_required_columns_fails() -> None:
    frame = valid_frame().drop(columns=["close"])

    result = validate_market_data(frame)

    assert not result.is_valid
    assert "missing_required_columns" in issue_codes(frame)


def test_duplicate_date_symbol_fails() -> None:
    frame = pd.concat([valid_frame(), valid_frame().iloc[[0]]], ignore_index=True)

    assert "duplicate_date_symbol" in issue_codes(frame)


def test_invalid_ohlc_relationship_fails() -> None:
    frame = valid_frame()
    frame.loc[0, "high"] = 98.0

    assert "invalid_ohlc_relationship" in issue_codes(frame)


def test_non_positive_price_fails() -> None:
    frame = valid_frame()
    frame.loc[0, "close"] = -1.0

    assert "non_positive_close" in issue_codes(frame)


def test_negative_volume_fails() -> None:
    frame = valid_frame()
    frame.loc[0, "volume"] = -1

    assert "negative_volume" in issue_codes(frame)


def test_missing_required_value_fails() -> None:
    frame = valid_frame()
    frame.loc[0, "open"] = None

    assert "missing_open" in issue_codes(frame)


def test_nonmonotonic_dates_within_symbol_fail() -> None:
    frame = valid_frame()
    frame.loc[1, "date"] = pd.Timestamp("2024-01-01")

    assert "nonmonotonic_symbol_dates" in issue_codes(frame)


def test_suspicious_adjusted_close_ratio_is_warning_not_failure() -> None:
    frame = valid_frame()
    frame.loc[1, "adjusted_close"] = 10.0

    result = validate_market_data(frame)

    assert result.is_valid
    assert "suspicious_adjustment_ratio_jump" in {issue.code for issue in result.warnings}

