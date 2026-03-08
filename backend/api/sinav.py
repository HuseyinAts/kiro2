"""
ÖSYM Uyumlu Sınav Sistemi API Endpoint'leri
Türkiye Üniversite Sınavları Hazırlık Platformu

Bu modül ÖSYM formatında TYT/AYT/YDT sınavları için API endpoint'lerini sağlar:
- Sınav oturumu yönetimi
- Gerçek zamanlı sınav takibi
- Performans analizi ve raporlama
- Otomatik kaydetme ve oturum yönetimi
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

from core.dependencies import get_current_user, AuthenticatedUser
from core.osym_exam_engine import ExamStatus, osym_exam_engine
from core.structured_logger import get_logger
from models.database import ExamType

router = APIRouter(prefix="/api/v1/osym-exam", tags=["ÖSYM Sınav Sistemi"])
security = HTTPBearer()
logger = get_logger("osym_exam_api")


# get_current_user function moved to core.dependencies - imported above


# Pydantic Models
class CreateExamRequest(BaseModel):
    """Sınav oluşturma isteği"""

    exam_type: ExamType = Field(..., description="Sınav türü (TYT/AYT/YDT)")
    custom_config: Optional[Dict[str, Any]] = Field(
        None, description="Özel sınav konfigürasyonları"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "exam_type": "TYT",
                "custom_config": {
                    "duration_minutes": 165,
                    "subject_distribution": {
                        "TURKCE": 40,
                        "MATEMATIK": 40,
                        "FEN": 20,
                        "SOSYAL": 20,
                    },
                },
            }
        }
    }


class SaveAnswerRequest(BaseModel):
    """Cevap kaydetme isteği"""

    question_id: str = Field(..., description="Soru ID")
    selected_answer: Optional[str] = Field(
        None, description="Seçilen cevap (A, B, C, D, E)"
    )
    response_time: Optional[float] = Field(
        None, description="Cevaplama süresi (saniye)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "question_id": "550e8400-e29b-41d4-a716-446655440000",
                "selected_answer": "A",
                "response_time": 45.5,
            }
        }
    }


class FlagQuestionRequest(BaseModel):
    """Soru işaretleme isteği"""

    question_id: str = Field(..., description="Soru ID")
    flagged: bool = Field(..., description="İşaretli durumu")

    model_config = {
        "json_schema_extra": {
            "example": {
                "question_id": "550e8400-e29b-41d4-a716-446655440000",
                "flagged": True,
            }
        }
    }


class NavigateQuestionRequest(BaseModel):
    """Soru navigasyon isteği"""

    question_index: int = Field(..., description="Hedef soru indeksi (0-based)", ge=0)

    model_config = {
        "json_schema_extra": {"example": {"question_index": 15}}
    }


class ExamSessionResponse(BaseModel):
    """Sınav oturum yanıtı"""

    session_id: str
    student_id: str
    exam_type: str
    status: str
    total_questions: int
    duration_minutes: int
    current_question_index: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "student_id": "student123",
                "exam_type": "TYT",
                "status": "in_progress",
                "total_questions": 120,
                "duration_minutes": 165,
                "current_question_index": 15,
                "started_at": "2024-01-15T10:00:00Z",
                "completed_at": None,
            }
        }
    }


class QuestionResponse(BaseModel):
    """Soru yanıtı"""

    id: str
    question_text: str
    question_image_url: Optional[str]
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    option_e: Optional[str]
    subject_area: str
    topic: str
    difficulty: str
    question_order: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "question_text": "Aşağıdakilerden hangisi...",
                "question_image_url": None,
                "option_a": "Seçenek A",
                "option_b": "Seçenek B",
                "option_c": "Seçenek C",
                "option_d": "Seçenek D",
                "option_e": None,
                "subject_area": "MATEMATIK",
                "topic": "Fonksiyonlar",
                "difficulty": "MEDIUM",
                "question_order": 16,
            }
        }
    }


class PerformanceResponse(BaseModel):
    """Performans yanıtı"""

    total_questions: int
    answered_questions: int
    correct_answers: int
    wrong_answers: int
    empty_answers: int
    net_score: float
    raw_score: float
    percentile: Optional[float]
    estimated_ability: float
    confidence_level: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_questions": 120,
                "answered_questions": 115,
                "correct_answers": 85,
                "wrong_answers": 30,
                "empty_answers": 5,
                "net_score": 77.5,
                "raw_score": 70.8,
                "percentile": 75.5,
                "estimated_ability": 1.2,
                "confidence_level": 0.95,
            }
        }
    }


class SubjectPerformanceResponse(BaseModel):
    """Konu performans yanıtı"""

    subject: str
    total_questions: int
    correct_answers: int
    wrong_answers: int
    empty_answers: int
    success_rate: float
    average_response_time: float
    difficulty_level: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "subject": "MATEMATIK",
                "total_questions": 40,
                "correct_answers": 28,
                "wrong_answers": 10,
                "empty_answers": 2,
                "success_rate": 70.0,
                "average_response_time": 65.5,
                "difficulty_level": 0.8,
            }
        }
    }


@router.get(
    "/my-exams", response_model=List[ExamSessionResponse], summary="Benim Sınavlarım"
)
async def get_my_exams(
    current_user: AuthenticatedUser = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
) -> List[ExamSessionResponse]:
    """
    Kullanıcının tüm sınavlarını listele

    - Sayfalama desteği
    - Sınav durumu filtreleme
    - Tarih sıralama
    """
    try:
        user_sessions = []

        for session_data in osym_exam_engine.active_sessions.values():
            if session_data.student_id == current_user.id:
                user_sessions.append(
                    ExamSessionResponse(
                        session_id=session_data.session_id,
                        student_id=session_data.student_id,
                        exam_type=session_data.exam_config.exam_type.value,
                        status=session_data.status.value,
                        total_questions=session_data.exam_config.total_questions,
                        duration_minutes=session_data.exam_config.duration_minutes,
                        current_question_index=session_data.current_question_index,
                        started_at=session_data.started_at,
                        completed_at=session_data.completed_at,
                    )
                )

        start_index = offset
        end_index = offset + limit
        return user_sessions[start_index:end_index]

    except Exception as e:
        logger.error(
            f"Kullanıcı sınavları getirme hatası: {e}",
            extra_data={"student_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sınavlar getirilirken beklenmeyen bir hata oluştu",
        )


@router.get("/exam-configs", summary="Sınav Konfigürasyonları")
async def get_exam_configs(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    ÖSYM sınav konfigürasyonlarını getir

    - TYT/AYT/YDT format bilgileri
    - Soru sayıları ve süre bilgileri
    - Konu dağılımları
    """
    try:
        configs = {}

        for exam_type, config in osym_exam_engine.exam_configs.items():
            configs[exam_type.value] = {
                "exam_type": config.exam_type.value,
                "total_questions": config.total_questions,
                "duration_minutes": config.duration_minutes,
                "subject_distribution": config.subject_distribution,
                "auto_save_interval": config.auto_save_interval,
                "warning_time_minutes": config.warning_time_minutes,
            }

        return {
            "success": True,
            "exam_configs": configs,
            "message": "ÖSYM sınav konfigürasyonları",
        }

    except Exception as e:
        logger.error(f"Sınav konfigürasyonları getirme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sınav konfigürasyonları getirilirken beklenmeyen bir hata oluştu",
        )


