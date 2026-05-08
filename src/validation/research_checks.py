"""Combined research validity checks for experiment configs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.validation.leakage import check_expressions, check_fit_period_not_test_overlap
from src.validation.splits import (
    CheckIssue,
    CheckReport,
    DateRange,
    ResearchSplits,
    parse_date,
    validate_date_splits,
)


class ResearchCheckError(ValueError):
    """Raised when a research config cannot be checked."""


@dataclass(frozen=True)
class ResearchCheckResult:
    """Combined research validation result."""

    issues: tuple[CheckIssue, ...]

    @property
    def status(self) -> str:
        return CheckReport(self.issues).status

    @property
    def failures(self) -> tuple[CheckIssue, ...]:
        return CheckReport(self.issues).failures

    @property
    def warnings(self) -> tuple[CheckIssue, ...]:
        return CheckReport(self.issues).warnings

    def summary(self) -> str:
        return (
            f"Research checks {self.status}: "
            f"{len(self.failures)} failures, {len(self.warnings)} warnings."
        )


def run_research_checks(config_path: str | Path) -> ResearchCheckResult:
    """Load a YAML config and run configured research validity checks."""
    payload = _load_yaml_mapping(config_path)
    issues: list[CheckIssue] = []

    splits = extract_research_splits(payload)
    if splits is None:
        issues.append(
            CheckIssue(
                status="warning",
                code="missing_date_splits",
                message="Could not find train/valid/test segments in config.",
            )
        )
    else:
        issues.extend(validate_date_splits(splits, min_days=1).issues)
        fit_period = extract_fit_period(payload)
        if fit_period is not None:
            issues.extend(check_fit_period_not_test_overlap(fit_period, splits.test).issues)

    expressions = extract_feature_expressions(payload)
    if expressions:
        issues.extend(check_expressions(expressions).issues)

    if not _has_transaction_cost(payload):
        issues.append(
            CheckIssue(
                status="fail",
                code="missing_transaction_cost",
                message="Config must declare transaction cost assumptions.",
            )
        )

    return ResearchCheckResult(tuple(issues))


def extract_research_splits(payload: dict[str, Any]) -> ResearchSplits | None:
    """Extract Qlib-style train/valid/test segments."""
    segments = (
        payload.get("task", {})
        .get("dataset", {})
        .get("kwargs", {})
        .get("segments")
    )
    if not isinstance(segments, dict):
        return None
    try:
        train = _segment_to_range(segments["train"])
        valid = _segment_to_range(segments["valid"])
        test = _segment_to_range(segments["test"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ResearchCheckError("Invalid train/valid/test segment structure.") from exc
    return ResearchSplits(train=train, valid=valid, test=test)


def extract_fit_period(payload: dict[str, Any]) -> DateRange | None:
    """Extract handler fit period when present."""
    handler_kwargs = (
        payload.get("task", {})
        .get("dataset", {})
        .get("kwargs", {})
        .get("handler", {})
        .get("kwargs", {})
    )
    if not isinstance(handler_kwargs, dict):
        return None
    if "fit_start_time" not in handler_kwargs or "fit_end_time" not in handler_kwargs:
        return None
    return DateRange(
        start=parse_date(handler_kwargs["fit_start_time"]),
        end=parse_date(handler_kwargs["fit_end_time"]),
    )


def extract_feature_expressions(payload: Any) -> list[str]:
    """Extract likely feature expressions from nested config structures."""
    expressions: list[str] = []

    def visit(value: Any, key: str = "") -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                visit(child_value, str(child_key))
        elif isinstance(value, list):
            for child_value in value:
                visit(child_value, key)
        elif isinstance(value, str):
            lower_key = key.lower()
            if any(term in lower_key for term in ("feature", "factor", "expression")):
                expressions.append(value)

    visit(payload)
    return expressions


def _segment_to_range(segment: Any) -> DateRange:
    if not isinstance(segment, list | tuple) or len(segment) != 2:
        raise ValueError("Segment must contain exactly two dates.")
    return DateRange(start=parse_date(segment[0]), end=parse_date(segment[1]))


def _has_transaction_cost(payload: dict[str, Any]) -> bool:
    experiment_cost = payload.get("experiment", {}).get("transaction_cost")
    if isinstance(experiment_cost, dict) and {"open_cost", "close_cost"} <= set(experiment_cost):
        return True
    return _contains_keys(payload, {"open_cost", "close_cost"})


def _contains_keys(value: Any, keys: set[str]) -> bool:
    if isinstance(value, dict):
        if keys <= set(value):
            return True
        return any(_contains_keys(child, keys) for child in value.values())
    if isinstance(value, list):
        return any(_contains_keys(child, keys) for child in value)
    return False


def _load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise ResearchCheckError(f"Research config does not exist: {config_path}")
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ResearchCheckError(f"Research config must be a YAML mapping: {config_path}")
    return payload

