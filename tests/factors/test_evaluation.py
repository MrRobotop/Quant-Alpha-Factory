"""Tests for factor evaluation metrics."""

from __future__ import annotations

import pandas as pd
import pytest

from src.factors.evaluation import evaluate_factor_ic


def test_evaluate_factor_ic_and_rank_ic() -> None:
    frame = pd.DataFrame(
        {
            "date": ["2024-01-02"] * 3 + ["2024-01-03"] * 3,
            "symbol": ["AAA", "BBB", "CCC", "AAA", "BBB", "CCC"],
            "factor": [1.0, 2.0, 3.0, 3.0, 2.0, 1.0],
            "forward_return": [0.01, 0.02, 0.03, 0.03, 0.02, 0.01],
        }
    )

    result = evaluate_factor_ic(frame)

    assert result.observations == 6
    assert result.mean_ic == pytest.approx(1.0)
    assert result.mean_rank_ic == pytest.approx(1.0)
    assert set(result.ic_by_date) == {"2024-01-02", "2024-01-03"}


def test_evaluate_factor_ic_drops_missing_values() -> None:
    frame = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-02", "2024-01-02"],
            "symbol": ["AAA", "BBB", "CCC"],
            "factor": [1.0, None, 3.0],
            "forward_return": [0.01, 0.02, 0.03],
        }
    )

    result = evaluate_factor_ic(frame)

    assert result.observations == 2
    assert result.mean_rank_ic == pytest.approx(1.0)


def test_evaluate_factor_ic_returns_none_when_not_enough_cross_section() -> None:
    frame = pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "symbol": ["AAA"],
            "factor": [1.0],
            "forward_return": [0.01],
        }
    )

    result = evaluate_factor_ic(frame)

    assert result.observations == 1
    assert result.mean_ic is None
    assert result.mean_rank_ic is None


def test_evaluate_factor_ic_requires_columns() -> None:
    frame = pd.DataFrame({"date": ["2024-01-02"], "symbol": ["AAA"], "factor": [1.0]})

    with pytest.raises(ValueError, match="Missing required evaluation columns"):
        evaluate_factor_ic(frame)

