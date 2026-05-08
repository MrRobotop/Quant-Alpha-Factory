"""Markdown research report generation from experiment manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.experiments.schema import ExperimentManifest


def build_experiment_report(
    manifest: ExperimentManifest,
    *,
    objective: str = "Evaluate a recorded Quant Alpha Factory experiment.",
) -> str:
    """Build a Markdown report from a stored experiment manifest."""
    lines = [
        f"# Experiment Report: {manifest.experiment_id}",
        "",
        "## Objective",
        "",
        objective,
        "",
        "## Run Status",
        "",
        f"- Status: `{manifest.status}`",
        f"- Created At: `{manifest.created_at}`",
        f"- Failure Reason: {_value_or_na(manifest.failure_reason)}",
        "",
        "## Reproducibility",
        "",
        f"- Config Path: {_value_or_na(manifest.config_path)}",
        f"- Config Hash: {_value_or_na(manifest.config_hash)}",
        f"- Data Source Path: {_value_or_na(manifest.data_source_path)}",
        f"- Data Hash: {_value_or_na(manifest.data_hash)}",
        f"- Code Hash: {_value_or_na(manifest.code_hash)}",
        f"- Seed: {_value_or_na(manifest.seed)}",
        f"- Command: `{_command_or_na(manifest.command)}`",
        "",
        "## Data And Universe",
        "",
        f"- Universe: {_value_or_na(manifest.universe)}",
        f"- Benchmark: {_value_or_na(manifest.benchmark)}",
        "",
        "## Date Split",
        "",
        *_date_split_lines(manifest),
        "",
        "## Transaction Costs",
        "",
        *_transaction_cost_lines(manifest),
        "",
        "## Metrics",
        "",
        *_metric_lines(manifest.metrics),
        "",
        "## Artifacts",
        "",
        *_artifact_lines(manifest.artifact_paths),
        "",
        "## Notes",
        "",
        _value_or_na(manifest.notes),
        "",
        "## Limitations",
        "",
        (
            "This report only summarizes recorded artifacts. Missing metrics are reported as "
            "`not available`; no performance values are inferred or fabricated."
        ),
        "",
        "Synthetic data or dry-run outputs must not be interpreted as live tradable performance.",
        "",
        "## Next Experiments",
        "",
        "- Re-run with validated real market data if available.",
        "- Compare against benchmark-relative and cost-adjusted metrics.",
        "- Review leakage checks before promoting any factor or model.",
        "",
    ]
    return "\n".join(lines)


def write_experiment_report(
    manifest: ExperimentManifest,
    output_dir: str | Path = "artifacts/reports",
) -> Path:
    """Write a Markdown experiment report and return its path."""
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    output_path = root / f"{manifest.experiment_id}.md"
    output_path.write_text(build_experiment_report(manifest), encoding="utf-8")
    return output_path


def _date_split_lines(manifest: ExperimentManifest) -> list[str]:
    if manifest.date_split is None:
        return ["- Train: not available", "- Validation: not available", "- Test: not available"]
    split = manifest.date_split
    return [
        f"- Train: `{split.train_start}` to `{split.train_end}`",
        f"- Validation: `{split.valid_start}` to `{split.valid_end}`",
        f"- Test: `{split.test_start}` to `{split.test_end}`",
    ]


def _transaction_cost_lines(manifest: ExperimentManifest) -> list[str]:
    if manifest.transaction_cost is None:
        return ["- Transaction costs: not available"]
    cost = manifest.transaction_cost
    return [
        f"- Open Cost: `{cost.open_cost}`",
        f"- Close Cost: `{cost.close_cost}`",
        f"- Minimum Cost: `{cost.min_cost}`",
    ]


def _metric_lines(metrics: dict[str, Any]) -> list[str]:
    if not metrics:
        return ["- Metrics: not available"]
    return [f"- {name}: `{_value_or_na(value)}`" for name, value in sorted(metrics.items())]


def _artifact_lines(artifacts: dict[str, str]) -> list[str]:
    if not artifacts:
        return ["- Artifacts: not available"]
    return [f"- {name}: `{path}`" for name, path in sorted(artifacts.items())]


def _value_or_na(value: object) -> str:
    if value is None or value == "":
        return "not available"
    return str(value)


def _command_or_na(command: list[str]) -> str:
    if not command:
        return "not available"
    return " ".join(command)
