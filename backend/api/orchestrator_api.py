"""
Orchestrator Admin API — dispatch tasks to the routing engine.

POST /api/v1/admin/orchestrator/dispatch
GET  /api/v1/admin/orchestrator/status
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.dependencies import AuthenticatedUser, get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/orchestrator",
    tags=["admin-orchestrator"],
)


class DispatchRequest(BaseModel):
    description: str = Field(..., description="Task description for the routing engine")
    files: list[str] = Field(default_factory=list, description="Affected file paths")


class DispatchResponse(BaseModel):
    primary_model: str
    agent_type: str
    max_diff_lines: int
    requires_human_review: bool
    confidence: float
    reason: str
    graph_available: bool


@router.post("/dispatch", response_model=DispatchResponse)
async def dispatch_task(
    request: DispatchRequest,
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
) -> DispatchResponse:
    """Route a task through the orchestrator's RoutingEngine."""
    try:
        from orchestrator.core.routing import RoutingEngine

        engine = RoutingEngine()
        decision = await engine.route(
            description=request.description,
            files=request.files,
        )

        try:
            from orchestrator import _GRAPH_AVAILABLE
        except ImportError:
            _GRAPH_AVAILABLE = False

        return DispatchResponse(
            primary_model=decision.primary_model.value,
            agent_type=decision.agent_type,
            max_diff_lines=decision.max_diff_lines,
            requires_human_review=decision.requires_human_review,
            confidence=decision.confidence,
            reason=decision.reason,
            graph_available=_GRAPH_AVAILABLE,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Orchestrator dispatch failed: %s", e)
        raise HTTPException(status_code=500, detail="Orchestrator dispatch failed")


@router.get("/status")
async def orchestrator_status(
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Check orchestrator availability and component status."""
    result: dict[str, Any] = {
        "routing_engine": False,
        "graph_available": False,
        "version": "unknown",
    }

    try:
        import orchestrator

        result["version"] = orchestrator.__version__
        result["routing_engine"] = True
        result["graph_available"] = getattr(orchestrator, "_GRAPH_AVAILABLE", False)
    except Exception as e:
        logger.error("Orchestrator status check failed: %s", e)
        result["error"] = "Orchestrator unavailable"

    return result


@router.post("/calibrate-irt")
async def calibrate_irt_batch(
    min_responses: int = 50,
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """
    Batch IRT calibration for questions with sufficient response data.

    Finds questions with >= min_responses answers, runs EAP estimation
    to update their irt_discrimination, irt_difficulty, irt_guessing.
    """
    from sqlalchemy import text

    from core.database import get_db_session_context

    calibrated = 0
    errors = 0

    try:
        async with get_db_session_context() as db:
            # Find questions with enough responses
            stmt = text("""
                SELECT sa.question_id,
                       COUNT(*) as resp_count,
                       AVG(CASE WHEN sa.is_correct THEN 1.0 ELSE 0.0 END)
                         as p_correct
                FROM student_answers sa
                WHERE sa.is_correct IS NOT NULL
                GROUP BY sa.question_id
                HAVING COUNT(*) >= :min_resp
                ORDER BY COUNT(*) DESC
                LIMIT 500
            """)
            rows = (await db.execute(stmt, {"min_resp": min_responses})).fetchall()

            for row in rows:
                q_id, resp_count, p_correct = row
                try:
                    # Simple EAP-based calibration from p_correct
                    # b = -logit(p_correct - c) / a
                    import math

                    c = 0.20  # guessing for 5-choice
                    p = max(c + 0.01, min(0.99, float(p_correct)))
                    b = -math.log((p - c) / (1.0 - p))
                    b = max(-3.0, min(3.0, b))

                    # a: higher response count → more confident
                    a = min(2.0, 0.5 + resp_count / 200.0)

                    await db.execute(
                        text("""
                            UPDATE question_bank
                            SET irt_difficulty = :b,
                                irt_discrimination = :a,
                                irt_guessing = :c
                            WHERE id = :qid
                        """),
                        {"b": round(b, 3), "a": round(a, 3), "c": c, "qid": q_id},
                    )
                    calibrated += 1
                except Exception as e:
                    errors += 1
                    logger.debug("Calibration skip q=%s: %s", q_id, e)

            await db.commit()
    except Exception as e:
        logger.error("IRT batch calibration failed: %s", e)
        raise HTTPException(status_code=500, detail="IRT calibration failed")

    return {
        "calibrated": calibrated,
        "errors": errors,
        "min_responses": min_responses,
    }
