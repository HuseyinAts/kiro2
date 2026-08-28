"""Enhanced Chat API - AI sohbet sistemi."""

import base64
import contextlib
import json
import logging
import os
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.ddos_protection import limiter
from core.learning_path_auth import (
    get_learning_path_profile_user_id,
    verify_student_access,
)
from core.turkish_nlp_utils import normalize_tr
from services.socratic_rag_guardrail_service import socratic_rag_guardrail_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/enhanced-chat", tags=["chat"])


# ---------------------------------------------------------------------------
# Auth dependency (graceful fallback for dev)
# ---------------------------------------------------------------------------
def _get_auth_dependency():
    try:
        from core.dependencies import get_current_user

        return Depends(get_current_user)
    except ImportError:
        _is_dev = os.getenv("ENVIRONMENT", "development") == "development"
        if _is_dev:
            logger.warning(
                "Auth module not available — enhanced-chat unauthenticated (dev mode)"
            )

            async def _noop_auth() -> None:
                return None

            return Depends(_noop_auth)
        raise RuntimeError(
            "Auth module required in production — core.dependencies.get_current_user not found"
        )


_auth_dep = _get_auth_dependency()


def _get_db_dependency():
    try:
        from core.dependencies import get_db

        return Depends(get_db)
    except ImportError:
        logger.warning("DB module not available — chat persistence disabled")

    async def _noop_db() -> None:
        return None

    return Depends(_noop_db)


_db_dep = _get_db_dependency()


async def _verify_enhanced_chat_student_context(
    student_id: str,
    current_user: Any,
    db: AsyncSession | None,
) -> None:
    """IDOR guard: require DB + ownership (or staff) when authenticated."""
    if current_user is None:
        return
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Öğrenci doğrulaması için veritabanı gerekli.",
        )
    await verify_student_access(student_id, current_user, db)


# ---------------------------------------------------------------------------
# DB helpers (raw SQL — chat tables use VARCHAR ids, not UUID)
# ---------------------------------------------------------------------------
_chat_tables_verified = False


async def _verify_chat_tables(db: AsyncSession) -> bool:
    """Check chat tables exist on first call. Logs error once if missing."""
    global _chat_tables_verified  # noqa: PLW0603
    if _chat_tables_verified:
        return True
    try:
        await db.execute(text("SELECT 1 FROM chat_sessions LIMIT 0"))
        await db.execute(text("SELECT 1 FROM chat_messages LIMIT 0"))
        _chat_tables_verified = True
        return True
    except Exception:
        logger.error(
            "Chat tables (chat_sessions, chat_messages) not found! "
            "Run: python backend/_scripts/create_chat_tables.py"
        )
        # Rollback the failed transaction so the connection is usable
        with contextlib.suppress(Exception):
            await db.rollback()
        return False


async def _get_or_create_session(
    db: AsyncSession,
    user_id: str,
    session_id: str | None,
    subject: str,
) -> str:
    """Get existing session or create a new one. Returns session_id."""
    if session_id:
        r = await db.execute(
            text("SELECT id FROM chat_sessions WHERE id = :sid"),
            {"sid": session_id},
        )
        if r.scalar_one_or_none():
            return session_id

    new_id = str(uuid4())
    title = subject.capitalize() if subject else "Yeni Sohbet"
    await db.execute(
        text(
            "INSERT INTO chat_sessions (id, user_id, title, subject_type, organization_id) "
            "VALUES (:id, :uid, :title, :subj, :org_id)"
        ),
        {
            "id": new_id,
            "uid": user_id,
            "title": title,
            "subj": subject or "general",
            "org_id": "org_legacy_default",
        },
    )
    await db.commit()
    return new_id


async def _save_message(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    model: str | None = None,
    confidence: float | None = None,
) -> str:
    """Save a message to chat_messages. Returns message id."""
    msg_id = str(uuid4())
    await db.execute(
        text(
            "INSERT INTO chat_messages (id, session_id, role, content, model, confidence_score) "
            "VALUES (:id, :sid, :role, :content, :model, :conf)"
        ),
        {
            "id": msg_id,
            "sid": session_id,
            "role": role,
            "content": content,
            "model": model,
            "conf": confidence,
        },
    )
    # Update session stats
    await db.execute(
        text(
            "UPDATE chat_sessions SET message_count = message_count + 1, "
            "last_message_at = NOW(), updated_at = NOW() WHERE id = :sid"
        ),
        {"sid": session_id},
    )
    await db.commit()
    return msg_id


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "Sen KIRO2 YKS hazirlik platformunun AI egitim asistanisin. "
    "Ogrencilere TYT/AYT konularinda yardimci oluyorsun. "
    "Turkce yanitla. Kisa, net ve dogru bilgi ver. "
    "Matematiksel ifadeleri LaTeX formatinda yaz: "
    "satir ici icin $...$ , ayri satir icin $$...$$ kullan. "
    "Kod orneklerini ```dil ... ``` bloklarinda yaz."
)

