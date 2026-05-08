"""Safe RD-Agent execution manager."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.experiments.manifest import create_experiment_manifest
from src.experiments.schema import ExperimentManifest
from src.experiments.store import ExperimentStore
from src.integrations.executables import resolve_executable
from src.rd_agent_adapter.commands import (
    RDAgentCommand,
    RDAgentCommandConfig,
    build_rdagent_command,
)


class RDAgentRunError(RuntimeError):
    """Raised when an RD-Agent run fails in real execution mode."""


@dataclass(frozen=True)
class RDAgentRunRequest:
    """Request to run or dry-run RD-Agent."""

    command_config: RDAgentCommandConfig
    artifact_dir: Path = Path("artifacts/logs/rd_agent")
    experiment_store: Path = Path("artifacts/experiments")


@dataclass(frozen=True)
class RDAgentRunResult:
    """Result from RD-Agent dry-run or execution."""

    command: RDAgentCommand
    dry_run: bool
    return_code: int | None
    stdout: str = ""
    stderr: str = ""
    manifest: ExperimentManifest | None = None
    log_dir: Path | None = None


def run_rdagent(request: RDAgentRunRequest, *, dry_run: bool = True) -> RDAgentRunResult:
    """Build an RD-Agent command and optionally execute it with logs and manifest."""
    command = build_rdagent_command(request.command_config)
    if dry_run:
        return RDAgentRunResult(command=command, dry_run=True, return_code=None)

    request.artifact_dir.mkdir(parents=True, exist_ok=True)
    executable_command = (resolve_executable(command.command[0]), *command.command[1:])
    completed = subprocess.run(executable_command, check=False, capture_output=True, text=True)
    stdout_path = request.artifact_dir / "rdagent_stdout.log"
    stderr_path = request.artifact_dir / "rdagent_stderr.log"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    status = "succeeded" if completed.returncode == 0 else "failed"
    failure_reason = None if completed.returncode == 0 else completed.stderr or "RD-Agent failed."
    manifest = create_experiment_manifest(
        status=status,
        command=list(command.command),
        artifact_paths={
            "stdout": stdout_path,
            "stderr": stderr_path,
            "log_dir": request.artifact_dir,
        },
        failure_reason=failure_reason,
        notes=f"RD-Agent mode: {request.command_config.mode}",
    )
    ExperimentStore(request.experiment_store).save(manifest)

    result = RDAgentRunResult(
        command=command,
        dry_run=False,
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        manifest=manifest,
        log_dir=request.artifact_dir,
    )
    if completed.returncode != 0:
        raise RDAgentRunError(
            "RD-Agent command failed with return code "
            f"{completed.returncode}. Manifest recorded as {manifest.experiment_id}."
        )
    return result