@router.post(
    "/create", response_model=ExamSessionResponse, summary="ÖSYM Sınavı Oluştur"
)
async def create_exam(
    request: CreateExamRequest, current_user: AuthenticatedUser = Depends(get_current_user)
) -> ExamSessionResponse:
    """
    Yeni ÖSYM formatında sınav oturumu oluştur

    - **exam_type**: TYT, AYT veya YDT
    - **custom_config**: Özel sınav konfigürasyonları (opsiyonel)

    ÖSYM Formatları:
    - **TYT**: 120 soru, 165 dakika (Türkçe: 40, Matematik: 40, Fen: 20, Sosyal: 20)
    - **AYT**: 160 soru, 210 dakika (Matematik: 40, Fizik: 14, Kimya: 13, Biyoloji: 13, vb.)
    - **YDT**: 80 soru, 180 dakika (İngilizce: 80)
    """
    try:
        session_id = await osym_exam_engine.create_exam_session(
            student_id=current_user.id,
            exam_type=request.exam_type,
            custom_config=request.custom_config,
        )

        session_data = await osym_exam_engine.get_session_data(session_id)

        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Sınav oturumu oluşturulamadı",
            )

        logger.info(
            "ÖSYM sınavı oluşturuldu",
            extra_data={
                "session_id": session_id,
                "student_id": current_user.id,
                "exam_type": request.exam_type.value,
            },
        )

        return ExamSessionResponse(
            session_id=session_data.session_id,
            student_id=session_data.student_id,
            exam_type=session_data.exam_config.exam_type.value,
            status=session_data.status.value,
            total_questions=session_data.exam_config.total_questions,
            duration_minutes=session_data.exam_config.duration_minutes,
            current_question_index=session_data.current_question_index,
            started_at=session_data.started_at,
            completed_at=session_data.completed_at,
        )

    except ValueError as e:
        logger.error(
            f"Sınav oluşturma hatası: {e}",
            extra_data={
                "student_id": current_user.id,
                "exam_type": request.exam_type.value,
            },
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            f"Beklenmeyen sınav oluşturma hatası: {e}",
            extra_data={
                "student_id": current_user.id,
                "exam_type": request.exam_type.value,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sınav oluşturulurken beklenmeyen bir hata oluştu",
        )


@router.post(
    "/{session_id}/start",
    response_model=ExamSessionResponse,
    summary="ÖSYM Sınavını Başlat",
)
async def start_exam(
    session_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> ExamSessionResponse:
    """
    ÖSYM sınavını başlat ve zaman sayacını çalıştır

    - Otomatik kaydetme başlatılır (30 saniye aralıklarla)
    - Sınav süresi sonunda otomatik tamamlanır
    - Gerçek zamanlı WebSocket güncellemeleri başlar
    """
    try:
        # Oturum kontrolü
        session_data = await osym_exam_engine.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sınav oturumu bulunamadı"
            )

        # Kullanıcı kontrolü
        if str(session_data.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu sınava erişim yetkiniz yok",
            )

        # Sınavı başlat
        updated_session = await osym_exam_engine.start_exam(session_id)

        logger.info(
            "ÖSYM sınavı başlatıldı",
            extra_data={
                "session_id": session_id,
                "student_id": current_user.id,
                "exam_type": updated_session.exam_config.exam_type.value,
            },
        )

        return ExamSessionResponse(
            session_id=updated_session.session_id,
            student_id=updated_session.student_id,
            exam_type=updated_session.exam_config.exam_type.value,
            status=updated_session.status.value,
            total_questions=updated_session.exam_config.total_questions,
            duration_minutes=updated_session.exam_config.duration_minutes,
            current_question_index=updated_session.current_question_index,
            started_at=updated_session.started_at,
            completed_at=updated_session.completed_at,
        )

    except ValueError as e:
        logger.error(
            f"Sınav başlatma hatası: {e}",
            extra_data={
                "session_id": session_id,
                "student_id": current_user.id,
            },
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            f"Beklenmeyen sınav başlatma hatası: {e}",
            extra_data={
                "session_id": session_id,
                "student_id": current_user.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sınav başlatılırken beklenmeyen bir hata oluştu",
        )


@router.get(
    "/{session_id}/current-question",
    response_model=QuestionResponse,
    summary="Mevcut Soruyu Getir",
)
async def get_current_question(
    session_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> QuestionResponse:
    """
    Sınavdaki mevcut soruyu getir

    - Soru metni ve seçenekleri
    - Konu ve zorluk bilgileri
    - Soru sırası bilgisi
    """
    try:
        # Oturum kontrolü
        session_data = await osym_exam_engine.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sınav oturumu bulunamadı"
            )

        # Kullanıcı kontrolü
        if str(session_data.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu sınava erişim yetkiniz yok",
            )

        # Mevcut soruyu getir
        question = await osym_exam_engine.get_current_question(session_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mevcut soru bulunamadı veya sınav tamamlandı",
            )

        return QuestionResponse(
            id=question.id,
            question_text=question.question_text,
            question_image_url=question.question_image_url,
            option_a=question.option_a,
            option_b=question.option_b,
            option_c=question.option_c,
            option_d=question.option_d,
            option_e=question.option_e,
            subject_area=question.subject_area,
            topic=question.subject_area,
            difficulty=question.difficulty_level.value if question.difficulty_level else "medium",
            question_order=session_data.current_question_index + 1,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Mevcut soru getirme hatası: {e}",
            extra_data={
                "session_id": session_id,
                "student_id": current_user.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Soru getirilirken beklenmeyen bir hata oluştu",
        )


@router.post("/{session_id}/save-answer", summary="Cevap Kaydet")
async def save_answer(
    session_id: str,
    request: SaveAnswerRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Soru cevabını kaydet (otomatik kaydetme ile)

    - Cevap anında veritabanına kaydedilir
    - Cevaplama süresi takip edilir
    - WebSocket ile gerçek zamanlı güncelleme gönderilir
    """
    try:
        # Oturum kontrolü
        session_data = await osym_exam_engine.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sınav oturumu bulunamadı"
            )

        # Kullanıcı kontrolü
        if str(session_data.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu sınava erişim yetkiniz yok",
            )

        # Cevabı kaydet
        success = await osym_exam_engine.save_answer(
            session_id=session_id,
            question_id=request.question_id,
            selected_answer=request.selected_answer,
            response_time=request.response_time,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cevap kaydedilemedi"
            )

        logger.debug(
            "Cevap kaydedildi",
            extra_data={
                "session_id": session_id,
                "question_id": request.question_id,
                "answer": request.selected_answer,
            },
        )

        return {
            "success": True,
            "message": "Cevap başarıyla kaydedildi",
            "auto_saved": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Cevap kaydetme hatası: {e}",
            extra_data={"session_id": session_id, "question_id": request.question_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cevap kaydedilirken beklenmeyen bir hata oluştu",
        )


@router.post(
    "/{session_id}/navigate", response_model=QuestionResponse, summary="Soruya Git"
)
async def navigate_to_question(
    session_id: str,
    request: NavigateQuestionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> QuestionResponse:
    """
    Belirli bir soruya git (soru navigasyonu)

    - İleri/geri navigasyon
    - Direkt soru numarasına atlama
    - Soru haritası desteği
    """
    try:
        # Oturum kontrolü
        session_data = await osym_exam_engine.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sınav oturumu bulunamadı"
            )

        # Kullanıcı kontrolü
        if str(session_data.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu sınava erişim yetkiniz yok",
            )

        # Soruya git
        question = await osym_exam_engine.navigate_to_question(
            session_id, request.question_index
        )

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hedef soru bulunamadı veya geçersiz soru indeksi",
            )

        return QuestionResponse(
            id=question.id,
            question_text=question.question_text,
            question_image_url=question.question_image_url,
            option_a=question.option_a,
            option_b=question.option_b,
            option_c=question.option_c,
            option_d=question.option_d,
            option_e=question.option_e,
            subject_area=question.subject_area,
            topic=question.subject_area,
            difficulty=question.difficulty_level.value if question.difficulty_level else "medium",
            question_order=request.question_index + 1,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Soru navigasyon hatası: {e}",
            extra_data={
                "session_id": session_id,
                "question_index": request.question_index,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Soru navigasyonunda beklenmeyen bir hata oluştu",
        )


@router.post("/{session_id}/flag-question", summary="Soru İşaretleme")
async def flag_question(
    session_id: str,
    request: FlagQuestionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Soruyu işaretle veya işareti kaldır

    - Daha sonra dönülecek sorular için işaretleme
    - İşaretli soruların listesi tutulur
    - Sınav sonunda işaretli sorular gösterilir
    """
    try:
        # Oturum kontrolü
        session_data = await osym_exam_engine.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sınav oturumu bulunamadı"
            )

        # Kullanıcı kontrolü
        if str(session_data.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu sınava erişim yetkiniz yok",
            )

        # Soruyu işaretle
        success = await osym_exam_engine.flag_question(
            session_id=session_id,
            question_id=request.question_id,
            flagged=request.flagged,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Soru işaretleme işlemi başarısız",
            )

        return {
            "success": True,
            "message": "Soru işaretleme durumu güncellendi",
            "flagged": request.flagged,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Soru işaretleme hatası: {e}",
            extra_data={"session_id": session_id, "question_id": request.question_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Soru işaretleme sırasında beklenmeyen bir hata oluştu",
        )


@router.get("/{session_id}/remaining-time", summary="Kalan Süre")
async def get_remaining_time(
    session_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Sınavın kalan süresini getir

    - Gerçek zamanlı kalan süre hesaplama
    - Dakika ve saniye formatında
    - Uyarı zamanları (son 15 dakika)
    """
    try:
        # Oturum kontrolü
        session_data = await osym_exam_engine.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sınav oturumu bulunamadı"
            )

        # Kullanıcı kontrolü
        if str(session_data.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu sınava erişim yetkiniz yok",
            )

        # Kalan süreyi getir
        remaining_seconds = await osym_exam_engine.get_remaining_time(session_id)

        if remaining_seconds is None:
            return {
                "remaining_seconds": None,
                "remaining_minutes": None,
                "formatted_time": "Sınav başlatılmamış",
                "warning": False,
            }

        remaining_minutes = remaining_seconds // 60
        warning = remaining_minutes <= session_data.exam_config.warning_time_minutes

        # Formatlanmış zaman
        hours = remaining_minutes // 60
        minutes = remaining_minutes % 60
        seconds = remaining_seconds % 60

        if hours > 0:
            formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            formatted_time = f"{minutes:02d}:{seconds:02d}"

        return {
            "remaining_seconds": remaining_seconds,
            "remaining_minutes": remaining_minutes,
            "formatted_time": formatted_time,
            "warning": warning,
            "exam_status": session_data.status.value,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Kalan süre getirme hatası: {e}", extra_data={"session_id": session_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kalan süre hesaplanırken beklenmeyen bir hata oluştu",
        )


@router.post(
    "/{session_id}/complete",
    response_model=PerformanceResponse,
    summary="Sınavı Tamamla",
)
async def complete_exam(
    session_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> PerformanceResponse:
    """
    Sınavı manuel olarak tamamla ve performans analizi yap

    - Detaylı performans metrikleri
    - Konu bazlı analiz
    - IRT tabanlı yetenek tahmini
    - ÖSYM benzeri puanlama sistemi
    """
    try:
        # Oturum kontrolü
        session_data = await osym_exam_engine.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sınav oturumu bulunamadı"
            )

        # Kullanıcı kontrolü
        if str(session_data.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu sınava erişim yetkiniz yok",
            )

        # Sınavı tamamla
        performance_metrics = await osym_exam_engine.complete_exam(
            session_id, manual_completion=True
        )

        logger.info(
            "ÖSYM sınavı tamamlandı",
            extra_data={
                "session_id": session_id,
                "student_id": current_user.id,
                "net_score": performance_metrics.net_score,
                "raw_score": performance_metrics.raw_score,
            },
        )

        return PerformanceResponse(
            total_questions=performance_metrics.total_questions,
            answered_questions=performance_metrics.answered_questions,
            correct_answers=performance_metrics.correct_answers,
            wrong_answers=performance_metrics.wrong_answers,
            empty_answers=performance_metrics.empty_answers,
            net_score=performance_metrics.net_score,
            raw_score=performance_metrics.raw_score,
            percentile=performance_metrics.percentile,
            estimated_ability=performance_metrics.estimated_ability,
            confidence_level=performance_metrics.confidence_level,
        )

    except ValueError as e:
        logger.error(
            f"Sınav tamamlama hatası: {e}", extra_data={"session_id": session_id}
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            f"Beklenmeyen sınav tamamlama hatası: {e}",
            extra_data={"session_id": session_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sınav tamamlanırken beklenmeyen bir hata oluştu",
        )


@router.get(
    "/{session_id}/session",
    response_model=ExamSessionResponse,
    summary="Sınav Oturum Bilgileri",
)
async def get_session_info(
    session_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> ExamSessionResponse:
    """
    Sınav oturum bilgilerini getir

    - Sınav durumu ve ilerleme
    - Başlangıç ve bitiş zamanları
    - Soru sayısı ve süre bilgileri
    """
    try:
        session_data = await osym_exam_engine.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sınav oturumu bulunamadı"
            )

        # Kullanıcı kontrolü
        if str(session_data.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu sınava erişim yetkiniz yok",
            )

        return ExamSessionResponse(
            session_id=session_data.session_id,
            student_id=session_data.student_id,
            exam_type=session_data.exam_config.exam_type.value,
            status=session_data.status.value,
            total_questions=session_data.exam_config.total_questions,
            duration_minutes=session_data.exam_config.duration_minutes,
            current_question_index=session_data.current_question_index,
            started_at=session_data.started_at,
            completed_at=session_data.completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Oturum bilgisi getirme hatası: {e}", extra_data={"session_id": session_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Oturum bilgileri getirilirken beklenmeyen bir hata oluştu",
        )


@router.get(
    "/{session_id}/performance",
    response_model=PerformanceResponse,
    summary="Performans Analizi",
)
async def get_performance_analysis(
    session_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> PerformanceResponse:
    """
    Sınav performans analizini getir (tamamlanmış sınavlar için)

    - Detaylı performans metrikleri
    - IRT tabanlı yetenek tahmini
    - Güven aralıkları
    """
    try:
        session_data = await osym_exam_engine.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sınav oturumu bulunamadı"
            )

        # Kullanıcı kontrolü
        if str(session_data.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu sınava erişim yetkiniz yok",
            )

        # Sınav tamamlanmış mı kontrol et
        if not session_data.performance_metrics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sınav henüz tamamlanmamış, performans analizi mevcut değil",
            )

        performance = session_data.performance_metrics

        return PerformanceResponse(
            total_questions=performance.total_questions,
            answered_questions=performance.answered_questions,
            correct_answers=performance.correct_answers,
            wrong_answers=performance.wrong_answers,
            empty_answers=performance.empty_answers,
            net_score=performance.net_score,
            raw_score=performance.raw_score,
            percentile=performance.percentile,
            estimated_ability=performance.estimated_ability,
            confidence_level=performance.confidence_level,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Performans analizi getirme hatası: {e}",
            extra_data={"session_id": session_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Performans analizi getirilirken beklenmeyen bir hata oluştu",
        )


@router.get(
    "/{session_id}/subject-performance",
    response_model=List[SubjectPerformanceResponse],
    summary="Konu Bazlı Performans",
)
async def get_subject_performance(
    session_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> List[SubjectPerformanceResponse]:
    """
    Konu bazlı performans analizini getir

    - Her konu için detaylı istatistikler
    - Başarı oranları ve ortalama cevaplama süreleri
    - Zorluk seviyesi analizleri
    """
    try:
        session_data = await osym_exam_engine.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sınav oturumu bulunamadı"
            )

        # Kullanıcı kontrolü
        if str(session_data.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu sınava erişim yetkiniz yok",
            )

        # Konu performanslarını getir
        subject_performances = await osym_exam_engine.get_subject_performance(
            session_id
        )

        return [
            SubjectPerformanceResponse(
                subject=perf.subject,
                total_questions=perf.total_questions,
                correct_answers=perf.correct_answers,
                wrong_answers=perf.wrong_answers,
                empty_answers=perf.empty_answers,
                success_rate=perf.success_rate,
                average_response_time=perf.average_response_time,
                difficulty_level=perf.difficulty_level,
            )
            for perf in subject_performances
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Konu performans analizi hatası: {e}",
            extra_data={"session_id": session_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Konu performans analizi getirilirken beklenmeyen bir hata oluştu",
        )


@router.delete("/{session_id}", summary="Sınavı İptal Et")
async def cancel_exam(
    session_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Sınavı iptal et (sadece başlatılmamış sınavlar için)

    - Sınav durumu 'abandoned' olarak işaretlenir
    - Otomatik kaydetme durdurulur
    - Oturum temizlenir
    """
    try:
        session_data = await osym_exam_engine.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sınav oturumu bulunamadı"
            )

        # Kullanıcı kontrolü
        if str(session_data.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu sınava erişim yetkiniz yok",
            )

        # Sadece başlatılmamış veya devam eden sınavlar iptal edilebilir
        if session_data.status not in [ExamStatus.NOT_STARTED, ExamStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tamamlanmış veya iptal edilmiş sınavlar tekrar iptal edilemez",
            )

        # Sınavı iptal et
        session_data.status = ExamStatus.ABANDONED
        session_data.completed_at = datetime.now()

        # Otomatik kaydetme task'ını durdur
        if session_id in osym_exam_engine.auto_save_tasks:
            osym_exam_engine.auto_save_tasks[session_id].cancel()
            del osym_exam_engine.auto_save_tasks[session_id]

        logger.info(
            "ÖSYM sınavı iptal edildi",
            extra_data={
                "session_id": session_id,
                "student_id": current_user.id,
            },
        )

        return {
            "success": True,
            "message": "Sınav başarıyla iptal edildi",
            "session_id": session_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Sınav iptal etme hatası: {e}", extra_data={"session_id": session_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sınav iptal edilirken beklenmeyen bir hata oluştu",
        )


# Task 69.2: Boş bırakma (Empty answer handling) - REQ-1.6
class UnansweredQuestionsResponse(BaseModel):
    """Cevaplanmamış sorular yanıtı"""

    session_id: str
    unanswered_question_ids: List[str]
    unanswered_count: int
    total_questions: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "unanswered_question_ids": ["q1", "q5", "q12", "q45", "q78"],
                "unanswered_count": 5,
                "total_questions": 120,
            }
        }
    }


class CompletionStatsResponse(BaseModel):
    """Tamamlanma istatistikleri yanıtı"""

    session_id: str
    total_questions: int
    answered_questions: int
    unanswered_questions: int
    completion_percentage: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "total_questions": 120,
                "answered_questions": 115,
                "unanswered_questions": 5,
                "completion_percentage": 95.83,
            }
        }
    }


