"""Optional FastAPI application entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.experiments.leaderboard import build_leaderboard
from src.experiments.store import ExperimentStore, ExperimentStoreError

DEFAULT_STORE_ROOT = Path("artifacts/experiments")


def health() -> dict[str, str]:
    """Return a minimal health payload without requiring FastAPI."""
    return {"status": "ok"}


def list_experiments_payload(store_root: str | Path = DEFAULT_STORE_ROOT) -> list[dict[str, Any]]:
    """Return stored experiment manifests as dictionaries."""
    return [manifest.to_dict() for manifest in ExperimentStore(store_root).list()]


def get_experiment_payload(
    experiment_id: str,
    store_root: str | Path = DEFAULT_STORE_ROOT,
) -> dict[str, Any]:
    """Return one experiment manifest payload."""
    return ExperimentStore(store_root).get(experiment_id).to_dict()


def leaderboard_payload(
    store_root: str | Path = DEFAULT_STORE_ROOT,
    *,
    metric: str = "net_return",
    descending: bool = True,
) -> list[dict[str, Any]]:
    """Return leaderboard rows as dictionaries."""
    return [
        {
            "experiment_id": row.experiment_id,
            "status": row.status,
            "metric_name": row.metric_name,
            "metric_value": row.metric_value,
            "benchmark": row.benchmark,
            "universe": row.universe,
            "created_at": row.created_at,
        }
        for row in build_leaderboard(
            ExperimentStore(store_root).list(),
            metric=metric,
            descending=descending,
        )
    ]


def create_app(store_root: str | Path = DEFAULT_STORE_ROOT):
    """Create a FastAPI app when FastAPI is installed."""
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise RuntimeError("FastAPI is optional. Install with `pip install -e '.[api]'`.") from exc

    app = FastAPI(title="Quant Alpha Factory API")

    @app.get("/health")
    def _health() -> dict[str, str]:
        return health()

    @app.get("/experiments")
    def _experiments() -> list[dict[str, Any]]:
        return list_experiments_payload(store_root)

    @app.get("/experiments/{experiment_id}")
    def _experiment(experiment_id: str) -> dict[str, Any]:
        try:
            return get_experiment_payload(experiment_id, store_root)
        except ExperimentStoreError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/leaderboard")
    def _leaderboard(metric: str = "net_return") -> list[dict[str, Any]]:
        return leaderboard_payload(store_root, metric=metric)

    return app


try:
    app = create_app()
except RuntimeError:
    app = None
