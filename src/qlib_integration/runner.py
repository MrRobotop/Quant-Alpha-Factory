"""Controlled Qlib qrun execution."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.integrations.executables import resolve_executable
from src.qlib_integration.config_builder import QlibConfigError, load_qlib_config


class QlibRunError(RuntimeError):
    """Raised when a Qlib run cannot be started or completed."""


@dataclass(frozen=True)
class QlibRunRequest:
    """Request for running a Qlib workflow config."""

    config_path: Path
    artifact_dir: Path = Path("artifacts/logs/qlib")
    qrun_executable: str = "qrun"


@dataclass(frozen=True)
class QlibRunResult:
    """Result returned by a Qlib qrun attempt."""

    command: tuple[str, ...]
    dry_run: bool
    return_code: int | None
    stdout: str = ""
    stderr: str = ""
    artifact_dir: Path | None = None


def build_qrun_command(request: QlibRunRequest) -> tuple[str, ...]:
    """Build a qrun command without executing it."""
    return (request.qrun_executable, str(request.config_path))


def run_qlib_experiment(request: QlibRunRequest, *, dry_run: bool = True) -> QlibRunResult:
    """Validate a Qlib config and optionally execute qrun."""
    try:
        load_qlib_config(request.config_path)
    except QlibConfigError as exc:
        raise QlibRunError(f"Cannot run Qlib experiment with invalid config: {exc}") from exc

    command = build_qrun_command(request)
    if dry_run:
        return QlibRunResult(command=command, dry_run=True, return_code=None)

    request.artifact_dir.mkdir(parents=True, exist_ok=True)
    executable_command = (resolve_executable(command[0]), *command[1:])
    completed = subprocess.run(executable_command, check=False, capture_output=True, text=True)

    stdout_path = request.artifact_dir / "qrun_stdout.log"
    stderr_path = request.artifact_dir / "qrun_stderr.log"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    if completed.returncode != 0:
        raise QlibRunError(
            "Qlib qrun failed with return code "
            f"{completed.returncode}. Logs written to {request.artifact_dir}."
        )

    return QlibRunResult(
        command=command,
        dry_run=False,
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        artifact_dir=request.artifact_dir,
    )
