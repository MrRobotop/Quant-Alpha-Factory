"""Tests for Markdown tearsheet generation."""

from __future__ import annotations

from src.backtest.metrics import PerformanceSummary
from src.backtest.tearsheet import build_markdown_tearsheet


def test_tearsheet_includes_costs_turnover_benchmark_and_limitations() -> None:
    summary = PerformanceSummary(
        gross_return=0.10,
        net_return=0.08,
        annualized_return=0.08,
        volatility=0.12,
        sharpe_ratio=0.66,
        information_ratio=0.2,
        max_drawdown=-0.05,
        turnover=0.4,
        transaction_cost=0.02,
        hit_rate=0.55,
        benchmark_return=0.06,
    )

    markdown = build_markdown_tearsheet(summary, benchmark="SPY")

    assert "Benchmark: SPY" in markdown
    assert "Gross Return" in markdown
    assert "Net Return" in markdown
    assert "Average Turnover" in markdown
    assert "Transaction Cost" in markdown
    assert "Limitations" in markdown
    assert "not live trading claims" in markdown

