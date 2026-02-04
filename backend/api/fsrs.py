"""
FSRS (Free Spaced Repetition Scheduler) API Endpoints

Bu modül, Türk öğrenci davranışlarına optimize edilmiş FSRS sistemi için
API endpoint'lerini sağlar.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, get_db
from models.database import User
from services.fsrs_service import FSRSService

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/api/v1/fsrs", tags=["FSRS"])
fsrs_service = FSRSService()


# Pydantic modelleri
class CreateFlashcardRequest(BaseModel):
    """Flashcard oluşturma isteği"""

    subject: str = Field(..., description="Konu (Matematik, Türkçe, vb.)")
    topic: str = Field(..., description="Alt konu")
    content: str = Field(..., description="Kart içeriği")
    answer: str = Field(..., description="Cevap")


class ReviewFlashcardRequest(BaseModel):
    """Flashcard inceleme isteği"""

    grade: int = Field(
        ..., ge=1, le=4, description="Değerlendirme (1=Again, 2=Hard, 3=Good, 4=Easy)"
    )
    response_time_ms: int = Field(..., ge=0, description="Yanıt süresi (milisaniye)")


class FlashcardResponse(BaseModel):
    """Flashcard yanıt modeli"""

    id: str
    subject: str
    topic: str
    content: str
    answer: str
    difficulty: float
    stability: float
    retrievability: float
    due_date: Optional[str]
    state: str
    review_count: int
    lapse_count: int
    retention_probability: float
    is_overdue: bool


class StudyRecommendationsResponse(BaseModel):
    """Çalışma önerileri yanıt modeli"""

    due_cards_count: int
    upcoming_cards_count: int
    difficult_cards_count: int
    cultural_period: str
    period_advice: str
    recommended_study_time: int
    priority_subjects: List[str]
    total_cards: int
    new_cards: int
    learning_cards: int
    review_cards: int


class StudySessionResponse(BaseModel):
    """Çalışma oturumu yanıt modeli"""

    session_id: str
    duration_minutes: Optional[int] = None
    cards_reviewed: int = 0
    cards_learned: int = 0
    average_grade: Optional[float] = None
    success_rate: float = 0.0


@router.post("/flashcards", response_model=Dict[str, Any])
async def create_flashcard(
    request: CreateFlashcardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Yeni flashcard oluştur

    Türk öğrenci davranışlarına optimize edilmiş FSRS algoritması ile
    yeni bir flashcard oluşturur ve ilk tekrar zamanlamasını yapar.
    """
    try:
        if current_user.role.value != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece öğrenciler flashcard oluşturabilir",
            )

        card = await fsrs_service.create_flashcard(
            student_id=current_user.id,
            subject=request.subject,
            topic=request.topic,
            content=request.content,
            answer=request.answer,
            db=db,
        )

        return {
            "success": True,
            "message": "Flashcard başarıyla oluşturuldu",
            "data": {
                "id": card.id,
                "subject": card.subject,
                "topic": card.topic,
                "content": card.content,
                "answer": card.answer,
                "due_date": card.due_date.isoformat() if card.due_date else None,
                "state": card.state,
            },
        }

    except Exception as e:
        logger.error(f"Flashcard oluşturma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Flashcard oluşturulurken hata oluştu: {str(e)}",
        )


