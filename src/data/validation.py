"""Validation checks for canonical daily OHLCV data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

from src.data.schema import (
    ADJUSTED_CLOSE_COLUMN,
    CLOSE_COLUMN,
    DATE_COLUMN,
    HIGH_COLUMN,
    LOW_COLUMN,
    OPEN_COLUMN,
    PRICE_COLUMNS,
    REQUIRED_COLUMNS,
    SYMBOL_COLUMN,
    VOLUME_COLUMN,
    missing_required_columns,
)

Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class ValidationIssue:
    """One data validation issue."""

    severity: Severity
    code: str
    message: str
    rows: tuple[int, ...] = ()


@dataclass(frozen=True)
class ValidationResult:
    """Structured validation output for market data checks."""

    row_count: int
    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "error")

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        status = "valid" if self.is_valid else "invalid"
        return (
            f"Market data validation {status}: {self.row_count} rows, "
            f"{len(self.errors)} errors, {len(self.warnings)} warnings."
        )


def validate_market_data(frame: pd.DataFrame) -> ValidationResult:
    """Run canonical OHLCV validation checks."""
    issues: list[ValidationIssue] = []
    issues.extend(_validate_required_columns(frame))

    if missing_required_columns(frame.columns):
        return ValidationResult(row_count=len(frame), issues=tuple(issues))

    issues.extend(_validate_missing_values(frame))
    issues.extend(_validate_duplicate_keys(frame))
    issues.extend(_validate_dates(frame))
    issues.extend(_validate_numeric_values(frame))
    issues.extend(_validate_ohlc_relationships(frame))
    issues.extend(_validate_adjusted_close(frame))

    return ValidationResult(row_count=len(frame), issues=tuple(issues))


def _validate_required_columns(frame: pd.DataFrame) -> list[ValidationIssue]:
    missing = missing_required_columns(frame.columns)
    if not missing:
        return []
    return [
        ValidationIssue(
            severity="error",
            code="missing_required_columns",
            message=f"Missing required columns: {', '.join(missing)}.",
        )
    ]


def _validate_missing_values(frame: pd.DataFrame) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for column in REQUIRED_COLUMNS:
        missing_mask = frame[column].isna()
        if missing_mask.any():
            issues.append(
                ValidationIssue(
                    severity="error",
                    code=f"missing_{column}",
                    message=f"Column '{column}' contains missing values.",
                    rows=_row_indices(missing_mask),
                )
            )
    return issues


def _validate_duplicate_keys(frame: pd.DataFrame) -> list[ValidationIssue]:
    duplicate_mask = frame.duplicated(subset=[DATE_COLUMN, SYMBOL_COLUMN], keep=False)
    if not duplicate_mask.any():
        return []
    return [
        ValidationIssue(
            severity="error",
            code="duplicate_date_symbol",
            message="Duplicate (date, symbol) rows are not allowed.",
            rows=_row_indices(duplicate_mask),
        )
    ]


def _validate_dates(frame: pd.DataFrame) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    parsed_dates = pd.to_datetime(frame[DATE_COLUMN], errors="coerce")
    invalid_mask = parsed_dates.isna()
    if invalid_mask.any():
        issues.append(
            ValidationIssue(
                severity="error",
                code="invalid_dates",
                message="Column 'date' contains values that cannot be parsed as dates.",
                rows=_row_indices(invalid_mask),
            )
        )
        return issues

    nonmonotonic_rows: list[int] = []
    for _, group in frame.assign(_parsed_date=parsed_dates).groupby(SYMBOL_COLUMN, sort=False):
        date_deltas = group["_parsed_date"].diff()
        bad_rows = group.index[date_deltas < pd.Timedelta(0)].tolist()
        nonmonotonic_rows.extend(int(row) for row in bad_rows)

    if nonmonotonic_rows:
        issues.append(
            ValidationIssue(
                severity="error",
                code="nonmonotonic_symbol_dates",
                message="Dates must be monotonic increasing within each symbol.",
                rows=tuple(nonmonotonic_rows),
            )
        )

    return issues


def _validate_numeric_values(frame: pd.DataFrame) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    numeric_columns = [*PRICE_COLUMNS, VOLUME_COLUMN]

    for column in numeric_columns:
        numeric = pd.to_numeric(frame[column], errors="coerce")
        nonnumeric_mask = numeric.isna() & frame[column].notna()
        if nonnumeric_mask.any():
            issues.append(
                ValidationIssue(
                    severity="error",
                    code=f"non_numeric_{column}",
                    message=f"Column '{column}' must be numeric.",
                    rows=_row_indices(nonnumeric_mask),
                )
            )
            continue

        if column in PRICE_COLUMNS:
            invalid_mask = numeric <= 0
            if invalid_mask.any():
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code=f"non_positive_{column}",
                        message=f"Column '{column}' must contain positive prices.",
                        rows=_row_indices(invalid_mask),
                    )
                )
        else:
            invalid_mask = numeric < 0
            if invalid_mask.any():
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="negative_volume",
                        message="Column 'volume' cannot contain negative values.",
                        rows=_row_indices(invalid_mask),
                    )
                )

    return issues


def _validate_ohlc_relationships(frame: pd.DataFrame) -> list[ValidationIssue]:
    open_ = pd.to_numeric(frame[OPEN_COLUMN], errors="coerce")
    high = pd.to_numeric(frame[HIGH_COLUMN], errors="coerce")
    low = pd.to_numeric(frame[LOW_COLUMN], errors="coerce")
    close = pd.to_numeric(frame[CLOSE_COLUMN], errors="coerce")

    invalid_mask = (high < open_) | (high < low) | (high < close) | (low > open_) | (low > close)
    invalid_mask = invalid_mask.fillna(False)

    if not invalid_mask.any():
        return []
    return [
        ValidationIssue(
            severity="error",
            code="invalid_ohlc_relationship",
            message=(
                "OHLC relationship failed: high must be >= open/low/close "
                "and low <= open/close."
            ),
            rows=_row_indices(invalid_mask),
        )
    ]


def _validate_adjusted_close(frame: pd.DataFrame) -> list[ValidationIssue]:
    if ADJUSTED_CLOSE_COLUMN not in frame.columns:
        return []

    issues: list[ValidationIssue] = []
    adjusted = pd.to_numeric(frame[ADJUSTED_CLOSE_COLUMN], errors="coerce")
    nonnumeric_mask = adjusted.isna() & frame[ADJUSTED_CLOSE_COLUMN].notna()
    if nonnumeric_mask.any():
        issues.append(
            ValidationIssue(
                severity="error",
                code="non_numeric_adjusted_close",
                message="Column 'adjusted_close' must be numeric when provided.",
                rows=_row_indices(nonnumeric_mask),
            )
        )
    non_positive_mask = adjusted <= 0
    if non_positive_mask.any():
        issues.append(
            ValidationIssue(
                severity="error",
                code="non_positive_adjusted_close",
                message="Column 'adjusted_close' must contain positive prices when provided.",
                rows=_row_indices(non_positive_mask),
            )
        )

    close = pd.to_numeric(frame[CLOSE_COLUMN], errors="coerce")
    ratio = adjusted / close
    jump_rows: list[int] = []
    working = frame.assign(_adjustment_ratio=ratio)
    for _, group in working.groupby(SYMBOL_COLUMN, sort=False):
        ratio_change = group["_adjustment_ratio"].pct_change().abs()
        jump_rows.extend(int(row) for row in group.index[ratio_change > 0.5].tolist())

    if jump_rows:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="suspicious_adjustment_ratio_jump",
                message="Adjusted-close ratio changed by more than 50% within a symbol.",
                rows=tuple(jump_rows),
            )
        )

    return issues


def _row_indices(mask: pd.Series) -> tuple[int, ...]:
    return tuple(int(index) for index in mask[mask].index.tolist())
