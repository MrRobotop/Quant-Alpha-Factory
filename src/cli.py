"""Command line entry point for Quant Alpha Factory."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import typer

from src.data.ingestion import DataIngestionError, load_market_data
from src.data.qlib_converter import QlibConversionConfig, QlibConversionError, convert_to_qlib
from src.data.validation import validate_market_data
from src.demo.synthetic import run_synthetic_demo
from src.experiments.leaderboard import build_leaderboard
from src.experiments.store import ExperimentStore, ExperimentStoreError
from src.factors.library import build_default_registry
from src.factors.registry import FactorRegistryError
from src.integrations.readiness import build_real_execution_readiness
from src.qlib_integration.demo import QlibDemoError, QlibDemoRequest, run_qlib_synthetic_demo
from src.qlib_integration.runner import QlibRunError, QlibRunRequest, run_qlib_experiment
from src.rd_agent_adapter.commands import RDAgentCommandConfig, RDAgentCommandError
from src.rd_agent_adapter.run_manager import RDAgentRunError, RDAgentRunRequest, run_rdagent
from src.reporting.markdown import write_experiment_report
from src.validation.research_checks import ResearchCheckError, run_research_checks

app = typer.Typer(help="Quant Alpha Factory research platform.")
api_app = typer.Typer(help="API server commands.")
dashboard_app = typer.Typer(help="Dashboard commands.")
data_app = typer.Typer(help="Data ingestion and validation commands.")
demo_app = typer.Typer(help="Synthetic demo commands.")
experiments_app = typer.Typer(help="Experiment manifest and leaderboard commands.")
factors_app = typer.Typer(help="Factor registry commands.")
qlib_app = typer.Typer(help="Qlib workflow commands.")
report_app = typer.Typer(help="Research report commands.")
research_app = typer.Typer(help="Research validity commands.")
rdagent_app = typer.Typer(help="RD-Agent workflow commands.")
app.add_typer(api_app, name="api")
app.add_typer(dashboard_app, name="dashboard")
app.add_typer(data_app, name="data")
app.add_typer(demo_app, name="demo")
app.add_typer(experiments_app, name="experiments")
app.add_typer(factors_app, name="factors")
app.add_typer(qlib_app, name="qlib")
app.add_typer(report_app, name="report")
app.add_typer(research_app, name="research")
app.add_typer(rdagent_app, name="rdagent")


@app.callback()
def main() -> None:
    """Run Quant Alpha Factory commands."""


@app.command()
def status() -> None:
    """Show the current scaffold status."""
    typer.echo(
        "Quant Alpha Factory is installed. Core dry-run Qlib/RD-Agent workflows, "
        "research checks, manifests, reporting, API/dashboard helpers, and synthetic "
        "demo are ready."
    )


@app.command()
def doctor(
    component: str = typer.Option(
        "all",
        "--component",
        "-c",
        help="Readiness scope: all, qlib, or rdagent.",
    ),
    qlib_config: str = typer.Option(
        "configs/qlib/baseline_lightgbm_alpha158.yaml",
        "--qlib-config",
        help="Qlib config used to inspect provider_uri.",
    ),
    docker_daemon: bool = typer.Option(
        True,
        "--docker-daemon/--skip-docker-daemon",
        help="Check whether the Docker daemon is reachable.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit nonzero if required checks fail.",
    ),
    require_llm: bool = typer.Option(
        True,
        "--require-llm/--allow-missing-llm",
        help="Treat missing LLM credentials as a failure unless --allow-missing-llm is used.",
    ),
) -> None:
    """Check whether real Qlib/RD-Agent execution prerequisites are available."""
    if component not in {"all", "qlib", "rdagent"}:
        typer.echo("Unsupported component. Use one of: all, qlib, rdagent.", err=True)
        raise typer.Exit(code=1)

    report = build_real_execution_readiness(
        component=component,  # type: ignore[arg-type]
        qlib_config_path=qlib_config,
        check_docker_daemon=docker_daemon,
        require_llm_credentials=require_llm,
    )
    typer.echo(report.summary())
    typer.echo("status\tcomponent\tcheck\tmessage")
    for check in report.checks:
        typer.echo(f"{check.status}\t{check.component}\t{check.name}\t{check.message}")
        if check.remediation:
            typer.echo(f"remediation\t{check.component}\t{check.name}\t{check.remediation}")

    if strict and not report.is_ready:
        raise typer.Exit(code=1)


@api_app.command("serve")
def serve_api(
    host: str = typer.Option("127.0.0.1", "--host", help="API host."),
    port: int = typer.Option(8000, "--port", help="API port."),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--execute",
        help="Print the uvicorn command unless --execute is used.",
    ),
) -> None:
    """Serve the optional FastAPI app."""
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "api.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    _run_optional_ui_command(command, dry_run=dry_run, label="API")


@dashboard_app.command("run")
def run_dashboard(
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--execute",
        help="Print the Streamlit command unless --execute is used.",
    ),
) -> None:
    """Run the optional Streamlit dashboard."""
    command = [sys.executable, "-m", "streamlit", "run", "dashboard/app.py"]
    _run_optional_ui_command(command, dry_run=dry_run, label="Dashboard")


def _run_optional_ui_command(command: list[str], *, dry_run: bool, label: str) -> None:
    mode = "dry-run" if dry_run else "executed"
    typer.echo(f"{label} {mode}.")
    typer.echo("Command:")
    typer.echo(" ".join(command))
    if dry_run:
        return
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise typer.Exit(code=completed.returncode)


@data_app.command("validate")
def validate_data(
    input: str = typer.Option(..., "--input", "-i", help="CSV or Parquet file."),
) -> None:
    """Validate canonical daily OHLCV market data."""
    try:
        frame = load_market_data(input)
    except DataIngestionError as exc:
        typer.echo(f"Data ingestion failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    result = validate_market_data(frame)
    typer.echo(result.summary())
    for issue in result.issues:
        rows = f" rows={list(issue.rows)}" if issue.rows else ""
        typer.echo(f"{issue.severity.upper()} {issue.code}: {issue.message}{rows}")

    if not result.is_valid:
        raise typer.Exit(code=1)


@data_app.command("convert")
def convert_data(
    input: str = typer.Option(..., "--input", "-i", help="Validated CSV or Parquet file."),
    output: str = typer.Option(..., "--output", "-o", help="Target Qlib provider directory."),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--execute",
        help="Build the Qlib command without executing it unless --execute is used.",
    ),
) -> None:
    """Convert validated market data into Qlib-compatible storage."""
    config = QlibConversionConfig(input_path=Path(input), output_dir=Path(output))
    try:
        result = convert_to_qlib(config, dry_run=dry_run)
    except QlibConversionError as exc:
        typer.echo(f"Qlib conversion failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    mode = "dry-run" if result.dry_run else "executed"
    typer.echo(f"Qlib conversion {mode}.")
    typer.echo("Command:")
    typer.echo(" ".join(result.command))


@demo_app.command("synthetic")
def synthetic_demo(
    store: str = typer.Option("artifacts/experiments", "--store", help="Experiment store root."),
    report_dir: str = typer.Option("artifacts/reports", "--report-dir", help="Report output dir."),
) -> None:
    """Run the deterministic synthetic end-to-end demo."""
    result = run_synthetic_demo(experiment_store_root=store, report_output_dir=report_dir)
    typer.echo("Synthetic demo completed.")
    typer.echo(f"Experiment ID: {result.experiment_id}")
    typer.echo(f"Manifest: {result.manifest_path}")
    typer.echo(f"Report: {result.report_path}")
    typer.echo(result.validation_summary)
    typer.echo("Qlib conversion dry-run command:")
    typer.echo(" ".join(result.qlib_conversion_command))
    typer.echo("Qlib run dry-run command:")
    typer.echo(" ".join(result.qlib_run_command))
    typer.echo("RD-Agent dry-run command:")
    typer.echo(" ".join(result.rdagent_command))
    typer.echo(f"Leaderboard rows: {result.leaderboard_rows}")


@experiments_app.command("list")
def list_experiments(
    store: str = typer.Option("artifacts/experiments", "--store", help="Experiment store root."),
) -> None:
    """List stored experiment manifests."""
    manifests = ExperimentStore(store).list()
    if not manifests:
        typer.echo("No experiments found.")
        return

    for manifest in manifests:
        typer.echo(f"{manifest.experiment_id}\t{manifest.status}\t{manifest.created_at}")


@experiments_app.command("show")
def show_experiment(
    experiment_id: str = typer.Option(..., "--experiment-id", "-e", help="Experiment ID."),
    store: str = typer.Option("artifacts/experiments", "--store", help="Experiment store root."),
) -> None:
    """Show one stored experiment manifest as JSON."""
    try:
        manifest = ExperimentStore(store).get(experiment_id)
    except ExperimentStoreError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))


@experiments_app.command("leaderboard")
def leaderboard(
    metric: str = typer.Option("net_return", "--metric", "-m", help="Metric to rank by."),
    store: str = typer.Option("artifacts/experiments", "--store", help="Experiment store root."),
    ascending: bool = typer.Option(False, "--ascending", help="Rank lower metric values first."),
) -> None:
    """Rank experiments by a selected metric."""
    manifests = ExperimentStore(store).list()
    rows = build_leaderboard(manifests, metric=metric, descending=not ascending)
    if not rows:
        typer.echo("No experiments found.")
        return

    typer.echo("experiment_id\tstatus\tmetric\tvalue\tbenchmark\tuniverse\tcreated_at")
    for row in rows:
        value = "NA" if row.metric_value is None else f"{row.metric_value:.6g}"
        typer.echo(
            f"{row.experiment_id}\t{row.status}\t{row.metric_name}\t{value}\t"
            f"{row.benchmark or 'NA'}\t{row.universe or 'NA'}\t{row.created_at}"
        )


@factors_app.command("list")
def list_factors() -> None:
    """List registered baseline factors."""
    registry = build_default_registry()
    typer.echo("name\tversion\tcategory\tscope\thorizon")
    for factor in registry.list():
        typer.echo(
            f"{factor.name}\t{factor.version}\t{factor.category}\t"
            f"{factor.scope}\t{factor.horizon}"
        )


@factors_app.command("describe")
def describe_factor(
    name: str = typer.Option(..., "--name", "-n", help="Factor name."),
    version: str | None = typer.Option(None, "--version", "-v", help="Optional factor version."),
) -> None:
    """Describe one registered factor as JSON."""
    registry = build_default_registry()
    try:
        factor = registry.get(name, version)
    except FactorRegistryError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(json.dumps(factor.to_dict(), indent=2, sort_keys=True))


@report_app.command("build")
def build_report(
    experiment_id: str = typer.Option(..., "--experiment-id", "-e", help="Experiment ID."),
    store: str = typer.Option("artifacts/experiments", "--store", help="Experiment store root."),
    output_dir: str = typer.Option("artifacts/reports", "--output-dir", help="Report output dir."),
) -> None:
    """Build a Markdown report from a stored experiment manifest."""
    try:
        manifest = ExperimentStore(store).get(experiment_id)
    except ExperimentStoreError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    output_path = write_experiment_report(manifest, output_dir)
    typer.echo(f"Report written: {output_path}")


@research_app.command("check")
def check_research_config(
    config: str = typer.Option(..., "--config", "-c", help="YAML experiment config."),
) -> None:
    """Run research validity checks for a config."""
    try:
        result = run_research_checks(config)
    except ResearchCheckError as exc:
        typer.echo(f"Research check failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(result.summary())
    for issue in result.issues:
        typer.echo(f"{issue.status.upper()} {issue.code}: {issue.message}")

    if result.status == "fail":
        raise typer.Exit(code=1)


@rdagent_app.command("health")
def rdagent_health(
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--execute",
        help="Build the RD-Agent health command without executing unless --execute is used.",
    ),
) -> None:
    """Run or dry-run RD-Agent health check."""
    request = RDAgentRunRequest(command_config=RDAgentCommandConfig(mode="health_check"))
    _run_rdagent_request(request, dry_run=dry_run)


@rdagent_app.command("run")
def rdagent_run(
    mode: str = typer.Option(..., "--mode", "-m", help="RD-Agent mode."),
    loop_n: int | None = typer.Option(None, "--loop-n", help="Optional loop count."),
    step_n: int | None = typer.Option(None, "--step-n", help="Optional step count."),
    path: str | None = typer.Option(None, "--path", help="Optional working path."),
    all_duration: str | None = typer.Option(None, "--all-duration", help="Optional duration."),
    checkout: bool = typer.Option(False, "--checkout", help="Pass checkout flag to RD-Agent."),
    report_folder: str | None = typer.Option(
        None,
        "--report-folder",
        help="Optional report folder for report-based modes.",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--execute",
        help="Build the RD-Agent command without executing unless --execute is used.",
    ),
) -> None:
    """Run or dry-run an RD-Agent finance workflow."""
    command_config = RDAgentCommandConfig(
        mode=mode,  # type: ignore[arg-type]
        loop_n=loop_n,
        step_n=step_n,
        path=Path(path) if path is not None else None,
        all_duration=all_duration,
        checkout=checkout,
        report_folder=Path(report_folder) if report_folder is not None else None,
    )
    _run_rdagent_request(RDAgentRunRequest(command_config=command_config), dry_run=dry_run)


def _run_rdagent_request(request: RDAgentRunRequest, *, dry_run: bool) -> None:
    try:
        result = run_rdagent(request, dry_run=dry_run)
    except (RDAgentCommandError, RDAgentRunError) as exc:
        typer.echo(f"RD-Agent run failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    mode = "dry-run" if result.dry_run else "executed"
    typer.echo(f"RD-Agent {mode}.")
    typer.echo("Command:")
    typer.echo(" ".join(result.command.command))
    if result.manifest is not None:
        typer.echo(f"Manifest: {result.manifest.experiment_id}")


@qlib_app.command("run")
def run_qlib(
    config: str = typer.Option(..., "--config", "-c", help="Qlib YAML workflow config."),
    artifact_dir: str = typer.Option(
        "artifacts/logs/qlib",
        "--artifact-dir",
        help="Directory for qrun stdout/stderr logs when executing.",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--execute",
        help="Build and validate the qrun command without executing unless --execute is used.",
    ),
) -> None:
    """Run a Qlib workflow through the project wrapper."""
    request = QlibRunRequest(config_path=Path(config), artifact_dir=Path(artifact_dir))
    try:
        result = run_qlib_experiment(request, dry_run=dry_run)
    except QlibRunError as exc:
        typer.echo(f"Qlib run failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    mode = "dry-run" if result.dry_run else "executed"
    typer.echo(f"Qlib run {mode}.")
    typer.echo("Command:")
    typer.echo(" ".join(result.command))


@qlib_app.command("demo")
def qlib_demo(
    input: str = typer.Option("data/sample/prices.csv", "--input", help="Synthetic CSV input."),
    output: str = typer.Option(
        "data/qlib_bin/sample",
        "--output",
        help="Target Qlib provider directory.",
    ),
    config: str = typer.Option(
        "configs/qlib/baseline_lightgbm_alpha158.yaml",
        "--config",
        "-c",
        help="Qlib baseline config.",
    ),
    store: str = typer.Option("artifacts/experiments", "--store", help="Experiment store root."),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--execute",
        help="Validate and build commands unless --execute is used.",
    ),
) -> None:
    """Run the synthetic Qlib workflow and record a project manifest."""
    request = QlibDemoRequest(
        input_path=Path(input),
        output_dir=Path(output),
        config_path=Path(config),
        experiment_store=Path(store),
    )
    try:
        result = run_qlib_synthetic_demo(request, dry_run=dry_run)
    except QlibDemoError as exc:
        typer.echo(f"Qlib demo failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    mode = "dry-run" if result.dry_run else "executed"
    typer.echo(f"Qlib synthetic demo {mode}.")
    typer.echo(f"Experiment ID: {result.manifest.experiment_id}")
    typer.echo(f"Manifest: {result.manifest_path}")
    if result.conversion is not None:
        typer.echo(f"Conversion backend: {result.conversion.backend}")
    if result.parsed_results.metrics:
        typer.echo(f"Parsed metrics: {len(result.parsed_results.metrics)}")
    else:
        typer.echo(f"Parsed metrics: 0 ({result.parsed_results.message})")


if __name__ == "__main__":
    app()