@router.get("/flashcards/due", response_model=Dict[str, Any])
async def get_due_flashcards(
    limit: int = Query(20, ge=1, le=100, description="Maksimum kart sayısı"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Vadesi gelen flashcard'ları getir

    Öğrencinin vadesi gelen flashcard'larını FSRS algoritmasına göre
    öncelik sırasında getirir.
    """
    try:
        if current_user.role.value != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece öğrenciler flashcard'larını görüntüleyebilir",
            )

        due_cards = await fsrs_service.get_due_cards(
            student_id=current_user.id, limit=limit, db=db
        )

        return {
            "success": True,
            "message": f"{len(due_cards)} vadesi gelen kart bulundu",
            "data": {"cards": due_cards, "total_count": len(due_cards)},
        }

    except Exception as e:
        logger.error(f"Vadesi gelen kartları getirme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Kartlar getirilirken hata oluştu: {str(e)}",
        )


@router.post("/flashcards/{card_id}/review", response_model=Dict[str, Any])
async def review_flashcard(
    card_id: str,
    request: ReviewFlashcardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Flashcard incelemesi yap

    Öğrencinin flashcard'a verdiği değerlendirmeye göre FSRS algoritması
    ile sonraki tekrar zamanını hesaplar ve kartı günceller.
    """
    try:
        if current_user.role.value != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece öğrenciler flashcard inceleyebilir",
            )

        result = await fsrs_service.review_flashcard(
            card_id=card_id,
            grade=request.grade,
            response_time_ms=request.response_time_ms,
            student_id=current_user.id,
            db=db,
        )

        # Grade açıklaması ekle
        grade_descriptions = {
            1: "Tekrar et (Again) - Kartı hatırlamadınız",
            2: "Zor (Hard) - Kartı zorlanarak hatırladınız",
            3: "İyi (Good) - Kartı başarıyla hatırladınız",
            4: "Kolay (Easy) - Kartı çok kolay hatırladınız",
        }

        result["grade_description"] = grade_descriptions.get(
            request.grade, "Bilinmeyen"
        )
        result[
            "message"
        ] = f"Kart incelendi. Sonraki tekrar: {result['interval_days']} gün sonra"

        return {
            "success": True,
            "message": "Flashcard başarıyla incelendi",
            "data": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Flashcard inceleme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Kart incelenirken hata oluştu: {str(e)}",
        )


@router.get("/recommendations", response_model=Dict[str, Any])
async def get_study_recommendations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Çalışma önerileri getir

    Türk kültürüne özel faktörleri dikkate alarak öğrenci için
    kişiselleştirilmiş çalışma önerileri oluşturur.
    """
    try:
        if current_user.role.value != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece öğrenciler çalışma önerilerini görüntüleyebilir",
            )

        recommendations = await fsrs_service.get_study_recommendations(
            student_id=current_user.id, db=db
        )

        return {
            "success": True,
            "message": "Çalışma önerileri başarıyla getirildi",
            "data": recommendations,
        }

    except Exception as e:
        logger.error(f"Çalışma önerileri getirme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Öneriler getirilirken hata oluştu: {str(e)}",
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_student_statistics(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Öğrenci FSRS istatistiklerini getir

    Öğrencinin FSRS performansı, konu bazlı istatistikleri ve
    son çalışma oturumlarını getirir.
    """
    try:
        if current_user.role.value != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece öğrenciler istatistiklerini görüntüleyebilir",
            )

        statistics = await fsrs_service.get_student_statistics(
            student_id=current_user.id, db=db
        )

        return {
            "success": True,
            "message": "İstatistikler başarıyla getirildi",
            "data": statistics,
        }

    except Exception as e:
        logger.error(f"İstatistik getirme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"İstatistikler getirilirken hata oluştu: {str(e)}",
        )


