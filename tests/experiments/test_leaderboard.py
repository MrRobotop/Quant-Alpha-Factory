"""Tests for experiment leaderboard queries."""

from __future__ import annotations

from dataclasses import replace

from src.experiments.leaderboard import build_leaderboard
from src.experiments.manifest import create_experiment_manifest


def test_leaderboard_sorts_metric_descending_with_missing_last() -> None:
    low = create_experiment_manifest(
        experiment_id="low",
        status="succeeded",
        metrics={"net_return": 0.01},
    )
    high = create_experiment_manifest(
        experiment_id="high",
        status="succeeded",
        metrics={"net_return": 0.03},
    )
    missing = create_experiment_manifest(experiment_id="missing", status="succeeded")

    rows = build_leaderboard([low, missing, high], metric="net_return")

    assert [row.experiment_id for row in rows] == ["high", "low", "missing"]
    assert rows[-1].metric_value is None


def test_leaderboard_can_sort_ascending() -> None:
    first = create_experiment_manifest(
        experiment_id="first",
        status="succeeded",
        metrics={"drawdown": -0.05},
    )
    second = create_experiment_manifest(
        experiment_id="second",
        status="succeeded",
        metrics={"drawdown": -0.10},
    )

    rows = build_leaderboard([first, second], metric="drawdown", descending=False)

    assert [row.experiment_id for row in rows] == ["second", "first"]


def test_leaderboard_rejects_non_numeric_metric_values() -> None:
    manifest = create_experiment_manifest(
        experiment_id="text-metric",
        status="succeeded",
        metrics={"net_return": "not available"},
    )

    rows = build_leaderboard([manifest], metric="net_return")

    assert rows[0].metric_value is None


def test_leaderboard_preserves_benchmark_and_universe() -> None:
    manifest = create_experiment_manifest(
        experiment_id="exp-meta",
        status="succeeded",
        universe="sample",
        benchmark="SPY",
        metrics={"net_return": 0.01},
    )

    row = build_leaderboard([replace(manifest)], metric="net_return")[0]

    assert row.benchmark == "SPY"
    assert row.universe == "sample"

