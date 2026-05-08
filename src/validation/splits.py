"""Date split validation for quant research workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

import pandas as pd

CheckStatus = Literal["pass", "warning", "fail"]


@dataclass(frozen=True)
class CheckIssue:
    """One research validation issue."""

    status: CheckStatus
    code: str
    message: str


@dataclass(frozen=True)
class CheckReport:
    """Structured report from one or more validation checks."""

    issues: tuple[CheckIssue, ...] = field(default_factory=tuple)

    @property
    def status(self) -> CheckStatus:
        if any(issue.status == "fail" for issue in self.issues):
            return "fail"
        if any(issue.status == "warning" for issue in self.issues):
            return "warning"
        return "pass"

    @property
    def failures(self) -> tuple[CheckIssue, ...]:
        return tuple(issue for issue in self.issues if issue.status == "fail")

    @property
    def warnings(self) -> tuple[CheckIssue, ...]:
        return tuple(issue for issue in self.issues if issue.status == "warning")


@dataclass(frozen=True)
class DateRange:
    """Inclusive date range."""

    start: date
    end: date

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


@dataclass(frozen=True)
class ResearchSplits:
    """Train, validation, and test date ranges."""

    train: DateRange
    valid: DateRange
    test: DateRange


def validate_date_splits(
    splits: ResearchSplits,
    *,
    min_days: int = 1,
) -> CheckReport:
    """Validate ordering, overlap, and minimum segment lengths."""
    issues: list[CheckIssue] = []
    for name, segment in (
        ("train", splits.train),
        ("valid", splits.valid),
        ("test", splits.test),
    ):
        if segment.start > segment.end:
            issues.append(
                CheckIssue(
                    status="fail",
                    code=f"{name}_start_after_end",
                    message=f"{name} start date must be on or before end date.",
                )
            )
        if segment.days < min_days:
            issues.append(
                CheckIssue(
                    status="fail",
                    code=f"{name}_too_short",
                    message=f"{name} segment has {segment.days} days; minimum is {min_days}.",
                )
            )

    if splits.train.end >= splits.valid.start:
        issues.append(
            CheckIssue(
                status="fail",
                code="train_valid_overlap",
                message="Train segment must end before validation segment starts.",
            )
        )
    if splits.valid.end >= splits.test.start:
        issues.append(
            CheckIssue(
                status="fail",
                code="valid_test_overlap",
                message="Validation segment must end before test segment starts.",
            )
        )
    if splits.train.end >= splits.test.start:
        issues.append(
            CheckIssue(
                status="fail",
                code="train_test_overlap",
                message="Train segment must end before test segment starts.",
            )
        )

    return CheckReport(tuple(issues))


def parse_date(value: object) -> date:
    """Parse a config date into a Python date."""
    parsed = pd.to_datetime(value, errors="raise")
    return parsed.date()

