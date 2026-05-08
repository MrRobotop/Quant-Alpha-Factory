"""Baseline economically motivated factor library."""

from __future__ import annotations

from src.factors.base import FactorSpec
from src.factors.registry import FactorRegistry


def baseline_factors() -> tuple[FactorSpec, ...]:
    """Return baseline factor specs used to seed the registry."""
    return (
        FactorSpec(
            name="momentum_20d",
            version="1.0.0",
            description="Twenty-day close-to-close momentum.",
            required_columns=("close",),
            horizon=20,
            category="momentum",
            scope="time_series",
            implementation_type="qlib_expression",
            qlib_expression="$close / Ref($close, 20) - 1",
            economic_rationale=(
                "Assets with persistent buying pressure may continue trending over intermediate "
                "horizons due to delayed information diffusion and investor underreaction."
            ),
            leakage_notes=(
                "Uses only current and lagged close prices. Must be aligned so labels are computed "
                "strictly after the factor timestamp."
            ),
        ),
        FactorSpec(
            name="reversal_5d",
            version="1.0.0",
            description="Five-day short-horizon reversal signal.",
            required_columns=("close",),
            horizon=5,
            category="reversal",
            scope="time_series",
            implementation_type="qlib_expression",
            qlib_expression="-( $close / Ref($close, 5) - 1 )",
            economic_rationale=(
                "Short-term overreaction and liquidity-driven price pressure can partially reverse "
                "over the following sessions."
            ),
            leakage_notes=(
                "Uses only current and lagged close prices. Do not compute returns using future "
                "prices inside the factor expression."
            ),
        ),
        FactorSpec(
            name="realized_volatility_20d",
            version="1.0.0",
            description="Twenty-day realized volatility proxy from close returns.",
            required_columns=("close",),
            horizon=20,
            category="volatility",
            scope="time_series",
            implementation_type="qlib_expression",
            qlib_expression="Std($close / Ref($close, 1) - 1, 20)",
            economic_rationale=(
                "Volatility captures uncertainty, risk appetite, and potential compensation for "
                "holding unstable assets."
            ),
            leakage_notes=(
                "Rolling window must use historical returns only. Volatility estimated on test "
                "data must not fit normalization parameters from future periods."
            ),
        ),
        FactorSpec(
            name="dollar_volume_liquidity",
            version="1.0.0",
            description="Dollar volume liquidity proxy.",
            required_columns=("close", "volume"),
            horizon=20,
            category="liquidity",
            scope="hybrid",
            implementation_type="qlib_expression",
            qlib_expression="Mean($close * $volume, 20)",
            economic_rationale=(
                "More liquid assets generally support lower trading costs and more reliable signal "
                "implementation."
            ),
            leakage_notes=(
                "Uses current and historical close/volume. Liquidity should be measured before "
                "portfolio construction and not with future traded volume."
            ),
        ),
        FactorSpec(
            name="volume_shock_20d",
            version="1.0.0",
            description="Current volume relative to twenty-day average volume.",
            required_columns=("volume",),
            horizon=20,
            category="volume_price",
            scope="time_series",
            implementation_type="qlib_expression",
            qlib_expression="$volume / Mean($volume, 20) - 1",
            economic_rationale=(
                "Unusual volume can indicate changing investor attention, information arrival, or "
                "temporary liquidity demand."
            ),
            leakage_notes=(
                "Average volume must be computed from current and lagged observations only. Avoid "
                "using future volume from the prediction horizon."
            ),
        ),
        FactorSpec(
            name="risk_adjusted_momentum_20d",
            version="1.0.0",
            description="Twenty-day momentum scaled by realized volatility.",
            required_columns=("close",),
            horizon=20,
            category="risk_adjusted_momentum",
            scope="time_series",
            implementation_type="qlib_expression",
            qlib_expression="($close / Ref($close, 20) - 1) / Std($close / Ref($close, 1) - 1, 20)",
            economic_rationale=(
                "Momentum with lower realized risk may be more robust after accounting for noisy "
                "or unstable price paths."
            ),
            leakage_notes=(
                "Both momentum and volatility components use historical prices only. Handle zero "
                "volatility explicitly in implementation-specific code."
            ),
        ),
    )


def build_default_registry() -> FactorRegistry:
    """Build a registry seeded with baseline factors."""
    registry = FactorRegistry()
    for factor in baseline_factors():
        registry.register(factor)
    return registry