SOCRATIC_SYSTEM_PROMPT = (
    "Sen KIRO2 YKS hazirlik platformunun AI egitim asistanisin. "
    "Sokratik ogretim yontemini kullaniyorsun.\n\n"
    "KURALLAR:\n"
    "1. Cevabi ASLA dogrudan verme.\n"
    "2. Once ogrencinin ne dusundugunu sor.\n"
    "3. Problemi kucuk adimlara bol ve her adimda yonlendirici soru sor.\n"
    "4. Ogrenci yanlis dusunuyorsa karsi ornek veya yonlendirici soru kullan.\n"
    "5. Ogrenci dogru adim attiginda takdir et.\n"
    "6. Kavram yanilgilarini tespit ettiginde nazikce duzelt.\n"
    "7. Turkce yanitla.\n"
    "8. Matematiksel ifadeleri LaTeX formatinda yaz: $...$ ve $$...$$ kullan."
    "\n\nORNEK:\n"
    "Ogrenci: '2x + 5 = 13 nasil cozulur?'\n"
    "Sen: 'Guzel bir soru! Once dusunelim: esitligin iki tarafindan "
    "ayni sayiyi cikarabilir miyiz? Hangi sayiyi cikarmaliyiz ve neden?'"
)

# U04 (12 Ağu 2026) — çıktı-tarafı zorlama sabitleri. Kanıt: canlı tetiklemede
# tek ısrar sonrası model TÜM yanıtı "C) 4" / "C" olarak üretti.
STRENGTHENED_REMINDER = (
    "\n\nÖNEMLİ UYARI: Az önce cevabı doğrudan söyledin. Bunu KESİNLİKLE YAPMA. "
    "Öğrenciye asla nihai cevabı veya şıkkı harf/sayı olarak verme — yalnızca "
    "yönlendirici bir soru sor."
)

