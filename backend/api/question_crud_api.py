"""
Soru CRUD API Endpoint'leri
Task 71: Soru Bankası CRUD Operasyonları

REQ-13.1: Makale/Soru içerik yönetimi
"""

import logging
import os
import unicodedata
from typing import Any, Dict, List, Optional

import httpx
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import get_current_user
from services.question_crud_service import QuestionCRUDService

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/questions", tags=["Question CRUD"])


# ========================================================================
# Pydantic Models
# ========================================================================


class QuestionCreateRequest(BaseModel):
    """Soru oluşturma isteği"""

    soru_metni: str = Field(..., description="Soru metni (plain text)")
    soru_html: Optional[str] = Field(None, description="Soru HTML (rich text)")
    soru_latex: Optional[str] = Field(None, description="LaTeX matematik formülü")
    secenekler: List[str] = Field(
        ..., min_items=4, max_items=5, description="Seçenekler (A, B, C, D, E)"
    )
    dogru_cevap: str = Field(..., description="Doğru cevap (A, B, C, D, E)")
    cozum_aciklamasi: Optional[str] = Field(None, description="Çözüm açıklaması")
    cozum_video_url: Optional[str] = Field(None, description="Çözüm video URL")
    alternatif_cozumler: Optional[Dict[str, Any]] = Field(
        None, description="Alternatif çözüm yolları"
    )
    sinav_tipi: str = Field("TYT", description="Sınav türü (TYT, AYT, YDT)")
    konu: str = Field(..., description="Ana konu")
    alt_konu: Optional[str] = Field(None, description="Alt konu")
    zorluk_seviyesi: str = Field(
        "orta", description="Zorluk seviyesi (kolay, orta, zor)"
    )
    sinif_seviyesi: int = Field(12, ge=9, le=12, description="Sınıf seviyesi")
    bloom_seviyesi: int = Field(1, ge=1, le=6, description="Bloom taksonomisi seviyesi")
    etiketler: Optional[List[str]] = Field(None, description="Soru etiketleri")
    genel_erisim: bool = Field(False, description="Genel erişime açık mı")


class QuestionUpdateRequest(BaseModel):
    """Soru güncelleme isteği"""

    soru_metni: Optional[str] = None
    soru_html: Optional[str] = None
    soru_latex: Optional[str] = None
    secenekler: Optional[List[str]] = None
    dogru_cevap: Optional[str] = None
    cozum_aciklamasi: Optional[str] = None
    zorluk_seviyesi: Optional[str] = None
    etiketler: Optional[List[str]] = None


class QuestionSearchRequest(BaseModel):
    """Soru arama isteği"""

    search_query: Optional[str] = Field(None, max_length=500, description="Arama sorgusu")
    exam_type: Optional[str] = Field(None, description="Sınav türü filtresi")
    subject_area: Optional[str] = Field(None, description="Konu filtresi")
    source_book: Optional[str] = Field(None, description="Kaynak kitap filtresi")
    difficulty: Optional[str] = Field(None, description="Zorluk filtresi")
    grade_level: Optional[int] = Field(None, description="Sınıf seviyesi")
    min_quality: Optional[float] = Field(None, description="Minimum kalite skoru")
    # IRT difficulty constraints from CLAUDE.md: [-4.0, 4.0]
    irt_difficulty_min: Optional[float] = Field(
        None, ge=-4.0, le=4.0, description="Min IRT zorluk [-4.0, 4.0]"
    )
    irt_difficulty_max: Optional[float] = Field(
        None, ge=-4.0, le=4.0, description="Max IRT zorluk [-4.0, 4.0]"
    )
    osym_compliant: Optional[bool] = Field(None, description="ÖSYM uyumlu mu")
    show_answers: bool = Field(
        False, description="Cevaplari goster (admin/review icin)"
    )
    facets: Optional[List[str]] = Field(
        None, description="Facet alanları (exam_type, subject_area, difficulty)"
    )
    limit: int = Field(100, ge=1, le=500)
    offset: int = Field(0, ge=0)


# ========================================================================
# Dependency Functions
# ========================================================================


async def get_question_service(
    db: AsyncSession = Depends(get_db_session),
) -> QuestionCRUDService:
    """Question CRUD servisi dependency"""
    return QuestionCRUDService(db)


