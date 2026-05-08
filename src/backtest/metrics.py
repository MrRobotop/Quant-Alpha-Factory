"""Backtest performance metrics."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


class BacktestMetricError(ValueError):
    """Raised when backtest metric inputs are invalid."""


@dataclass(frozen=True)
class PerformanceSummary:
    """Standardized performance metric table."""

    gross_return: float
    net_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float | None
    information_ratio: float | None
    max_drawdown: float
    turnover: float
    transaction_cost: float
    hit_rate: float | None
    benchmark_return: float | None = None


def total_return(returns: pd.Series) -> float:
    """Compute compounded total return."""
    clean = _clean_returns(returns)
    if clean.empty:
        return 0.0
    return float((1.0 + clean).prod() - 1.0)


def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Compute annualized compounded return."""
    clean = _clean_returns(returns)
    if clean.empty:
        return 0.0
    compounded = (1.0 + clean).prod()
    return float(compounded ** (periods_per_year / len(clean)) - 1.0)


def volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Compute annualized volatility."""
    clean = _clean_returns(returns)
    if len(clean) < 2:
        return 0.0
    return float(clean.std(ddof=1) * periods_per_year**0.5)


def sharpe_ratio(
    returns: pd.Series,
    *,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float | None:
    """Compute annualized Sharpe ratio."""
    clean = _clean_returns(returns)
    if clean.empty:
        return None
    excess = clean - risk_free_rate / periods_per_year
    vol = volatility(excess, periods_per_year)
    if vol == 0:
        return None
    return float(annualized_return(excess, periods_per_year) / vol)


def information_ratio(
    returns: pd.Series,
    benchmark_returns: pd.Series,
    *,
    periods_per_year: int = 252,
) -> float | None:
    """Compute annualized information ratio versus benchmark."""
    clean_returns = _clean_returns(returns)
    clean_benchmark = _clean_returns(benchmark_returns)
    aligned = pd.concat([clean_returns, clean_benchmark], axis=1, join="inner").dropna()
    if aligned.empty:
        return None
    active = aligned.iloc[:, 0] - aligned.iloc[:, 1]
    tracking_error = volatility(active, periods_per_year)
    if tracking_error == 0:
        return None
    return float(annualized_return(active, periods_per_year) / tracking_error)


def max_drawdown(returns: pd.Series) -> float:
    """Compute max drawdown as a negative decimal."""
    clean = _clean_returns(returns)
    if clean.empty:
        return 0.0
    equity = (1.0 + clean).cumprod()
    drawdowns = equity / equity.cummax() - 1.0
    return float(drawdowns.min())


def turnover(weights: pd.DataFrame) -> float:
    """Compute average one-way portfolio turnover from target weights."""
    if weights.empty:
        return 0.0
    numeric = weights.fillna(0.0).astype(float)
    changes = numeric.diff().abs().sum(axis=1) / 2.0
    if len(changes) <= 1:
        return 0.0
    return float(changes.iloc[1:].mean())


def transaction_cost_drag(turnover_series: pd.Series, cost_per_turnover: float) -> pd.Series:
    """Convert turnover into per-period transaction cost drag."""
    if cost_per_turnover < 0:
        raise BacktestMetricError("cost_per_turnover must be non-negative.")
    clean_turnover = turnover_series.fillna(0.0).astype(float)
    return clean_turnover * cost_per_turnover


def cost_adjusted_returns(
    gross_returns: pd.Series,
    turnover_series: pd.Series,
    *,
    cost_per_turnover: float,
) -> pd.Series:
    """Subtract transaction cost drag from gross returns."""
    aligned = pd.concat(
        [_clean_returns(gross_returns), turnover_series.fillna(0.0).astype(float)],
        axis=1,
        join="inner",
    )
    if aligned.empty:
        return pd.Series(dtype=float)
    aligned.columns = ["gross_return", "turnover"]
    return aligned["gross_return"] - transaction_cost_drag(aligned["turnover"], cost_per_turnover)


def hit_rate(returns: pd.Series) -> float | None:
    """Return fraction of positive periods."""
    clean = _clean_returns(returns)
    if clean.empty:
        return None
    return float((clean > 0).mean())


def summarize_performance(
    gross_returns: pd.Series,
    weights: pd.DataFrame,
    *,
    cost_per_turnover: float,
    benchmark_returns: pd.Series | None = None,
    periods_per_year: int = 252,
) -> PerformanceSummary:
    """Build a standardized cost-aware performance summary."""
    period_turnover = weights.fillna(0.0).astype(float).diff().abs().sum(axis=1).fillna(0.0) / 2.0
    net_returns = cost_adjusted_returns(
        gross_returns,
        period_turnover,
        cost_per_turnover=cost_per_turnover,
    )
    benchmark_return = total_return(benchmark_returns) if benchmark_returns is not None else None
    return PerformanceSummary(
        gross_return=total_return(gross_returns),
        net_return=total_return(net_returns),
        annualized_return=annualized_return(net_returns, periods_per_year),
        volatility=volatility(net_returns, periods_per_year),
        sharpe_ratio=sharpe_ratio(net_returns, periods_per_year=periods_per_year),
        information_ratio=(
            information_ratio(net_returns, benchmark_returns, periods_per_year=periods_per_year)
            if benchmark_returns is not None
            else None
        ),
        max_drawdown=max_drawdown(net_returns),
        turnover=turnover(weights),
        transaction_cost=float(transaction_cost_drag(period_turnover, cost_per_turnover).sum()),
        hit_rate=hit_rate(net_returns),
        benchmark_return=benchmark_return,
    )


def _clean_returns(returns: pd.Series) -> pd.Series:
    if returns is None:
        raise BacktestMetricError("returns must not be None.")
    return pd.to_numeric(returns, errors="coerce").dropna().astype(float)

