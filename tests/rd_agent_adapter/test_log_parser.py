"""Tests for conservative RD-Agent log parsing."""

from __future__ import annotations

from src.rd_agent_adapter.log_parser import parse_rdagent_logs


def test_missing_log_dir_is_unknown(tmp_path) -> None:
    result = parse_rdagent_logs(tmp_path / "missing")

    assert result.status == "unknown"


def test_parse_hypotheses_and_errors(tmp_path) -> None:
    log = tmp_path / "run.log"
    log.write_text(
        "Hypothesis: quality momentum should outperform\n"
        "ERROR: provider credential missing\n",
        encoding="utf-8",
    )

    result = parse_rdagent_logs(tmp_path)

    assert result.status == "error"
    assert result.hypotheses == ("quality momentum should outperform",)
    assert result.errors == ("provider credential missing",)


def test_unstructured_logs_are_unknown(tmp_path) -> None:
    (tmp_path / "run.log").write_text("ordinary text", encoding="utf-8")

    result = parse_rdagent_logs(tmp_path)

    assert result.status == "unknown"
    assert result.source_files == (tmp_path / "run.log",)

