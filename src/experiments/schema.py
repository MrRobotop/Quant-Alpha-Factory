"""Experiment manifest schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ExperimentStatus = Literal["pending", "running", "succeeded", "failed"]


@dataclass(frozen=True)
class DateSplit:
    """Train, validation, and test date boundaries."""

    train_start: str
    train_end: str
    valid_start: str
    valid_end: str
    test_start: str
    test_end: str


@dataclass(frozen=True)
class TransactionCostAssumptions:
    """Transaction cost assumptions attached to a run."""

    open_cost: float
    close_cost: float
    min_cost: float = 0.0


@dataclass(frozen=True)
class ExperimentManifest:
    """Auditable metadata for one research run."""

    experiment_id: str
    created_at: str
    status: ExperimentStatus
    config_path: str | None
    config_hash: str | None
    data_source_path: str | None
    data_hash: str | None
    code_hash: str | None
    seed: int | None
    universe: str | None
    benchmark: str | None
    date_split: DateSplit | None
    transaction_cost: TransactionCostAssumptions | None
    metrics: dict[str, Any] = field(default_factory=dict)
    artifact_paths: dict[str, str] = field(default_factory=dict)
    command: list[str] = field(default_factory=list)
    failure_reason: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ExperimentManifest:
        """Create a manifest from a JSON dictionary."""
        date_split = payload.get("date_split")
        transaction_cost = payload.get("transaction_cost")
        return cls(
            experiment_id=payload["experiment_id"],
            created_at=payload["created_at"],
            status=payload["status"],
            config_path=payload.get("config_path"),
            config_hash=payload.get("config_hash"),
            data_source_path=payload.get("data_source_path"),
            data_hash=payload.get("data_hash"),
            code_hash=payload.get("code_hash"),
            seed=payload.get("seed"),
            universe=payload.get("universe"),
            benchmark=payload.get("benchmark"),
            date_split=DateSplit(**date_split) if isinstance(date_split, dict) else None,
            transaction_cost=(
                TransactionCostAssumptions(**transaction_cost)
                if isinstance(transaction_cost, dict)
                else None
            ),
            metrics=dict(payload.get("metrics", {})),
            artifact_paths=dict(payload.get("artifact_paths", {})),
            command=list(payload.get("command", [])),
            failure_reason=payload.get("failure_reason"),
            notes=payload.get("notes"),
        )

