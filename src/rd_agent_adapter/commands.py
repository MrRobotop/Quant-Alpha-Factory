"""RD-Agent command construction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

RDAgentMode = Literal[
    "health_check",
    "fin_factor",
    "fin_model",
    "fin_quant",
    "fin_factor_report",
    "ui",
]

SUPPORTED_MODES: tuple[RDAgentMode, ...] = (
    "health_check",
    "fin_factor",
    "fin_model",
    "fin_quant",
    "fin_factor_report",
    "ui",
)


class RDAgentCommandError(ValueError):
    """Raised when an RD-Agent command request is invalid."""


@dataclass(frozen=True)
class RDAgentCommand:
    """Deterministic RD-Agent command representation."""

    mode: RDAgentMode
    args: tuple[str, ...]

    @property
    def command(self) -> tuple[str, ...]:
        """Return shell-safe command tokens."""
        return ("rdagent", *self.args)


@dataclass(frozen=True)
class RDAgentCommandConfig:
    """Options for constructing RD-Agent commands."""

    mode: RDAgentMode
    loop_n: int | None = None
    step_n: int | None = None
    path: Path | None = None
    all_duration: str | None = None
    checkout: bool = False
    report_folder: Path | None = None


def build_rdagent_command(config: RDAgentCommandConfig) -> RDAgentCommand:
    """Build an RD-Agent command without executing it."""
    if config.mode not in SUPPORTED_MODES:
        raise RDAgentCommandError(f"Unsupported RD-Agent mode: {config.mode}")
    args: list[str] = [config.mode]

    _append_positive_int(args, "--loop_n", config.loop_n)
    _append_positive_int(args, "--step_n", config.step_n)
    if config.path is not None:
        args.extend(["--path", str(config.path)])
    if config.all_duration is not None:
        if not config.all_duration.strip():
            raise RDAgentCommandError("all_duration must not be empty.")
        args.extend(["--all_duration", config.all_duration])
    if config.checkout:
        args.append("--checkout")
    if config.report_folder is not None:
        args.extend(["--report_folder", str(config.report_folder)])

    return RDAgentCommand(mode=config.mode, args=tuple(args))


def _append_positive_int(args: list[str], flag: str, value: int | None) -> None:
    if value is None:
        return
    if value <= 0:
        raise RDAgentCommandError(f"{flag} must be positive.")
    args.extend([flag, str(value)])

