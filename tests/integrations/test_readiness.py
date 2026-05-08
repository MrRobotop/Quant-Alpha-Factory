"""Tests for real integration readiness checks."""

from __future__ import annotations

import subprocess

from src.integrations.readiness import build_real_execution_readiness


def test_readiness_passes_when_real_prerequisites_are_mocked(tmp_path) -> None:
    qlib_dir = tmp_path / "qlib"
    qlib_dir.mkdir()
    config_path = tmp_path / "qlib.yaml"
    config_path.write_text(
        "qlib_init:\n"
        f"  provider_uri: {qlib_dir}\n"
        "task:\n"
        "  model: {}\n"
        "  dataset: {}\n"
        "  record: []\n",
        encoding="utf-8",
    )

    report = build_real_execution_readiness(
        qlib_config_path=config_path,
        environ={"OPENAI_API_KEY": "set", "DS_CODER_COSTEER_ENV_TYPE": "docker"},
        python_version=(3, 11),
        find_spec=lambda name: object() if name == "qlib" else None,
        which=lambda name: f"/usr/bin/{name}" if name in {"qrun", "rdagent", "docker"} else None,
        runner=lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], returncode=0, stdout="ok", stderr=""
        ),
    )

    assert report.is_ready
    assert report.failures == ()
    assert any(check.name == "docker_daemon" and check.status == "pass" for check in report.checks)


def test_readiness_fails_for_missing_real_prerequisites(tmp_path) -> None:
    config_path = tmp_path / "qlib.yaml"
    config_path.write_text(
        "qlib_init:\n"
        "  provider_uri: missing_qlib_dir\n"
        "task:\n"
        "  model: {}\n"
        "  dataset: {}\n"
        "  record: []\n",
        encoding="utf-8",
    )

    report = build_real_execution_readiness(
        qlib_config_path=config_path,
        environ={},
        python_version=(3, 14),
        find_spec=lambda name: None,
        which=lambda name: None,
        check_docker_daemon=False,
    )

    failure_names = {check.name for check in report.failures}
    assert not report.is_ready
    assert "python_version" in failure_names
    assert "module:qlib" in failure_names
    assert "executable:qrun" in failure_names
    assert "provider_uri" in failure_names
    assert "executable:rdagent" in failure_names
    assert "executable:docker" in failure_names
    assert "llm_credentials" in failure_names


def test_rdagent_component_does_not_check_qlib(tmp_path) -> None:
    report = build_real_execution_readiness(
        component="rdagent",
        environ={"AZURE_API_KEY": "set"},
        python_version=(3, 11),
        find_spec=lambda name: None,
        which=lambda name: "/usr/bin/rdagent" if name == "rdagent" else None,
        check_docker_daemon=False,
    )

    names = {check.name for check in report.checks}
    assert "module:qlib" not in names
    assert "executable:rdagent" in names


def test_missing_llm_credentials_can_be_warning_for_public_preflight() -> None:
    report = build_real_execution_readiness(
        component="rdagent",
        environ={"DS_CODER_COSTEER_ENV_TYPE": "docker"},
        python_version=(3, 11),
        which=lambda name: f"/usr/bin/{name}" if name in {"rdagent", "docker"} else None,
        check_docker_daemon=False,
        require_llm_credentials=False,
    )

    assert report.is_ready
    llm_check = next(check for check in report.checks if check.name == "llm_credentials")
    assert llm_check.status == "warn"