# ========================================================================
# TASK 71.1: Soru Ekleme (Rich Text Editor, Image Upload)
# ========================================================================


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_question(
    request: QuestionCreateRequest,
    image: Optional[UploadFile] = File(None),
    current_user: Dict = Depends(get_current_user),
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Yeni soru oluştur

    - **Rich text editor** desteği (HTML formatında)
    - **Image upload** desteği
    - **LaTeX** matematik formülü desteği
    - Otomatik konu ve etiket yönetimi
    """
    try:
        # Görsel dosyasını oku
        image_file = None
        image_filename = None
        if image:
            image_file = await image.read()
            image_filename = image.filename

        # Soru oluştur
        question = await service.create_question(
            question_data=request.dict(),
            created_by=current_user.get("user_id", "unknown"),
            image_file=image_file,
            image_filename=image_filename,
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "data": {
                    "id": question.id,
                    "question_text": question.question_text,
                    "question_image_url": question.question_image_url,
                    "exam_type": question.exam_type,
                    "subject_area": question.subject_area,
                    "difficulty": question.difficulty_level.value,
                    "created_at": question.created_at.isoformat(),
                },
                "message": "Soru başarıyla oluşturuldu",
            },
        )

    except Exception as e:
        logger.error(f"Soru oluşturma hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Soru oluşturma hatası: {str(e)}",
        )


@router.post("/bulk-create", status_code=status.HTTP_201_CREATED)
async def bulk_create_questions(
    questions: List[QuestionCreateRequest],
    current_user: Dict = Depends(get_current_user),
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Toplu soru oluşturma

    Birden fazla soruyu aynı anda oluşturur.
    """
    try:
        questions_data = [q.dict() for q in questions]

        result = await service.bulk_create_questions(
            questions_data=questions_data,
            created_by=current_user.get("user_id", "unknown"),
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "data": result,
                "message": f"{result['success_count']}/{len(questions)} soru başarıyla oluşturuldu",
            },
        )

    except Exception as e:
        logger.error(f"Toplu oluşturma hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Toplu oluşturma hatası: {str(e)}",
        )


# ========================================================================
# TASK 71.2: Soru Güncelleme (Version Control, Change History)
# ========================================================================


@router.put("/{question_id}", status_code=status.HTTP_200_OK)
async def update_question(
    question_id: str,
    request: QuestionUpdateRequest,
    create_version: bool = Query(True, description="Versiyon oluştur"),
    current_user: Dict = Depends(get_current_user),
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Soruyu güncelle

    - **Version control**: Her güncelleme için otomatik versiyon oluşturur
    - **Change history**: Değişiklik geçmişini tutar
    - Seçici güncelleme: Sadece değişen alanları günceller
    """
    try:
        # Sadece None olmayan alanları güncelle
        update_data = {k: v for k, v in request.dict().items() if v is not None}

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Güncellenecek alan bulunamadı",
            )

        question = await service.update_question(
            question_id=question_id,
            update_data=update_data,
            updated_by=current_user.get("user_id", "unknown"),
            create_version=create_version,
        )

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "id": question.id,
                    "updated_fields": list(update_data.keys()),
                    "updated_at": question.updated_at.isoformat(),
                    "version_created": create_version,
                },
                "message": "Soru başarıyla güncellendi",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Soru güncelleme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Soru güncelleme hatası: {str(e)}",
        )


@router.get("/{question_id}/history", status_code=status.HTTP_200_OK)
async def get_question_history(
    question_id: str,
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Soru değişiklik geçmişini getir

    Sorunun tüm versiyon geçmişini döndürür.
    """
    try:
        history = await service.get_question_history(question_id)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "question_id": question_id,
                    "version_count": len(history),
                    "versions": history,
                },
                "message": f"{len(history)} versiyon bulundu",
            },
        )

    except Exception as e:
        logger.error(f"Geçmiş getirme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geçmiş getirme hatası: {str(e)}",
        )


# ========================================================================
# TASK 71.3: Soru Silme (Soft Delete, Archive, Restore)
# ========================================================================


