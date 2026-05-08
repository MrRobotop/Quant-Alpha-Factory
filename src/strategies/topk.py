"""Top-K portfolio strategy."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.strategies.base import StrategyMetadata


@dataclass(frozen=True)
class TopKStrategy:
    """Long-only equal-weight top-k strategy from cross-sectional scores."""

    k: int
    metadata: StrategyMetadata = StrategyMetadata(
        name="topk",
        version="1.0.0",
        description="Long-only equal-weight top-k strategy.",
    )

    def target_weights(self, scores: pd.DataFrame) -> pd.DataFrame:
        """Return equal weights for the top-k names on each date."""
        if self.k <= 0:
            raise ValueError("k must be positive.")
        if scores.empty:
            return pd.DataFrame(index=scores.index, columns=scores.columns, dtype=float)

        weights = pd.DataFrame(0.0, index=scores.index, columns=scores.columns)
        for date, row in scores.iterrows():
            valid = row.dropna()
            if valid.empty:
                continue
            selected = valid.sort_values(ascending=False).head(self.k).index
            weights.loc[date, selected] = 1.0 / len(selected)
        return weights

