"""Factor metadata definitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

FactorCategory = Literal[
    "momentum",
    "reversal",
    "volatility",
    "liquidity",
    "volume_price",
    "risk_adjusted_momentum",
]
FactorScope = Literal["cross_sectional", "time_series", "hybrid"]
ImplementationType = Literal["qlib_expression", "python"]


@dataclass(frozen=True)
class FactorSpec:
    """Versioned factor metadata required before research use."""

    name: str
    version: str
    description: str
    required_columns: tuple[str, ...]
    horizon: int
    category: FactorCategory
    scope: FactorScope
    implementation_type: ImplementationType
    economic_rationale: str
    leakage_notes: str
    qlib_expression: str | None = None

    @property
    def identifier(self) -> str:
        """Return stable name/version identifier."""
        return f"{self.name}:{self.version}"

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary."""
        return asdict(self)

