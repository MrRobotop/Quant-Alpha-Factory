"""Tests for filesystem experiment storage."""

from __future__ import annotations

from src.experiments.manifest import create_experiment_manifest
from src.experiments.store import ExperimentStore


def test_store_save_get_and_list(tmp_path) -> None:
    store = ExperimentStore(tmp_path)
    first = create_experiment_manifest(experiment_id="exp-a", status="succeeded")
    second = create_experiment_manifest(
        experiment_id="exp-b",
        status="failed",
        failure_reason="bad",
    )

    first_path = store.save(first)
    second_path = store.save(second)

    assert first_path.exists()
    assert second_path.exists()
    assert store.get("exp-a") == first
    assert [manifest.experiment_id for manifest in store.list()] == ["exp-a", "exp-b"]


def test_empty_store_lists_no_experiments(tmp_path) -> None:
    assert ExperimentStore(tmp_path / "missing").list() == []
