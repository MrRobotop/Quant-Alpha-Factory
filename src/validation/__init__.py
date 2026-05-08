"""Research validity and leakage validation modules."""

from src.validation.leakage import (
    check_expressions,
    check_factor_expression,
    check_fit_period_not_test_overlap,
)
from src.validation.research_checks import (
    ResearchCheckError,
    ResearchCheckResult,
    run_research_checks,
)
from src.validation.splits import (
    CheckIssue,
    CheckReport,
    DateRange,
    ResearchSplits,
    validate_date_splits,
)

__all__ = [
    "CheckIssue",
    "CheckReport",
    "DateRange",
    "ResearchCheckError",
    "ResearchCheckResult",
    "ResearchSplits",
    "check_expressions",
    "check_factor_expression",
    "check_fit_period_not_test_overlap",
    "run_research_checks",
    "validate_date_splits",
]
