"""Transaction-cost-aware strategy helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.backtest.metrics import cost_adjusted_returns


@dataclass(frozen=True)
class TransactionCostModel:
    """Simple linear transaction cost model."""

    cost_per_turnover: float
    min_cost: float = 0.0

    def cost(self, turnover: pd.Series) -> pd.Series:
        """Return cost drag from turnover."""
        if self.cost_per_turnover < 0 or self.min_cost < 0:
            raise ValueError("Transaction costs must be non-negative.")
        costs = turnover.fillna(0.0).astype(float) * self.cost_per_turnover
        if self.min_cost:
            costs = costs.where(costs == 0.0, costs.clip(lower=self.min_cost))
        return costs


def apply_transaction_costs(
    gross_returns: pd.Series,
    turnover: pd.Series,
    cost_model: TransactionCostModel,
) -> pd.Series:
    """Apply a transaction cost model to gross returns."""
    if cost_model.min_cost == 0:
        return cost_adjusted_returns(
            gross_returns,
            turnover,
            cost_per_turnover=cost_model.cost_per_turnover,
        )
    aligned = pd.concat([gross_returns.astype(float), turnover.fillna(0.0).astype(float)], axis=1)
    aligned.columns = ["gross_return", "turnover"]
    return aligned["gross_return"] - cost_model.cost(aligned["turnover"])

