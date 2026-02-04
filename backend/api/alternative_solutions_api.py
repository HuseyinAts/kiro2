"""
Alternatif Çözüm Yolları API
Task 73: Alternatif Çözüm Yolları
Task 73.4: Öğrenci Çözüm Paylaşımı

REQ-13.1: Makale/Soru içerik yönetimi - Alternatif çözüm yolları
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import get_current_user
from services.alternative_solutions_service import AlternativeSolutionsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/questions", tags=["Alternative Solutions"])


# ========================================================================
# Pydantic Models
# ========================================================================


class SolutionStep(BaseModel):
    """Çözüm adımı"""

    step_number: int = Field(..., ge=1, description="Adım numarası")
    description: str = Field(..., min_length=1, description="Adım açıklaması")
    formula: Optional[str] = Field(None, description="Matematiksel formül (LaTeX)")
    explanation: Optional[str] = Field(None, description="Ek açıklama")


class AlternativeSolutionCreate(BaseModel):
    """Alternatif çözüm oluşturma"""

    title: str = Field(..., min_length=1, max_length=200, description="Çözüm başlığı")
    category: str = Field(
        ..., description="Çözüm kategorisi (klasik, hızlı, görsel, mantıksal, formül)"
    )
    difficulty: str = Field(..., description="Zorluk seviyesi (kolay, orta, zor)")
    estimated_time_seconds: int = Field(
        ..., ge=1, le=3600, description="Tahmini çözüm süresi (saniye)"
    )
    steps: List[SolutionStep] = Field(..., min_items=1, description="Çözüm adımları")
    tips: Optional[List[str]] = Field(None, description="İpuçları")
    prerequisites: Optional[List[str]] = Field(
        None, description="Ön gereksinimler (bilgi/beceri)"
    )
    advantages: Optional[List[str]] = Field(None, description="Avantajları")
    disadvantages: Optional[List[str]] = Field(None, description="Dezavantajları")
    video_url: Optional[str] = Field(None, description="Video çözüm URL")
    created_by_type: str = Field(
        "teacher", description="Oluşturan tipi (teacher, student, ai)"
    )


class SolutionVote(BaseModel):
    """Çözüm oylama"""

    vote_type: str = Field(..., description="Oy tipi (upvote, downvote)")
    comment: Optional[str] = Field(None, max_length=500, description="Yorum")


# ========================================================================
# Dependency Functions
# ========================================================================


async def get_solutions_service(
    db: AsyncSession = Depends(get_db_session),
) -> AlternativeSolutionsService:
    """Alternative Solutions servisi dependency"""
    return AlternativeSolutionsService(db)


# ========================================================================
# TASK 73.1: Çoklu Çözüm Desteği
# ========================================================================


@router.post("/{question_id}/solutions", status_code=status.HTTP_201_CREATED)
async def add_alternative_solution(
    question_id: str,
    solution: AlternativeSolutionCreate,
    current_user: Dict = Depends(get_current_user),
    service: AlternativeSolutionsService = Depends(get_solutions_service),
):
    """Soruya alternatif çözüm ekle"""
    try:
        result = await service.add_solution(
            question_id=question_id,
            solution_data=solution.dict(),
            created_by=current_user.get("user_id", "unknown"),
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "Soru bulunamadı"),
            )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "data": {
                    "solution_id": result["solution_id"],
                    "question_id": question_id,
                },
                "message": "Alternatif çözüm başarıyla eklendi",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Çözüm ekleme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Çözüm ekleme hatası: {str(e)}",
        )


@router.get("/{question_id}/solutions", status_code=status.HTTP_200_OK)
async def get_alternative_solutions(
    question_id: str,
    service: AlternativeSolutionsService = Depends(get_solutions_service),
):
    """Sorunun tüm alternatif çözümlerini getir"""
    try:
        solutions = await service.get_solutions(question_id=question_id)

        if solutions is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "question_id": question_id,
                    "solutions": solutions,
                    "count": len(solutions),
                },
                "message": f"{len(solutions)} alternatif çözüm bulundu",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Çözüm getirme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Çözüm getirme hatası: {str(e)}",
        )


# ========================================================================
# TASK 73.4: Öğrenci Çözüm Paylaşımı
# ========================================================================


@router.get(
    "/{question_id}/solutions/student-submissions", status_code=status.HTTP_200_OK
)
async def get_student_submissions(
    question_id: str,
    sort_by: str = Query(
        "votes", description="Sıralama (votes, created_at, difficulty)"
    ),
    min_votes: int = Query(0, description="Minimum oy sayısı"),
    service: AlternativeSolutionsService = Depends(get_solutions_service),
):
    """
    Öğrenci tarafından gönderilen çözümleri getir

    **TASK 73.4 Özellikleri:**
    - User-submitted solutions (öğrenci çözümleri)
    - Peer review system entegrasyonu
    - Upvote/downvote mekanizması ile sıralama
    """
    try:
        submissions = await service.get_student_submissions(
            question_id=question_id,
            sort_by=sort_by,
            min_votes=min_votes,
        )

        if submissions is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "question_id": question_id,
                    "submissions": submissions,
                    "count": len(submissions),
                },
                "message": f"{len(submissions)} öğrenci çözümü bulundu",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Öğrenci çözümleri getirme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Öğrenci çözümleri getirme hatası: {str(e)}",
        )


@router.get(
    "/{question_id}/solutions/{solution_id}/reviews", status_code=status.HTTP_200_OK
)
async def get_solution_reviews(
    question_id: str,
    solution_id: str,
    service: AlternativeSolutionsService = Depends(get_solutions_service),
):
    """
    Çözümün peer review'larını getir (TASK 73.4)

    **Bilgiler:**
    - Tüm oy geçmişi
    - Yorumlar
    - Oy dağılımı
    - Review istatistikleri
    """
    try:
        reviews = await service.get_solution_reviews(
            question_id=question_id, solution_id=solution_id
        )

        if not reviews:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Çözüm bulunamadı veya review yok",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": reviews,
                "message": "Review'lar başarıyla getirildi",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Review getirme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Review getirme hatası: {str(e)}",
        )


@router.get("/{question_id}/solutions/top-rated", status_code=status.HTTP_200_OK)
async def get_top_rated_solutions(
    question_id: str,
    limit: int = Query(5, ge=1, le=20, description="Maksimum sonuç sayısı"),
    created_by_type: Optional[str] = Query(
        None, description="Oluşturan tipi filtresi (student, teacher, ai)"
    ),
    service: AlternativeSolutionsService = Depends(get_solutions_service),
):
    """
    En çok oy alan çözümleri getir (TASK 73.4)

    **Özellikler:**
    - Oy sayısına göre sıralı
    - Limit ile sonuç sayısı kontrolü
    - Oluşturan tipi filtresi
    """
    try:
        top_solutions = await service.get_top_rated_solutions(
            question_id=question_id,
            limit=limit,
            created_by_type=created_by_type,
        )

        if top_solutions is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Soru bulunamadı"
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "question_id": question_id,
                    "solutions": top_solutions,
                    "count": len(top_solutions),
                },
                "message": f"En iyi {len(top_solutions)} çözüm bulundu",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Top rated çözümler hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Top rated çözümler hatası: {str(e)}",
        )


@router.post(
    "/{question_id}/solutions/{solution_id}/vote", status_code=status.HTTP_200_OK
)
async def vote_solution(
    question_id: str,
    solution_id: str,
    vote: SolutionVote,
    current_user: Dict = Depends(get_current_user),
    service: AlternativeSolutionsService = Depends(get_solutions_service),
):
    """
    Çözüme oy ver (upvote/downvote) - TASK 73.4
    """
    try:
        result = await service.vote_solution(
            question_id=question_id,
            solution_id=solution_id,
            user_id=current_user.get("user_id", "unknown"),
            vote_type=vote.vote_type,
            comment=vote.comment,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Oy verilemedi"),
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "solution_id": solution_id,
                    "vote_type": vote.vote_type,
                    "total_votes": result.get("total_votes", 0),
                },
                "message": "Oy başarıyla kaydedildi",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Oylama hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Oylama hatası: {str(e)}",
        )


@router.delete(
    "/{question_id}/solutions/{solution_id}/vote", status_code=status.HTTP_200_OK
)
async def remove_vote(
    question_id: str,
    solution_id: str,
    current_user: Dict = Depends(get_current_user),
    service: AlternativeSolutionsService = Depends(get_solutions_service),
):
    """
    Verilen oyu geri çek - TASK 73.4
    """
    try:
        result = await service.remove_vote(
            question_id=question_id,
            solution_id=solution_id,
            user_id=current_user.get("user_id", "unknown"),
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Oy geri çekilemedi"),
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "solution_id": solution_id,
                    "total_votes": result.get("total_votes", 0),
                },
                "message": "Oy başarıyla geri çekildi",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Oy geri çekme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Oy geri çekme hatası: {str(e)}",
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """API sağlık kontrolü"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "data": {
                "service": "Alternative Solutions API",
                "status": "healthy",
                "version": "1.0.0",
                "features": [
                    "Multiple Solution Storage (Task 73.1)",
                    "Solution Categorization (Task 73.1)",
                    "Difficulty Comparison (Task 73.1)",
                    "Solution Comparison (Task 73.2)",
                    "Fastest Solution (Task 73.3)",
                    "Student Submissions (Task 73.4)",
                    "Peer Review System (Task 73.4)",
                    "Upvote/Downvote Mechanism (Task 73.4)",
                ],
            },
            "message": "Alternative Solutions API çalışıyor - Task 73.4 tamamlandı",
        },
    )
