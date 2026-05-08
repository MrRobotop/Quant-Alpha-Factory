"""Preflight checks for real Qlib and RD-Agent execution."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.integrations.executables import find_executable
from src.qlib_integration.config_builder import QlibConfigError, load_qlib_config

CheckStatus = Literal["pass", "warn", "fail"]
ReadinessComponent = Literal["all", "qlib", "rdagent"]

FindSpec = Callable[[str], object | None]
Which = Callable[[str], str | None]
Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class ReadinessCheck:
    """One actionable external-integration readiness check."""

    component: str
    name: str
    status: CheckStatus
    message: str
    remediation: str | None = None


@dataclass(frozen=True)
class ReadinessReport:
    """Collection of readiness checks."""

    checks: tuple[ReadinessCheck, ...]

    @property
    def failures(self) -> tuple[ReadinessCheck, ...]:
        """Return failing checks."""
        return tuple(check for check in self.checks if check.status == "fail")

    @property
    def warnings(self) -> tuple[ReadinessCheck, ...]:
        """Return warning checks."""
        return tuple(check for check in self.checks if check.status == "warn")

    @property
    def is_ready(self) -> bool:
        """Return whether all required checks passed."""
        return not self.failures

    def summary(self) -> str:
        """Return a compact status summary."""
        return (
            f"readiness={'ready' if self.is_ready else 'not_ready'} "
            f"checks={len(self.checks)} failures={len(self.failures)} warnings={len(self.warnings)}"
        )


def build_real_execution_readiness(
    *,
    component: ReadinessComponent = "all",
    qlib_config_path: str | Path = "configs/qlib/baseline_lightgbm_alpha158.yaml",
    environ: Mapping[str, str] | None = None,
    python_version: tuple[int, int] | None = None,
    find_spec: FindSpec = importlib.util.find_spec,
    which: Which | None = None,
    runner: Runner = subprocess.run,
    check_docker_daemon: bool = True,
    require_llm_credentials: bool = True,
) -> ReadinessReport:
    """Build a real-execution readiness report without requiring credentials or live data."""
    if component not in {"all", "qlib", "rdagent"}:
        raise ValueError(f"Unsupported readiness component: {component}")

    checks: list[ReadinessCheck] = []
    env = os.environ if environ is None else environ
    version = python_version or (sys.version_info.major, sys.version_info.minor)
    executable_lookup = which or _which_from_current_python

    checks.append(_check_python_version(version))
    if component in {"all", "qlib"}:
        checks.extend(_check_qlib(qlib_config_path, find_spec=find_spec, which=executable_lookup))
    if component in {"all", "rdagent"}:
        checks.extend(
            _check_rdagent(
                env,
                which=executable_lookup,
                runner=runner,
                check_docker_daemon=check_docker_daemon,
                require_llm_credentials=require_llm_credentials,
            )
        )

    return ReadinessReport(checks=tuple(checks))


def _which_from_current_python(executable: str) -> str | None:
    """Find an executable on PATH or next to the active Python interpreter."""
    return find_executable(executable)


def _check_python_version(version: tuple[int, int]) -> ReadinessCheck:
    major, minor = version
    if major == 3 and minor in {11, 12}:
        return ReadinessCheck(
            component="environment",
            name="python_version",
            status="pass",
            message=f"Python {major}.{minor} is compatible with the project real-execution path.",
        )
    return ReadinessCheck(
        component="environment",
        name="python_version",
        status="fail",
        message=f"Python {major}.{minor} is not the recommended real-execution runtime.",
        remediation="Create a Python 3.11 virtual environment and reinstall the project extras.",
    )


def _check_qlib(
    qlib_config_path: str | Path,
    *,
    find_spec: FindSpec,
    which: Which,
) -> list[ReadinessCheck]:
    checks = [
        _check_module(
            component="qlib",
            module_name="qlib",
            find_spec=find_spec,
            remediation='Install with: python -m pip install -e ".[qlib]"',
        ),
        _check_executable(
            component="qlib",
            executable="qrun",
            which=which,
            remediation=(
                "Confirm Qlib installed correctly and the virtualenv bin directory is on PATH."
            ),
        ),
    ]

    config_path = Path(qlib_config_path)
    try:
        config = load_qlib_config(config_path)
    except QlibConfigError as exc:
        checks.append(
            ReadinessCheck(
                component="qlib",
                name="provider_uri",
                status="fail",
                message=f"Qlib config is not loadable: {exc}",
                remediation="Fix the config before real qrun execution.",
            )
        )
        return checks

    provider_uri = Path(str(config["qlib_init"]["provider_uri"]))
    if provider_uri.exists():
        checks.append(
            ReadinessCheck(
                component="qlib",
                name="provider_uri",
                status="pass",
                message=f"Qlib provider URI exists: {provider_uri}",
            )
        )
    else:
        checks.append(
            ReadinessCheck(
                component="qlib",
                name="provider_uri",
                status="fail",
                message=f"Qlib provider URI does not exist: {provider_uri}",
                remediation="Run data validation and conversion with --execute before qrun.",
            )
        )
    return checks


def _check_rdagent(
    environ: Mapping[str, str],
    *,
    which: Which,
    runner: Runner,
    check_docker_daemon: bool,
    require_llm_credentials: bool,
) -> list[ReadinessCheck]:
    checks = [
        _check_executable(
            component="rdagent",
            executable="rdagent",
            which=which,
            remediation='Install with: python -m pip install -e ".[rdagent]"',
        ),
        _check_executable(
            component="rdagent",
            executable="docker",
            which=which,
            remediation="Install/start Docker before real RD-Agent workflows.",
        ),
        _check_llm_credentials(environ, required=require_llm_credentials),
        _check_rd_agent_env_type(environ),
    ]

    if check_docker_daemon and which("docker") is not None:
        checks.append(_check_docker_daemon(runner))
    return checks


def _check_module(
    *,
    component: str,
    module_name: str,
    find_spec: FindSpec,
    remediation: str,
) -> ReadinessCheck:
    if find_spec(module_name) is not None:
        return ReadinessCheck(
            component=component,
            name=f"module:{module_name}",
            status="pass",
            message=f"Python module is importable: {module_name}",
        )
    return ReadinessCheck(
        component=component,
        name=f"module:{module_name}",
        status="fail",
        message=f"Python module is not importable: {module_name}",
        remediation=remediation,
    )


def _check_executable(
    *,
    component: str,
    executable: str,
    which: Which,
    remediation: str,
) -> ReadinessCheck:
    path = which(executable)
    if path is not None:
        return ReadinessCheck(
            component=component,
            name=f"executable:{executable}",
            status="pass",
            message=f"Executable found: {executable} at {path}",
        )
    return ReadinessCheck(
        component=component,
        name=f"executable:{executable}",
        status="fail",
        message=f"Executable not found on PATH: {executable}",
        remediation=remediation,
    )


def _check_llm_credentials(environ: Mapping[str, str], *, required: bool) -> ReadinessCheck:
    supported_keys = (
        "OPENAI_API_KEY",
        "AZURE_API_KEY",
        "ANTHROPIC_API_KEY",
        "DEEPSEEK_API_KEY",
    )
    present = [key for key in supported_keys if environ.get(key)]
    if present:
        return ReadinessCheck(
            component="rdagent",
            name="llm_credentials",
            status="pass",
            message="At least one supported LLM credential variable is set.",
        )
    if not required:
        return ReadinessCheck(
            component="rdagent",
            name="llm_credentials",
            status="warn",
            message=(
                "No supported LLM credential variable is set; "
                "agent execution will remain disabled."
            ),
            remediation="Set a provider credential in .env before running real RD-Agent workflows.",
        )
    return ReadinessCheck(
        component="rdagent",
        name="llm_credentials",
        status="fail",
        message="No supported LLM credential variable is set.",
        remediation="Set an OpenAI-compatible, Azure, Anthropic, or DeepSeek credential in .env.",
    )


def _check_rd_agent_env_type(environ: Mapping[str, str]) -> ReadinessCheck:
    value = environ.get("DS_CODER_COSTEER_ENV_TYPE")
    if value == "docker":
        return ReadinessCheck(
            component="rdagent",
            name="execution_isolation",
            status="pass",
            message="RD-Agent execution isolation is configured for Docker.",
        )
    return ReadinessCheck(
        component="rdagent",
        name="execution_isolation",
        status="warn",
        message="DS_CODER_COSTEER_ENV_TYPE is not set to docker.",
        remediation="Set DS_CODER_COSTEER_ENV_TYPE=docker for isolated RD-Agent code execution.",
    )


def _check_docker_daemon(runner: Runner) -> ReadinessCheck:
    command: Sequence[str] = ("docker", "info")
    try:
        completed = runner(command, check=False, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return ReadinessCheck(
            component="rdagent",
            name="docker_daemon",
            status="fail",
            message=f"Docker daemon check could not run: {exc}",
            remediation="Start Docker Desktop or the Docker daemon.",
        )
    if completed.returncode == 0:
        return ReadinessCheck(
            component="rdagent",
            name="docker_daemon",
            status="pass",
            message="Docker daemon is reachable.",
        )
    stderr = completed.stderr.strip() or completed.stdout.strip() or "docker info failed"
    return ReadinessCheck(
        component="rdagent",
        name="docker_daemon",
        status="fail",
        message=f"Docker daemon is not reachable: {stderr}",
        remediation="Start Docker Desktop or the Docker daemon.",
    )
