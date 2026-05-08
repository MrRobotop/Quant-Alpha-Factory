"""Tests for API and dashboard artifact readers."""

from __future__ import annotations

from typer.testing import CliRunner

from api.main import (
    get_experiment_payload,
    health,
    leaderboard_payload,
    list_experiments_payload,
)
from dashboard.app import dashboard_status, load_dashboard_data
from src.cli import app
from src.experiments.manifest import create_experiment_manifest
from src.experiments.store import ExperimentStore


def test_health_payload() -> None:
    assert health() == {"status": "ok"}


def test_experiment_payload_helpers(tmp_path) -> None:
    store = ExperimentStore(tmp_path)
    store.save(
        create_experiment_manifest(
            experiment_id="exp-api",
            status="succeeded",
            metrics={"net_return": 0.02},
            benchmark="SPY",
            universe="sample",
        )
    )

    experiments = list_experiments_payload(tmp_path)
    experiment = get_experiment_payload("exp-api", tmp_path)
    leaderboard = leaderboard_payload(tmp_path, metric="net_return")

    assert experiments[0]["experiment_id"] == "exp-api"
    assert experiment["metrics"]["net_return"] == 0.02
    assert leaderboard[0]["experiment_id"] == "exp-api"
    assert leaderboard[0]["metric_value"] == 0.02


def test_dashboard_data_loads_from_store(tmp_path) -> None:
    store = ExperimentStore(tmp_path)
    store.save(
        create_experiment_manifest(
            experiment_id="exp-dashboard",
            status="succeeded",
            metrics={"net_return": 0.01},
        )
    )

    data = load_dashboard_data(tmp_path)

    assert dashboard_status() == "dashboard scaffold"
    assert data["experiments"][0]["experiment_id"] == "exp-dashboard"
    assert data["leaderboard"][0]["experiment_id"] == "exp-dashboard"


def test_api_serve_dry_run_cli() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["api", "serve", "--host", "0.0.0.0", "--port", "9000"])

    assert result.exit_code == 0
    assert "API dry-run." in result.output
    assert "uvicorn api.main:app --host 0.0.0.0 --port 9000" in result.output


def test_dashboard_run_dry_run_cli() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["dashboard", "run"])

    assert result.exit_code == 0
    assert "Dashboard dry-run." in result.output
    assert "streamlit run dashboard/app.py" in result.output

