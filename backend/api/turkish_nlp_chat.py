"""
Türkçe NLP Chat API Endpoints
Requirements: 2.1, 2.2, 2.3, 2.5, 2.6
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from core.dependencies import AuthenticatedUser, get_current_user

try:
    from core.turkish_nlp_chat_system import turkish_nlp_chat_system
except (ImportError, TypeError):
    turkish_nlp_chat_system = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/turkish-nlp-chat", tags=["Turkish NLP Chat"])


def _require_nlp_system():
    """NLP sistemi None ise 503 döndür."""
    if turkish_nlp_chat_system is None:
        raise HTTPException(
            status_code=503,
            detail="Türkçe NLP Chat sistemi şu an kullanılamıyor (import başarısız).",
        )


async def _ensure_initialized():
    """Sistem mevcut ama henüz başlatılmamışsa başlat."""
    _require_nlp_system()
    if not hasattr(turkish_nlp_chat_system, "nlp_service"):
        await turkish_nlp_chat_system.initialize()


# Request/Response Models
class ChatMessageRequest(BaseModel):
    """Chat mesajı isteği"""

    student_id: str = Field(..., description="Öğrenci ID'si")
    message: str = Field(
        ..., min_length=1, max_length=1000, description="Öğrenci mesajı"
    )
    session_id: str | None = Field(None, description="Oturum ID'si")
    subject: str = Field("genel", description="Konu alanı")
    context_data: dict[str, Any] | None = Field(None, description="Ek bağlam verisi")


class ChatMessageResponse(BaseModel):
    """Chat mesajı yanıtı"""

    success: bool
    message: str
    response_id: str
    agent: str = "turkish_nlp"
    timestamp: str
    data: dict[str, Any] | None = None


class ConversationHistoryRequest(BaseModel):
    """Konuşma geçmişi isteği"""

    student_id: str = Field(..., description="Öğrenci ID'si")
    session_id: str | None = Field(None, description="Oturum ID'si")
    limit: int = Field(20, ge=1, le=100, description="Maksimum mesaj sayısı")


class ConversationHistoryResponse(BaseModel):
    """Konuşma geçmişi yanıtı"""

    success: bool
    data: dict[str, Any]
    message: str


class BionicReadingRequest(BaseModel):
    """Bionic Reading isteği"""

    text: str = Field(
        ..., min_length=1, max_length=2000, description="Dönüştürülecek metin"
    )


class BionicReadingResponse(BaseModel):
    """Bionic Reading yanıtı"""

    success: bool
    data: dict[str, str]
    message: str


class ContextManagementRequest(BaseModel):
    """Bağlam yönetimi isteği"""

    student_id: str = Field(..., description="Öğrenci ID'si")
    session_id: str | None = Field(None, description="Oturum ID'si")
    action: str = Field(..., description="Eylem: clear, get_stats")


@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Türkçe NLP Chat sistemine mesaj gönder

    Bu endpoint:
    - Öğrenci mesajını analiz eder
    - Bağlamsal yanıt üretir
    - Eğitim terminolojisi kullanır
    - Adım adım çözümler sunar
    """
    try:
        logger.info(
            f"Chat mesajı alındı - Öğrenci: {request.student_id}, Mesaj uzunluğu: {len(request.message)}"
        )

        # Chat sisteminin başlatıldığından emin ol
        await _ensure_initialized()

        # Mesajı işle
        response = await turkish_nlp_chat_system.process_message(
            student_id=request.student_id,
            message=request.message,
            session_id=request.session_id,
            subject=request.subject,
            context_data=request.context_data,
        )

        # Response ID oluştur
        response_id = f"resp_{datetime.now().timestamp()}_{request.student_id}"

        # Yanıt verilerini hazırla
        response_data = {
            "response_text": response.response_text,
            "explanation_type": response.explanation_type,
            "difficulty_level": response.difficulty_level,
            "related_concepts": response.related_concepts,
            "follow_up_questions": response.follow_up_questions,
            "motivational_elements": response.motivational_elements,
            "confidence_score": response.confidence_score,
        }

        # Bionic Reading varsa ekle
        if response.bionic_reading_text:
            response_data["bionic_reading_text"] = response.bionic_reading_text

        # Background task: İstatistikleri güncelle
        background_tasks.add_task(
            _update_chat_statistics,
            request.student_id,
            request.subject,
            response.explanation_type,
        )

        return ChatMessageResponse(
            success=True,
            message=response.response_text,
            response_id=response_id,
            agent="turkish_nlp",
            timestamp=datetime.now().isoformat(),
            data=response_data,
        )

    except HTTPException:
        # Optional-dep 503 from _require_nlp_system / _ensure_initialized must
        # propagate as-is; do not re-wrap as 500 (GF22/GF56/GF57 pattern).
        raise
    except Exception as e:
        logger.error(f"Chat mesajı işleme hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_id: str | None = None,
    limit: int = 20,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Öğrencinin konuşma geçmişini al

    Bu endpoint:
    - Belirli oturumdaki mesajları getirir
    - Bağlam bilgilerini içerir
    - Sayfalama desteği sunar
    """
    try:
        student_id = str(current_user.id)
        logger.info(
            f"Konuşma geçmişi istendi - Öğrenci: {student_id}, Oturum: {session_id}"
        )

        # Konuşma geçmişini al
        history = await turkish_nlp_chat_system.get_conversation_history(
            student_id=student_id, session_id=session_id
        )

        # Limit uygula
        limited_history = history[-limit:] if len(history) > limit else history

        # Yanıt verilerini hazırla
        response_data = {
            "history": limited_history,
            "total_messages": len(history),
            "returned_messages": len(limited_history),
            "student_id": student_id,
            "session_id": session_id,
        }

        return ConversationHistoryResponse(
            success=True,
            data=response_data,
            message=f"{len(limited_history)} mesaj getirildi",
        )

    except Exception as e:
        logger.error(f"Konuşma geçmişi alma hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/bionic-reading", response_model=BionicReadingResponse)
async def apply_bionic_reading(
    request: BionicReadingRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Metne Türkçe Bionic Reading uygula

    Bu endpoint:
    - Türkçe metni Bionic Reading formatına çevirir
    - Kök-ek ayrımını dikkate alır
    - Disleksi dostu format sunar
    """
    try:
        logger.info(f"Bionic Reading isteği - Metin uzunluğu: {len(request.text)}")

        # Chat sisteminin başlatıldığından emin ol
        await _ensure_initialized()

        # Bionic Reading uygula
        bionic_text = await turkish_nlp_chat_system._apply_bionic_reading(request.text)

        response_data = {
            "original_text": request.text,
            "bionic_text": bionic_text,
            "character_count": len(request.text),
            "word_count": len(request.text.split()),
        }

        return BionicReadingResponse(
            success=True,
            data=response_data,
            message="Bionic Reading başarıyla uygulandı",
        )

    except Exception as e:
        logger.error(f"Bionic Reading hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/context/manage")
async def manage_conversation_context(
    request: ContextManagementRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Konuşma bağlamını yönet

    Bu endpoint:
    - Bağlamı temizleyebilir
    - Bağlam istatistiklerini getirebilir
    - Bağlam durumunu kontrol edebilir
    """
    try:
        logger.info(
            f"Bağlam yönetimi - Öğrenci: {request.student_id}, Eylem: {request.action}"
        )

        if request.action == "clear":
            # Bağlamı temizle
            success = await turkish_nlp_chat_system.clear_conversation_context(
                student_id=request.student_id, session_id=request.session_id
            )

            return {
                "success": success,
                "message": "Bağlam temizlendi" if success else "Bağlam bulunamadı",
                "data": {
                    "action": "clear",
                    "student_id": request.student_id,
                    "session_id": request.session_id,
                },
            }

        if request.action == "get_stats":
            # İstatistikleri al
            stats = turkish_nlp_chat_system.get_performance_stats()

            return {
                "success": True,
                "message": "İstatistikler getirildi",
                "data": {"action": "get_stats", "statistics": stats},
            }

        raise HTTPException(status_code=400, detail=f"Geçersiz eylem: {request.action}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bağlam yönetimi hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/health")
async def health_check():
    """
    Türkçe NLP Chat sisteminin sağlık kontrolü
    """
    try:
        if turkish_nlp_chat_system is None:
            return {
                "success": False,
                "message": "NLP sistemi devre dışı (import başarısız)",
                "data": {
                    "system_status": "unavailable",
                    "timestamp": datetime.now().isoformat(),
                },
            }
        # Sistem durumunu kontrol et
        stats = turkish_nlp_chat_system.get_performance_stats()

        # NLP servislerinin durumunu kontrol et
        nlp_status = hasattr(turkish_nlp_chat_system, "nlp_service")
        berturk_status = hasattr(turkish_nlp_chat_system, "berturk_service")

        return {
            "success": True,
            "message": "Türkçe NLP Chat sistemi çalışıyor",
            "data": {
                "system_status": "healthy",
                "nlp_service_loaded": nlp_status,
                "berturk_service_loaded": berturk_status,
                "active_contexts": stats.get("active_contexts", 0),
                "total_conversations": stats.get("total_conversations", 0),
                "successful_responses": stats.get("successful_responses", 0),
                "timestamp": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"Sağlık kontrolü hatası: {e}")
        return {
            "success": False,
            "message": f"Sistem hatası: {e!s}",
            "data": {
                "system_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        }


@router.post("/step-by-step-solution")
async def generate_step_by_step_solution(
    request: ChatMessageRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Adım adım çözüm üret

    Bu endpoint özellikle adım adım çözüm talepleri için optimize edilmiştir
    """
    try:
        logger.info(f"Adım adım çözüm isteği - Öğrenci: {request.student_id}")

        # Chat sisteminin başlatıldığından emin ol
        await _ensure_initialized()

        # Bağlam verilerini güncelle - adım adım çözüm talebi olduğunu belirt
        context_data = request.context_data or {}
        context_data["force_step_by_step"] = True

        # Mesajı işle
        response = await turkish_nlp_chat_system.process_message(
            student_id=request.student_id,
            message=request.message,
            session_id=request.session_id,
            subject=request.subject,
            context_data=context_data,
        )

        # Response ID oluştur
        response_id = f"step_resp_{datetime.now().timestamp()}_{request.student_id}"

        return {
            "success": True,
            "message": response.response_text,
            "response_id": response_id,
            "agent": "turkish_nlp_step_solver",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "response_text": response.response_text,
                "explanation_type": response.explanation_type,
                "difficulty_level": response.difficulty_level,
                "related_concepts": response.related_concepts,
                "follow_up_questions": response.follow_up_questions,
                "confidence_score": response.confidence_score,
                "bionic_reading_text": response.bionic_reading_text,
            },
        }

    except Exception as e:
        logger.error(f"Adım adım çözüm hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Background Tasks
async def _update_chat_statistics(student_id: str, subject: str, explanation_type: str):
    """Chat istatistiklerini güncelle (background task)"""
    try:
        # Burada veritabanına istatistik kaydetme işlemi yapılabilir
        logger.info(
            f"İstatistik güncellendi - Öğrenci: {student_id}, Konu: {subject}, Tür: {explanation_type}"
        )
    except Exception as e:
        logger.error(f"İstatistik güncelleme hatası: {e}")


# Startup event
@router.on_event("startup")
async def startup_event():
    """Router başlatma eventi"""
    # FIX 2026-04-02: turkish_nlp_chat_system None ise (import basarisiz)
    # None.initialize() -> AttributeError log spam'i durdur.
    if turkish_nlp_chat_system is None:
        logger.warning(
            "Türkçe NLP Chat API: core.turkish_nlp_chat_system import edilemedi, devre dışı."
        )
        return
    try:
        logger.info("Türkçe NLP Chat API başlatılıyor...")
        await turkish_nlp_chat_system.initialize()
        logger.info("Türkçe NLP Chat API başarıyla başlatıldı")
    except Exception as e:
        logger.error(f"Türkçe NLP Chat API başlatma hatası: {e}")


# Shutdown event
@router.on_event("shutdown")
async def shutdown_event():
    """Router kapatma eventi"""
    # FIX 2026-04-02: None.close() -> AttributeError log spam'i durdur.
    if turkish_nlp_chat_system is None:
        return
    try:
        logger.info("Türkçe NLP Chat API kapatılıyor...")
        await turkish_nlp_chat_system.close()
        logger.info("Türkçe NLP Chat API başarıyla kapatıldı")
    except Exception as e:
        logger.error(f"Türkçe NLP Chat API kapatma hatası: {e}")
