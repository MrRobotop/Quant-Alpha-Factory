"""Tests for RD-Agent command construction."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.rd_agent_adapter.commands import (
    RDAgentCommandConfig,
    RDAgentCommandError,
    build_rdagent_command,
)


def test_health_check_command() -> None:
    command = build_rdagent_command(RDAgentCommandConfig(mode="health_check"))

    assert command.command == ("rdagent", "health_check")


@pytest.mark.parametrize("mode", ["fin_factor", "fin_model", "fin_quant", "ui"])
def test_finance_mode_commands(mode) -> None:  # noqa: ANN001
    command = build_rdagent_command(
        RDAgentCommandConfig(
            mode=mode,
            loop_n=1,
            step_n=2,
            path=Path("workspace"),
            all_duration="1h",
            checkout=True,
        )
    )

    assert command.command == (
        "rdagent",
        mode,
        "--loop_n",
        "1",
        "--step_n",
        "2",
        "--path",
        "workspace",
        "--all_duration",
        "1h",
        "--checkout",
    )


def test_report_folder_command() -> None:
    command = build_rdagent_command(
        RDAgentCommandConfig(mode="fin_factor_report", report_folder=Path("reports"))
    )

    assert command.command == ("rdagent", "fin_factor_report", "--report_folder", "reports")


def test_non_positive_loop_rejected() -> None:
    with pytest.raises(RDAgentCommandError, match="positive"):
        build_rdagent_command(RDAgentCommandConfig(mode="fin_factor", loop_n=0))

