"""Tests for Qlib config loading and overrides."""

from __future__ import annotations

import pytest

from src.qlib_integration.config_builder import (
    QlibConfigError,
    apply_overrides,
    load_qlib_config,
)


def test_load_baseline_config() -> None:
    config = load_qlib_config("configs/qlib/baseline_lightgbm_alpha158.yaml")

    assert config["qlib_init"]["provider_uri"] == "data/qlib_bin/sample"
    assert config["task"]["model"]["class"] == "LGBModel"
    assert config["task"]["dataset"]["kwargs"]["segments"]["train"] == [
        "2024-01-02",
        "2024-06-30",
    ]
    strategy_kwargs = config["task"]["record"][2]["kwargs"]["config"]["strategy"]["kwargs"]
    assert strategy_kwargs["signal"] == "<PRED>"


def test_apply_provider_uri_override_without_mutating_original() -> None:
    config = load_qlib_config("configs/qlib/baseline_lightgbm_alpha158.yaml")

    updated = apply_overrides(config, {"qlib_init.provider_uri": "data/qlib_bin/other"})

    assert updated["qlib_init"]["provider_uri"] == "data/qlib_bin/other"
    assert config["qlib_init"]["provider_uri"] == "data/qlib_bin/sample"


def test_missing_config_fails() -> None:
    with pytest.raises(QlibConfigError, match="does not exist"):
        load_qlib_config("configs/qlib/missing.yaml")


def test_missing_required_sections_fail(tmp_path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("qlib_init:\n  provider_uri: data/qlib_bin/sample\n", encoding="utf-8")

    with pytest.raises(QlibConfigError, match="missing required sections"):
        load_qlib_config(path)