SOCRATIC_FALLBACK_MESSAGE = (
    "Cevabı doğrudan söyleyemem, ama beraber bulalım: bu sorudaki ilk adımı "
    "birlikte düşünelim mi? Sence hangi işlemi yapmalıyız?"
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ChatMessageType(str, Enum):
    USER_MESSAGE = "user_message"
    AI_RESPONSE = "ai_response"
    SYSTEM = "system"
    ERROR = "error"


class ResponseMode(str, Enum):
    STANDARD = "standard"
    DETAILED = "detailed"
    SIMPLE = "simple"
    EXAM_MODE = "exam_mode"


class EnhancedChatResponse(BaseModel):
    message: str = ""
    message_type: ChatMessageType = ChatMessageType.AI_RESPONSE
    confidence_score: float = 0.85
    suggestions: list[str] = Field(default_factory=list)


class ChatMessageRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    subject: str = Field(default="")
    session_id: str | None = None
    response_mode: str | None = None
    teaching_mode: str = Field(default="direct")
    include_bionic: bool = False
    context_data: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Fallback responses (when no LLM available)
# ---------------------------------------------------------------------------
SUBJECT_HINTS: dict[str, str] = {
    "matematik": "Matematik sorunuzu aliyorum. Lutfen soruyu detayli yazin, adim adim cozelim.",
    "fizik": "Fizik sorunuzu aliyorum. Formul ve kavram aciklamalariyla yardimci olabilirim.",
    "kimya": "Kimya sorunuzu aliyorum. Element, baglar ve tepkimeler konusunda yardimci olabilirim.",
    "biyoloji": "Biyoloji sorunuzu aliyorum. Hucre, genetik ve ekoloji konularinda yardimci olabilirim.",
    "turkce": "Turkce sorunuzu aliyorum. Dil bilgisi ve paragraf sorularinda yardimci olabilirim.",
    "tarih": "Tarih sorunuzu aliyorum. Donem ve olaylari kronolojik olarak aciklayabilirim.",
    "geometri": "Geometri sorunuzu aliyorum. Sekiller, acilar ve alan hesaplamalarinda yardimci olabilirim.",
}

SUBJECT_CHAT_PROMPTS: dict[str, str] = {
    "matematik": (
        "MATEMATIK KONUSU:\n"
        "- Formulleri LaTeX ile yaz: $ax^2 + bx + c = 0$\n"
        "- Cozumu adim adim goster, her adimda ne yapildigini acikla.\n"
        "- Sayisal sonuclari kontrol et."
    ),
    "fizik": (
        "FIZIK KONUSU:\n"
        "- Formulleri LaTeX ile yaz ve birimlerini belirt.\n"
        "- Birim analizini goster (m/s, N, J vb.).\n"
        "- Gunluk hayattan orneklerle acikla."
    ),
    "kimya": (
        "KIMYA KONUSU:\n"
        "- Kimyasal formulleri dogru yaz.\n"
        "- Tepkime denklemlerini dengele.\n"
        "- Mol hesaplamalarini adim adim goster."
    ),
    "biyoloji": (
        "BIYOLOJI KONUSU:\n"
        "- Biyolojik surecleri adim adim anlat.\n"
        "- Terminolojiyi acikla.\n"
        "- Liste ile gorsellestirebilecek yapilar olustur."
    ),
    "turkce": (
        "TURKCE KONUSU:\n"
        "- Dil bilgisi kurallarini orneklerle acikla.\n"
        "- Paragraf sorularinda ana dusunce ve yardimci dusunceyi ayirt et.\n"
        "- Edebi sanatlari orneklerle goster."
    ),
    "tarih": (
        "TARIH KONUSU:\n"
        "- Olaylari kronolojik siralama ile anlat.\n"
        "- Neden-sonuc iliskilerini vurgula.\n"
        "- Donem karsilastirmalari yap."
    ),
    "geometri": (
        "GEOMETRI KONUSU:\n"
        "- Sekilleri sozel olarak tanimla.\n"
        "- Formulleri LaTeX ile yaz: $A = \\frac{1}{2} \\cdot a \\cdot h$\n"
        "- Ispatlari adim adim goster."
    ),
    "cografya": (
        "COGRAFYA KONUSU:\n"
        "- Konumlari ve bolgeleri tanimla.\n"
        "- Iklim, bitki ortusu ve ekonomik faaliyet iliskilerini acikla."
    ),
    "edebiyat": (
        "EDEBIYAT KONUSU:\n"
        "- Edebi donem ve akimlari kronolojik acikla.\n"
        "- Yazar ve eser iliskilerini vurgula.\n"
        "- Edebi tur ozelliklerini orneklerle anlat."
    ),
}


def _get_system_prompt(
    subject: str, teaching_mode: str = "direct", user_query: str = ""
) -> str:
    """Build system prompt with RAG curriculum grounding based on subject and teaching mode."""
    base = SOCRATIC_SYSTEM_PROMPT if teaching_mode == "socratic" else SYSTEM_PROMPT
    subject_addition = SUBJECT_CHAT_PROMPTS.get(normalize_tr(subject), "")
    if subject_addition:
        base += "\n\n" + subject_addition

    if user_query and subject:
        rag_data = socratic_rag_guardrail_service.get_curriculum_grounding(
            subject, user_query
        )
        base += "\n\n" + rag_data["rag_context_text"]

    return base


def _generate_fallback(message: str, subject: str) -> str:
    """Generate a subject-aware fallback response when no LLM is available."""
    subject_lower = normalize_tr(subject) if subject else ""

    for key, hint in SUBJECT_HINTS.items():
        if key in subject_lower or key in message.lower():
            return hint

    return (
        "Sorunuzu aldim. Su anda AI motoru baglantisi kuruluyor. "
        "Lutfen biraz sonra tekrar deneyin veya sorunuzu daha detayli yazin."
    )


# ---------------------------------------------------------------------------
# U04: Sokratik guardrail çıktı-tarafı zorlaması
# ---------------------------------------------------------------------------
async def enforce_socratic_output(
    response_text: str,
    teaching_mode: str,
    regenerate: Callable[[], Awaitable[str]],
) -> str:
    """Sokratik modda dogrudan-cevap sizintisini zorlayici sekilde engeller.

    teaching_mode != "socratic" ise dokunmadan doner (direct mod ogrencisi
    bilerek dogrudan cevap istiyor, bu bir ihlal degil).
    Sizinti varsa `regenerate()` ile BIR KEZ yeniden dener; retry sonucu da
    AYNI dedektorle yeniden kontrol edilir. O da sizarsa (veya bossa) sabit
    yonlendirme sablonuna duser -- sizinti HICBIR dalda client'a ulasmaz.
    """
    if teaching_mode != "socratic":
        return response_text

    eval_res = socratic_rag_guardrail_service.validate_socratic_compliance(
        response_text
    )
    if not eval_res["direct_answer_detected"]:
        return response_text

    logger.warning(
        "Sokratik sizinti tespit edildi, guclendirilmis prompt ile yeniden deneniyor"
    )
    retried_text = await regenerate()
    retried_eval = socratic_rag_guardrail_service.validate_socratic_compliance(
        retried_text
    )
    if retried_text and not retried_eval["direct_answer_detected"]:
        return retried_text

    logger.warning(
        "Sokratik sizinti yeniden deneme sonrasi da tespit edildi, sabit sablona dusuluyor"
    )
    return SOCRATIC_FALLBACK_MESSAGE


# ---------------------------------------------------------------------------
# LLM call with fallback chain and Guardrail validation
# ---------------------------------------------------------------------------
async def _call_llm(
    message: str, subject: str, teaching_mode: str = "direct"
) -> EnhancedChatResponse:
    """Try LLM backends in order: LiteLLM → Ollama → fallback, with Guardrail checks."""
    safety_check = socratic_rag_guardrail_service.inspect_input_safety(message)
    if not safety_check["is_safe"]:
        return EnhancedChatResponse(
            message=safety_check["reason"] or "Güvenlik Uyarısı: Girdi engellendi.",
            confidence_score=0.0,
            suggestions=["Lütfen müfredata uygun eğitim soruları sorun."],
        )

    system_prompt = _get_system_prompt(subject, teaching_mode, user_query=message)

    # --- Try 1: LiteLLM proxy ---
    if os.getenv("LLM_BACKEND") == "litellm":
        try:
            from core.llm_service import _get_llm_service

            client = _get_llm_service()
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ]
            response_text = await client.chat(messages=messages)
            if response_text:

                async def _regenerate_litellm() -> str:
                    retry_messages = [
                        {
                            "role": "system",
                            "content": system_prompt + STRENGTHENED_REMINDER,
                        },
                        {"role": "user", "content": message},
                    ]
                    return await client.chat(messages=retry_messages) or ""

                response_text = await enforce_socratic_output(
                    response_text, teaching_mode, _regenerate_litellm
                )
                eval_res = socratic_rag_guardrail_service.validate_socratic_compliance(
                    response_text
                )
                return EnhancedChatResponse(
                    message=response_text,
                    confidence_score=eval_res["socratic_score"],
                    suggestions=eval_res["suggestions"],
                )
        except Exception as e:
            logger.warning(f"LiteLLM failed: {e}")

    # --- Try 2: Ollama (localhost:11434) ---
    try:
        import httpx

        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message},
                    ],
                    "stream": False,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("message", {}).get("content", "")
                if content:

                    async def _regenerate_ollama() -> str:
                        retry_resp = await client.post(
                            f"{ollama_url}/api/chat",
                            json={
                                "model": model,
                                "messages": [
                                    {
                                        "role": "system",
                                        "content": system_prompt
                                        + STRENGTHENED_REMINDER,
                                    },
                                    {"role": "user", "content": message},
                                ],
                                "stream": False,
                            },
                        )
                        if retry_resp.status_code == 200:
                            retry_data = retry_resp.json()
                            return str(retry_data.get("message", {}).get("content", ""))
                        return ""

                    content = await enforce_socratic_output(
                        content, teaching_mode, _regenerate_ollama
                    )
                    eval_res = (
                        socratic_rag_guardrail_service.validate_socratic_compliance(
                            content
                        )
                    )
                    return EnhancedChatResponse(
                        message=content,
                        confidence_score=eval_res["socratic_score"],
                        suggestions=eval_res["suggestions"],
                    )
    except Exception as e:
        logger.debug(f"Ollama not available: {e}")

    # --- Fallback: smart placeholder ---
    fallback_text = _generate_fallback(message, subject)
    return EnhancedChatResponse(
        message=fallback_text,
        confidence_score=0.5,
        suggestions=["Konuyu belirtin", "Soruyu detaylandirin"],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/message")
@limiter.limit("10/minute")
async def send_message(
    request: Request,
    response: Response,
    payload: ChatMessageRequest,
    current_user: Any = _auth_dep,
    db: AsyncSession = _db_dep,
) -> dict[str, Any]:
    """Send a chat message and get AI response.

    GF24 fix: ``response: Response`` is required by slowapi's ``@limiter.limit``
    wrapper — without it the decorator tries to attach rate-limit headers to
    the dict return value and crashes 500 with
    ``parameter 'response' must be an instance of starlette.responses.Response``.
    The bug only surfaces when the upstream LLM responds fast enough that the
    request doesn't time out first (GF24 was previously a state-dependent skip).
    """
    await _verify_enhanced_chat_student_context(payload.student_id, current_user, db)

    llm_response = await _call_llm(
        payload.message, payload.subject, payload.teaching_mode
    )

    now = datetime.now(UTC).isoformat()
    resp_id = f"resp-{uuid4().hex[:8]}"

    # Persist to DB if available
    session_id = payload.session_id
    if db is not None and await _verify_chat_tables(db):
        try:
            user_id = (
                getattr(current_user, "id", "anonymous")
                if current_user
                else "anonymous"
            )
            session_id = await _get_or_create_session(
                db,
                str(user_id),
                payload.session_id,
                payload.subject,
            )
            await _save_message(db, session_id, "user", payload.message)
            await _save_message(
                db,
                session_id,
                "assistant",
                llm_response.message,
                model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
                confidence=llm_response.confidence_score,
            )
        except Exception as e:
            logger.warning(f"Chat DB persist failed: {e}")

    return {
        "success": True,
        "data": {
            "response_id": resp_id,
            "message": llm_response.message,
            "session_id": session_id,
        },
        "response": llm_response.message,
        "agent": "turkish_nlp",
        "timestamp": now,
        "session_id": session_id,
        "message_type": llm_response.message_type.value,
        "confidence_score": llm_response.confidence_score,
    }


@router.post("/socratic-dialogue")
@limiter.limit("10/minute")
async def socratic_dialogue(
    request: Request,
    response: Response,
    payload: ChatMessageRequest,
    current_user: Any = _auth_dep,
    db: AsyncSession = _db_dep,
) -> dict[str, Any]:
    """Sokratik diyalog ve pedagojik yönlendirme ucu."""
    await _verify_enhanced_chat_student_context(payload.student_id, current_user, db)

    payload.teaching_mode = "socratic"
    llm_response = await _call_llm(
        payload.message, payload.subject, teaching_mode="socratic"
    )

    socratic_eval = socratic_rag_guardrail_service.validate_socratic_compliance(
        llm_response.message
    )
    latex_eval = socratic_rag_guardrail_service.validate_latex_formatting(
        llm_response.message
    )

    now = datetime.now(UTC).isoformat()
    resp_id = f"soc-{uuid4().hex[:8]}"

    session_id = payload.session_id
    if db is not None and await _verify_chat_tables(db):
        try:
            user_id = (
                str(getattr(current_user, "id", "anonymous"))
                if current_user
                else "anonymous"
            )
            session_id = await _get_or_create_session(
                db,
                user_id,
                payload.session_id,
                payload.subject,
            )
            await _save_message(db, session_id, "user", payload.message)
            await _save_message(
                db,
                session_id,
                "assistant",
                llm_response.message,
                model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
                confidence=socratic_eval["socratic_score"],
            )
        except Exception as e:
            logger.warning(f"Socratic DB persist failed: {e}")

    return {
        "success": True,
        "data": {
            "response_id": resp_id,
            "message": llm_response.message,
            "session_id": session_id,
            "socratic_score": socratic_eval["socratic_score"],
            "direct_answer_detected": socratic_eval["direct_answer_detected"],
            "latex_formatting_valid": latex_eval["is_valid"],
            "suggestions": socratic_eval["suggestions"],
        },
        "response": llm_response.message,
        "agent": "socratic_tutor",
        "timestamp": now,
        "session_id": session_id,
        "confidence_score": socratic_eval["socratic_score"],
    }


# ---------------------------------------------------------------------------
# SSE Streaming endpoint
# ---------------------------------------------------------------------------
async def _stream_ollama(
    message: str,
    subject: str,
    teaching_mode: str = "direct",
    strengthen: bool = False,
) -> AsyncIterator[str]:
    """Stream Ollama response as SSE events.

    strengthen=True: U04 retry yolu -- guardrail sizintisi tespit edildikten
    sonra guclendirilmis hatirlatmayla YENIDEN uretim icin kullanilir.
    """
    import httpx

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    system_prompt = _get_system_prompt(subject, teaching_mode)
    if strengthen:
        system_prompt += STRENGTHENED_REMINDER

    try:
        async with (
            httpx.AsyncClient(timeout=120.0) as client,
            client.stream(
                "POST",
                f"{ollama_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message},
                    ],
                    "stream": True,
                },
            ) as resp,
        ):
            async for line in resp.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                if data.get("done"):
                    break
    except Exception as e:
        logger.warning(f"Ollama stream failed: {e}")
        fallback = _generate_fallback(message, subject)
        yield f"data: {json.dumps({'content': fallback}, ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"


