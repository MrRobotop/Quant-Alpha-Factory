"""Tests for backtest metrics."""

from __future__ import annotations

import pandas as pd
import pytest

from src.backtest.metrics import (
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


def test_total_and_annualized_return() -> None:
    returns = pd.Series([0.01, 0.02])

    assert total_return(returns) == pytest.approx(0.0302)
    assert annualized_return(returns, periods_per_year=2) == pytest.approx(0.0302)


def test_volatility_and_sharpe() -> None:
    returns = pd.Series([0.01, -0.01, 0.02])

    assert volatility(returns, periods_per_year=1) == pytest.approx(0.0152752523)
    assert sharpe_ratio(returns, periods_per_year=1) is not None


def test_information_ratio() -> None:
    returns = pd.Series([0.02, 0.01, -0.01])
    benchmark = pd.Series([0.01, 0.0, -0.02])

    assert information_ratio(returns, benchmark, periods_per_year=1) is None


def test_max_drawdown_edge_cases() -> None:
    assert max_drawdown(pd.Series(dtype=float)) == 0.0
    assert max_drawdown(pd.Series([0.1, -0.2, 0.05])) == pytest.approx(-0.2)


def test_turnover_calculation() -> None:
    weights = pd.DataFrame(
        {
            "AAA": [1.0, 0.5, 0.0],
            "BBB": [0.0, 0.5, 1.0],
        }
    )

    assert turnover(weights) == pytest.approx(0.5)


def test_transaction_cost_drag_and_cost_adjusted_returns() -> None:
    gross = pd.Series([0.01, 0.02])
    turns = pd.Series([0.0, 0.5])

    assert transaction_cost_drag(turns, 0.01).tolist() == [0.0, 0.005]
    net = cost_adjusted_returns(gross, turns, cost_per_turnover=0.01)
    assert net.tolist() == [0.01, 0.015]


def test_hit_rate() -> None:
    assert hit_rate(pd.Series([0.01, -0.02, 0.0])) == pytest.approx(1 / 3)
    assert hit_rate(pd.Series(dtype=float)) is None


def test_summarize_performance_includes_costs_turnover_and_benchmark() -> None:
    returns = pd.Series([0.01, 0.02], index=pd.Index(["d1", "d2"]))
    benchmark = pd.Series([0.005, 0.01], index=pd.Index(["d1", "d2"]))
    weights = pd.DataFrame(
        {"AAA": [1.0, 0.5], "BBB": [0.0, 0.5]},
        index=pd.Index(["d1", "d2"]),
    )

    summary = summarize_performance(
        returns,
        weights,
        cost_per_turnover=0.01,
        benchmark_returns=benchmark,
        periods_per_year=2,
    )

    assert summary.gross_return == pytest.approx(0.0302)
    assert summary.net_return == pytest.approx((1.01 * 1.015) - 1)
    assert summary.turnover == pytest.approx(0.5)
    assert summary.transaction_cost == pytest.approx(0.005)
    assert summary.benchmark_return == pytest.approx((1.005 * 1.01) - 1)

