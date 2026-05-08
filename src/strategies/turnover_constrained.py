"""Turnover-constrained rebalance helpers."""

from __future__ import annotations

import pandas as pd


def constrain_turnover(
    current_weights: pd.Series,
    target_weights: pd.Series,
    *,
    max_turnover: float,
) -> pd.Series:
    """Move from current toward target weights subject to one-way turnover cap."""
    if max_turnover < 0:
        raise ValueError("max_turnover must be non-negative.")
    aligned = pd.concat(
        [current_weights.fillna(0.0), target_weights.fillna(0.0)],
        axis=1,
        join="outer",
    ).fillna(0.0)
    aligned.columns = ["current", "target"]
    delta = aligned["target"] - aligned["current"]
    required_turnover = delta.abs().sum() / 2.0
    if required_turnover == 0 or required_turnover <= max_turnover:
        return aligned["target"]
    scale = max_turnover / required_turnover
    adjusted = aligned["current"] + delta * scale
    total_weight = adjusted.sum()
    if total_weight != 0:
        adjusted = adjusted / total_weight
    return adjusted


def apply_turnover_constraint(targets: pd.DataFrame, *, max_turnover: float) -> pd.DataFrame:
    """Apply turnover constraint through time to target weights."""
    if targets.empty:
        return targets.copy()
    constrained = pd.DataFrame(0.0, index=targets.index, columns=targets.columns)
    current = pd.Series(0.0, index=targets.columns)
    for date, target in targets.iterrows():
        current = constrain_turnover(current, target, max_turnover=max_turnover)
        constrained.loc[date, current.index] = current
    return constrained.loc[:, targets.columns]

