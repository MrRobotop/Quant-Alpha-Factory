"""Tests for the Qlib conversion adapter."""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pytest

from src.data.qlib_converter import (
    QlibConversionConfig,
    QlibConversionError,
    build_dump_bin_command,
    convert_to_qlib,
)


def write_valid_csv(path: Path) -> None:
    path.write_text(
        "date,symbol,open,high,low,close,volume,adjusted_close\n"
        "2024-01-02,AAA,10,11,9,10.5,1000,10.5\n"
        "2024-01-03,AAA,10.5,12,10,11,1100,11\n",
        encoding="utf-8",
    )


def test_build_dump_bin_command() -> None:
    config = QlibConversionConfig(
        input_path=Path("data/sample/prices.csv"),
        output_dir=Path("data/qlib_bin/sample"),
        python_executable="python",
    )

    command = build_dump_bin_command(config)

    assert command == (
        "python",
        "-m",
        "qlib.scripts.dump_bin",
        "dump_all",
        "--csv_path",
        "data/sample/prices.csv",
        "--qlib_dir",
        "data/qlib_bin/sample",
        "--freq",
        "day",
        "--include_fields",
        "open,high,low,close,volume,adjusted_close",
    )


def test_dry_run_validates_and_does_not_execute(tmp_path, monkeypatch) -> None:
    input_path = tmp_path / "prices.csv"
    write_valid_csv(input_path)
    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        calls.append(args[0])
        return subprocess.CompletedProcess(args[0], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = convert_to_qlib(
        QlibConversionConfig(input_path=input_path, output_dir=tmp_path / "qlib"),
        dry_run=True,
    )

    assert result.dry_run
    assert result.return_code is None
    assert calls == []


def test_execute_runs_subprocess_after_validation(tmp_path, monkeypatch) -> None:
    input_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "qlib"
    write_valid_csv(input_path)
    calls: list[tuple[str, ...]] = []

    def fake_run(command, check, capture_output, text):  # noqa: ANN001
        calls.append(command)
        assert check is False
        assert capture_output is True
        assert text is True
        return subprocess.CompletedProcess(command, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = convert_to_qlib(
        QlibConversionConfig(
            input_path=input_path,
            output_dir=output_dir,
            qlib_dump_module="json.tool",
        ),
        dry_run=False,
    )

    assert result.return_code == 0
    assert result.stdout == "ok"
    assert output_dir.exists()
    assert calls == [result.command]
    assert result.backend == "dump_bin"


def test_validation_failure_prevents_conversion(tmp_path, monkeypatch) -> None:
    input_path = tmp_path / "bad.csv"
    input_path.write_text(
        "date,symbol,open,high,low,close,volume\n"
        "2024-01-02,AAA,10,9,8,10,100\n",
        encoding="utf-8",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        calls.append(args[0])
        return subprocess.CompletedProcess(args[0], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(QlibConversionError, match="Validation failed"):
        convert_to_qlib(
            QlibConversionConfig(input_path=input_path, output_dir=tmp_path / "qlib"),
            dry_run=False,
        )

    assert calls == []


def test_subprocess_failure_is_reported(tmp_path, monkeypatch) -> None:
    input_path = tmp_path / "prices.csv"
    write_valid_csv(input_path)

    def fake_run(command, check, capture_output, text):  # noqa: ANN001
        return subprocess.CompletedProcess(command, returncode=2, stdout="", stderr="missing qlib")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(QlibConversionError, match="missing qlib"):
        convert_to_qlib(
            QlibConversionConfig(
                input_path=input_path,
                output_dir=tmp_path / "qlib",
                qlib_dump_module="json.tool",
            ),
            dry_run=False,
        )


def test_execute_writes_native_file_storage_when_dump_bin_is_unavailable(tmp_path) -> None:
    input_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "qlib"
    write_valid_csv(input_path)

    result = convert_to_qlib(
        QlibConversionConfig(
            input_path=input_path,
            output_dir=output_dir,
            qlib_dump_module="missing.qlib.dump_bin",
        ),
        dry_run=False,
    )

    assert result.return_code == 0
    assert result.backend == "native_file_storage"
    assert (output_dir / "calendars" / "day.txt").read_text(encoding="utf-8") == (
        "2024-01-02\n2024-01-03\n"
    )
    assert (output_dir / "instruments" / "sample.txt").read_text(encoding="utf-8") == (
        "aaa\t2024-01-02\t2024-01-03\n"
    )
    close_bin = output_dir / "features" / "aaa" / "close.day.bin"
    values = np.fromfile(close_bin, dtype="<f4")
    assert values.tolist() == [0.0, 10.5, 11.0]