async def _collect_stream_text(
    message: str, subject: str, teaching_mode: str, strengthen: bool = False
) -> str:
    """`_stream_ollama`'yi tuketip TAM metni dondurur; client'a hicbir sey gondermez."""
    accumulated = ""
    async for chunk in _stream_ollama(
        message, subject, teaching_mode, strengthen=strengthen
    ):
        if chunk.startswith("data: ") and "[DONE]" not in chunk:
            with contextlib.suppress(Exception):
                chunk_data = json.loads(chunk[6:].strip())
                accumulated += chunk_data.get("content", "")
    return accumulated


@router.post("/stream")
@limiter.limit("10/minute")
async def stream_message(
    request: Request,
    payload: ChatMessageRequest,
    current_user: Any = _auth_dep,
    db: AsyncSession = _db_dep,
) -> StreamingResponse:
    """Stream AI response as Server-Sent Events."""

    await _verify_enhanced_chat_student_context(payload.student_id, current_user, db)

    # Resolve session before streaming starts
    session_id = payload.session_id
    user_id = "anonymous"
    if db is not None and current_user is not None and await _verify_chat_tables(db):
        try:
            user_id = str(getattr(current_user, "id", "anonymous"))
            session_id = await _get_or_create_session(
                db,
                user_id,
                payload.session_id,
                payload.subject,
            )
            await _save_message(db, session_id, "user", payload.message)
        except Exception as e:
            logger.warning(f"Chat DB persist (stream-pre) failed: {e}")

    async def _stream_and_persist() -> AsyncIterator[str]:
        """Direct mod: gercek zamanli akis (degismedi).
        Socratic mod: biriktir -> guardrail kontrolu -> SONRA gonder (U04)."""
        if payload.teaching_mode != "socratic":
            accumulated = ""
            async for chunk in _stream_ollama(
                payload.message, payload.subject, payload.teaching_mode
            ):
                # Collect content for DB persistence
                if chunk.startswith("data: ") and "[DONE]" not in chunk:
                    with contextlib.suppress(Exception):
                        chunk_data = json.loads(chunk[6:].strip())
                        accumulated += chunk_data.get("content", "")
                # Inject session_id in first chunk
                yield chunk
            final_text = accumulated
        else:
            raw_text = await _collect_stream_text(
                payload.message, payload.subject, payload.teaching_mode
            )

            async def _regenerate() -> str:
                return await _collect_stream_text(
                    payload.message,
                    payload.subject,
                    payload.teaching_mode,
                    strengthen=True,
                )

            final_text = await enforce_socratic_output(
                raw_text, payload.teaching_mode, _regenerate
            )
            yield f"data: {json.dumps({'content': final_text}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        # Persist AI response after stream completes
        if db is not None and final_text and session_id:
            try:
                await _save_message(
                    db,
                    session_id,
                    "assistant",
                    final_text,
                    model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
                )
            except Exception as e:
                logger.warning(f"Chat DB persist (stream-post) failed: {e}")

    # Send session_id as first SSE event so frontend knows
    async def _with_session_header() -> AsyncIterator[str]:
        if session_id:
            yield f"data: {json.dumps({'session_id': session_id})}\n\n"
        async for chunk in _stream_and_persist():
            yield chunk

    return StreamingResponse(
        _with_session_header(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions")
async def list_sessions(
    current_user: Any = _auth_dep,
    db: AsyncSession = _db_dep,
    limit: int = Query(default=20, le=100),
) -> dict[str, Any]:
    """List user's chat sessions."""
    if db is None:
        return {"success": True, "sessions": []}

    user_id = (
        str(getattr(current_user, "id", "anonymous")) if current_user else "anonymous"
    )
    r = await db.execute(
        text(
            "SELECT id, title, subject_type, message_count, created_at, updated_at "
            "FROM chat_sessions WHERE user_id = :uid "
            "ORDER BY updated_at DESC LIMIT :lim"
        ),
        {"uid": user_id, "lim": limit},
    )
    sessions = [
        {
            "id": row[0],
            "title": row[1],
            "subject": row[2],
            "message_count": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
            "updated_at": row[5].isoformat() if row[5] else None,
        }
        for row in r.fetchall()
    ]
    return {"success": True, "sessions": sessions}


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    current_user: Any = _auth_dep,
    db: AsyncSession = _db_dep,
    limit: int = Query(default=100, le=500),
) -> dict[str, Any]:
    """Get messages for a specific chat session."""
    if db is None:
        return {"success": True, "messages": [], "session_id": session_id}

    # SECURITY: Verify session belongs to current user (IDOR prevention)
    user_id = str(getattr(current_user, "id", "")) if current_user else ""
    r = await db.execute(
        text(
            "SELECT cm.id, cm.role, cm.content, cm.model, cm.confidence_score, cm.created_at "
            "FROM chat_messages cm "
            "JOIN chat_sessions cs ON cm.session_id = cs.id "
            "WHERE cm.session_id = :sid AND cs.user_id = :uid "
            "ORDER BY cm.created_at ASC LIMIT :lim"
        ),
        {"sid": session_id, "uid": user_id, "lim": limit},
    )
    messages = [
        {
            "id": row[0],
            "role": "agent" if row[1] == "assistant" else row[1],
            "content": row[2],
            "agent": "turkish_nlp" if row[1] == "assistant" else None,
            "timestamp": row[5].isoformat() if row[5] else None,
        }
        for row in r.fetchall()
    ]
    return {"success": True, "messages": messages, "session_id": session_id}


@router.get("/history/{student_id}")
async def get_history(
    student_id: str,
    current_user: Any = _auth_dep,
    db: AsyncSession = _db_dep,
) -> dict[str, Any]:
    """Get chat history for a student (legacy endpoint)."""
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Bu kaynak için kimlik doğrulama gerekli",
        )
    if db is None:
        return {
            "success": True,
            "data": {"history": []},
            "student_id": student_id,
            "messages": [],
        }

    await verify_student_access(student_id, current_user, db)
    owner_uid = await get_learning_path_profile_user_id(student_id, db)

    r = await db.execute(
        text(
            "SELECT cm.id, cm.role, cm.content, cm.created_at "
            "FROM chat_messages cm "
            "JOIN chat_sessions cs ON cm.session_id = cs.id "
            "WHERE cs.user_id = :uid "
            "ORDER BY cm.created_at DESC LIMIT 50"
        ),
        {"uid": owner_uid},
    )
    history = [
        {
            "id": row[0],
            "role": row[1],
            "content": row[2],
            "timestamp": row[3].isoformat() if row[3] else None,
        }
        for row in r.fetchall()
    ]
    return {
        "success": True,
        "data": {"history": history},
        "student_id": student_id,
        "messages": history,
    }


