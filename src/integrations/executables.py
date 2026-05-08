"""Executable resolution helpers for local virtual environments."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def find_executable(executable: str) -> str | None:
    """Find an executable on PATH or next to the active Python interpreter."""
    path = shutil.which(executable)
    if path is not None:
        return path

    candidate_dirs = (
        Path(sys.executable).parent,
        Path(sys.prefix) / "bin",
        Path(sys.executable).resolve().parent,
    )
    for candidate_dir in candidate_dirs:
        candidate = candidate_dir / executable
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    return None


def resolve_executable(executable: str) -> str:
    """Return a resolved executable path when possible, otherwise the original token."""
    return find_executable(executable) or executable
