"""CLI tests for research checks."""

from __future__ import annotations

from typer.testing import CliRunner

from src.cli import app


def test_research_check_baseline_passes() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["research", "check", "--config", "configs/qlib/baseline_lightgbm_alpha158.yaml"],
    )

    assert result.exit_code == 0
    assert "Research checks pass" in result.output


def test_research_check_bad_config_fails(tmp_path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
task:
  dataset:
    kwargs:
      handler:
        kwargs:
          feature_expression: "future_return"
      segments:
        train: ["2024-01-01", "2024-06-30"]
        valid: ["2024-07-01", "2024-09-30"]
        test: ["2024-10-01", "2024-12-31"]
""",
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["research", "check", "--config", str(path)])

    assert result.exit_code == 1
    assert "forward_return_in_feature" in result.output
    assert "missing_transaction_cost" in result.output