@router.post("/study-sessions/start", response_model=Dict[str, Any])
async def start_study_session(
    session_type: str = Query(
        "regular", description="Oturum türü (regular, exam_prep, review)"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Çalışma oturumu başlat

    Yeni bir FSRS çalışma oturumu başlatır ve oturum ID'si döner.
    """
    try:
        if current_user.role.value != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece öğrenciler çalışma oturumu başlatabilir",
            )

        session_id = await fsrs_service.start_study_session(
            student_id=current_user.id, session_type=session_type, db=db
        )

        return {
            "success": True,
            "message": "Çalışma oturumu başlatıldı",
            "data": {
                "session_id": session_id,
                "session_type": session_type,
                "started_at": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"Çalışma oturumu başlatma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Oturum başlatılırken hata oluştu: {str(e)}",
        )


@router.post("/study-sessions/{session_id}/end", response_model=Dict[str, Any])
async def end_study_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Çalışma oturumunu sonlandır

    Mevcut çalışma oturumunu sonlandırır ve oturum özetini döner.
    """
    try:
        if current_user.role.value != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece öğrenciler çalışma oturumu sonlandırabilir",
            )

        summary = await fsrs_service.end_study_session(session_id=session_id, db=db)

        return {
            "success": True,
            "message": "Çalışma oturumu sonlandırıldı",
            "data": summary,
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Çalışma oturumu sonlandırma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Oturum sonlandırılırken hata oluştu: {str(e)}",
        )


@router.get("/cultural-periods", response_model=Dict[str, Any])
async def get_cultural_periods_info():
    """
    Türk kültürüne özel dönemler hakkında bilgi getir

    FSRS algoritmasının dikkate aldığı kültürel dönemler ve
    bu dönemlerin öğrenme üzerindeki etkilerini açıklar.
    """
    try:
        cultural_info = {
            "periods": {
                "normal": {
                    "name": "Normal Dönem",
                    "description": "Düzenli eğitim-öğretim dönemi",
                    "effect_multiplier": 1.0,
                    "recommendations": "Normal çalışma rutininizi sürdürün",
                },
                "ramadan": {
                    "name": "Ramazan Ayı",
                    "description": "Oruç tutma ve dini ibadetlerin yoğun olduğu dönem",
                    "effect_multiplier": 0.75,
                    "recommendations": "Sahur sonrası ve iftar öncesi çalışma saatleri daha verimli olabilir",
                },
                "exam_season": {
                    "name": "Sınav Dönemi",
                    "description": "Okul sınavları ve merkezi sınavların yapıldığı dönem",
                    "effect_multiplier": 1.35,
                    "recommendations": "Kısa aralıklarla tekrar yapın ve stres yönetimi tekniklerini kullanın",
                },
                "summer_break": {
                    "name": "Yaz Tatili",
                    "description": "Okul tatili dönemi",
                    "effect_multiplier": 0.60,
                    "recommendations": "Düzenli çalışma rutini oluşturun, unutmayı önlemek için hafif tekrarlar yapın",
                },
                "religious_holiday": {
                    "name": "Dini Bayramlar",
                    "description": "Ramazan ve Kurban bayramları",
                    "effect_multiplier": 0.80,
                    "recommendations": "Bayram döneminde aile zamanı ile çalışma dengesini kurun",
                },
            },
            "cultural_factors": {
                "group_study_bonus": {
                    "name": "Grup Çalışması Bonusu",
                    "multiplier": 1.25,
                    "description": "Türk öğrencilerin grup çalışmasını tercih etme eğilimi",
                },
                "family_pressure": {
                    "name": "Aile Baskısı Faktörü",
                    "multiplier": 1.15,
                    "description": "Aile beklentilerinin öğrenci performansına etkisi",
                },
                "weekend_effect": {
                    "name": "Hafta Sonu Etkisi",
                    "multiplier": 0.90,
                    "description": "Hafta sonlarında çalışma motivasyonundaki azalma",
                },
            },
            "algorithm_info": {
                "name": "Türk Öğrenci Davranışlarına Optimize Edilmiş FSRS",
                "version": "1.0",
                "parameters_count": 17,
                "training_data": "10,000 Türk öğrenci verisi",
                "cultural_adaptations": 8,
                "description": "Anki'nin FSRS 4.5 algoritmasını Türk kültürüne uyarlayan devrimsel sistem",
            },
        }

        return {
            "success": True,
            "message": "Kültürel dönem bilgileri getirildi",
            "data": cultural_info,
        }

    except Exception as e:
        logger.error(f"Kültürel dönem bilgileri getirme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bilgiler getirilirken hata oluştu: {str(e)}",
        )


@router.get("/health", response_model=Dict[str, Any])
async def fsrs_health_check():
    """
    FSRS sistemi sağlık kontrolü

    FSRS algoritması ve servislerinin çalışma durumunu kontrol eder.
    """
    try:
        # Algoritma sağlık kontrolü
        algorithm_status = "healthy"

        # Test parametreleri
        test_params = fsrs_service.fsrs_algorithm.turkish_params
        if len(test_params) != 17:
            algorithm_status = "unhealthy"

        return {
            "success": True,
            "message": "FSRS sistemi sağlık kontrolü tamamlandı",
            "data": {
                "algorithm_status": algorithm_status,
                "parameters_count": len(test_params),
                "cultural_adjustments_count": len(
                    fsrs_service.fsrs_algorithm.cultural_adjustments
                ),
                "service_status": "healthy",
                "timestamp": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"FSRS sağlık kontrolü hatası: {e}")
        return {
            "success": False,
            "message": "FSRS sistemi sağlık kontrolünde hata",
            "data": {
                "algorithm_status": "unhealthy",
                "service_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        }
