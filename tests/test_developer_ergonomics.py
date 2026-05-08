"""Tests for developer ergonomics files."""

from __future__ import annotations

from pathlib import Path


def test_ci_workflow_runs_lint_and_tests() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "python -m ruff check ." in workflow
    assert "python -m pytest" in workflow
    assert "actions/setup-python@v5" in workflow


def test_dockerfile_installs_optional_interfaces_without_qlib() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert 'pip install -e ".[dev,api,dashboard]"' in dockerfile
    assert "pyqlib" not in dockerfile
    assert 'CMD ["python", "-m", "src.cli", "--help"]' in dockerfile


def test_makefile_has_ci_and_docker_targets() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "ci: lint test" in makefile
    assert "install-real:" in makefile
    assert "doctor-no-llm:" in makefile
    assert "quickstart: ci" in makefile
    assert "validate-release: quickstart doctor-no-llm" in makefile
    assert "qlib-demo-real:" in makefile
    assert "src.cli qlib demo --dry-run" in makefile
    assert "src.cli rdagent run --mode fin_factor --loop-n 1 --dry-run" in makefile
    assert "docker-build:" in makefile
    assert "docker-test:" in makefile
    assert "rm -rf .pytest_cache .ruff_cache" in makefile


def test_private_agent_files_are_ignored() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    for name in ("AGENTS.md", "prompts.md", "prompts-readme.md", "mlruns", "selector.log"):
        assert name in gitignore or name == "mlruns"
        assert name in dockerignore


def test_pyproject_exposes_console_script() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'authors = [{ name = "Rishabh Patil" }]' in pyproject
    assert "[project.scripts]" in pyproject
    assert 'qaf = "src.cli:app"' in pyproject
    assert "rdagent = [" in pyproject
    assert "real = [" in pyproject
