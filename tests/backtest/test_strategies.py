"""Tests for portfolio strategies."""

from __future__ import annotations

import pandas as pd
import pytest

from src.strategies.cost_aware import TransactionCostModel, apply_transaction_costs
from src.strategies.topk import TopKStrategy
from src.strategies.turnover_constrained import apply_turnover_constraint, constrain_turnover


def test_topk_strategy_selects_equal_weight_top_scores() -> None:
    scores = pd.DataFrame(
        {
            "AAA": [0.1, 0.4],
            "BBB": [0.3, 0.2],
            "CCC": [0.2, 0.1],
        },
        index=["d1", "d2"],
    )

    weights = TopKStrategy(k=2).target_weights(scores)

    assert weights.loc["d1", "BBB"] == 0.5
    assert weights.loc["d1", "CCC"] == 0.5
    assert weights.loc["d1", "AAA"] == 0.0
    assert weights.loc["d2", "AAA"] == 0.5
    assert weights.loc["d2", "BBB"] == 0.5


def test_topk_rejects_non_positive_k() -> None:
    with pytest.raises(ValueError, match="positive"):
        TopKStrategy(k=0).target_weights(pd.DataFrame({"AAA": [1.0]}))


def test_constrain_turnover_moves_partway_to_target() -> None:
    current = pd.Series({"AAA": 1.0, "BBB": 0.0})
    target = pd.Series({"AAA": 0.0, "BBB": 1.0})

    adjusted = constrain_turnover(current, target, max_turnover=0.25)

    assert adjusted["AAA"] == pytest.approx(0.75)
    assert adjusted["BBB"] == pytest.approx(0.25)
    assert adjusted.sum() == pytest.approx(1.0)


def test_apply_turnover_constraint_through_time() -> None:
    targets = pd.DataFrame(
        {"AAA": [1.0, 0.0], "BBB": [0.0, 1.0]},
        index=["d1", "d2"],
    )

    constrained = apply_turnover_constraint(targets, max_turnover=0.25)

    assert constrained.loc["d1", "AAA"] == pytest.approx(1.0)
    assert constrained.loc["d2", "AAA"] == pytest.approx(0.75)
    assert constrained.loc["d2", "BBB"] == pytest.approx(0.25)


def test_apply_transaction_costs() -> None:
    gross = pd.Series([0.01, 0.02])
    turns = pd.Series([0.0, 0.5])

    net = apply_transaction_costs(gross, turns, TransactionCostModel(cost_per_turnover=0.01))

    assert net.tolist() == [0.01, 0.015]


def test_transaction_cost_model_with_min_cost() -> None:
    turns = pd.Series([0.0, 0.1])

    costs = TransactionCostModel(cost_per_turnover=0.01, min_cost=0.005).cost(turns)

    assert costs.tolist() == [0.0, 0.005]

