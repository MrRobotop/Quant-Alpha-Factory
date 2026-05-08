"""Tests for experiment manifest creation and serialization."""

from __future__ import annotations

import pytest

from src.experiments.manifest import (
    ManifestError,
    create_experiment_manifest,
    hash_path,
    load_manifest,
    save_manifest,
)
from src.experiments.schema import DateSplit, TransactionCostAssumptions


def test_hash_path_is_stable_for_files(tmp_path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("seed: 42\n", encoding="utf-8")

    assert hash_path(path) == hash_path(path)


def test_hash_path_changes_when_file_changes(tmp_path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("seed: 42\n", encoding="utf-8")
    first_hash = hash_path(path)
    path.write_text("seed: 43\n", encoding="utf-8")

    assert hash_path(path) != first_hash


def test_hash_path_is_stable_for_directories(tmp_path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "a.csv").write_text("a\n", encoding="utf-8")
    (data_dir / "b.csv").write_text("b\n", encoding="utf-8")

    assert hash_path(data_dir) == hash_path(data_dir)


def test_create_manifest_records_reproducibility_metadata(tmp_path) -> None:
    config = tmp_path / "config.yaml"
    data = tmp_path / "prices.csv"
    config.write_text("seed: 42\n", encoding="utf-8")
    data.write_text("date,symbol\n", encoding="utf-8")

    manifest = create_experiment_manifest(
        experiment_id="exp-test",
        status="succeeded",
        config_path=config,
        data_source_path=data,
        seed=42,
        universe="sample",
        benchmark="SPY",
        date_split=DateSplit(
            train_start="2024-01-01",
            train_end="2024-06-30",
            valid_start="2024-07-01",
            valid_end="2024-09-30",
            test_start="2024-10-01",
            test_end="2024-12-31",
        ),
        transaction_cost=TransactionCostAssumptions(open_cost=0.0005, close_cost=0.0015),
        metrics={"net_return": 0.01},
        artifact_paths={"metrics": tmp_path / "metrics.json"},
        command=["qrun", "config.yaml"],
    )

    assert manifest.experiment_id == "exp-test"
    assert manifest.config_hash == hash_path(config)
    assert manifest.data_hash == hash_path(data)
    assert manifest.metrics["net_return"] == 0.01
    assert manifest.artifact_paths["metrics"].endswith("metrics.json")


def test_failed_manifest_requires_failure_reason() -> None:
    with pytest.raises(ManifestError, match="failure_reason"):
        create_experiment_manifest(status="failed")


def test_manifest_json_round_trip(tmp_path) -> None:
    manifest = create_experiment_manifest(
        experiment_id="exp-round-trip",
        status="failed",
        failure_reason="qrun failed",
    )
    path = save_manifest(manifest, tmp_path / "manifest.json")

    loaded = load_manifest(path)

    assert loaded == manifest


def test_hash_missing_path_fails(tmp_path) -> None:
    with pytest.raises(ManifestError, match="missing path"):
        hash_path(tmp_path / "missing.csv")

