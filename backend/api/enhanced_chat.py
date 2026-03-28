"""Enhanced Chat API - AI sohbet sistemi."""

import base64
import json
import logging
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.turkish_nlp_utils import normalize_tr

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


# ---------------------------------------------------------------------------
# DB helpers (raw SQL — chat tables use VARCHAR ids, not UUID)
# ---------------------------------------------------------------------------
_chat_tables_verified = False


async def _verify_chat_tables(db: AsyncSession) -> bool:
    """Check chat tables exist on first call. Logs error once if missing."""
    global _chat_tables_verified
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
        try:
            await db.rollback()
        except Exception:
            pass
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
            "INSERT INTO chat_sessions (id, user_id, title, subject_type) "
            "VALUES (:id, :uid, :title, :subj)"
        ),
        {"id": new_id, "uid": user_id, "title": title, "subj": subject or "general"},
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


def _get_system_prompt(subject: str, teaching_mode: str = "direct") -> str:
    """Build system prompt based on subject and teaching mode."""
    base = SOCRATIC_SYSTEM_PROMPT if teaching_mode == "socratic" else SYSTEM_PROMPT
    subject_addition = SUBJECT_CHAT_PROMPTS.get(normalize_tr(subject), "")
    if subject_addition:
        base += "\n\n" + subject_addition
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
# LLM call with fallback chain
# ---------------------------------------------------------------------------
async def _call_llm(
    message: str, subject: str, teaching_mode: str = "direct"
) -> EnhancedChatResponse:
    """Try LLM backends in order: LiteLLM → Ollama → fallback."""
    system_prompt = _get_system_prompt(subject, teaching_mode)

    # --- Try 1: LiteLLM proxy ---
    if os.getenv("LLM_BACKEND") == "litellm":
        try:
            from core.llm_service import _get_llm_service

            client = _get_llm_service()
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ]
            response = await client.chat_completion(
                messages=messages,
                stream=False,
            )
            content = response.choices[0].message.content
            return EnhancedChatResponse(message=content, confidence_score=0.9)
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
                    return EnhancedChatResponse(
                        message=content,
                        confidence_score=0.85,
                    )
    except Exception as e:
        logger.debug(f"Ollama not available: {e}")

    # --- Fallback: smart placeholder ---
    return EnhancedChatResponse(
        message=_generate_fallback(message, subject),
        confidence_score=0.3,
        suggestions=["Konuyu belirtin", "Soruyu detaylandirin"],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/message")
async def send_message(
    request: ChatMessageRequest,
    current_user: Any = _auth_dep,
    db: AsyncSession = _db_dep,
) -> dict[str, Any]:
    """Send a chat message and get AI response."""
    response = await _call_llm(request.message, request.subject, request.teaching_mode)

    now = datetime.now(UTC).isoformat()
    resp_id = f"resp-{uuid4().hex[:8]}"

    # Persist to DB if available
    session_id = request.session_id
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
                request.session_id,
                request.subject,
            )
            await _save_message(db, session_id, "user", request.message)
            await _save_message(
                db,
                session_id,
                "assistant",
                response.message,
                model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
                confidence=response.confidence_score,
            )
        except Exception as e:
            logger.warning(f"Chat DB persist failed: {e}")

    return {
        "success": True,
        "data": {
            "response_id": resp_id,
            "message": response.message,
            "session_id": session_id,
        },
        "response": response.message,
        "agent": "turkish_nlp",
        "timestamp": now,
        "session_id": session_id,
        "message_type": response.message_type.value,
        "confidence_score": response.confidence_score,
    }


# ---------------------------------------------------------------------------
# SSE Streaming endpoint
# ---------------------------------------------------------------------------
async def _stream_ollama(
    message: str, subject: str, teaching_mode: str = "direct"
) -> AsyncIterator[str]:
    """Stream Ollama response as SSE events."""
    import httpx

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    system_prompt = _get_system_prompt(subject, teaching_mode)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
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
            ) as resp:
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


@router.post("/stream")
async def stream_message(
    request: ChatMessageRequest,
    current_user: Any = _auth_dep,
    db: AsyncSession = _db_dep,
) -> StreamingResponse:
    """Stream AI response as Server-Sent Events."""

    # Resolve session before streaming starts
    session_id = request.session_id
    user_id = "anonymous"
    if db is not None and current_user is not None and await _verify_chat_tables(db):
        try:
            user_id = str(getattr(current_user, "id", "anonymous"))
            session_id = await _get_or_create_session(
                db,
                user_id,
                request.session_id,
                request.subject,
            )
            await _save_message(db, session_id, "user", request.message)
        except Exception as e:
            logger.warning(f"Chat DB persist (stream-pre) failed: {e}")

    async def _stream_and_persist() -> AsyncIterator[str]:
        """Wrap streaming to collect full response and persist after."""
        accumulated = ""
        async for chunk in _stream_ollama(
            request.message, request.subject, request.teaching_mode
        ):
            # Collect content for DB persistence
            if chunk.startswith("data: ") and "[DONE]" not in chunk:
                try:
                    payload = json.loads(chunk[6:].strip())
                    accumulated += payload.get("content", "")
                except Exception:
                    pass
            # Inject session_id in first chunk
            yield chunk

        # Persist AI response after stream completes
        if db is not None and accumulated and session_id:
            try:
                await _save_message(
                    db,
                    session_id,
                    "assistant",
                    accumulated,
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
    user_id = (
        str(getattr(current_user, "id", student_id)) if current_user else student_id
    )
    if db is None:
        return {
            "success": True,
            "data": {"history": []},
            "student_id": student_id,
            "messages": [],
        }

    r = await db.execute(
        text(
            "SELECT cm.id, cm.role, cm.content, cm.created_at "
            "FROM chat_messages cm "
            "JOIN chat_sessions cs ON cm.session_id = cs.id "
            "WHERE cs.user_id = :uid "
            "ORDER BY cm.created_at DESC LIMIT 50"
        ),
        {"uid": user_id},
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


async def _fetch_url_content(url: str) -> str:
    """Fetch and extract readable text from a URL (SSRF-safe)."""
    import ipaddress
    import socket
    from urllib.parse import urlparse

    import httpx

    # Scheme + hostname validation
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "Sadece http ve https URL'ler desteklenir."
    if not parsed.hostname:
        return "Gecersiz URL."

    # Block private/loopback/link-local IPs (SSRF prevention)
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
        ip = infos[0][4][0]
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback or addr.is_link_local:
            return "Yerel ag adreslerine erisim engellenmistir."
    except (socket.gaierror, ValueError):
        return "URL cozumlenemedi."

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "KIRO2-Bot/1.0"})
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
                return resp.text[:5000]
            return resp.text[:5000]
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
            return result
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
                    return content
    except Exception as e:
        logger.debug(f"Ollama vision not available: {e}")

    return (
        "Gorsel analizi su anda kullanilabilir degil. Lutfen soruyu metin olarak yazin."
    )


@router.post("/message-with-attachment")
async def message_with_attachment(
    current_user: Any = _auth_dep,
    db: AsyncSession = _db_dep,
    file: UploadFile | None = File(None),
    message: str = Form(default=""),
    subject: str = Form(default=""),
    session_id: str | None = Form(default=None),
    teaching_mode: str = Form(default="direct"),
    url: str | None = Form(default=None),
) -> dict[str, Any]:
    """Send a chat message with an optional file or URL attachment."""

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
