"""
Duel API — F1 1v1 Düello Endpoints
SSE streaming for real-time game events.
"""

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.quality_gate import safe_for_beta_gate
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
    session_id: str | None = None
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
    opponent_id: str | None
    my_score: int
    opponent_score: int
    won: bool
    draw: bool
    elo_change: float
    finished_at: str | None


class DuelCurrentQuestionResponse(BaseModel):
    """S179 fix (B-P0-40): DuelPage frontend bekliyordu, backend'de yoktu."""

    session_id: str
    status: str
    question_order: int | None
    question_id: str | None
    question_text: str | None
    options: dict[str, str] | None  # {"A": "...", "B": "..."}
    time_per_question_sec: int
    total_questions: int
    player1_score: int
    player2_score: int
    answered: bool  # bu istemci için cevaplandı mı


class DuelResultResponse(BaseModel):
    """S179 fix (B-P0-40): final result payload."""

    session_id: str
    status: str
    subject: str
    finished: bool
    my_score: int
    opponent_score: int
    won: bool
    draw: bool
    elo_change: float
    finished_at: str | None


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

        # Get or create ELO rating and IRT Theta
        async with get_db_session_context() as db:
            rating = await get_or_create_rating(db=db, student_id=current_user.id)
            elo = rating.elo_rating

            from sqlalchemy import select as sa_select

            from models.cat_models import UserTheta

            theta_res = await db.execute(
                sa_select(UserTheta.theta_estimate).where(
                    UserTheta.user_id == str(current_user.id),
                    UserTheta.subject_area == request.subject.upper(),
                )
            )
            theta_row = theta_res.scalar_one_or_none()
            theta_estimate = float(theta_row) if theta_row is not None else 0.0

        # Try matchmaking
        session_id = await enqueue_matchmaking(
            redis,
            student_id=str(current_user.id),
            subject=request.subject,
            elo_rating=elo,
            theta_estimate=theta_estimate,
        )

        if session_id:
            # Match found — create DB session with questions
            from services.duel_service import create_duel_session

            match_data = await redis.get(f"duel:session:{session_id}")
            if match_data:
                match_info = json.loads(match_data)

                # Select 5 questions for the duel (IRT-calibrated based on shared ZPD)
                shared_theta = match_info.get("shared_theta", 0.0)
                question_ids = await _select_duel_questions(
                    subject=request.subject, count=5, target_theta=shared_theta
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
                await redis.publish(f"duel:events:{session_id}", json.dumps(event))

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
            # SSE bildirimi best-effort — cevap kaydını bozmasın diye kasıtlı
            # yutuluyor, ama iz bırakarak (sessiz yutma düellonun neden
            # "bitti" event'i göndermediğini görünmez kılıyordu; bandit B110).
            logger.debug("Düello SSE bildirimi gönderilemedi", exc_info=True)

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
        # Oturum bulunamadıysa akış boş dönsün — kontrol akışı kasıtlı olarak
        # yutuyor, ama sessizce değil: iz bırakmadan yutmak bu akışın neden
        # boş döndüğünü hata ayıklanamaz hale getiriyordu (bandit B110).
        logger.debug(
            "Düello SSE yetki ön-kontrolü atlandı (oturum okunamadı)",
            exc_info=True,
        )

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
# S179 fix (B-P0-40): DuelPage frontend bekledigi 2 endpoint
# ---------------------------------------------------------------------------


def _verify_session_player(session, user_id: str) -> str:
    """Return 'p1' or 'p2' for the requesting user, else raise 403."""
    uid = str(user_id)
    if str(session.player1_id) == uid:
        return "p1"
    if session.player2_id and str(session.player2_id) == uid:
        return "p2"
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Bu düelloya erişim yetkiniz yok.",
    )


