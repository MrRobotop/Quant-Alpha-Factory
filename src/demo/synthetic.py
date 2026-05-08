"""Synthetic end-to-end demo workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.metrics import summarize_performance
from src.data.ingestion import load_market_data
from src.data.qlib_converter import QlibConversionConfig, convert_to_qlib
from src.data.validation import validate_market_data
from src.experiments.leaderboard import build_leaderboard
from src.experiments.manifest import create_experiment_manifest
from src.experiments.schema import DateSplit, TransactionCostAssumptions
from src.experiments.store import ExperimentStore
from src.qlib_integration.runner import QlibRunRequest, run_qlib_experiment
from src.rd_agent_adapter.commands import RDAgentCommandConfig
from src.rd_agent_adapter.run_manager import RDAgentRunRequest, run_rdagent
from src.reporting.markdown import write_experiment_report
from src.strategies.topk import TopKStrategy
from src.validation.research_checks import run_research_checks


@dataclass(frozen=True)
class SyntheticDemoResult:
    """Outputs from the synthetic demo."""

    experiment_id: str
    manifest_path: Path
    report_path: Path
    validation_summary: str
    qlib_conversion_command: tuple[str, ...]
    qlib_run_command: tuple[str, ...]
    rdagent_command: tuple[str, ...]
    leaderboard_rows: int


def run_synthetic_demo(
    *,
    sample_data_path: str | Path = "data/sample/prices.csv",
    qlib_config_path: str | Path = "configs/qlib/baseline_lightgbm_alpha158.yaml",
    qlib_output_dir: str | Path = "data/qlib_bin/sample",
    experiment_store_root: str | Path = "artifacts/experiments",
    report_output_dir: str | Path = "artifacts/reports",
) -> SyntheticDemoResult:
    """Run a deterministic local demo using synthetic data and dry-run integrations."""
    sample_path = Path(sample_data_path)
    qlib_config = Path(qlib_config_path)
    store = ExperimentStore(experiment_store_root)

    frame = load_market_data(sample_path)
    validation = validate_market_data(frame)
    if not validation.is_valid:
        messages = "; ".join(issue.message for issue in validation.errors)
        raise ValueError(f"Synthetic sample data failed validation: {messages}")

    qlib_conversion = convert_to_qlib(
        QlibConversionConfig(input_path=sample_path, output_dir=Path(qlib_output_dir)),
        dry_run=True,
    )
    qlib_run = run_qlib_experiment(QlibRunRequest(config_path=qlib_config), dry_run=True)
    research_check = run_research_checks(qlib_config)
    if research_check.status == "fail":
        messages = "; ".join(issue.message for issue in research_check.failures)
        raise ValueError(f"Baseline Qlib config failed research checks: {messages}")

    rdagent = run_rdagent(
        RDAgentRunRequest(
            command_config=RDAgentCommandConfig(mode="fin_factor", loop_n=1),
        ),
        dry_run=True,
    )

    gross_returns, weights, benchmark_returns = _synthetic_portfolio_inputs()
    summary = summarize_performance(
        gross_returns,
        weights,
        cost_per_turnover=0.001,
        benchmark_returns=benchmark_returns,
        periods_per_year=252,
    )
    metrics = {
        "gross_return": summary.gross_return,
        "net_return": summary.net_return,
        "annualized_return": summary.annualized_return,
        "volatility": summary.volatility,
        "max_drawdown": summary.max_drawdown,
        "turnover": summary.turnover,
        "transaction_cost": summary.transaction_cost,
        "benchmark_return": summary.benchmark_return,
    }
    if summary.sharpe_ratio is not None:
        metrics["sharpe_ratio"] = summary.sharpe_ratio
    if summary.information_ratio is not None:
        metrics["information_ratio"] = summary.information_ratio
    if summary.hit_rate is not None:
        metrics["hit_rate"] = summary.hit_rate

    manifest = create_experiment_manifest(
        experiment_id="synthetic-demo",
        status="succeeded",
        config_path=qlib_config,
        data_source_path=sample_path,
        seed=42,
        universe="synthetic_sample",
        benchmark="synthetic_benchmark",
        date_split=DateSplit(
            train_start="2024-01-02",
            train_end="2024-01-02",
            valid_start="2024-01-03",
            valid_end="2024-01-03",
            test_start="2024-01-04",
            test_end="2024-01-04",
        ),
        transaction_cost=TransactionCostAssumptions(open_cost=0.0005, close_cost=0.0015),
        metrics=metrics,
        artifact_paths={
            "sample_data": sample_path,
            "qlib_config": qlib_config,
        },
        command=[
            "python",
            "-m",
            "src.cli",
            "demo",
            "synthetic",
        ],
        notes=(
            "Synthetic demo only. Qlib conversion, Qlib run, and RD-Agent run are dry-runs; "
            "metrics come from deterministic synthetic portfolio inputs."
        ),
    )
    manifest_path = store.save(manifest)
    report_path = write_experiment_report(manifest, report_output_dir)
    leaderboard = build_leaderboard(store.list(), metric="net_return")

    return SyntheticDemoResult(
        experiment_id=manifest.experiment_id,
        manifest_path=manifest_path,
        report_path=report_path,
        validation_summary=validation.summary(),
        qlib_conversion_command=qlib_conversion.command,
        qlib_run_command=qlib_run.command,
        rdagent_command=rdagent.command.command,
        leaderboard_rows=len(leaderboard),
    )


def _synthetic_portfolio_inputs() -> tuple[pd.Series, pd.DataFrame, pd.Series]:
    dates = pd.Index(pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]), name="date")
    scores = pd.DataFrame(
        {
            "AAA": [0.3, 0.1, 0.4],
            "BBB": [0.2, 0.4, 0.2],
            "CCC": [0.1, 0.2, 0.3],
        },
        index=dates,
    )
    weights = TopKStrategy(k=2).target_weights(scores)
    gross_returns = pd.Series([0.002, -0.001, 0.003], index=dates, name="gross_return")
    benchmark_returns = pd.Series([0.001, -0.0005, 0.0015], index=dates, name="benchmark")
    return gross_returns, weights, benchmark_returns

