"""Conservative parsing for Qlib experiment artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

ParseStatus = Literal["available", "partial", "unavailable"]


@dataclass(frozen=True)
class ParsedQlibResults:
    """Parsed Qlib artifact summary."""

    status: ParseStatus
    metrics: dict[str, Any] = field(default_factory=dict)
    artifacts: tuple[Path, ...] = ()
    message: str = ""


KNOWN_JSON_ARTIFACTS: tuple[str, ...] = (
    "metrics.json",
    "portfolio_analysis.json",
    "signal_analysis.json",
    "results.json",
)


def parse_qlib_results(artifact_dir: str | Path) -> ParsedQlibResults:
    """Parse supported Qlib result artifacts if they exist."""
    root = Path(artifact_dir)
    if not root.exists():
        return ParsedQlibResults(
            status="unavailable",
            message=f"Artifact directory does not exist: {root}",
        )
    if not root.is_dir():
        return ParsedQlibResults(
            status="unavailable",
            message=f"Artifact path is not a directory: {root}",
        )

    parsed: dict[str, Any] = {}
    artifacts: list[Path] = []
    errors: list[str] = []

    metrics_dir = root / "metrics"
    if metrics_dir.is_dir():
        metric_values, metric_artifacts, metric_errors = _parse_mlflow_metric_dir(metrics_dir)
        parsed.update(metric_values)
        artifacts.extend(metric_artifacts)
        errors.extend(metric_errors)

    for artifact_name in KNOWN_JSON_ARTIFACTS:
        for path in root.rglob(artifact_name):
            artifacts.append(path)
            try:
                parsed[path.stem] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{path}: {exc}")

    if not artifacts:
        return ParsedQlibResults(
            status="unavailable",
            message=f"No supported Qlib result artifacts found under {root}.",
        )

    if errors:
        return ParsedQlibResults(
            status="partial",
            metrics=parsed,
            artifacts=tuple(artifacts),
            message="Some Qlib artifacts could not be parsed: " + "; ".join(errors),
        )

    return ParsedQlibResults(
        status="available",
        metrics=parsed,
        artifacts=tuple(artifacts),
        message=f"Parsed {len(artifacts)} supported Qlib result artifact(s).",
    )


def _parse_mlflow_metric_dir(metrics_dir: Path) -> tuple[dict[str, float], list[Path], list[str]]:
    parsed: dict[str, float] = {}
    artifacts: list[Path] = []
    errors: list[str] = []

    for path in sorted(file_path for file_path in metrics_dir.iterdir() if file_path.is_file()):
        artifacts.append(path)
        lines = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not lines:
            continue
        latest = lines[-1].split()
        if len(latest) < 2:
            errors.append(f"{path}: expected MLflow metric row with timestamp value step")
            continue
        try:
            parsed[path.name] = float(latest[1])
        except ValueError as exc:
            errors.append(f"{path}: {exc}")

    return parsed, artifacts, errors
