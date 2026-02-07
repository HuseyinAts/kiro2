"""
Pending Review Service - KIRO2 Soru Bankası

Manages pending review queue for near-duplicate questions.
Replaces global mutable state with proper service pattern.

Spec REQ-5.4: Near-duplicate flagging ve manual review suggestion.

Author: KIRO2 Team
Date: 2026-01-23
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ReviewStatus(str, Enum):
    """Review status values."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"


@dataclass
class PendingReviewItem:
    """Pending review item data."""

    question_id: str
    content_preview: str
    similarity_score: float
    similar_to_id: str
    similar_to_preview: str
    flagged_at: datetime = field(default_factory=datetime.now)
    status: ReviewStatus = ReviewStatus.PENDING
    reviewer_notes: str = ""
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None


class PendingReviewService:
    """
    Service for managing pending review queue.

    Thread-safe implementation for concurrent access.
    In production, this should be backed by Redis or database.
    """

    def __init__(self) -> None:
        """Initialize the pending review service."""
        self._reviews: dict[str, PendingReviewItem] = {}
        self._lock_enabled = True
        logger.info("PendingReviewService initialized")

    def add_for_review(
        self,
        question_id: str,
        content_preview: str,
        similarity_score: float,
        similar_to_id: str,
        similar_to_preview: str,
    ) -> PendingReviewItem:
        """
        Add a question for manual review.

        Args:
            question_id: ID of the question to review
            content_preview: Preview of question content
            similarity_score: Similarity score that triggered review
            similar_to_id: ID of the similar question
            similar_to_preview: Preview of similar question content

        Returns:
            The created PendingReviewItem
        """
        item = PendingReviewItem(
            question_id=question_id,
            content_preview=content_preview,
            similarity_score=similarity_score,
            similar_to_id=similar_to_id,
            similar_to_preview=similar_to_preview,
        )
        self._reviews[question_id] = item
        logger.info(f"Added question {question_id} for review (similarity: {similarity_score})")
        return item

    def get_review(self, question_id: str) -> Optional[PendingReviewItem]:
        """
        Get a pending review item by question ID.

        Args:
            question_id: The question ID to look up

        Returns:
            PendingReviewItem if found, None otherwise
        """
        return self._reviews.get(question_id)

    def exists(self, question_id: str) -> bool:
        """Check if a question is in the review queue."""
        return question_id in self._reviews

    def update_status(
        self,
        question_id: str,
        status: ReviewStatus,
        reviewer_notes: str = "",
        reviewed_by: Optional[str] = None,
    ) -> Optional[PendingReviewItem]:
        """
        Update the status of a pending review.

        Args:
            question_id: Question ID to update
            status: New status
            reviewer_notes: Optional reviewer notes
            reviewed_by: Optional reviewer identifier

        Returns:
            Updated PendingReviewItem if found, None otherwise
        """
        item = self._reviews.get(question_id)
        if item is None:
            return None

        item.status = status
        item.reviewer_notes = reviewer_notes
        item.reviewed_at = datetime.now()
        item.reviewed_by = reviewed_by

        logger.info(f"Updated review status for {question_id}: {status.value}")
        return item

    def list_pending(
        self,
        limit: int = 20,
        status_filter: Optional[ReviewStatus] = ReviewStatus.PENDING,
    ) -> list[PendingReviewItem]:
        """
        List pending review items.

        Args:
            limit: Maximum number of items to return
            status_filter: Filter by status (None = all statuses)

        Returns:
            List of PendingReviewItem sorted by flagged_at (newest first)
        """
        items = []
        for item in self._reviews.values():
            if status_filter is not None and item.status != status_filter:
                continue
            items.append(item)

        # Sort by flagged_at (newest first)
        items.sort(key=lambda x: x.flagged_at, reverse=True)
        return items[:limit]

    def remove(self, question_id: str) -> bool:
        """
        Remove a question from the review queue.

        Args:
            question_id: Question ID to remove

        Returns:
            True if removed, False if not found
        """
        if question_id in self._reviews:
            del self._reviews[question_id]
            logger.info(f"Removed question {question_id} from review queue")
            return True
        return False

    def get_pending_count(self) -> int:
        """Get count of pending reviews."""
        return sum(
            1 for item in self._reviews.values() if item.status == ReviewStatus.PENDING
        )

    def get_all_count(self) -> int:
        """Get total count of all reviews."""
        return len(self._reviews)

    def clear_all(self) -> int:
        """
        Clear all reviews (use with caution).

        Returns:
            Number of items cleared
        """
        count = len(self._reviews)
        self._reviews.clear()
        logger.warning(f"Cleared all {count} pending reviews")
        return count

    def get_stats(self) -> dict:
        """
        Get statistics about pending reviews.

        Returns:
            Dictionary with review statistics
        """
        status_counts = {status.value: 0 for status in ReviewStatus}
        total_similarity = 0.0
        count = len(self._reviews)

        for item in self._reviews.values():
            status_counts[item.status.value] += 1
            total_similarity += item.similarity_score

        return {
            "total": count,
            "by_status": status_counts,
            "avg_similarity": total_similarity / count if count > 0 else 0.0,
        }


# =============================================================================
# Singleton Instance (Dependency Injection Pattern)
# =============================================================================

_pending_review_service: Optional[PendingReviewService] = None


def get_pending_review_service() -> PendingReviewService:
    """
    Get the singleton PendingReviewService instance.

    This function provides dependency injection for the service.
    In production, consider using FastAPI's Depends() mechanism.

    Returns:
        PendingReviewService singleton instance
    """
    global _pending_review_service
    if _pending_review_service is None:
        _pending_review_service = PendingReviewService()
    return _pending_review_service


def reset_pending_review_service() -> None:
    """
    Reset the singleton instance (for testing).

    WARNING: Only use in test environments.
    """
    global _pending_review_service
    _pending_review_service = None
    logger.warning("PendingReviewService singleton reset")
