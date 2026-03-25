"""
KIRO2 — CAT API Router
=======================
Endpoint'ler:
  POST   /api/v1/cat/sessions              → Yeni oturum başlat
  POST   /api/v1/cat/sessions/{id}/answer  → Yanıt gönder, sonraki soru al
  GET    /api/v1/cat/sessions/{id}         → Oturum durumunu sorgula
  DELETE /api/v1/cat/sessions/{id}         → Oturumu iptal et

Neden 3 endpoint, tek "soru ver" değil?
  - start: placement ve warm-up mantığı farklı
  - answer: θ güncelle + sonraki seç (atomik)
  - GET:    frontend reconnect sonrası state yenile
  - DELETE: kullanıcı oturumu yarıda bırakırsa temizlik
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import User, get_current_user, get_db, get_redis
from app.schemas.cat_schemas import (
    FeedbackResponse,
    SessionStateResponse,
    StartSessionRequest,
    StartSessionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.services.cat_session import CATSessionService

router = APIRouter(prefix="/api/v1/cat", tags=["CAT"])


# ── Dependency: CATSessionService ────────────────────────────────

def get_cat_service(
    db:    AsyncSession = Depends(get_db),
    redis              = Depends(get_redis),
) -> CATSessionService:
    if redis is None:
        try:
            import redis.asyncio as _aioredis
            redis = _aioredis.from_url("redis://localhost:6379", decode_responses=False)
        except Exception:
            pass
    return CATSessionService(redis=redis, db=db)


# ── Endpoints ────────────────────────────────────────────────────

@router.post(
    "/sessions",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni CAT oturumu başlat",
    description="""
    Belirtilen ders için yeni bir adaptif test oturumu başlatır.

    - Önceki aktif oturumu iptal eder.
    - İlk soru warm-up (kolay) bölgesinden seçilir.
    - Redis'te 1 saatlik oturum açılır.
    """,
)
async def start_cat_session(
    body:         StartSessionRequest,
    current_user: User               = Depends(get_current_user),
    service:      CATSessionService  = Depends(get_cat_service),
) -> StartSessionResponse:
    try:
        result = await service.start_session(
            user_id=str(current_user.id),
            subject_id=str(body.subject_id),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return StartSessionResponse(**result)


@router.post(
    "/sessions/{session_id}/answer",
    response_model=SubmitAnswerResponse,
    summary="Yanıt gönder — θ güncelle — sonraki soruyu al",
    description="""
    Bir soruyu yanıtlar ve sonucu döndürür.

    **Oturum bitme koşulları:**
    - `se < 0.35` — θ yeterince hassas tahmin edildi
    - `n_questions >= 20` — maksimum soru sayısına ulaşıldı

    Bitmişse `is_complete=true` ve `next_question=null` gelir.
    """,
)
async def submit_answer(
    session_id:   str,
    body:         SubmitAnswerRequest,
    current_user: User              = Depends(get_current_user),
    service:      CATSessionService = Depends(get_cat_service),
) -> SubmitAnswerResponse:
    # Önce oturumun bu kullanıcıya ait olduğunu doğrula
    state = await service.get_session_state(session_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Oturum bulunamadı veya süresi dolmuş",
        )
    if state.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu oturum size ait değil",
        )

    # Doğru mu?  — DB'den doğru seçeneği al
    is_correct = await _check_answer(
        service.db, str(body.question_id), body.get_selected()
    )

    try:
        result = await service.submit_answer(
            session_id=session_id,
            question_id=str(body.question_id),
            is_correct=is_correct,
            response_ms=body.response_ms,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    # FeedbackResponse: doğru şıkkı ekle
    result["feedback"] = FeedbackResponse(
        is_correct=is_correct,
        correct_option=None,   # İsteğe bağlı: doğru şıkkı hemen göster/gizle
    )
    return SubmitAnswerResponse(**result)


@router.get(
    "/sessions/{session_id}",
    response_model=SessionStateResponse,
    summary="Oturum durumunu getir",
)
async def get_session(
    session_id:   str,
    current_user: User              = Depends(get_current_user),
    service:      CATSessionService = Depends(get_cat_service),
) -> SessionStateResponse:
    state = await service.get_session_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Oturum bulunamadı")
    if state.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Erişim reddedildi")

    return SessionStateResponse(
        session_id=  state.session_id,
        state=       state.state,
        theta=       state.theta,
        se=          state.se,
        n_questions= state.n_questions,
        warm_up_done=state.warm_up_done,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Oturumu iptal et",
)
async def abandon_session(
    session_id:   str,
    current_user: User              = Depends(get_current_user),
    service:      CATSessionService = Depends(get_cat_service),
) -> None:
    state = await service.get_session_state(session_id)
    if state and state.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Erişim reddedildi")
    await service.abandon_session(session_id)


# ── Yardımcı ──────────────────────────────────────────────────────

async def _check_answer(db, question_id: str, selected_option: str) -> bool:
    """DB'den doğru şıkkı çek, karşılaştır."""
    from sqlalchemy import text

    result = await db.execute(
        text("SELECT correct_answer FROM question_bank WHERE id = :qid"),
        {"qid": question_id},
    )
    row = result.fetchone()
    if not row:
        return False
    return row.correct_answer.upper() == selected_option.upper()