# ---------------------------------------------------------------------------
# Attachment endpoint (image / PDF / URL)
# ---------------------------------------------------------------------------
_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
_PDF_TYPES = {"application/pdf"}
_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber."""
    try:
        import io

        import pdfplumber

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = []
            for i, page in enumerate(pdf.pages[:20]):  # max 20 pages
                text_content = page.extract_text() or ""
                if text_content.strip():
                    pages.append(f"[Sayfa {i + 1}]\n{text_content}")
            return "\n\n".join(pages) if pages else "PDF'den metin cikarilmadi."
    except ImportError:
        return "PDF isleme kutuphanesi (pdfplumber) yuklu degil."
    except Exception as e:
        logger.warning(f"PDF extraction failed: {e}")
        return f"PDF okuma hatasi: {e}"


# Bir URL'yi getirirken izin verilen azami yonlendirme sayisi (SSRF sertlestirme).
_URL_FETCH_MAX_REDIRECTS = 5


def _ssrf_url_guvenli(url: str) -> tuple[bool, str]:
    """URL'nin SSRF acisindan guvenli olup olmadigini dogrular.

    (guvenli, hata_mesaji) doner. Bu bekci TEK bir hop'u dener; cagiran
    taraf ilk URL'yi VE her yonlendirme hedefini ayri ayri buradan gecirir
    (bkz. _fetch_url_content). CodeQL py/full-ssrf (alert #114, CWE-918).

    Kapsanan bosluklar:
      - Sema: yalniz http/https (file://, gopher://, dict:// vb. reddedilir).
      - Hostname'in COZUMLENEN TUM IP'leri denetlenir (yalniz ilki degil) —
        cok-A-kayitli bir isim ile bir public + bir private IP karisimi
        engellenir.
      - private / loopback / link-local (169.254.169.254 = bulut metadata) /
        reserved / multicast / unspecified araliklarinin tumu engellenir.

    Bilinen kalinti (kabul edildi): getaddrinfo on-cozumlemesi ile httpx'in
    fiili baglanti cozumlemesi ayri oldugundan teorik bir DNS-rebinding /
    TOCTOU penceresi kalir. Sifirlamak icin cozulen IP'ye baglanip Host
    basligini elde tutmak gerekir (TLS SNI ile karmasik); pratikte pencere
    cok dar ve asil somurulen yol olan yonlendirme-ile-metadata bu bekciyle
    kapatildi.
    """
    import ipaddress
    import socket
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "Sadece http ve https URL'ler desteklenir."
    if not parsed.hostname:
        return False, "Gecersiz URL."

    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except (socket.gaierror, ValueError, UnicodeError):
        return False, "URL cozumlenemedi."

    for info in infos:
        try:
            addr = ipaddress.ip_address(info[4][0])
        except ValueError:
            return False, "URL cozumlenemedi."
        if (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
            or addr.is_unspecified
        ):
            return False, "Yerel/dahili ag adreslerine erisim engellenmistir."

    return True, ""


async def _fetch_url_content(url: str) -> str:  # noqa: PLR0911
    """Fetch and extract readable text from a URL (SSRF-safe).

    follow_redirects=False + manuel, her-hop dogrulanan yonlendirme takibi:
    httpx'in dogrulanmamis 3xx takibi bir public URL'den bulut metadata /
    dahili servise SSRF yolu aciyordu (alert #114). Artik ilk URL de her
    yonlendirme hedefi de _ssrf_url_guvenli'den gecirilir.
    """
    from urllib.parse import urljoin

    import httpx

    current = url
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
            for _hop in range(_URL_FETCH_MAX_REDIRECTS + 1):
                guvenli, mesaj = _ssrf_url_guvenli(current)
                if not guvenli:
                    return mesaj

                resp = await client.get(
                    current, headers={"User-Agent": "KIRO2-Bot/1.0"}
                )

                if resp.is_redirect:
                    location = resp.headers.get("location", "")
                    if not location:
                        return "Yonlendirme hedefi bulunamadi."
                    # Goreli Location'i mutlak URL'ye cevir, sonra tekrar dogrula.
                    current = urljoin(current, location)
                    continue

                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "")
                if "text/html" in content_type:
                    # Simple HTML text extraction
                    import re

                    html = resp.text
                    # Remove script/style tags
                    html = re.sub(
                        r"<(script|style)[^>]*>.*?</\1>",
                        "",
                        html,
                        flags=re.DOTALL | re.IGNORECASE,
                    )
                    # Remove HTML tags
                    text_content = re.sub(r"<[^>]+>", " ", html)
                    # Clean whitespace
                    text_content = re.sub(r"\s+", " ", text_content).strip()
                    return text_content[:5000]  # max 5000 chars
                if "application/json" in content_type:
                    return str(resp.text)[:5000]
                return str(resp.text)[:5000]

            return "Cok fazla yonlendirme (limit asildi)."
    except Exception as e:
        logger.warning(f"URL fetch failed: {e}")
        return f"URL icerigi alinamadi: {e}"


async def _analyze_image_with_vision(
    image_b64: str,
    message: str,
    subject: str,
    teaching_mode: str,
) -> str:
    """Send image to vision model for analysis/solving."""
    system_prompt = _get_system_prompt(subject, teaching_mode)
    prompt = (
        f"{system_prompt}\n\n"
        f"Ogrenci asagidaki gorseli gonderdi.\n"
        f"Ogrenci mesaji: {message or 'Bu gorseli analiz et ve acikla.'}\n\n"
        "Gorseldeki soruyu adim adim coz ve acikla. "
        "Matematiksel ifadeleri LaTeX formatinda yaz."
    )

    # Try LiteLLM vision
    try:
        from core.litellm.client import get_litellm_client

        client = get_litellm_client()
        result = await client.analyze_image(image_b64, prompt)
        if result:
            return str(result)
    except Exception as e:
        logger.debug(f"LiteLLM vision not available: {e}")

    # Try Ollama with vision model
    try:
        import httpx

        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        vision_model = os.getenv("OLLAMA_VISION_MODEL", "llava")
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": vision_model,
                    "messages": [
                        {"role": "user", "content": prompt, "images": [image_b64]},
                    ],
                    "stream": False,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("message", {}).get("content", "")
                if content:
                    return str(content)
    except Exception as e:
        logger.debug(f"Ollama vision not available: {e}")

    return (
        "Gorsel analizi su anda kullanilabilir degil. Lutfen soruyu metin olarak yazin."
    )


@router.post("/message-with-attachment")
@limiter.limit("10/minute")
async def message_with_attachment(  # noqa: PLR0912
    request: Request,
    current_user: Any = _auth_dep,
    db: AsyncSession = _db_dep,
    file: UploadFile | None = File(None),
    message: str = Form(default=""),
    subject: str = Form(default=""),
    session_id: str | None = Form(default=None),
    teaching_mode: str = Form(default="direct"),
    url: str | None = Form(default=None),
    student_id: str = Form(default=""),
) -> dict[str, Any]:
    """Send a chat message with an optional file or URL attachment."""

    if current_user is not None and not (student_id or "").strip():
        raise HTTPException(
            status_code=400,
            detail="student_id gerekli (kimliği doğrulanmış istekler için)",
        )
    await _verify_enhanced_chat_student_context(
        (student_id or "").strip(), current_user, db
    )

    # --- Determine attachment type and extract context ---
    attachment_context = ""
    attachment_type = ""

    if file and file.filename:
        # Chunked read — reject oversized files without loading fully into memory
        chunks: list[bytes] = []
        total_size = 0
        while True:
            chunk = await file.read(64 * 1024)  # 64 KB
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > _MAX_FILE_SIZE:
                return {"success": False, "error": "Dosya boyutu 10MB'yi asamaz."}
            chunks.append(chunk)
        file_bytes = b"".join(chunks)

        content_type = file.content_type or ""

        if content_type in _IMAGE_TYPES:
            # Image → vision model
            attachment_type = "image"
            image_b64 = base64.b64encode(file_bytes).decode("utf-8")
            attachment_context = await _analyze_image_with_vision(
                image_b64,
                message,
                subject,
                teaching_mode,
            )
        elif content_type in _PDF_TYPES or (
            file.filename and file.filename.lower().endswith(".pdf")
        ):
            # PDF → text extraction
            attachment_type = "pdf"
            pdf_text = await _extract_text_from_pdf(file_bytes)
            # Send extracted text to LLM
            augmented_message = (
                f"Ogrenci bir PDF dosyasi yukledi ({file.filename}).\n"
                f"PDF icerigi:\n---\n{pdf_text[:4000]}\n---\n\n"
                f"Ogrenci mesaji: {message or 'Bu icerigi acikla.'}"
            )
            response = await _call_llm(augmented_message, subject, teaching_mode)
            attachment_context = response.message
        else:
            # Other file types → try as text
            attachment_type = "text"
            try:
                text_content = file_bytes.decode("utf-8")[:4000]
            except UnicodeDecodeError:
                return {"success": False, "error": "Desteklenmeyen dosya formati."}
            augmented_message = (
                f"Ogrenci bir dosya yukledi ({file.filename}).\n"
                f"Dosya icerigi:\n---\n{text_content}\n---\n\n"
                f"Ogrenci mesaji: {message or 'Bu icerigi acikla.'}"
            )
            response = await _call_llm(augmented_message, subject, teaching_mode)
            attachment_context = response.message

    elif url:
        # URL → fetch and extract
        attachment_type = "url"
        url_text = await _fetch_url_content(url)
        augmented_message = (
            f"Ogrenci su URL'yi paylasti: {url}\n"
            f"Sayfa icerigi:\n---\n{url_text[:4000]}\n---\n\n"
            f"Ogrenci mesaji: {message or 'Bu icerigi acikla.'}"
        )
        response = await _call_llm(augmented_message, subject, teaching_mode)
        attachment_context = response.message

    else:
        return {"success": False, "error": "Dosya veya URL gerekli."}

    # --- Persist to DB ---
    resp_session_id = session_id
    if db is not None and await _verify_chat_tables(db):
        try:
            user_id = (
                str(getattr(current_user, "id", "anonymous"))
                if current_user
                else "anonymous"
            )
            resp_session_id = await _get_or_create_session(
                db,
                user_id,
                session_id,
                subject,
            )
            user_content = (
                f"[{attachment_type}] {message}" if message else f"[{attachment_type}]"
            )
            await _save_message(db, resp_session_id, "user", user_content)
            await _save_message(
                db,
                resp_session_id,
                "assistant",
                attachment_context,
                model="vision"
                if attachment_type == "image"
                else os.getenv("OLLAMA_MODEL", "qwen3:8b"),
            )
        except Exception as e:
            logger.warning(f"Chat DB persist (attachment) failed: {e}")

    return {
        "success": True,
        "data": {
            "message": attachment_context,
            "attachment_type": attachment_type,
            "session_id": resp_session_id,
        },
        "session_id": resp_session_id,
    }


# ---------------------------------------------------------------------------
# Bionic reading — FE beklentisi: POST /api/v1/enhanced-chat/bionic-reading
# (aynı cevap şekli: success + data.bionic_text)
# ---------------------------------------------------------------------------


@router.post("/bionic-reading")
async def bionic_reading_enhanced_chat(
    body: dict[str, Any] = Body(...),
    current_user: Any = _auth_dep,
) -> dict[str, Any]:
    text = (body or {}).get("text")
    if not text or not str(text).strip():
        raise HTTPException(status_code=400, detail="Metin gerekli")

    from core.bionic_reading_service import BionicReadingService
    from core.cache import cache_manager

    svc = BionicReadingService(cache_service=cache_manager)
    user_id = str(
        getattr(current_user, "id", "anonymous") if current_user else "anonymous"
    )
    res = await svc.process_text(
        text=str(text).strip(), user_id=user_id, use_cache=True
    )
    return dict(res) if isinstance(res, dict) else {}
