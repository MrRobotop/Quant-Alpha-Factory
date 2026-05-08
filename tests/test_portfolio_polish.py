"""Tests for final portfolio-facing documentation."""

from __future__ import annotations

from pathlib import Path


def test_recruiter_docs_exist() -> None:
    assert Path("docs/recruiter_summary.md").exists()
    assert Path("docs/limitations.md").exists()
    assert Path("docs/real_execution.md").exists()
    assert Path("docs/project_walkthrough.md").exists()


def test_readme_is_not_phase_oriented() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Author: Rishabh Patil" in readme
    assert "## Getting Started" in readme
    assert "make quickstart" in readme
    assert "make install-real" in readme
    assert "## What This Demonstrates" in readme
    assert "## What Is Real, Dry-Run, And Synthetic" in readme
    assert "## One-Command Qlib Synthetic Demo" in readme
    assert "## Feature Map" in readme
    assert "## Why This Matters" in readme
    assert "python -m src.cli qlib demo --execute" in readme
    assert "docs/project_walkthrough.md" in readme
    assert "[docs/real_execution.md](docs/real_execution.md)" in readme
    assert "This repository is in Phase" not in readme


def test_recruiter_summary_has_claim_discipline() -> None:
    summary = Path("docs/recruiter_summary.md").read_text(encoding="utf-8")

    assert "does not claim live tradable performance" in summary
    assert "Qlib" in summary
    assert "RD-Agent" in summary


def test_real_execution_guide_is_actionable_without_claiming_results() -> None:
    guide = Path("docs/real_execution.md").read_text(encoding="utf-8")

    assert "python -m pip install -e" in guide
    assert "docker run hello-world" in guide
    assert "python -m src.cli qlib run" in guide
    assert "python -m src.cli qlib demo --execute" in guide
    assert "python -m src.cli rdagent run" in guide
    assert "--mode fin_factor" in guide
    assert "--loop-n 1" in guide
    assert "Do not publish or compare metrics until the manifest" in guide
    assert "https://github.com/microsoft/qlib" in guide
    assert "https://github.com/microsoft/RD-Agent" in guide
