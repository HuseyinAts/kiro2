"""
BlackboardService — Singleton wrapper for DomainBlackboard.

Provides fire-and-forget learning event publishing from the algorithm pipeline.
Uses in-memory fallback if Redis is unavailable.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any

logger = logging.getLogger(__name__)

# Type alias for async subscriber callbacks
Subscriber = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]

_instance: BlackboardService | None = None


class BlackboardService:
    """Thin singleton over DomainBlackboard for learning event publishing."""

    def __init__(self) -> None:
        self._board = None
        self._connected = False
        self._subscribers: dict[str, list[Subscriber]] = {}

    @classmethod
    def get(cls) -> BlackboardService:
        """Return singleton instance."""
        global _instance
        if _instance is None:
            _instance = cls()
        return _instance

    async def _ensure_board(self) -> Any:
        """Lazy-init DomainBlackboard on first use."""
        if self._board is not None:
            return self._board
        try:
            from agents.coordination.blackboard import DomainBlackboard

            self._board = DomainBlackboard()
            self._connected = await self._board.connect()
        except Exception as e:
            logger.warning("BlackboardService init failed (in-memory fallback): %s", e)
            # Create board anyway — it will use in-memory fallback
            from agents.coordination.blackboard import DomainBlackboard

            self._board = DomainBlackboard()
            self._board._use_fallback = True
            self._connected = False
        return self._board

    async def publish_learning_event(
        self,
        *,
        student_id: str,
        topic_id: str,
        event_data: dict[str, Any],
    ) -> str | None:
        """
        Publish a learning event to the blackboard.

        Returns message_id on success, None on failure.
        """
        try:
            board = await self._ensure_board()
            content = {
                "student_id": student_id,
                "topic_id": topic_id,
                **event_data,
            }
            msg_id = await board.post_message(
                source_agent="algorithm_pipeline",
                message_type="learning_event",
                content=content,
                target_agent=None,  # broadcast
            )
            # Notify local subscribers
            await self._notify_subscribers("learning_event", content)
            return msg_id
        except Exception as e:
            logger.warning("Blackboard publish failed: %s", e)
            return None

    def subscribe(self, event_type: str, callback: Subscriber) -> None:
        """Register an async callback for a given event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def _notify_subscribers(
        self, event_type: str, content: dict[str, Any]
    ) -> None:
        """Call all subscribers for the event type (best-effort)."""
        for cb in self._subscribers.get(event_type, []):
            try:
                await cb(content)
            except Exception as e:
                logger.warning("Subscriber callback failed: %s", e)


# ---------------------------------------------------------------------------
# Built-in subscriber: LP mastery trigger
# ---------------------------------------------------------------------------


async def _on_mastery_event(content: dict[str, Any]) -> None:
    """
    When a student reaches mastery (zpd_zone=MASTERED, theta_se<0.5),
    invalidate LP facade cache so next /status call gets fresh data.
    """
    zpd = content.get("zpd_zone", "")
    theta_se = content.get("theta_se", 1.0)
    if zpd == "MASTERED" and theta_se < 0.5:
        student_id = content.get("student_id")
        topic_id = content.get("topic_id")
        logger.info(
            "Mastery reached: student=%s topic=%s (theta_se=%.2f)",
            student_id,
            topic_id,
            theta_se,
        )
        # LP cache invalidation — force fresh path on next request
        try:
            from agents.learning_path.facade import get_learning_path_facade

            facade = get_learning_path_facade()
            facade.clear_cache()
            logger.info("LP facade cache cleared for mastery event")
        except Exception as e:
            logger.warning("LP cache invalidation failed: %s", e)

        # XP award for mastery achievement
        try:
            from uuid import UUID

            from core.database import get_db
            from core.gamification.experience_manager import ExperienceManager

            db_gen = get_db()
            db_session = next(db_gen)
            try:
                xp_mgr = ExperienceManager(db=db_session, redis_client=None)
                xp_mgr.add_xp(UUID(student_id), 50, "mastery")
                logger.info("XP awarded: student=%s +50 (mastery)", student_id)
            finally:
                try:
                    next(db_gen)
                except StopIteration:
                    pass
        except Exception as e:
            logger.warning("Mastery XP award failed: %s", e)


def register_default_subscribers() -> None:
    """Register built-in subscribers. Call once at app startup."""
    svc = BlackboardService.get()
    svc.subscribe("learning_event", _on_mastery_event)
