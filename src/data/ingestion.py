"""Market data ingestion helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.schema import (
    DATE_COLUMN,
    SYMBOL_COLUMN,
    normalize_column_names,
    ordered_canonical_columns,
)


class DataIngestionError(ValueError):
    """Raised when market data cannot be loaded into a canonical frame."""


def load_market_data(path: str | Path) -> pd.DataFrame:
    """Load CSV or Parquet market data and normalize it toward the canonical schema."""
    source = Path(path)
    if not source.exists():
        raise DataIngestionError(f"Input data file does not exist: {source}")
    if not source.is_file():
        raise DataIngestionError(f"Input data path is not a file: {source}")

    suffix = source.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(source)
    elif suffix in {".parquet", ".pq"}:
        try:
            frame = pd.read_parquet(source)
        except ImportError as exc:
            raise DataIngestionError(
                "Parquet input requires an installed pandas parquet engine such as pyarrow."
            ) from exc
    else:
        raise DataIngestionError(f"Unsupported data file extension '{source.suffix}'.")

    return normalize_market_data(frame)


def normalize_market_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize columns, parse dates, and sort by symbol/date when available."""
    normalized = normalize_column_names(frame)

    if DATE_COLUMN in normalized.columns:
        try:
            normalized[DATE_COLUMN] = pd.to_datetime(normalized[DATE_COLUMN], errors="raise")
        except (TypeError, ValueError) as exc:
            raise DataIngestionError("Could not parse the 'date' column as datetimes.") from exc

    if SYMBOL_COLUMN in normalized.columns:
        normalized[SYMBOL_COLUMN] = normalized[SYMBOL_COLUMN].astype("string").str.strip()

    sort_columns = [
        column for column in (SYMBOL_COLUMN, DATE_COLUMN) if column in normalized.columns
    ]
    if sort_columns:
        normalized = normalized.sort_values(sort_columns, kind="mergesort").reset_index(drop=True)

    return normalized.loc[:, ordered_canonical_columns(normalized)]
