"""Filesystem-backed experiment store."""

from __future__ import annotations

from pathlib import Path

from src.experiments.manifest import ManifestError, load_manifest, save_manifest
from src.experiments.schema import ExperimentManifest

MANIFEST_FILENAME = "manifest.json"


class ExperimentStoreError(ValueError):
    """Raised when an experiment store operation fails."""


class ExperimentStore:
    """Simple filesystem store under ``artifacts/experiments``."""

    def __init__(self, root: str | Path = "artifacts/experiments") -> None:
        self.root = Path(root)

    def save(self, manifest: ExperimentManifest) -> Path:
        """Save a manifest under ``<root>/<experiment_id>/manifest.json``."""
        return save_manifest(manifest, self.manifest_path(manifest.experiment_id))

    def get(self, experiment_id: str) -> ExperimentManifest:
        """Load one experiment manifest by ID."""
        try:
            return load_manifest(self.manifest_path(experiment_id))
        except ManifestError as exc:
            raise ExperimentStoreError(f"Experiment not found: {experiment_id}") from exc

    def list(self) -> list[ExperimentManifest]:
        """List all manifests in deterministic order."""
        if not self.root.exists():
            return []
        manifests: list[ExperimentManifest] = []
        for path in sorted(self.root.glob(f"*/{MANIFEST_FILENAME}")):
            manifests.append(load_manifest(path))
        return sorted(manifests, key=lambda manifest: manifest.created_at)

    def manifest_path(self, experiment_id: str) -> Path:
        """Return the manifest path for an experiment ID."""
        if not experiment_id:
            raise ExperimentStoreError("experiment_id must not be empty.")
        return self.root / experiment_id / MANIFEST_FILENAME

