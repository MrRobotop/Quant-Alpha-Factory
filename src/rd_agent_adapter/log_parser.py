"""Conservative RD-Agent log parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class RDAgentLogSummary:
    """Conservative summary of RD-Agent logs."""

    status: str
    hypotheses: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    source_files: tuple[Path, ...] = field(default_factory=tuple)


HYPOTHESIS_PATTERN = re.compile(r"^\s*(?:hypothesis|idea)\s*:\s*(.+)$", re.IGNORECASE)
ERROR_PATTERN = re.compile(r"^\s*(?:error|exception|traceback)\b[:\s]*(.*)$", re.IGNORECASE)


def parse_rdagent_logs(log_dir: str | Path) -> RDAgentLogSummary:
    """Parse logs when they contain recognizable fields; otherwise return unknown."""
    root = Path(log_dir)
    if not root.exists() or not root.is_dir():
        return RDAgentLogSummary(status="unknown")

    hypotheses: list[str] = []
    errors: list[str] = []
    files: list[Path] = []
    for path in sorted(root.rglob("*.log")):
        files.append(path)
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            hypothesis_match = HYPOTHESIS_PATTERN.match(line)
            if hypothesis_match:
                hypotheses.append(hypothesis_match.group(1).strip())
            error_match = ERROR_PATTERN.match(line)
            if error_match:
                errors.append(error_match.group(1).strip() or line.strip())

    if errors:
        status = "error"
    elif hypotheses:
        status = "parsed"
    else:
        status = "unknown"

    return RDAgentLogSummary(
        status=status,
        hypotheses=tuple(hypotheses),
        errors=tuple(errors),
        source_files=tuple(files),
    )