@router.delete("/{question_id}", status_code=status.HTTP_200_OK)
async def delete_question(
    question_id: str,
    permanent: bool = Query(False, description="Kalıcı silme"),
    current_user: Dict = Depends(get_current_user),
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Soruyu sil

    - **Soft delete** (varsayılan): Soru deaktif edilir, geri yüklenebilir
    - **Permanent delete**: Soru kalıcı olarak silinir
    """
    try:
        success = await service.delete_question(
            question_id=question_id,
            deleted_by=current_user.get("user_id", "unknown"),
            permanent=permanent,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "question_id": question_id,
                    "permanent": permanent,
                    "can_restore": not permanent,
                },
                "message": "Soru başarıyla silindi"
                if permanent
                else "Soru deaktif edildi (geri yüklenebilir)",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Soru silme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Soru silme hatası: {str(e)}",
        )


@router.post("/{question_id}/archive", status_code=status.HTTP_200_OK)
async def archive_question(
    question_id: str,
    current_user: Dict = Depends(get_current_user),
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Soruyu arşivle

    Soru arşive taşınır, aktif kullanımdan çıkar ama geri yüklenebilir.
    """
    try:
        success = await service.archive_question(
            question_id=question_id,
            archived_by=current_user.get("user_id", "unknown"),
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {"question_id": question_id, "status": "archived"},
                "message": "Soru başarıyla arşivlendi",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Arşivleme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Arşivleme hatası: {str(e)}",
        )


@router.post("/{question_id}/restore", status_code=status.HTTP_200_OK)
async def restore_question(
    question_id: str,
    current_user: Dict = Depends(get_current_user),
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Arşivlenmiş/silinmiş soruyu geri yükle

    Deaktif edilmiş veya arşivlenmiş soruyu tekrar aktif hale getirir.
    """
    try:
        success = await service.restore_question(
            question_id=question_id,
            restored_by=current_user.get("user_id", "unknown"),
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {"question_id": question_id, "status": "active"},
                "message": "Soru başarıyla geri yüklendi",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Geri yükleme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geri yükleme hatası: {str(e)}",
        )


@router.get("/archived", status_code=status.HTTP_200_OK)
async def get_archived_questions(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Arşivlenmiş soruları listele
    """
    try:
        questions = await service.get_archived_questions(limit=limit, offset=offset)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "questions": [
                        {
                            "id": q.id,
                            "question_text": q.question_text,
                            "exam_type": q.exam_type,
                            "subject_area": q.subject_area,
                            "archived_at": q.updated_at.isoformat(),
                        }
                        for q in questions
                    ],
                    "count": len(questions),
                    "limit": limit,
                    "offset": offset,
                },
                "message": f"{len(questions)} arşivlenmiş soru bulundu",
            },
        )

    except Exception as e:
        logger.error(f"Arşiv listeleme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Arşiv listeleme hatası: {str(e)}",
        )


# ========================================================================
# TASK 71.4: Soru Arama (Full-text Search, Advanced Filters, Faceted Search)
# ========================================================================


