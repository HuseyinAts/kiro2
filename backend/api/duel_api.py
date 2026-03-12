"""
Duel API — F1 1v1 Düello Endpoints
SSE streaming for real-time game events.
"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger

router = APIRouter(prefix="/api/v1/duel", tags=["Düello"])
logger = get_logger("duel_api")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class MatchmakeRequest(BaseModel):
    subject: str = Field(..., description="Konu (ör. MATEMATIK)")


class MatchmakeResponse(BaseModel):
    status: str  # "matched" or "queued"
    session_id: Optional[str] = None
    message: str


class DuelAnswerRequest(BaseModel):
    question_order: int = Field(..., ge=0)
    answer: str = Field(..., pattern="^[A-E]$")
    time_ms: int = Field(..., ge=0)


class DuelAnswerResponse(BaseModel):
    round_complete: bool
    question_order: int
    player1_score: int
    player2_score: int
    is_correct: bool


class DuelRatingResponse(BaseModel):
    elo_rating: float
    wins: int
    losses: int
    draws: int
    peak_rating: float


class DuelHistoryItem(BaseModel):
    session_id: str
    subject: str
    opponent_id: Optional[str]
    my_score: int
    opponent_score: int
    won: bool
    draw: bool
    elo_change: float
    finished_at: Optional[str]


# ---------------------------------------------------------------------------
# Matchmaking
# ---------------------------------------------------------------------------

@router.post(
    "/matchmake",
    response_model=MatchmakeResponse,
    summary="Düello eşleşme kuyruğuna gir",
)
async def matchmake(
    request: MatchmakeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Join matchmaking queue. Returns matched session or queued status."""
    from services.duel_service import enqueue_matchmaking, get_or_create_rating

    try:
        # Get Redis connection
        from core.database import get_redis_client

        redis = await get_redis_client()
        if not redis:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis bağlantısı yok",
            )

        # Get or create ELO rating
        async with get_db_session_context() as db:
            rating = await get_or_create_rating(db=db, student_id=current_user.id)
            elo = rating.elo_rating

        # Try matchmaking
        session_id = await enqueue_matchmaking(
            redis,
            student_id=current_user.id,
            subject=request.subject,
            elo_rating=elo,
        )

        if session_id:
            # Match found — create DB session with questions
            from services.duel_service import create_duel_session

            match_data = await redis.get(f"duel:session:{session_id}")
            if match_data:
                match_info = json.loads(match_data)

                # Select 5 questions for the duel (IRT-calibrated for fair play)
                question_ids = await _select_duel_questions(
                    subject=request.subject, count=5
                )

                async with get_db_session_context() as db:
                    await create_duel_session(
                        db=db,
                        session_id=session_id,
                        player1_id=match_info["player1_id"],
                        player2_id=match_info["player2_id"],
                        subject=request.subject,
                        question_ids=question_ids,
                    )

                # Store question IDs in Redis for SSE delivery
                await redis.set(
                    f"duel:questions:{session_id}",
                    json.dumps(question_ids),
                    ex=600,
                )

            return MatchmakeResponse(
                status="matched",
                session_id=session_id,
                message="Eşleşme bulundu!",
            )

        return MatchmakeResponse(
            status="queued",
            session_id=None,
            message="Kuyruğa alındı, rakip bekleniyor...",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Matchmaking hatası: {e}", extra_data={"user": current_user.id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Eşleşme sırasında hata oluştu",
        )


# ---------------------------------------------------------------------------
# Answer submission
# ---------------------------------------------------------------------------