@router.get(
    "/{session_id}/current-question",
    response_model=DuelCurrentQuestionResponse,
    summary="Sıradaki cevaplanmamış düello sorusu",
)
async def get_current_question(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Return the next unanswered question for this player in the duel.

    S179 (B-P0-40): created so DuelPage.tsx no longer 404s. Frontend was
    expecting this endpoint but only /matchmake, /answer, /stream existed.
    """
    from sqlalchemy import select as sa_select

    from models.duel import DuelMatch, DuelSession
    from models.question_bank import QuestionBankItem, QuestionContent

    async with get_db_session_context() as db:
        session = (
            await db.execute(sa_select(DuelSession).where(DuelSession.id == session_id))
        ).scalar_one_or_none()
        if not session:
            raise HTTPException(404, "Düello oturumu bulunamadı.")
        role = _verify_session_player(session, current_user.id)

        # Bulunamayan sıradaki match: bu öğrenci için cevaplanmamış ilk soru
        if role == "p1":
            answer_col = DuelMatch.player1_answer
        else:
            answer_col = DuelMatch.player2_answer

        next_match = (
            await db.execute(
                sa_select(DuelMatch)
                .where(
                    DuelMatch.session_id == session_id,
                    answer_col.is_(None),
                )
                .order_by(DuelMatch.question_order.asc())
                .limit(1)
            )
        ).scalar_one_or_none()

        total_q = session.question_count or 5

        if not next_match:
            # Tüm sorular bu oyuncu tarafından cevaplandı; veya duel bitti
            return DuelCurrentQuestionResponse(
                session_id=session_id,
                status=session.status,
                question_order=None,
                question_id=None,
                question_text=None,
                options=None,
                time_per_question_sec=session.time_per_question_sec,
                total_questions=total_q,
                player1_score=session.player1_score,
                player2_score=session.player2_score,
                answered=True,
            )

        # Soru metni ve şıklar question_content'e taşındı (#485).
        q_row = (
            await db.execute(
                sa_select(
                    QuestionBankItem.id,
                    QuestionContent.question_text,
                    QuestionContent.option_a,
                    QuestionContent.option_b,
                    QuestionContent.option_c,
                    QuestionContent.option_d,
                    QuestionContent.option_e,
                )
                .join(QuestionContent, QuestionContent.id == QuestionBankItem.id)
                .where(QuestionBankItem.id == next_match.question_id)
            )
        ).first()

        if not q_row:
            raise HTTPException(404, "Soru bulunamadı.")

        opts: dict[str, str] = {}
        for label, val in (
            ("A", q_row.option_a),
            ("B", q_row.option_b),
            ("C", q_row.option_c),
            ("D", q_row.option_d),
            ("E", q_row.option_e),
        ):
            if val:
                opts[label] = val

        return DuelCurrentQuestionResponse(
            session_id=session_id,
            status=session.status,
            question_order=next_match.question_order,
            question_id=str(q_row.id),
            question_text=q_row.question_text,
            options=opts,
            time_per_question_sec=session.time_per_question_sec,
            total_questions=total_q,
            player1_score=session.player1_score,
            player2_score=session.player2_score,
            answered=False,
        )


@router.get(
    "/{session_id}/result",
    response_model=DuelResultResponse,
    summary="Düello sonucu (bitmişse)",
)
async def get_duel_result(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Return final score + ELO delta when the duel is finished.

    S179 (B-P0-40): frontend was calling this; it didn't exist before.
    """
    from sqlalchemy import select as sa_select

    from models.duel import DuelSession

    async with get_db_session_context() as db:
        session = (
            await db.execute(sa_select(DuelSession).where(DuelSession.id == session_id))
        ).scalar_one_or_none()
        if not session:
            raise HTTPException(404, "Düello oturumu bulunamadı.")
        role = _verify_session_player(session, current_user.id)

        if session.status not in ("finished", "completed"):
            # Henüz bitmedi — frontend bunu polling ile çağıracak
            return DuelResultResponse(
                session_id=session_id,
                status=session.status,
                subject=session.subject,
                finished=False,
                my_score=0,
                opponent_score=0,
                won=False,
                draw=False,
                elo_change=0.0,
                finished_at=None,
            )

        if role == "p1":
            my_score = session.player1_score
            opp_score = session.player2_score
            elo_change = session.player1_elo_change
        else:
            my_score = session.player2_score
            opp_score = session.player1_score
            elo_change = session.player2_elo_change

        won = bool(session.winner_id) and str(session.winner_id) == str(current_user.id)
        draw = session.winner_id is None and session.status in (
            "finished",
            "completed",
        )

        return DuelResultResponse(
            session_id=session_id,
            status=session.status,
            subject=session.subject,
            finished=True,
            my_score=my_score,
            opponent_score=opp_score,
            won=won,
            draw=draw,
            elo_change=float(elo_change or 0.0),
            finished_at=(
                session.finished_at.isoformat() if session.finished_at else None
            ),
        )


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
    from models.question_bank import QuestionContent

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
        # correct_answer question_content'e taşındı (#485). question_content.id
        # question_bank.id'nin ta kendisi (FK+PK), o yüzden JOIN gerekmiyor.
        q_result = await db.execute(
            select(QuestionContent.correct_answer).where(QuestionContent.id == row[0])
        )
        q_row = q_result.first()
        if not q_row or not q_row[0]:
            return False

        # Compare (correct_answer is like "A" or "B")
        correct = q_row[0].strip().upper()
        # Handle "A) ..." format
        if len(correct) > 1:
            correct = correct[0]
        return bool(answer.upper() == correct)


async def _select_duel_questions(
    subject: str, count: int = 5, target_theta: float = 0.0
) -> list[str]:
    """Select IRT-calibrated questions for fair duel play.

    S179 fix (B-P1-12): pre-fix docstring claimed "IRT-calibrated"
    but body was just `ORDER BY random()`. True IRT bracket pick:
    questions with `irt_difficulty` around the target_theta (shared ZPD).
    Falls back to random over the full pool only if the calibrated
    band is empty.
    """
    from sqlalchemy import func, select
    from sqlalchemy import true as sa_true

    from models.question_bank import (
        QuestionBankItem,
        QuestionMetadata,
        QuestionStatistics,
    )

    async with get_db_session_context() as db:
        # NOT: select(...).tablesample() SQLAlchemy 2.0'da YOK — postgresql dalı
        # AttributeError ile patlıyordu, yani düello soru seçimi üretimde HER ZAMAN
        # 500 veriyordu. func.random() her iki dialect'te de çalışır
        # (bkz offline_sync_service.py:112).
        result = await db.execute(
            select(QuestionBankItem.id)
            # subject_area -> question_metadata, irt_difficulty ->
            # question_statistics (#485).
            .join(QuestionMetadata, QuestionMetadata.id == QuestionBankItem.id)
            .join(QuestionStatistics, QuestionStatistics.id == QuestionBankItem.id)
            .where(
                QuestionBankItem.is_active,
                # Kalite kapısı (core/quality_gate.py) — kapısız sorgu 85.731
                # yargılanmamış/reddedilmiş soruyu öğrenciye servis ediyordu.
                safe_for_beta_gate(QuestionBankItem.id),
                QuestionMetadata.subject_area == subject.upper(),
                QuestionStatistics.irt_difficulty.isnot(None),
                QuestionStatistics.irt_difficulty >= target_theta - 0.75,
                QuestionStatistics.irt_difficulty <= target_theta + 0.75,
            )
            .order_by(func.random())
            .limit(count)
        )
        ids = [r[0] for r in result.all()]

        if len(ids) < count:
            # Top-up from full pool if calibrated band is thin.
            need = count - len(ids)
            extra = await db.execute(
                select(QuestionBankItem.id)
                # subject_area -> question_metadata (#485)
                .join(QuestionMetadata, QuestionMetadata.id == QuestionBankItem.id)
                .where(
                    QuestionBankItem.is_active,
                    # Kalite kapısı — top-up fallback da kapılı olmalı, aksi
                    # halde IRT bandı ince olduğunda sızıntı buradan geri gelir.
                    safe_for_beta_gate(QuestionBankItem.id),
                    QuestionMetadata.subject_area == subject.upper(),
                    # sa_true(): çıplak Python `True` SQLAlchemy'nin where()
                    # tip sözleşmesini bozuyordu (mypy arg-type).
                    QuestionBankItem.id.notin_(ids) if ids else sa_true(),
                )
                .order_by(func.random())
                .limit(need)
            )
            ids.extend(r[0] for r in extra.all())

    if not ids:
        logger.warning(
            "No questions found for subject %s (IRT-band empty + fallback empty)",
            subject,
            exc_info=True,
        )
    return ids
