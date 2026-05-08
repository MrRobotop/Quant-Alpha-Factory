"""Backtest metric and tearsheet modules."""

from src.backtest.metrics import (
    BacktestMetricError,
    PerformanceSummary,
    annualized_return,
    cost_adjusted_returns,
    hit_rate,
    information_ratio,
    max_drawdown,
    sharpe_ratio,
    summarize_performance,
    total_return,
    transaction_cost_drag,
    turnover,
    volatility,
)
from src.backtest.tearsheet import build_markdown_tearsheet

__all__ = [
    "BacktestMetricError",
    "PerformanceSummary",
    "annualized_return",
    "build_markdown_tearsheet",
    "cost_adjusted_returns",
    "hit_rate",
    "information_ratio",
    "max_drawdown",
    "sharpe_ratio",
    "summarize_performance",
    "total_return",
    "transaction_cost_drag",
    "turnover",
    "volatility",
]