@router.post("/search", status_code=status.HTTP_200_OK)
async def search_questions(
    request: QuestionSearchRequest,
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Gelişmiş soru arama

    - **Full-text search**: Soru metni, açıklama ve seçeneklerde arama
    - **Advanced filters**: Sınav türü, konu, zorluk, IRT parametreleri
    - **Faceted search**: Konu, zorluk, sınav türü grupları
    """
    try:
        # Filtreleri hazırla
        filters = {}
        if request.exam_type:
            filters["exam_type"] = request.exam_type
        if request.subject_area:
            filters["subject_area"] = request.subject_area
        if request.source_book:
            filters["source_book"] = request.source_book
        if request.difficulty:
            filters["difficulty"] = request.difficulty
        if request.grade_level:
            filters["grade_level"] = request.grade_level
        if request.min_quality:
            filters["min_quality"] = request.min_quality
        if (
            request.irt_difficulty_min is not None
            and request.irt_difficulty_max is not None
        ):
            filters["irt_difficulty_range"] = (
                request.irt_difficulty_min,
                request.irt_difficulty_max,
            )
        if request.osym_compliant is not None:
            filters["osym_compliant"] = request.osym_compliant

        # Arama yap
        result = await service.search_questions(
            search_query=request.search_query,
            filters=filters if filters else None,
            facets=request.facets,
            limit=request.limit,
            offset=request.offset,
        )

        # Response formatina donustur
        # TODO: Production icin auth zorunlu yapilmali (get_current_user)
        questions_data = []
        for q in result["questions"]:
            item: Dict[str, Any] = {
                "id": q.id,
                "question_text": q.question_text,
                "question_image_url": q.question_image_url,
                "exam_type": q.exam_type,
                "subject_area": q.subject_area,
                "source_book": q.source_book,
                "topic": q.primary_topic_id,
                "difficulty": q.difficulty_level.value,
                "bloom_level": q.bloom_level,
                "bloom_category": q.bloom_category,
                "irt_difficulty": q.irt_difficulty,
                "quality_score": q.quality_score,
                "word_count": q.word_count,
                "times_asked": q.times_asked,
                "success_rate": (
                    q.times_correct / max(1, q.times_asked)
                    if q.times_asked > 0
                    else 0
                ),
                "created_at": q.created_at.isoformat(),
            }
            # Cevaplar sadece show_answers=true ile gosterilir
            if request.show_answers:
                item["options"] = {
                    "A": q.option_a,
                    "B": q.option_b,
                    "C": q.option_c,
                    "D": q.option_d,
                    "E": q.option_e,
                }
                item["correct_answer"] = q.correct_answer
            questions_data.append(item)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "questions": questions_data,
                    "total_count": result["total_count"],
                    "limit": result["limit"],
                    "offset": result["offset"],
                    "facets": result["facets"],
                    "has_more": (result["offset"] + result["limit"])
                    < result["total_count"],
                },
                "message": f"{len(questions_data)} soru bulundu",
            },
        )

    except Exception as e:
        logger.error(f"Arama hatasi: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Arama sirasinda bir hata olustu",
        )


@router.get("/search/elasticsearch", status_code=status.HTTP_200_OK)
async def elasticsearch_search(
    query: str = Query(..., description="Arama sorgusu"),
    exam_type: Optional[str] = Query(None, description="Sınav türü"),
    subject: Optional[str] = Query(None, description="Konu"),
    difficulty: Optional[str] = Query(None, description="Zorluk"),
    limit: int = Query(100, ge=1, le=500),
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Elasticsearch ile gelişmiş arama

    Fuzzy matching ve semantic search desteği.
    """
    try:
        filters = {}
        if exam_type:
            filters["exam_type"] = exam_type
        if subject:
            filters["subject_area"] = subject
        if difficulty:
            filters["difficulty"] = difficulty

        questions = await service.advanced_search_with_elasticsearch(
            search_query=query, filters=filters if filters else None, limit=limit
        )

        questions_data = []
        for q in questions:
            questions_data.append(
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "exam_type": q.exam_type,
                    "subject_area": q.subject_area,
                    "difficulty": q.difficulty_level.value,
                    "quality_score": q.quality_score,
                }
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "questions": questions_data,
                    "count": len(questions_data),
                    "search_engine": "elasticsearch",
                },
                "message": f"{len(questions_data)} soru bulundu (Elasticsearch)",
            },
        )

    except Exception as e:
        logger.error(f"Elasticsearch arama hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Elasticsearch arama hatası: {str(e)}",
        )


# ========================================================================
# Yardımcı Endpoint'ler
# ========================================================================


