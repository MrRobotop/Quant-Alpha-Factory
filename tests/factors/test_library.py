"""Tests for the baseline factor library."""

from __future__ import annotations

from src.factors.library import baseline_factors, build_default_registry


def test_baseline_factor_names() -> None:
    names = {factor.name for factor in baseline_factors()}

    assert names == {
        "momentum_20d",
        "reversal_5d",
        "realized_volatility_20d",
        "dollar_volume_liquidity",
        "volume_shock_20d",
        "risk_adjusted_momentum_20d",
    }


def test_every_baseline_factor_has_required_research_metadata() -> None:
    for factor in baseline_factors():
        assert factor.version
        assert factor.required_columns
        assert factor.scope in {"cross_sectional", "time_series", "hybrid"}
        assert factor.economic_rationale
        assert factor.leakage_notes
        assert factor.qlib_expression


def test_default_registry_contains_baseline_factors() -> None:
    registry = build_default_registry()

    assert len(registry.list()) == 6
    assert registry.get("momentum_20d").category == "momentum"


def test_momentum_expression_uses_current_over_lagged_close() -> None:
    factor = build_default_registry().get("momentum_20d")

    assert factor.qlib_expression == "$close / Ref($close, 20) - 1"

