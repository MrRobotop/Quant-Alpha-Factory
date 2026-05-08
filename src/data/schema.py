"""Canonical market data schema definitions."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

DATE_COLUMN = "date"
SYMBOL_COLUMN = "symbol"
OPEN_COLUMN = "open"
HIGH_COLUMN = "high"
LOW_COLUMN = "low"
CLOSE_COLUMN = "close"
VOLUME_COLUMN = "volume"
ADJUSTED_CLOSE_COLUMN = "adjusted_close"

REQUIRED_COLUMNS: tuple[str, ...] = (
    DATE_COLUMN,
    SYMBOL_COLUMN,
    OPEN_COLUMN,
    HIGH_COLUMN,
    LOW_COLUMN,
    CLOSE_COLUMN,
    VOLUME_COLUMN,
)

OPTIONAL_COLUMNS: tuple[str, ...] = (ADJUSTED_CLOSE_COLUMN,)

PRICE_COLUMNS: tuple[str, ...] = (
    OPEN_COLUMN,
    HIGH_COLUMN,
    LOW_COLUMN,
    CLOSE_COLUMN,
)

CANONICAL_COLUMNS: tuple[str, ...] = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

COLUMN_ALIASES: dict[str, str] = {
    "datetime": DATE_COLUMN,
    "timestamp": DATE_COLUMN,
    "time": DATE_COLUMN,
    "ticker": SYMBOL_COLUMN,
    "instrument": SYMBOL_COLUMN,
    "asset": SYMBOL_COLUMN,
    "adj close": ADJUSTED_CLOSE_COLUMN,
    "adj_close": ADJUSTED_CLOSE_COLUMN,
    "adjusted close": ADJUSTED_CLOSE_COLUMN,
}


def canonicalize_column_name(column: object) -> str:
    """Normalize one incoming column name to the canonical schema style."""
    normalized = str(column).strip().lower().replace("-", "_")
    normalized = "_".join(normalized.split())
    return COLUMN_ALIASES.get(normalized, normalized)


def normalize_column_names(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``frame`` with canonicalized column names."""
    normalized = frame.copy()
    normalized.columns = [canonicalize_column_name(column) for column in normalized.columns]
    return normalized


def missing_required_columns(columns: Iterable[str]) -> list[str]:
    """Return required canonical columns absent from ``columns``."""
    present = set(columns)
    return [column for column in REQUIRED_COLUMNS if column not in present]


def ordered_canonical_columns(frame: pd.DataFrame) -> list[str]:
    """Return known canonical columns first, then any extra columns in original order."""
    known = [column for column in CANONICAL_COLUMNS if column in frame.columns]
    extras = [column for column in frame.columns if column not in known]
    return known + extras

