"""Tests for factor registry behavior."""

from __future__ import annotations

import pytest

from src.factors.base import FactorSpec
from src.factors.registry import FactorRegistry, FactorRegistryError


def make_factor(name: str = "test_factor", version: str = "1.0.0") -> FactorSpec:
    return FactorSpec(
        name=name,
        version=version,
        description="Test factor.",
        required_columns=("close",),
        horizon=5,
        category="momentum",
        scope="time_series",
        implementation_type="qlib_expression",
        qlib_expression="$close / Ref($close, 5) - 1",
        economic_rationale="Tests metadata validation with a plausible momentum rationale.",
        leakage_notes="Uses only current and lagged close prices.",
    )


def test_register_and_get_factor() -> None:
    registry = FactorRegistry()
    factor = make_factor()

    registry.register(factor)

    assert registry.get("test_factor") == factor
    assert registry.get("test_factor", "1.0.0") == factor


def test_duplicate_factor_rejected() -> None:
    registry = FactorRegistry()
    factor = make_factor()
    registry.register(factor)

    with pytest.raises(FactorRegistryError, match="already registered"):
        registry.register(factor)


def test_multiple_versions_require_explicit_version() -> None:
    registry = FactorRegistry()
    registry.register(make_factor(version="1.0.0"))
    registry.register(make_factor(version="1.1.0"))

    with pytest.raises(FactorRegistryError, match="Multiple versions"):
        registry.get("test_factor")


def test_missing_required_metadata_rejected() -> None:
    registry = FactorRegistry()
    bad_factor = FactorSpec(
        name="bad",
        version="1.0.0",
        description="",
        required_columns=("close",),
        horizon=5,
        category="momentum",
        scope="time_series",
        implementation_type="qlib_expression",
        qlib_expression="$close",
        economic_rationale="",
        leakage_notes="",
    )

    with pytest.raises(FactorRegistryError, match="missing required metadata"):
        registry.register(bad_factor)


def test_qlib_expression_required_for_expression_factor() -> None:
    registry = FactorRegistry()
    bad_factor = FactorSpec(
        name="bad",
        version="1.0.0",
        description="Missing expression.",
        required_columns=("close",),
        horizon=5,
        category="momentum",
        scope="time_series",
        implementation_type="qlib_expression",
        qlib_expression=None,
        economic_rationale="Economic rationale is present.",
        leakage_notes="Leakage notes are present.",
    )

    with pytest.raises(FactorRegistryError, match="qlib_expression"):
        registry.register(bad_factor)

