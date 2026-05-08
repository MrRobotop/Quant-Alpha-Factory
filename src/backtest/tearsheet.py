"""Markdown performance tearsheet generation."""

from __future__ import annotations

from src.backtest.metrics import PerformanceSummary


def build_markdown_tearsheet(
    summary: PerformanceSummary,
    *,
    title: str = "Backtest Performance Summary",
    benchmark: str | None = None,
    limitations: str = (
        "Backtest results are historical or synthetic and are not live trading claims."
    ),
) -> str:
    """Build a concise Markdown tearsheet with costs and turnover."""
    rows = [
        ("Gross Return", summary.gross_return),
        ("Net Return", summary.net_return),
        ("Annualized Return", summary.annualized_return),
        ("Volatility", summary.volatility),
        ("Sharpe Ratio", summary.sharpe_ratio),
        ("Information Ratio", summary.information_ratio),
        ("Max Drawdown", summary.max_drawdown),
        ("Average Turnover", summary.turnover),
        ("Transaction Cost", summary.transaction_cost),
        ("Hit Rate", summary.hit_rate),
        ("Benchmark Return", summary.benchmark_return),
    ]
    benchmark_text = benchmark or "Not specified"
    lines = [
        f"# {title}",
        "",
        f"Benchmark: {benchmark_text}",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {name} | {_format_metric(value)} |" for name, value in rows)
    lines.extend(
        [
            "",
            "## Cost And Turnover",
            "",
            (
                "Net return is gross return after transaction cost drag. "
                "Turnover is reported explicitly."
            ),
            "",
            "## Limitations",
            "",
            limitations,
            "",
        ]
    )
    return "\n".join(lines)


def _format_metric(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{value:.6g}"
