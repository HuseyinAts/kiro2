"""
Müfredat Uyumluluk API Endpoints
MEB ve ÖSYM müfredat uyumluluk yönetimi için REST API
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from core.curriculum_compliance_system import CurriculumComplianceSystem
from core.dependencies import get_cache_service, get_database_service
from models.curriculum import (
    CurriculumUpdateRequest,
    ExamType,
    GradeLevel,
    MEBCurriculumStandard,
    OSYMStandard,
    SubjectType,
)

logger = logging.getLogger(__name__)

# Router oluştur
router = APIRouter(prefix="/api/v1/curriculum", tags=["Müfredat Uyumluluk"])

# Curriculum Compliance System instance
curriculum_system = None


async def get_curriculum_system():
    """Curriculum Compliance System dependency"""
    global curriculum_system
    if curriculum_system is None:
        db_service = await get_database_service()
        cache_service = await get_cache_service()
        curriculum_system = CurriculumComplianceSystem(db_service, cache_service)
        await curriculum_system.initialize()
    return curriculum_system


# MEB Müfredat Standartları Endpoints


@router.post("/meb/standards", response_model=dict[str, Any])
async def add_meb_standard(
    standard: MEBCurriculumStandard,
    system: CurriculumComplianceSystem = Depends(get_curriculum_system),
):
    """
    MEB müfredat standardı ekle

    Gereksinim 3.1: MEB müfredat standartlarına uygun konular
    """
    try:
        success = await system.add_meb_standard(standard)

        if success:
            return {
                "success": True,
                "message": "MEB standardı başarıyla eklendi",
                "data": {
                    "standard_id": standard.id,
                    "topic_name": standard.topic_name,
                    "subject": standard.subject,
                    "grade_level": standard.grade_level,
                },
            }
        raise HTTPException(
            status_code=400, detail="MEB standardı eklenirken hata oluştu"
        )

    except Exception as e:
        logger.error(f"MEB standardı ekleme API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/meb/standards/{subject}", response_model=dict[str, Any])
async def get_meb_standards_by_subject(
    subject: SubjectType = Path(..., description="Ders türü"),
    grade_level: GradeLevel | None = Query(None, description="Sınıf seviyesi"),
    system: CurriculumComplianceSystem = Depends(get_curriculum_system),
):
    """
    Derse göre MEB standartlarını getir
    """
    try:
        standards = await system.get_meb_standards_by_subject(subject, grade_level)

        return {
            "success": True,
            "message": f"{subject} dersi için MEB standartları getirildi",
            "data": {
                "subject": subject,
                "grade_level": grade_level,
                "standards_count": len(standards),
                "standards": [
                    {
                        "id": std.id,
                        "topic_name": std.topic_name,
                        "unit_name": std.unit_name,
                        "learning_outcomes_count": len(std.learning_outcomes),
                        "duration_hours": std.duration_hours,
                    }
                    for std in standards
                ],
            },
        }

    except Exception as e:
        logger.error(f"MEB standartları getirme API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/meb/learning-outcomes/{standard_id}", response_model=dict[str, Any])
async def get_learning_outcomes(
    standard_id: str = Path(..., description="MEB standardı ID"),
    system: CurriculumComplianceSystem = Depends(get_curriculum_system),
):
    """
    Öğrenme kazanımlarını getir

    Gereksinim 3.3: MEB'in belirlediği kazanımlarla eşleşme
    """
    try:
        outcomes = await system.get_learning_outcomes(standard_id)

        return {
            "success": True,
            "message": "Öğrenme kazanımları getirildi",
            "data": {
                "standard_id": standard_id,
                "outcomes_count": len(outcomes),
                "outcomes": [
                    {
                        "id": outcome.id,
                        "code": outcome.code,
                        "description": outcome.description,
                        "cognitive_level": outcome.cognitive_level,
                        "bloom_taxonomy": outcome.bloom_taxonomy,
                    }
                    for outcome in outcomes
                ],
            },
        }

    except Exception as e:
        logger.error(f"Öğrenme kazanımları getirme API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# ÖSYM Standartları Endpoints


@router.post("/osym/standards", response_model=dict[str, Any])
async def add_osym_standard(
    standard: OSYMStandard,
    system: CurriculumComplianceSystem = Depends(get_curriculum_system),
):
    """ÖSYM sınav standardı ekle"""
    try:
        success = await system.add_osym_standard(standard)

        if success:
            return {
                "success": True,
                "message": "ÖSYM standardı başarıyla eklendi",
                "data": {
                    "standard_id": standard.id,
                    "topic_name": standard.topic_name,
                    "exam_type": standard.exam_type,
                    "priority_level": standard.priority_level,
                },
            }
        raise HTTPException(
            status_code=400, detail="ÖSYM standardı eklenirken hata oluştu"
        )

    except Exception as e:
        logger.error(f"ÖSYM standardı ekleme API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/osym/standards/{exam_type}", response_model=dict[str, Any])
async def get_osym_standards_by_priority(
    exam_type: ExamType = Path(..., description="Sınav türü"),
    subject: SubjectType | None = Query(None, description="Ders türü"),
    system: CurriculumComplianceSystem = Depends(get_curriculum_system),
):
    """
    ÖSYM standartlarını öncelik sırasına göre getir

    Gereksinim 3.5: ÖSYM'nin belirlediği öncelik sırası
    """
    try:
        standards = await system.get_osym_standards_by_priority(exam_type, subject)

        return {
            "success": True,
            "message": f"{exam_type} sınavı için ÖSYM standartları getirildi",
            "data": {
                "exam_type": exam_type,
                "subject": subject,
                "standards_count": len(standards),
                "standards": [
                    {
                        "id": std.id,
                        "topic_name": std.topic_name,
                        "topic_code": std.topic_code,
                        "priority_level": std.priority_level,
                        "exam_frequency": std.exam_frequency,
                        "question_count_range": std.question_count_range,
                    }
                    for std in standards
                ],
            },
        }

    except Exception as e:
        logger.error(f"ÖSYM standartları getirme API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Uyumluluk Analizi Endpoints


@router.post("/alignment/analyze", response_model=dict[str, Any])
async def analyze_curriculum_alignment(
    subject: SubjectType = Query(..., description="Ders türü"),
    exam_type: ExamType = Query(..., description="Sınav türü"),
    system: CurriculumComplianceSystem = Depends(get_curriculum_system),
):
    """MEB ve ÖSYM standartları arasında uyumluluk analizi yap"""
    try:
        alignment = await system.analyze_curriculum_alignment(subject, exam_type)

        if alignment:
            return {
                "success": True,
                "message": "Uyumluluk analizi tamamlandı",
                "data": {
                    "alignment_id": alignment.id,
                    "subject": subject,
                    "exam_type": exam_type,
                    "alignment_score": alignment.alignment_score,
                    "alignment_type": alignment.alignment_type,
                    "gaps_count": len(alignment.gaps_identified),
                    "gaps_identified": alignment.gaps_identified,
                    "recommendations_count": len(alignment.recommendations),
                    "recommendations": alignment.recommendations,
                    "created_at": alignment.created_at.isoformat(),
                },
            }
        raise HTTPException(status_code=400, detail="Uyumluluk analizi yapılamadı")

    except Exception as e:
        logger.error(f"Uyumluluk analizi API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Soru Bankası Uyumluluk Endpoints


@router.get(
    "/question-bank/compliance/{subject}/{topic_id}", response_model=dict[str, Any]
)
async def validate_question_bank_compliance(
    subject: SubjectType = Path(..., description="Ders türü"),
    topic_id: str = Path(..., description="Konu ID"),
    system: CurriculumComplianceSystem = Depends(get_curriculum_system),
):
    """
    Soru bankası uyumluluk kontrolü

    Gereksinim 3.2: Her konu için en az 1000 ÖSYM tarzı soru
    """
    try:
        compliance = await system.validate_question_bank_compliance(subject, topic_id)

        if compliance:
            return {
                "success": True,
                "message": "Soru bankası uyumluluk kontrolü tamamlandı",
                "data": {
                    "compliance_id": compliance.id,
                    "subject": subject,
                    "topic_id": topic_id,
                    "total_questions": compliance.total_questions,
                    "osym_format_questions": compliance.osym_format_questions,
                    "meb_aligned_questions": compliance.meb_aligned_questions,
                    "minimum_required": compliance.minimum_required,
                    "compliance_score": compliance.compliance_score,
                    "compliance_status": compliance.compliance_status,
                    "difficulty_distribution": compliance.difficulty_distribution,
                    "meets_requirement": compliance.total_questions
                    >= compliance.minimum_required,
                    "next_review_date": compliance.next_review_date.isoformat(),
                },
            }
        raise HTTPException(
            status_code=400, detail="Soru bankası uyumluluk kontrolü yapılamadı"
        )

    except Exception as e:
        logger.error(f"Soru bankası uyumluluk API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Uyumluluk Raporlama Endpoints


@router.get("/reports/compliance", response_model=dict[str, Any])
async def generate_compliance_report(
    subject: SubjectType | None = Query(None, description="Ders türü"),
    exam_type: ExamType | None = Query(None, description="Sınav türü"),
    system: CurriculumComplianceSystem = Depends(get_curriculum_system),
):
    """Kapsamlı uyumluluk raporu oluştur"""
    try:
        report = await system.generate_compliance_report(subject, exam_type)

        if report:
            return {
                "success": True,
                "message": "Uyumluluk raporu oluşturuldu",
                "data": {
                    "report_id": report.id,
                    "report_type": report.report_type,
                    "subject": report.subject,
                    "exam_type": report.exam_type,
                    "overall_compliance_score": report.overall_compliance_score,
                    "meb_compliance_score": report.meb_compliance_score,
                    "osym_compliance_score": report.osym_compliance_score,
                    "compliant_topics_count": len(report.compliant_topics),
                    "compliant_topics": report.compliant_topics,
                    "non_compliant_topics_count": len(report.non_compliant_topics),
                    "non_compliant_topics": report.non_compliant_topics,
                    "missing_topics_count": len(report.missing_topics),
                    "missing_topics": report.missing_topics,
                    "question_bank_status": {
                        topic: {
                            "total_questions": status.total_questions,
                            "compliance_score": status.compliance_score,
                            "compliance_status": status.compliance_status,
                        }
                        for topic, status in report.question_bank_status.items()
                    },
                    "recommendations": report.recommendations,
                    "priority_actions": report.priority_actions,
                    "generated_at": report.generated_at.isoformat(),
                    "generated_by": report.generated_by,
                },
            }
        raise HTTPException(status_code=400, detail="Uyumluluk raporu oluşturulamadı")

    except Exception as e:
        logger.error(f"Uyumluluk raporu API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Müfredat Güncelleme Endpoints


@router.post("/updates/request", response_model=dict[str, Any])
async def handle_curriculum_update(
    update_request: CurriculumUpdateRequest,
    system: CurriculumComplianceSystem = Depends(get_curriculum_system),
):
    """
    Müfredat güncelleme talebini işle

    Gereksinim 3.4: Müfredat güncellendiğinde sistem uyum sağlamalı
    """
    try:
        success = await system.handle_curriculum_update(update_request)

        if success:
            return {
                "success": True,
                "message": "Müfredat güncelleme talebi başarıyla işlendi",
                "data": {
                    "update_id": update_request.id,
                    "update_type": update_request.update_type,
                    "subject": update_request.subject,
                    "affected_standards_count": len(update_request.affected_standards),
                    "requested_by": update_request.requested_by,
                    "requested_at": update_request.requested_at.isoformat(),
                    "status": "processed",
                },
            }
        raise HTTPException(
            status_code=400, detail="Müfredat güncelleme talebi işlenemedi"
        )

    except Exception as e:
        logger.error(f"Müfredat güncelleme API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Sistem Durumu Endpoints


@router.get("/status", response_model=dict[str, Any])
async def get_compliance_system_status(
    system: CurriculumComplianceSystem = Depends(get_curriculum_system),
):
    """Müfredat uyumluluk sistemi durumunu getir"""
    try:
        summary = await system.get_compliance_summary()

        return {"success": True, "message": "Sistem durumu getirildi", "data": summary}

    except Exception as e:
        logger.error(f"Sistem durumu API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/health", response_model=dict[str, Any])
async def curriculum_compliance_health_check():
    """Müfredat uyumluluk sistemi sağlık kontrolü"""
    try:
        return {
            "success": True,
            "message": "Müfredat uyumluluk sistemi çalışıyor",
            "data": {
                "service": "curriculum_compliance",
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
            },
        }

    except Exception as e:
        logger.error(f"Sağlık kontrolü API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Toplu İşlemler


@router.post("/bulk/validate-all-subjects", response_model=dict[str, Any])
async def validate_all_subjects_compliance(
    system: CurriculumComplianceSystem = Depends(get_curriculum_system),
):
    """Tüm dersler için uyumluluk kontrolü yap"""
    try:
        results = {}

        # Her ders için uyumluluk kontrolü
        for subject in SubjectType:
            try:
                report = await system.generate_compliance_report(subject)
                if report:
                    results[subject.value] = {
                        "overall_score": report.overall_compliance_score,
                        "meb_score": report.meb_compliance_score,
                        "osym_score": report.osym_compliance_score,
                        "status": "completed",
                    }
                else:
                    results[subject.value] = {
                        "status": "failed",
                        "error": "Rapor oluşturulamadı",
                    }
            except Exception as e:
                logger.error(f"Curriculum compliance error for {subject.value}: {e}")
                results[subject.value] = {
                    "status": "error",
                    "error": "Analiz basarisiz",
                }

        return {
            "success": True,
            "message": "Toplu uyumluluk kontrolü tamamlandı",
            "data": {
                "validation_results": results,
                "completed_at": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"Toplu uyumluluk kontrolü API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/statistics/overview", response_model=dict[str, Any])
async def get_curriculum_statistics(
    system: CurriculumComplianceSystem = Depends(get_curriculum_system),
):
    """Müfredat uyumluluk istatistikleri getir"""
    try:
        summary = await system.get_compliance_summary()

        # Ek istatistikler hesapla
        statistics = {
            "total_meb_standards": summary.get("meb_standards_count", 0),
            "total_osym_standards": summary.get("osym_standards_count", 0),
            "total_alignments": summary.get("alignments_count", 0),
            "system_status": summary.get("system_status", "unknown"),
            "last_updated": summary.get("last_updated"),
            "subjects_covered": len(SubjectType),
            "exam_types_supported": len(ExamType),
            "grade_levels_supported": len(GradeLevel),
        }

        return {
            "success": True,
            "message": "Müfredat uyumluluk istatistikleri getirildi",
            "data": statistics,
        }

    except Exception as e:
        logger.error(f"İstatistikler API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )
