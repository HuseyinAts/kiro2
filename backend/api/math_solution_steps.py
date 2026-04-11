"""
Matematik Adım Adım Çözüm API Endpoints
Requirements: REQ-51.21-51.40 (Diskalkuli Desteği - Adım Adım Çözüm)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.dependencies import (
    AuthenticatedUser,
    UserRole,
    get_current_admin_user,
    get_current_user,
)
from services.math_solution_step_service import (
    DifficultyLevel,
    math_solution_step_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/math-solution-steps", tags=["Math Solution Steps"])


def _verify_student_access(current_user: AuthenticatedUser, student_id: str) -> None:
    """IDOR: student own data only, admin/teacher any."""
    if current_user.role in (
        UserRole.ADMIN,
        UserRole.TEACHER,
        UserRole.SUPER_ADMIN,
    ):
        return
    if str(current_user.id) != student_id:
        raise HTTPException(
            status_code=403,
            detail="Bu ogrenci verisine erisim yetkiniz yok",
        )


# Request/Response Models
class GenerateSolutionRequest(BaseModel):
    """Çözüm oluşturma isteği"""

    problem_id: str = Field(..., description="Problem ID'si")
    problem_statement: str = Field(
        ..., min_length=1, max_length=1000, description="Problem ifadesi"
    )
    problem_type: str = Field(
        ...,
        description="Problem türü (linear_equation, quadratic_equation, fraction_operations, etc.)",
    )
    difficulty_level: str = Field(
        "medium", description="Zorluk seviyesi (easy, medium, hard, very_hard)"
    )


class GetStepRequest(BaseModel):
    """Adım getirme isteği"""

    problem_id: str = Field(..., description="Problem ID'si")
    step_number: int = Field(..., ge=1, description="Adım numarası")


class GetHintRequest(BaseModel):
    """İpucu getirme isteği"""

    problem_id: str = Field(..., description="Problem ID'si")
    step_number: int = Field(..., ge=1, description="Adım numarası")
    hint_level: int = Field(
        1, ge=1, le=3, description="İpucu seviyesi (1: hafif, 2: orta, 3: detaylı)"
    )


class CheckAnswerRequest(BaseModel):
    """Cevap kontrol isteği"""

    student_id: str = Field(..., description="Öğrenci ID'si")
    problem_id: str = Field(..., description="Problem ID'si")
    step_number: int = Field(..., ge=1, description="Adım numarası")
    student_answer: str = Field(..., description="Öğrenci cevabı")
    correct_answer: str = Field(..., description="Doğru cevap")


@router.post("/generate")
async def generate_solution(
    request: GenerateSolutionRequest,
    _current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Matematik problemi için adım adım çözüm oluştur

    Bu endpoint:
    - Problem türüne göre adım adım çözüm oluşturur
    - Her adım için açıklama, ipucu ve yaygın hataları içerir
    - Görsel yardımcılar ve renk kodlama sağlar
    - Progressive disclosure için optimize edilmiştir

    Requirements: REQ-51.21-51.25
    """
    try:
        logger.info(f"Generating solution for problem: {request.problem_id}")

        # Zorluk seviyesini enum'a çevir
        try:
            difficulty = DifficultyLevel(request.difficulty_level)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Geçersiz zorluk seviyesi: {request.difficulty_level}. Geçerli değerler: easy, medium, hard, very_hard",
            )

        # Çözüm oluştur
        solution = math_solution_step_service.generate_solution(
            problem_id=request.problem_id,
            problem_statement=request.problem_statement,
            problem_type=request.problem_type,
            difficulty_level=difficulty,
        )

        return {
            "success": True,
            "message": f"{len(solution.steps)} adımlı çözüm oluşturuldu",
            "data": solution.to_dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Solution generation error: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/solution/{problem_id}")
async def get_solution(problem_id: str):
    """
    Belirli bir problem için tam çözümü getir

    Bu endpoint:
    - Daha önce oluşturulmuş çözümü cache'den getirir
    - Tüm adımları ve detayları içerir
    - Progressive disclosure için kullanılabilir

    Requirements: REQ-51.21-51.25
    """
    try:
        logger.info(f"Getting solution for problem: {problem_id}")

        # Cache'den çözümü al
        solution = math_solution_step_service.solutions_cache.get(problem_id)

        if not solution:
            raise HTTPException(
                status_code=404,
                detail=f"Problem bulunamadı: {problem_id}. Önce /generate endpoint'ini kullanın.",
            )

        return {
            "success": True,
            "message": "Çözüm getirildi",
            "data": solution.to_dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get solution error: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/step/{problem_id}/{step_number}")
async def get_step(problem_id: str, step_number: int):
    """
    Belirli bir adımı getir

    Bu endpoint:
    - Tek bir adımın detaylarını getirir
    - Progressive disclosure için kullanılır
    - Adım navigasyonu için optimize edilmiştir

    Requirements: REQ-51.21-51.25
    """
    try:
        logger.info(f"Getting step {step_number} for problem: {problem_id}")

        step = math_solution_step_service.get_step(problem_id, step_number)

        if not step:
            raise HTTPException(
                status_code=404,
                detail=f"Adım bulunamadı: Problem {problem_id}, Adım {step_number}",
            )

        return {
            "success": True,
            "message": f"Adım {step_number} getirildi",
            "data": step.to_dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get step error: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/hint")
async def get_hint(
    request: GetHintRequest,
    student_id: str | None = None,
    _current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Belirli bir adım için ipucu getir

    Bu endpoint:
    - 3 seviyeli ipucu sistemi sağlar (hafif, orta, detaylı)
    - Kademeli yardım için kullanılır
    - İpucu kullanımını takip eder

    Requirements: REQ-51.31-51.35
    """
    try:
        logger.info(
            f"Getting hint level {request.hint_level} for problem: {request.problem_id}, step: {request.step_number}"
        )

        hint = math_solution_step_service.get_hint(
            problem_id=request.problem_id,
            step_number=request.step_number,
            hint_level=request.hint_level,
        )

        if not hint:
            raise HTTPException(
                status_code=404,
                detail=f"İpucu bulunamadı: Problem {request.problem_id}, Adım {request.step_number}, Seviye {request.hint_level}",
            )

        # İpucu kullanımını kaydet (student_id varsa)
        if student_id:
            from services.hint_tracking_service import hint_tracking_service

            hint_tracking_service.track_hint_usage(
                student_id=student_id,
                problem_id=request.problem_id,
                step_number=request.step_number,
                hint_level=request.hint_level,
            )

        # İpucu seviye açıklamaları
        hint_level_names = {
            1: "Hafif İpucu (Genel Yönlendirme)",
            2: "Orta İpucu (Spesifik Yönlendirme)",
            3: "Detaylı İpucu (Neredeyse Tam Çözüm)",
        }

        return {
            "success": True,
            "message": f"İpucu seviye {request.hint_level} getirildi",
            "data": {
                "hint": hint,
                "hint_level": request.hint_level,
                "hint_level_name": hint_level_names.get(
                    request.hint_level, "Bilinmeyen"
                ),
                "problem_id": request.problem_id,
                "step_number": request.step_number,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get hint error: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/navigation/{problem_id}")
async def get_navigation_info(problem_id: str):
    """
    Problem için navigasyon bilgilerini getir

    Bu endpoint:
    - Toplam adım sayısını döner
    - İleri/geri navigasyon için kullanılır
    - Progress tracking için bilgi sağlar

    Requirements: REQ-51.21-51.25
    """
    try:
        logger.info(f"Getting navigation info for problem: {problem_id}")

        solution = math_solution_step_service.solutions_cache.get(problem_id)

        if not solution:
            raise HTTPException(
                status_code=404, detail=f"Problem bulunamadı: {problem_id}"
            )

        return {
            "success": True,
            "message": "Navigasyon bilgileri getirildi",
            "data": {
                "problem_id": problem_id,
                "total_steps": len(solution.steps),
                "total_duration_estimate_seconds": solution.total_duration_estimate_seconds,
                "difficulty_level": solution.difficulty_level.value,
                "problem_type": solution.problem_type,
                "step_numbers": [step.step_number for step in solution.steps],
                "step_titles": [step.title for step in solution.steps],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get navigation info error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.delete("/cache")
async def clear_cache(
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
):
    """
    Çözüm cache'ini temizle (admin only)

    Bu endpoint:
    - Tüm cache'lenmiş çözümleri siler
    - Test ve development için kullanılır
    """
    try:
        logger.info("Clearing solution cache")

        math_solution_step_service.clear_cache()

        return {"success": True, "message": "Cache temizlendi"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear cache error: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/hint-stats/{student_id}")
async def get_hint_statistics(
    student_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Öğrencinin ipucu kullanım istatistiklerini getir

    Bu endpoint:
    - Toplam ipucu kullanımını gösterir
    - Seviye bazlı dağılımı verir
    - Bağımlılık skorunu hesaplar

    Requirements: REQ-51.35
    """
    _verify_student_access(current_user, student_id)
    try:
        from services.hint_tracking_service import hint_tracking_service

        logger.info(f"Getting hint stats for student: {student_id}")

        stats = hint_tracking_service.get_student_stats(student_id)

        if not stats:
            return {
                "success": True,
                "message": "Henüz ipucu kullanımı yok",
                "data": {
                    "student_id": student_id,
                    "total_hints_used": 0,
                    "hints_by_level": {1: 0, 2: 0, 3: 0},
                    "problems_with_hints": [],
                    "average_hint_level": 0.0,
                    "hint_dependency_score": 0.0,
                },
            }

        return {
            "success": True,
            "message": "İstatistikler getirildi",
            "data": stats.to_dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get hint stats error: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/hint-trends/{student_id}")
async def get_hint_trends(
    student_id: str,
    limit: int = 10,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Öğrencinin ipucu kullanım trendlerini analiz et

    Bu endpoint:
    - Son N problemdeki ipucu kullanımını analiz eder
    - Trend belirler (high/moderate/low dependency)
    - Öneriler sunar

    Requirements: REQ-51.35
    """
    _verify_student_access(current_user, student_id)
    try:
        from services.hint_tracking_service import hint_tracking_service

        logger.info(f"Getting hint trends for student: {student_id}")

        trends = hint_tracking_service.get_hint_usage_trends(student_id, limit)

        return {"success": True, "message": "Trend analizi tamamlandı", "data": trends}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get hint trends error: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/check-answer")
async def check_answer(
    request: CheckAnswerRequest,
    _current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Öğrenci cevabını kontrol et ve hata varsa tespit et

    Bu endpoint:
    - Cevabın doğruluğunu kontrol eder
    - Hata varsa türünü belirler
    - Düzeltici öneriler sunar
    - Tekrarlayan hataları takip eder

    Requirements: REQ-51.36-51.40
    """
    try:
        from services.error_detection_service import error_detection_service

        logger.info(
            f"Checking answer for student {request.student_id}, "
            f"problem {request.problem_id}, step {request.step_number}"
        )

        # Hata tespiti
        error = error_detection_service.detect_error(
            student_answer=request.student_answer, correct_answer=request.correct_answer
        )

        if error:
            # Hatayı kaydet
            error_detection_service.track_student_error(
                student_id=request.student_id, error=error
            )

            return {
                "success": True,
                "is_correct": False,
                "message": "Cevap yanlış - Hata tespit edildi",
                "data": {
                    "error": error.to_dict(),
                    "student_answer": request.student_answer,
                    "correct_answer": request.correct_answer,
                },
            }
        return {
            "success": True,
            "is_correct": True,
            "message": "Cevap doğru! 🎉",
            "data": {
                "student_answer": request.student_answer,
                "correct_answer": request.correct_answer,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Check answer error: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/error-analysis/{student_id}")
async def get_error_analysis(
    student_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Öğrencinin hata analizini getir

    Bu endpoint:
    - Tekrarlayan hataları listeler
    - Hata türlerine göre dağılım verir
    - Özel öneriler sunar

    Requirements: REQ-51.40
    """
    _verify_student_access(current_user, student_id)
    try:
        from services.error_detection_service import error_detection_service

        logger.info(f"Getting error analysis for student: {student_id}")

        # Tekrarlayan hataları al
        recurring_errors = error_detection_service.get_recurring_errors(student_id)

        # Önerileri al
        suggestions = error_detection_service.get_error_suggestions(student_id)

        return {
            "success": True,
            "message": "Hata analizi tamamlandı",
            "data": {
                "student_id": student_id,
                "recurring_errors": [
                    {"error_type": error_type.value, "count": count}
                    for error_type, count in recurring_errors
                ],
                "suggestions": suggestions,
                "total_errors": len(
                    error_detection_service.student_error_history.get(student_id, [])
                ),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get error analysis error: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/health")
async def health_check():
    """
    Matematik çözüm sistemi sağlık kontrolü
    """
    try:
        cache_size = len(math_solution_step_service.solutions_cache)

        return {
            "success": True,
            "message": "Matematik çözüm sistemi çalışıyor",
            "data": {
                "system_status": "healthy",
                "cached_solutions": cache_size,
                "supported_problem_types": [
                    "linear_equation",
                    "quadratic_equation",
                    "fraction_operations",
                    "generic",
                ],
            },
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "success": False,
            "message": "Sistem hatasi. Lutfen tekrar deneyin.",
            "data": {"system_status": "unhealthy"},
        }
