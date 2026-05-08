"""Portfolio strategy interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pandas as pd


@dataclass(frozen=True)
class StrategyMetadata:
    """Strategy metadata preserved with results."""

    name: str
    version: str
    description: str
    requires_scores: bool = True
    benchmark: str | None = None


class Strategy(Protocol):
    """Target-weight strategy protocol."""

    metadata: StrategyMetadata

    def target_weights(self, scores: pd.DataFrame) -> pd.DataFrame:
        """Convert scores into target weights."""