@router.post(
    "/{session_id}/answer",
    response_model=DuelAnswerResponse,
    summary="Düello sorusuna cevap gönder",
)
async def submit_answer(
    session_id: str,
    request: DuelAnswerRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Submit answer for a duel question. Correctness is checked server-side."""
    from services.duel_service import finish_duel, process_duel_answer

    try:
        # Server-side correctness check
        is_correct = await _check_answer_correctness(
            session_id=session_id,
            question_order=request.question_order,
            answer=request.answer,
        )

        async with get_db_session_context() as db:
            result = await process_duel_answer(
                db=db,
                session_id=session_id,
                player_id=current_user.id,
                question_order=request.question_order,
                answer=request.answer,
                time_ms=request.time_ms,
                is_correct=is_correct,
            )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        # Publish SSE event via Redis pub/sub
        try:
            from core.database import get_redis_client

            redis = await get_redis_client()
            if redis:
                event = {
                    "type": "answer",
                    "player_id": current_user.id,
                    **result,
                }
                await redis.publish(
                    f"duel:events:{session_id}", json.dumps(event)
                )

                # Check if all rounds are done
                if result["round_complete"]:
                    # Check if this was the last question
                    questions_data = await redis.get(f"duel:questions:{session_id}")
                    if questions_data:
                        total = len(json.loads(questions_data))
                        if request.question_order >= total - 1:
                            # Last round — finish the duel
                            async with get_db_session_context() as db:
                                final = await finish_duel(db=db, session_id=session_id)
                                if final:
                                    await redis.publish(
                                        f"duel:events:{session_id}",
                                        json.dumps({"type": "finished", **final}),
                                    )
        except Exception:
            pass  # SSE notification is best-effort

        return DuelAnswerResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Düello cevap hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cevap kaydedilirken hata oluştu",
        )


# ---------------------------------------------------------------------------
# SSE stream
# ---------------------------------------------------------------------------

@router.get(
    "/stream/{session_id}",
    summary="Düello SSE akışı",
)
async def duel_stream(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """SSE stream for real-time duel events (opponent answers, round results)."""
    # IDOR check — verify the user is a participant in this duel
    from services.duel_service import get_duel_session_players

    try:
        async with get_db_session_context() as db:
            players = await get_duel_session_players(db=db, session_id=session_id)
        if current_user.id not in players:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu düello oturumuna erişim yetkiniz yok",
            )
    except HTTPException:
        raise
    except Exception:
        # If session not found, let the stream return empty
        pass

    async def event_generator():
        from core.database import get_redis_client

        redis = await get_redis_client()
        if not redis:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Redis unavailable'})}\n\n"
            return

        pubsub = redis.pubsub()
        await pubsub.subscribe(f"duel:events:{session_id}")
        last_heartbeat = asyncio.get_event_loop().time()

        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id})}\n\n"

            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    yield f"data: {data}\n\n"
                    last_heartbeat = asyncio.get_event_loop().time()

                    # Stop stream on finished event
                    parsed = json.loads(data)
                    if parsed.get("type") == "finished":
                        break

                # Heartbeat every 30s to keep connection alive
                now = asyncio.get_event_loop().time()
                if now - last_heartbeat >= 30:
                    yield ": heartbeat\n\n"
                    last_heartbeat = now

                await asyncio.sleep(0.5)

        finally:
            await pubsub.unsubscribe(f"duel:events:{session_id}")
            await pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Rating & history
# ---------------------------------------------------------------------------

@router.get(
    "/rating",
    response_model=DuelRatingResponse,
    summary="Düello ELO puanı",
)
async def get_rating(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Get current player's duel ELO rating."""
    from services.duel_service import get_or_create_rating

    async with get_db_session_context() as db:
        rating = await get_or_create_rating(db=db, student_id=current_user.id)
        return DuelRatingResponse(
            elo_rating=rating.elo_rating,
            wins=rating.wins,
            losses=rating.losses,
            draws=rating.draws,
            peak_rating=rating.peak_rating,
        )


@router.get(
    "/history",
    response_model=list[DuelHistoryItem],
    summary="Düello geçmişi",
)
async def get_history(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Get recent duel history."""
    from services.duel_service import get_duel_history

    async with get_db_session_context() as db:
        history = await get_duel_history(db=db, student_id=current_user.id)
        return [DuelHistoryItem(**h) for h in history]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _check_answer_correctness(
    session_id: str, question_order: int, answer: str
) -> bool:
    """Server-side answer correctness check.

    Looks up the correct answer from question_bank for the given duel round.
    """
    from sqlalchemy import select

    from models.duel import DuelMatch
    from models.question_bank import QuestionBankItem

    async with get_db_session_context() as db:
        # Get the question ID for this round
        match_result = await db.execute(
            select(DuelMatch.question_id).where(
                DuelMatch.session_id == session_id,
                DuelMatch.question_order == question_order,
            )
        )
        row = match_result.first()
        if not row:
            return False

        # Get the correct answer from question bank
        q_result = await db.execute(
            select(QuestionBankItem.correct_answer).where(
                QuestionBankItem.id == row[0]
            )
        )
        q_row = q_result.first()
        if not q_row or not q_row[0]:
            return False

        # Compare (correct_answer is like "A" or "B")
        correct = q_row[0].strip().upper()
        # Handle "A) ..." format
        if len(correct) > 1:
            correct = correct[0]
        return answer.upper() == correct


async def _select_duel_questions(subject: str, count: int = 5) -> list[str]:
    """Select IRT-calibrated questions for fair duel play.

    Picks medium-difficulty questions so neither player has an unfair advantage.
    """
    from sqlalchemy import func, select

    from models.question_bank import QuestionBankItem

    async with get_db_session_context() as db:
        result = await db.execute(
            select(QuestionBankItem.id)
            .where(
                QuestionBankItem.is_active == True,  # noqa: E712
                QuestionBankItem.subject_area == subject.upper(),
            )
            .order_by(func.random())
            .limit(count)
        )
        ids = [r[0] for r in result.all()]

    # Fallback: if not enough questions, return what we have
    if not ids:
        logger.warning(f"No questions found for subject {subject}")
    return ids