@router.get("/{question_id}", status_code=status.HTTP_200_OK)
async def get_question(
    question_id: str,
    include_relations: bool = Query(False, description="İlişkileri dahil et"),
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Soru detaylarını getir
    """
    try:
        question = await service.get_question_by_id(
            question_id=question_id, include_relations=include_relations
        )

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
            )

        question_data = {
            "id": question.id,
            "question_text": question.question_text,
            "question_html": question.question_html,
            "question_latex": question.question_latex,
            "question_image_url": question.question_image_url,
            "options": {
                "A": question.option_a,
                "B": question.option_b,
                "C": question.option_c,
                "D": question.option_d,
                "E": question.option_e,
            },
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "explanation_video_url": question.explanation_video_url,
            "alternative_solutions": question.alternative_solutions,
            "exam_type": question.exam_type,
            "subject_area": question.subject_area,
            "grade_level": question.grade_level,
            "difficulty": question.difficulty_level.value,
            "bloom_level": question.bloom_level,
            "bloom_category": question.bloom_category,
            "irt_parameters": {
                "difficulty": question.irt_difficulty,
                "discrimination": question.irt_discrimination,
                "guessing": question.irt_guessing,
                "upper_asymptote": question.irt_upper_asymptote,
            },
            "morphology_complexity": question.morphology_complexity,
            "readability_score": question.readability_score,
            "statistics": {
                "times_asked": question.times_asked,
                "times_correct": question.times_correct,
                "times_wrong": question.times_wrong,
                "times_skipped": question.times_skipped,
                "success_rate": (
                    question.times_correct / max(1, question.times_asked)
                    if question.times_asked > 0
                    else 0
                ),
                "average_response_time": question.average_response_time,
            },
            "quality": {
                "score": question.quality_score,
                "review_status": question.quality_review_status,
                "osym_compliant": question.osym_format_compliant,
            },
            "created_at": question.created_at.isoformat(),
            "updated_at": question.updated_at.isoformat(),
            "is_active": question.is_active,
            "is_public": question.is_public,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": question_data,
                "message": "Soru detayları başarıyla getirildi",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Soru getirme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Soru getirme hatası: {str(e)}",
        )


@router.get("/statistics/overview", status_code=status.HTTP_200_OK)
async def get_statistics(
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Soru bankası istatistikleri
    """
    try:
        stats = await service.get_question_statistics()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": stats,
                "message": "İstatistikler başarıyla getirildi",
            },
        )

    except Exception as e:
        logger.error(f"İstatistik hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"İstatistik hatası: {str(e)}",
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    API sağlık kontrolü
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "data": {
                "service": "Question CRUD API",
                "status": "healthy",
                "version": "1.0.0",
                "features": [
                    "Rich Text Editor Support",
                    "Image Upload",
                    "Version Control",
                    "Change History",
                    "Soft Delete",
                    "Archive/Restore",
                    "Full-text Search",
                    "Advanced Filters",
                    "Faceted Search",
                    "Elasticsearch Integration",
                    "Random Sampling",
                    "Source Book Filtering",
                ],
            },
            "message": "Question CRUD API çalışıyor",
        },
    )


# ========================================================================
# A3: Random Question Sampling
# ========================================================================


