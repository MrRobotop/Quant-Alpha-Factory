"""Conservative leakage checks for factor/model configs."""

from __future__ import annotations

import re
from collections.abc import Iterable

from src.validation.splits import CheckIssue, CheckReport, DateRange

FUTURE_REF_PATTERN = re.compile(r"\bRef\s*\([^,]+,\s*-", re.IGNORECASE)
FORWARD_TERM_PATTERN = re.compile(
    r"\b(forward|future|lead)\b|"
    r"\b(next|future|forward)[_\s-]?returns?[_\s-]?\w*\b",
    re.IGNORECASE,
)
LABEL_TERM_PATTERN = re.compile(r"\b(label|LABEL\d*|y_true|target)\b", re.IGNORECASE)


def check_factor_expression(
    expression: str,
    *,
    allow_label_definition: bool = False,
) -> CheckReport:
    """Check one expression for obvious future references or direct label use."""
    issues: list[CheckIssue] = []
    if FUTURE_REF_PATTERN.search(expression):
        issues.append(
            CheckIssue(
                status="fail",
                code="future_ref_expression",
                message="Expression appears to reference future data with negative Ref offset.",
            )
        )
    if FORWARD_TERM_PATTERN.search(expression):
        issues.append(
            CheckIssue(
                status="fail",
                code="forward_return_in_feature",
                message="Expression or feature name references forward/future returns.",
            )
        )
    if LABEL_TERM_PATTERN.search(expression) and not allow_label_definition:
        issues.append(
            CheckIssue(
                status="fail",
                code="label_leakage",
                message="Expression appears to reference labels or targets in a feature context.",
            )
        )
    if "Ref(" in expression and "-" not in expression and "+" in expression:
        issues.append(
            CheckIssue(
                status="warning",
                code="ambiguous_ref_expression",
                message="Expression contains Ref and arithmetic; verify alignment manually.",
            )
        )
    return CheckReport(tuple(issues))


def check_expressions(
    expressions: Iterable[str],
    *,
    allow_label_definition: bool = False,
) -> CheckReport:
    """Check multiple expressions and combine results."""
    issues: list[CheckIssue] = []
    for expression in expressions:
        issues.extend(
            check_factor_expression(
                expression,
                allow_label_definition=allow_label_definition,
            ).issues
        )
    return CheckReport(tuple(issues))


def check_fit_period_not_test_overlap(fit_period: DateRange, test_period: DateRange) -> CheckReport:
    """Fail if a processor/model fit period overlaps the test period."""
    if fit_period.end >= test_period.start and fit_period.start <= test_period.end:
        return CheckReport(
            (
                CheckIssue(
                    status="fail",
                    code="fit_period_overlaps_test",
                    message=(
                        "Fit period overlaps test period; processors must not learn from "
                        "test data."
                    ),
                ),
            )
        )
    return CheckReport()
