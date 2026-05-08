"""Qlib experiment config loading and validation."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


class QlibConfigError(ValueError):
    """Raised when a Qlib config is missing or invalid."""


REQUIRED_TOP_LEVEL_SECTIONS: tuple[str, ...] = ("qlib_init", "task")


def load_qlib_config(path: str | Path) -> dict[str, Any]:
    """Load and validate a Qlib YAML config."""
    config_path = Path(path)
    if not config_path.exists():
        raise QlibConfigError(f"Qlib config file does not exist: {config_path}")
    if not config_path.is_file():
        raise QlibConfigError(f"Qlib config path is not a file: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)

    if not isinstance(loaded, dict):
        raise QlibConfigError(f"Qlib config must be a YAML mapping: {config_path}")

    validate_qlib_config(loaded)
    return loaded


def validate_qlib_config(config: dict[str, Any]) -> None:
    """Validate the minimum sections required by this project wrapper."""
    missing = [section for section in REQUIRED_TOP_LEVEL_SECTIONS if section not in config]
    if missing:
        raise QlibConfigError(f"Qlib config missing required sections: {', '.join(missing)}")

    qlib_init = config["qlib_init"]
    if not isinstance(qlib_init, dict):
        raise QlibConfigError("Qlib config section 'qlib_init' must be a mapping.")
    if "provider_uri" not in qlib_init:
        raise QlibConfigError("Qlib config section 'qlib_init' must include provider_uri.")

    task = config["task"]
    if not isinstance(task, dict):
        raise QlibConfigError("Qlib config section 'task' must be a mapping.")
    for section in ("model", "dataset", "record"):
        if section not in task:
            raise QlibConfigError(f"Qlib config section 'task' must include {section}.")


def apply_overrides(config: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Apply dot-path overrides to a config without mutating the input."""
    updated = deepcopy(config)
    for dotted_key, value in overrides.items():
        if not dotted_key:
            raise QlibConfigError("Override keys must not be empty.")
        cursor = updated
        parts = dotted_key.split(".")
        for part in parts[:-1]:
            next_value = cursor.get(part)
            if not isinstance(next_value, dict):
                next_value = {}
                cursor[part] = next_value
            cursor = next_value
        cursor[parts[-1]] = value

    validate_qlib_config(updated)
    return updated

