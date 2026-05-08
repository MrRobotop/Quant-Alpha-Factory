"""End-to-end Qlib synthetic demo orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.data.qlib_converter import QlibConversionConfig, QlibConversionResult, convert_to_qlib
from src.experiments.manifest import create_experiment_manifest
from src.experiments.schema import DateSplit, ExperimentManifest, TransactionCostAssumptions
from src.experiments.store import ExperimentStore
from src.qlib_integration.config_builder import load_qlib_config
from src.qlib_integration.result_parser import ParsedQlibResults, parse_qlib_results
from src.qlib_integration.runner import QlibRunRequest, QlibRunResult, run_qlib_experiment
from src.validation.research_checks import run_research_checks


class QlibDemoError(RuntimeError):
    """Raised when the Qlib demo fails after recording a manifest."""


@dataclass(frozen=True)
class QlibDemoRequest:
    """Request for running the synthetic Qlib demo."""

    input_path: Path = Path("data/sample/prices.csv")
    output_dir: Path = Path("data/qlib_bin/sample")
    config_path: Path = Path("configs/qlib/baseline_lightgbm_alpha158.yaml")
    qrun_log_dir: Path = Path("artifacts/logs/qlib")
    experiment_store: Path = Path("artifacts/experiments")
    mlruns_dir: Path = Path("mlruns")


@dataclass(frozen=True)
class QlibDemoResult:
    """Result of a Qlib demo run."""

    manifest: ExperimentManifest
    manifest_path: Path
    conversion: QlibConversionResult | None
    qrun: QlibRunResult | None
    parsed_results: ParsedQlibResults
    dry_run: bool


def run_qlib_synthetic_demo(request: QlibDemoRequest, *, dry_run: bool = True) -> QlibDemoResult:
    """Run the synthetic Qlib workflow and persist a project manifest."""
    conversion: QlibConversionResult | None = None
    qrun: QlibRunResult | None = None
    parsed = ParsedQlibResults(status="unavailable", message="Qlib execution was not run.")
    store = ExperimentStore(request.experiment_store)

    try:
        config = load_qlib_config(request.config_path)
        conversion = convert_to_qlib(
            QlibConversionConfig(input_path=request.input_path, output_dir=request.output_dir),
            dry_run=dry_run,
        )
        research_check = run_research_checks(request.config_path)
        if research_check.status == "fail":
            messages = "; ".join(issue.message for issue in research_check.issues)
            raise QlibDemoError(f"Research checks failed: {messages}")

        qrun = run_qlib_experiment(
            QlibRunRequest(config_path=request.config_path, artifact_dir=request.qrun_log_dir),
            dry_run=dry_run,
        )
        latest_run = None if dry_run else _latest_mlflow_run(request.mlruns_dir)
        parsed = (
            ParsedQlibResults(status="unavailable", message="Qlib run was dry-run only.")
            if latest_run is None
            else parse_qlib_results(latest_run)
        )
        manifest = _build_manifest(
            request=request,
            config=config,
            status="succeeded",
            metrics=parsed.metrics,
            conversion=conversion,
            qrun=qrun,
            mlflow_run_dir=latest_run,
            dry_run=dry_run,
        )
        manifest_path = store.save(manifest)
        return QlibDemoResult(
            manifest=manifest,
            manifest_path=manifest_path,
            conversion=conversion,
            qrun=qrun,
            parsed_results=parsed,
            dry_run=dry_run,
        )
    except Exception as exc:
        config = _load_config_or_empty(request.config_path)
        command = list(qrun.command) if qrun is not None else []
        manifest = _build_manifest(
            request=request,
            config=config,
            status="failed",
            metrics={},
            conversion=conversion,
            qrun=qrun,
            mlflow_run_dir=None,
            dry_run=dry_run,
            failure_reason=str(exc),
            command=command,
        )
        manifest_path = store.save(manifest)
        raise QlibDemoError(
            f"Qlib synthetic demo failed. Manifest recorded: {manifest_path}"
        ) from exc


def _build_manifest(
    *,
    request: QlibDemoRequest,
    config: dict[str, Any],
    status: str,
    metrics: dict[str, Any],
    conversion: QlibConversionResult | None,
    qrun: QlibRunResult | None,
    mlflow_run_dir: Path | None,
    dry_run: bool,
    failure_reason: str | None = None,
    command: list[str] | None = None,
) -> ExperimentManifest:
    artifact_paths: dict[str, Path] = {
        "qlib_provider_uri": request.output_dir,
        "qrun_log_dir": request.qrun_log_dir,
    }
    if mlflow_run_dir is not None:
        artifact_paths["mlflow_run_dir"] = mlflow_run_dir

    return create_experiment_manifest(
        status=status,  # type: ignore[arg-type]
        config_path=request.config_path,
        data_source_path=request.input_path,
        seed=_config_seed(config),
        universe=_config_universe(config),
        benchmark=_config_benchmark(config),
        date_split=_config_date_split(config),
        transaction_cost=_config_transaction_cost(config),
        metrics=metrics,
        artifact_paths=artifact_paths,
        command=command or (list(qrun.command) if qrun is not None else []),
        failure_reason=failure_reason,
        notes=(
            "Synthetic Qlib demo. Metrics are produced from deterministic synthetic data "
            "and are not live market performance claims. "
            f"Qlib conversion backend: {conversion.backend if conversion else 'not_run'}. "
            f"Execution mode: {'dry-run' if dry_run else 'execute'}."
        ),
    )


def _latest_mlflow_run(mlruns_dir: Path) -> Path | None:
    if not mlruns_dir.exists():
        return None
    run_dirs = [path.parent for path in mlruns_dir.glob("*/*/meta.yaml")]
    if not run_dirs:
        return None
    return max(run_dirs, key=lambda path: path.stat().st_mtime)


def _load_config_or_empty(config_path: Path) -> dict[str, Any]:
    try:
        return load_qlib_config(config_path)
    except Exception:
        return {}


def _config_seed(config: dict[str, Any]) -> int | None:
    value = config.get("experiment", {}).get("seed")
    return int(value) if value is not None else None


def _config_universe(config: dict[str, Any]) -> str | None:
    return config.get("experiment", {}).get("universe")


def _config_benchmark(config: dict[str, Any]) -> str | None:
    return config.get("experiment", {}).get("benchmark")


def _config_date_split(config: dict[str, Any]) -> DateSplit | None:
    segments = config.get("task", {}).get("dataset", {}).get("kwargs", {}).get("segments", {})
    try:
        return DateSplit(
            train_start=segments["train"][0],
            train_end=segments["train"][1],
            valid_start=segments["valid"][0],
            valid_end=segments["valid"][1],
            test_start=segments["test"][0],
            test_end=segments["test"][1],
        )
    except (KeyError, IndexError, TypeError):
        return None


def _config_transaction_cost(config: dict[str, Any]) -> TransactionCostAssumptions | None:
    cost = config.get("experiment", {}).get("transaction_cost", {})
    try:
        return TransactionCostAssumptions(
            open_cost=float(cost["open_cost"]),
            close_cost=float(cost["close_cost"]),
            min_cost=float(cost.get("min_cost", 0.0)),
        )
    except (KeyError, TypeError, ValueError):
        return None
