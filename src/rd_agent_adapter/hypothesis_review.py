"""Human review model for RD-Agent generated hypotheses."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

ReviewStatus = Literal["proposed", "approved", "rejected", "needs_revision"]


class HypothesisReviewError(ValueError):
    """Raised when hypothesis review transitions are invalid."""


@dataclass(frozen=True)
class HypothesisReview:
    """Human review record for an agent-generated hypothesis."""

    review_id: str
    hypothesis_text: str
    rationale: str
    risk_notes: str
    status: ReviewStatus = "proposed"
    reviewer: str | None = None
    decision_notes: str | None = None
    promoted: bool = False
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def propose(
        cls,
        *,
        hypothesis_text: str,
        rationale: str,
        risk_notes: str,
    ) -> HypothesisReview:
        """Create a proposed hypothesis review."""
        if not hypothesis_text.strip():
            raise HypothesisReviewError("hypothesis_text must not be empty.")
        if not rationale.strip():
            raise HypothesisReviewError("rationale must not be empty.")
        if not risk_notes.strip():
            raise HypothesisReviewError("risk_notes must not be empty.")
        timestamp = datetime.now(UTC).isoformat()
        return cls(
            review_id=f"hyp-{uuid4().hex[:12]}",
            hypothesis_text=hypothesis_text,
            rationale=rationale,
            risk_notes=risk_notes,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def decide(
        self,
        *,
        status: ReviewStatus,
        reviewer: str,
        decision_notes: str,
        promoted: bool = False,
    ) -> HypothesisReview:
        """Return an updated review after human decision."""
        if status == "proposed":
            raise HypothesisReviewError("Decision status cannot remain proposed.")
        if promoted and status != "approved":
            raise HypothesisReviewError("Only approved hypotheses can be promoted.")
        if not reviewer.strip():
            raise HypothesisReviewError("reviewer must not be empty.")
        if not decision_notes.strip():
            raise HypothesisReviewError("decision_notes must not be empty.")
        return HypothesisReview(
            review_id=self.review_id,
            hypothesis_text=self.hypothesis_text,
            rationale=self.rationale,
            risk_notes=self.risk_notes,
            status=status,
            reviewer=reviewer,
            decision_notes=decision_notes,
            promoted=promoted,
            created_at=self.created_at,
            updated_at=datetime.now(UTC).isoformat(),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary."""
        return asdict(self)
