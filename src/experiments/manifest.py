"""Manifest creation, hashing, and JSON serialization."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.experiments.schema import (
    DateSplit,
    ExperimentManifest,
    ExperimentStatus,
    TransactionCostAssumptions,
)


class ManifestError(ValueError):
    """Raised when a manifest cannot be created or loaded."""


def create_experiment_manifest(
    *,
    experiment_id: str | None = None,
    status: ExperimentStatus = "pending",
    config_path: str | Path | None = None,
    data_source_path: str | Path | None = None,
    seed: int | None = None,
    universe: str | None = None,
    benchmark: str | None = None,
    date_split: DateSplit | None = None,
    transaction_cost: TransactionCostAssumptions | None = None,
    metrics: dict[str, Any] | None = None,
    artifact_paths: dict[str, str | Path] | None = None,
    command: list[str] | None = None,
    failure_reason: str | None = None,
    notes: str | None = None,
) -> ExperimentManifest:
    """Create a manifest with reproducibility metadata."""
    resolved_config = Path(config_path) if config_path is not None else None
    resolved_data = Path(data_source_path) if data_source_path is not None else None
    if status == "failed" and not failure_reason:
        raise ManifestError("Failed experiments must include a failure_reason.")

    return ExperimentManifest(
        experiment_id=experiment_id or f"exp-{uuid4().hex[:12]}",
        created_at=datetime.now(UTC).isoformat(),
        status=status,
        config_path=str(resolved_config) if resolved_config is not None else None,
        config_hash=hash_path(resolved_config) if resolved_config is not None else None,
        data_source_path=str(resolved_data) if resolved_data is not None else None,
        data_hash=hash_path(resolved_data) if resolved_data is not None else None,
        code_hash=current_git_commit(),
        seed=seed,
        universe=universe,
        benchmark=benchmark,
        date_split=date_split,
        transaction_cost=transaction_cost,
        metrics=metrics or {},
        artifact_paths={
            name: str(path) for name, path in (artifact_paths or {}).items()
        },
        command=command or [],
        failure_reason=failure_reason,
        notes=notes,
    )


def hash_path(path: str | Path) -> str:
    """Compute a stable SHA-256 hash for a file or directory."""
    target = Path(path)
    if not target.exists():
        raise ManifestError(f"Cannot hash missing path: {target}")
    digest = hashlib.sha256()

    if target.is_file():
        _update_digest_from_file(digest, target)
        return digest.hexdigest()

    if target.is_dir():
        for file_path in sorted(path for path in target.rglob("*") if path.is_file()):
            relative = file_path.relative_to(target).as_posix()
            digest.update(relative.encode("utf-8"))
            _update_digest_from_file(digest, file_path)
        return digest.hexdigest()

    raise ManifestError(f"Cannot hash unsupported path type: {target}")


def save_manifest(manifest: ExperimentManifest, path: str | Path) -> Path:
    """Write a manifest JSON file."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def load_manifest(path: str | Path) -> ExperimentManifest:
    """Load a manifest JSON file."""
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise ManifestError(f"Manifest file does not exist: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ManifestError(f"Manifest JSON must be an object: {manifest_path}")
    return ExperimentManifest.from_dict(payload)


def current_git_commit() -> str | None:
    """Return the current git commit hash when available."""
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    commit = completed.stdout.strip()
    return commit or None


def _update_digest_from_file(digest: Any, path: Path) -> None:
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