@router.get(
    "/{session_id}/unanswered-questions",
    response_model=UnansweredQuestionsResponse,
    summary="Cevaplanmamış Soruları Getir",
)
async def get_unanswered_questions(
    session_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> UnansweredQuestionsResponse:
    """
    Cevaplanmamış soruların listesini getir - REQ-1.6

    - Boş bırakılan soru ID'leri
    - Toplam cevaplanmamış soru sayısı
    - Sınav tamamlanma durumu

    Bu endpoint öğrencilerin hangi soruları boş bıraktığını görmelerini sağlar.
    """
    try:
        # Oturum kontrolü
        session_data = await osym_exam_engine.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sınav oturumu bulunamadı"
            )

        # Kullanıcı kontrolü
        if str(session_data.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu sınava erişim yetkiniz yok",
            )

        # Cevaplanmamış soruları getir
        unanswered_ids = await osym_exam_engine.get_unanswered_questions(session_id)

        logger.debug(
            "Cevaplanmamış sorular getirildi",
            extra_data={
                "session_id": session_id,
                "unanswered_count": len(unanswered_ids),
                "total_questions": len(session_data.questions),
            },
        )

        return UnansweredQuestionsResponse(
            session_id=session_id,
            unanswered_question_ids=unanswered_ids,
            unanswered_count=len(unanswered_ids),
            total_questions=len(session_data.questions),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Cevaplanmamış sorular getirme hatası: {e}",
            extra_data={"session_id": session_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cevaplanmamış sorular getirilirken beklenmeyen bir hata oluştu",
        )


@router.get(
    "/{session_id}/completion-stats",
    response_model=CompletionStatsResponse,
    summary="Tamamlanma İstatistikleri",
)
async def get_completion_stats(
    session_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> CompletionStatsResponse:
    """
    Sınav tamamlanma istatistiklerini getir - REQ-1.6

    - Toplam soru sayısı
    - Cevaplanan soru sayısı
    - Cevaplanmamış soru sayısı
    - Tamamlanma yüzdesi

    Bu endpoint öğrencilerin sınav ilerlemesini takip etmelerini sağlar.
    """
    try:
        # Oturum kontrolü
        session_data = await osym_exam_engine.get_session_data(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sınav oturumu bulunamadı"
            )

        # Kullanıcı kontrolü
        if str(session_data.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu sınava erişim yetkiniz yok",
            )

        # Cevap istatistiklerini getir
        stats = await osym_exam_engine.get_answer_statistics(session_id)

        logger.debug(
            "Tamamlanma istatistikleri getirildi",
            extra_data={
                "session_id": session_id,
                "completion_percentage": stats["completion_percentage"],
            },
        )

        return CompletionStatsResponse(
            session_id=session_id,
            total_questions=stats["total_questions"],
            answered_questions=stats["answered_questions"],
            unanswered_questions=stats["unanswered_questions"],
            completion_percentage=stats["completion_percentage"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Tamamlanma istatistikleri getirme hatası: {e}",
            extra_data={"session_id": session_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tamamlanma istatistikleri getirilirken beklenmeyen bir hata oluştu",
        )
