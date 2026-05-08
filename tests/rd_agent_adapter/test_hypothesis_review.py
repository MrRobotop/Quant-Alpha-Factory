"""Tests for human hypothesis review workflow."""

from __future__ import annotations

import pytest

from src.rd_agent_adapter.hypothesis_review import HypothesisReview, HypothesisReviewError


def test_propose_hypothesis_review() -> None:
    review = HypothesisReview.propose(
        hypothesis_text="Momentum after earnings revisions may persist.",
        rationale="Delayed information diffusion.",
        risk_notes="Check lookahead and sector concentration.",
    )

    assert review.status == "proposed"
    assert review.promoted is False
    assert review.review_id.startswith("hyp-")


def test_approve_and_promote_hypothesis() -> None:
    review = HypothesisReview.propose(
        hypothesis_text="Volume shocks may predict reversal.",
        rationale="Liquidity pressure.",
        risk_notes="Turnover may be high.",
    )

    decided = review.decide(
        status="approved",
        reviewer="lead",
        decision_notes="Approve for controlled experiment.",
        promoted=True,
    )

    assert decided.status == "approved"
    assert decided.promoted is True


def test_only_approved_hypotheses_can_be_promoted() -> None:
    review = HypothesisReview.propose(
        hypothesis_text="Bad idea.",
        rationale="Weak.",
        risk_notes="High leakage risk.",
    )

    with pytest.raises(HypothesisReviewError, match="Only approved"):
        review.decide(
            status="rejected",
            reviewer="lead",
            decision_notes="Reject.",
            promoted=True,
        )

