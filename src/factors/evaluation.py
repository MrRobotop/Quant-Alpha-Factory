"""Factor quality evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.data.schema import DATE_COLUMN, SYMBOL_COLUMN


@dataclass(frozen=True)
class FactorICResult:
    """Information coefficient summary for a factor."""

    observations: int
    mean_ic: float | None
    mean_rank_ic: float | None
    ic_by_date: dict[str, float]
    rank_ic_by_date: dict[str, float]


def evaluate_factor_ic(
    frame: pd.DataFrame,
    *,
    factor_column: str = "factor",
    forward_return_column: str = "forward_return",
    date_column: str = DATE_COLUMN,
    symbol_column: str = SYMBOL_COLUMN,
) -> FactorICResult:
    """Compute cross-sectional IC and rank IC from factor values and forward returns."""
    required = {date_column, symbol_column, factor_column, forward_return_column}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required evaluation columns: {', '.join(missing)}")

    working = frame.loc[
        :,
        [date_column, symbol_column, factor_column, forward_return_column],
    ].copy()
    working[factor_column] = pd.to_numeric(working[factor_column], errors="coerce")
    working[forward_return_column] = pd.to_numeric(working[forward_return_column], errors="coerce")
    working = working.dropna(subset=[factor_column, forward_return_column])

    ic_by_date: dict[str, float] = {}
    rank_ic_by_date: dict[str, float] = {}
    for date, group in working.groupby(date_column, sort=True):
        if len(group) < 2:
            continue
        factor = group[factor_column]
        returns = group[forward_return_column]
        if factor.nunique() < 2 or returns.nunique() < 2:
            continue
        ic = factor.corr(returns, method="pearson")
        rank_ic = factor.rank(method="average").corr(returns.rank(method="average"))
        if pd.notna(ic):
            ic_by_date[str(date)] = float(ic)
        if pd.notna(rank_ic):
            rank_ic_by_date[str(date)] = float(rank_ic)

    return FactorICResult(
        observations=len(working),
        mean_ic=_mean_or_none(ic_by_date.values()),
        mean_rank_ic=_mean_or_none(rank_ic_by_date.values()),
        ic_by_date=ic_by_date,
        rank_ic_by_date=rank_ic_by_date,
    )


def _mean_or_none(values) -> float | None:  # noqa: ANN001
    values = list(values)
    if not values:
        return None
    return float(sum(values) / len(values))