@router.get("/random", status_code=status.HTTP_200_OK)
async def get_random_questions(
    count: int = Query(10, ge=1, le=50, description="Soru sayısı"),
    subject_area: Optional[str] = Query(None, description="Konu filtresi"),
    exam_type: Optional[str] = Query(None, description="Sınav türü (TYT/AYT/YDT)"),
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Rastgele soru seçimi (adaptif öğrenme için)

    - subject_area ve exam_type ile filtrelenebilir
    - Her çağrıda farklı sorular döner
    """
    try:
        questions = await service.get_random_questions(
            count=count,
            subject_area=subject_area,
            exam_type=exam_type,
        )

        questions_data = []
        for q in questions:
            questions_data.append(
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "options": {
                        "A": q.option_a,
                        "B": q.option_b,
                        "C": q.option_c,
                        "D": q.option_d,
                        "E": q.option_e,
                    },
                    "correct_answer": q.correct_answer,
                    "exam_type": q.exam_type,
                    "subject_area": q.subject_area,
                    "difficulty": q.difficulty_level.value,
                    "quality_score": q.quality_score,
                    "source_book": q.source_book,
                }
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "questions": questions_data,
                    "count": len(questions_data),
                    "filters": {
                        "subject_area": subject_area,
                        "exam_type": exam_type,
                    },
                },
                "message": f"{len(questions_data)} rastgele soru seçildi",
            },
        )

    except Exception as e:
        logger.error(f"Rastgele soru hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rastgele soru hatası: {str(e)}",
        )


# ========================================================================
# A4: Source Book Listing & Filtering
# ========================================================================


@router.get("/books", status_code=status.HTTP_200_OK)
async def list_source_books(
    subject_area: Optional[str] = Query(None, description="Konu filtresi"),
    exam_type: Optional[str] = Query(None, description="Sınav türü filtresi"),
    service: QuestionCRUDService = Depends(get_question_service),
):
    """
    Kaynak kitap listesi (soru sayılarıyla birlikte)
    """
    try:
        books = await service.list_source_books(
            subject_area=subject_area,
            exam_type=exam_type,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "books": books,
                    "total_books": len(books),
                },
                "message": f"{len(books)} kaynak kitap bulundu",
            },
        )

    except Exception as e:
        logger.error(f"Kitap listeleme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kitap listeleme sirasinda bir hata olustu",
        )


# ──────────────────────────────────────────────────────────────
# Semantic Search (pgvector + nomic-embed-text via Ollama)
# ──────────────────────────────────────────────────────────────


class SemanticSearchRequest(BaseModel):
    """Anlamsal soru arama istegi"""

    query: str = Field(..., min_length=3, max_length=1000, description="Arama metni")
    top_k: int = Field(10, ge=1, le=50, description="Sonuc sayisi")
    exam_type: Optional[str] = Field(None, description="Sinav turu filtresi")
    subject_area: Optional[str] = Field(None, description="Konu filtresi")
    min_similarity: float = Field(0.3, ge=0.0, le=1.0, description="Minimum benzerlik skoru")
    show_answers: bool = Field(False, description="Cevaplari goster")


@router.post("/semantic-search", summary="Anlamsal soru arama (pgvector)")
async def semantic_search(
    request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Anlamsal (semantic) soru arama.

    Ollama nomic-embed-text ile query embedding olusturur,
    pgvector HNSW index ile en benzer sorulari bulur.
    """
    try:
        # 1. NFC normalize Turkish text before embedding
        query_text = unicodedata.normalize("NFC", request.query)

        # 2. Generate query embedding via Ollama (async, non-blocking)
        prefixed = f"search_query: {query_text}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{OLLAMA_URL}/api/embed",
                    json={"model": "nomic-embed-text", "input": prefixed},
                )
                result = resp.json()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Embedding servisi zaman asimina ugradi",
            )
        except Exception as embed_err:
            logger.error(f"Ollama embedding error: {embed_err}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Embedding servisi kullanilamiyor",
            )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Embedding modeli kullanilamiyor",
            )

        query_embedding = result["embeddings"][0]
        vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # 3. Build similarity query with filters

        filters = []
        params: Dict[str, Any] = {"emb": vec_str, "min_sim": request.min_similarity}

        if request.exam_type:
            filters.append("q.exam_type = :exam_type")
            params["exam_type"] = request.exam_type
        if request.subject_area:
            filters.append("q.subject_area = :subject_area")
            params["subject_area"] = request.subject_area

        where_clause = " AND ".join(["q.embedding IS NOT NULL"] + filters)
        params["top_k"] = request.top_k

        sql = sa_text(f"""
            SELECT q.id, q.question_text, q.question_image_url,
                   q.exam_type, q.subject_area, q.source_book,
                   q.difficulty_level, q.bloom_level, q.bloom_category,
                   q.quality_score, q.word_count,
                   q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
                   q.correct_answer,
                   1 - (q.embedding <=> :emb::vector) as similarity
            FROM question_bank q
            WHERE {where_clause}
              AND 1 - (q.embedding <=> :emb::vector) >= :min_sim
            ORDER BY q.embedding <=> :emb::vector
            LIMIT :top_k
        """)

        result_rows = await db.execute(sql, params)
        rows = result_rows.fetchall()

        # 3. Format response
        questions = []
        for r in rows:
            item: Dict[str, Any] = {
                "id": str(r.id),
                "question_text": r.question_text,
                "question_image_url": r.question_image_url,
                "exam_type": r.exam_type,
                "subject_area": r.subject_area,
                "source_book": r.source_book,
                "difficulty": r.difficulty_level,
                "bloom_level": r.bloom_level,
                "bloom_category": r.bloom_category,
                "quality_score": r.quality_score,
                "word_count": r.word_count,
                "similarity": round(float(r.similarity), 4),
            }
            if request.show_answers:
                item["options"] = {
                    "A": r.option_a, "B": r.option_b, "C": r.option_c,
                    "D": r.option_d, "E": r.option_e,
                }
                item["correct_answer"] = r.correct_answer
            questions.append(item)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "questions": questions,
                    "total_results": len(questions),
                    "query": request.query,
                    "model": "nomic-embed-text",
                    "embedding_dim": 768,
                },
                "message": f"{len(questions)} benzer soru bulundu",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semantic search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Anlamsal arama sirasinda bir hata olustu",
        )
