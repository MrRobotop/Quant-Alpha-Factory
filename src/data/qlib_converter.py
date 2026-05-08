"""Qlib conversion adapter for validated market data."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.ingestion import DataIngestionError, load_market_data
from src.data.validation import ValidationIssue, validate_market_data


class QlibConversionError(RuntimeError):
    """Raised when Qlib conversion cannot be started or completed."""


@dataclass(frozen=True)
class QlibConversionConfig:
    """Configuration for converting canonical market data into Qlib binary storage."""

    input_path: Path
    output_dir: Path
    freq: str = "day"
    include_fields: tuple[str, ...] = (
        "open",
        "high",
        "low",
        "close",
        "volume",
        "adjusted_close",
    )
    python_executable: str = sys.executable
    qlib_dump_module: str = "qlib.scripts.dump_bin"


@dataclass(frozen=True)
class QlibConversionResult:
    """Result returned by a Qlib conversion attempt."""

    command: tuple[str, ...]
    dry_run: bool
    return_code: int | None
    stdout: str = ""
    stderr: str = ""
    validation_issues: tuple[ValidationIssue, ...] = ()
    backend: str = "dump_bin"


def build_dump_bin_command(config: QlibConversionConfig) -> tuple[str, ...]:
    """Build the Qlib dump_bin command without executing it."""
    return (
        config.python_executable,
        "-m",
        config.qlib_dump_module,
        "dump_all",
        "--csv_path",
        str(config.input_path),
        "--qlib_dir",
        str(config.output_dir),
        "--freq",
        config.freq,
        "--include_fields",
        ",".join(config.include_fields),
    )


def convert_to_qlib(
    config: QlibConversionConfig,
    *,
    dry_run: bool = True,
) -> QlibConversionResult:
    """Validate input data and optionally execute Qlib dump_bin conversion."""
    try:
        frame = load_market_data(config.input_path)
    except DataIngestionError as exc:
        raise QlibConversionError(f"Could not load input before Qlib conversion: {exc}") from exc

    validation = validate_market_data(frame)
    command = build_dump_bin_command(config)

    if not validation.is_valid:
        messages = "; ".join(issue.message for issue in validation.errors)
        raise QlibConversionError(f"Validation failed before Qlib conversion: {messages}")

    if dry_run:
        return QlibConversionResult(
            command=command,
            dry_run=True,
            return_code=None,
            validation_issues=validation.issues,
        )

    config.output_dir.mkdir(parents=True, exist_ok=True)
    if _module_exists(config.qlib_dump_module):
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            raise QlibConversionError(
                "Qlib dump_bin conversion failed with return code "
                f"{completed.returncode}: {completed.stderr}"
            )
        return QlibConversionResult(
            command=command,
            dry_run=False,
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            validation_issues=validation.issues,
        )

    _write_native_qlib_storage(frame, config)
    return QlibConversionResult(
        command=command,
        dry_run=False,
        return_code=0,
        stdout=(
            f"Qlib dump_bin module {config.qlib_dump_module!r} was not available; "
            "wrote native Qlib file storage."
        ),
        stderr="",
        validation_issues=validation.issues,
        backend="native_file_storage",
    )


def _module_exists(module_name: str) -> bool:
    try:
        return find_spec(module_name) is not None
    except ModuleNotFoundError:
        return False


def _write_native_qlib_storage(frame: pd.DataFrame, config: QlibConversionConfig) -> None:
    """Write Qlib file storage directly for current pyqlib versions without dump_bin."""
    output_dir = config.output_dir
    calendar_dir = output_dir / "calendars"
    instrument_dir = output_dir / "instruments"
    feature_dir = output_dir / "features"
    calendar_dir.mkdir(parents=True, exist_ok=True)
    instrument_dir.mkdir(parents=True, exist_ok=True)
    feature_dir.mkdir(parents=True, exist_ok=True)

    normalized = frame.copy()
    normalized["date"] = pd.to_datetime(normalized["date"])
    normalized["symbol"] = normalized["symbol"].astype(str).str.lower()
    normalized = normalized.sort_values(["symbol", "date"])
    calendar = pd.Index(sorted(normalized["date"].unique()))
    calendar_strings = [pd.Timestamp(value).strftime("%Y-%m-%d") for value in calendar]

    _write_text_lines(calendar_dir / f"{config.freq}.txt", calendar_strings)
    _write_text_lines(calendar_dir / f"{config.freq}_future.txt", calendar_strings)

    instrument_lines = []
    for symbol, group in normalized.groupby("symbol", sort=True):
        start = group["date"].min().strftime("%Y-%m-%d")
        end = group["date"].max().strftime("%Y-%m-%d")
        instrument_lines.append(f"{symbol}\t{start}\t{end}")

    _write_text_lines(instrument_dir / "all.txt", instrument_lines)
    _write_text_lines(instrument_dir / "sample.txt", instrument_lines)

    for symbol, group in normalized.groupby("symbol", sort=True):
        symbol_dir = feature_dir / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        by_date = group.set_index("date").reindex(calendar)
        first_valid_index = _first_valid_calendar_index(by_date, config.include_fields)
        if first_valid_index is None:
            continue
        for field in config.include_fields:
            if field not in by_date.columns:
                continue
            values = by_date[field].iloc[first_valid_index:].astype(float).to_numpy()
            _write_feature_bin(
                symbol_dir / f"{field.lower()}.{config.freq.lower()}.bin",
                values,
                first_valid_index,
            )


def _first_valid_calendar_index(frame: pd.DataFrame, fields: tuple[str, ...]) -> int | None:
    available = [field for field in fields if field in frame.columns]
    if not available:
        return None
    valid_mask = frame[available].notna().any(axis=1)
    if not valid_mask.any():
        return None
    return int(np.flatnonzero(valid_mask.to_numpy())[0])


def _write_feature_bin(path: Path, values: np.ndarray, start_index: int) -> None:
    data = np.hstack([[start_index], values]).astype("<f4")
    data.tofile(path)


def _write_text_lines(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
