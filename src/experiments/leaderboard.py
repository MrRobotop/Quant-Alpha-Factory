"""Experiment leaderboard queries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.experiments.schema import ExperimentManifest


@dataclass(frozen=True)
class LeaderboardRow:
    """One ranked experiment row."""

    experiment_id: str
    status: str
    metric_name: str
    metric_value: float | None
    benchmark: str | None
    universe: str | None
    created_at: str


def build_leaderboard(
    manifests: list[ExperimentManifest],
    *,
    metric: str,
    descending: bool = True,
) -> list[LeaderboardRow]:
    """Build a leaderboard, keeping missing metrics explicit and ranked last."""
    rows = [
        LeaderboardRow(
            experiment_id=manifest.experiment_id,
            status=manifest.status,
            metric_name=metric,
            metric_value=_metric_as_float(manifest.metrics.get(metric)),
            benchmark=manifest.benchmark,
            universe=manifest.universe,
            created_at=manifest.created_at,
        )
        for manifest in manifests
    ]

    return sorted(
        rows,
        key=lambda row: (
            row.metric_value is None,
            -row.metric_value if descending and row.metric_value is not None else row.metric_value,
            row.created_at,
        ),
    )


def _metric_as_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

