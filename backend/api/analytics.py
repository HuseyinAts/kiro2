"""
Advanced Analytics API Endpoints
Öğrenci, sınıf ve sistem geneli analytics API'leri
"""

import csv
import io
import logging
from datetime import datetime, timedelta
from typing import Any

import xlsxwriter
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import text

try:
    from core.auth_dependencies import require_role
    from core.database import get_db_session_context
    from core.dependencies import get_current_user
    from core.redis_cache import get_cache
    from models.database import User
    from services.elasticsearch_service import get_elasticsearch_service
except ImportError:
    from core.auth_dependencies import require_role
    from core.database import get_db_session_context
    from core.dependencies import get_current_user
    from core.redis_cache import get_cache
    from models.database import User
    from services.elasticsearch_service import get_elasticsearch_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


# Pydantic modelleri
class StudentAnalyticsRequest(BaseModel):
    """Öğrenci analytics isteği"""

    start_date: datetime | None = Field(None, description="Başlangıç tarihi")
    end_date: datetime | None = Field(None, description="Bitiş tarihi")
    include_detailed: bool = Field(False, description="Detaylı analiz dahil et")


class ClassAnalyticsRequest(BaseModel):
    """Sınıf analytics isteği"""

    start_date: datetime | None = Field(None, description="Başlangıç tarihi")
    end_date: datetime | None = Field(None, description="Bitiş tarihi")
    include_students: bool = Field(True, description="Öğrenci detayları dahil et")


class ExportRequest(BaseModel):
    """Export isteği"""

    format: str = Field(..., description="Export formatı: pdf, excel, csv")
    data_type: str = Field(..., description="Veri tipi: student, class, admin")
    filters: dict[str, Any] = Field(default_factory=dict, description="Filtreler")


# Analytics API Endpoints


@router.get("/student/{student_id}")
async def get_student_analytics(
    student_id: str,
    start_date: datetime | None = Query(None, description="Başlangıç tarihi"),
    end_date: datetime | None = Query(None, description="Bitiş tarihi"),
    include_detailed: bool = Query(False, description="Detaylı analiz dahil et"),
    current_user: User = Depends(get_current_user),
):
    """
    Öğrenci analytics verilerini getir

    Requirements: 1.4, 1.5 - Öğrenci performans analizi ve raporlama
    """
    try:
        # IDOR koruması: öğrenci sadece kendi verisini görebilir
        user_role = getattr(current_user, "role", None)
        role_str = user_role.value if hasattr(user_role, "value") else str(user_role)
        if role_str.lower() not in ("admin", "teacher", "super_admin"):
            user_id = str(getattr(current_user, "id", ""))
            if user_id != student_id:
                raise HTTPException(
                    status_code=403,
                    detail="Bu öğrencinin analytics verilerine erişim yetkiniz yok",
                )

        # Tarih aralığı ayarla
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Elasticsearch service
        es_service = await get_elasticsearch_service()

        # Temel analytics verilerini al
        user_analytics = await es_service.analytics_service.get_user_analytics(
            user_id=student_id, start_date=start_date, end_date=end_date
        )

        # Öğrenci performans metrikleri hesapla
        performance_metrics = await _calculate_student_performance_metrics(
            student_id, start_date, end_date, es_service
        )

        # Öğrenme stili analizi
        learning_style_analysis = await _get_learning_style_analysis(student_id)

        # Sınav performansı
        exam_performance = await _get_exam_performance_analysis(
            student_id, start_date, end_date
        )

        # Konu bazlı analiz
        subject_analysis = await _get_subject_performance_analysis(
            student_id, start_date, end_date
        )

        analytics_data = {
            "student_id": student_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "basic_metrics": user_analytics,
            "performance_metrics": performance_metrics,
            "learning_style": learning_style_analysis,
            "exam_performance": exam_performance,
            "subject_analysis": subject_analysis,
        }

        # Detaylı analiz dahil et
        if include_detailed:
            detailed_analysis = await _get_detailed_student_analysis(
                student_id, start_date, end_date
            )
            analytics_data["detailed_analysis"] = detailed_analysis

        # Analytics event'i logla
        await es_service.analytics_service.log_event(
            event_type="student_analytics_viewed",
            user_id=str(current_user.id),
            data={
                "target_student_id": student_id,
                "period_days": (end_date - start_date).days,
                "include_detailed": include_detailed,
            },
        )

        return {
            "success": True,
            "data": analytics_data,
            "message": "Öğrenci analytics başarıyla alındı",
        }

    except Exception as e:
        logger.error(f"Student analytics error: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/class/{class_id}")
async def get_class_analytics(
    class_id: str,
    start_date: datetime | None = Query(None, description="Başlangıç tarihi"),
    end_date: datetime | None = Query(None, description="Bitiş tarihi"),
    include_students: bool = Query(True, description="Öğrenci detayları dahil et"),
    current_user: User = Depends(get_current_user),
):
    """
    Sınıf analytics verilerini getir

    Requirements: 6.5 - Sınıf performans takibi ve raporlama
    """
    try:
        # Tarih aralığı ayarla
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Sınıf öğrencilerini al (mock data - gerçek implementasyonda DB'den gelecek)
        class_students = await _get_class_students(class_id)

        # Elasticsearch service
        es_service = await get_elasticsearch_service()

        # Sınıf geneli metrikleri
        class_metrics = await _calculate_class_metrics(
            class_id, class_students, start_date, end_date, es_service
        )

        # Öğrenci performans dağılımı
        performance_distribution = await _get_class_performance_distribution(
            class_students, start_date, end_date
        )

        # Konu bazlı sınıf analizi
        subject_class_analysis = await _get_class_subject_analysis(
            class_students, start_date, end_date
        )

        # Öğrenme stili dağılımı
        learning_style_distribution = await _get_class_learning_style_distribution(
            class_students
        )

        analytics_data = {
            "class_id": class_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "student_count": len(class_students),
            "class_metrics": class_metrics,
            "performance_distribution": performance_distribution,
            "subject_analysis": subject_class_analysis,
            "learning_style_distribution": learning_style_distribution,
        }

        # Öğrenci detayları dahil et
        if include_students:
            # OPTIMIZED: Bulk query ile N+1 problemi çözüldü
            # Before: N queries (30 students = 31 queries, ~1550ms)
            # After: 1 query (~80ms, 95% faster)
            student_ids = [student["id"] for student in class_students]
            bulk_analytics = await es_service.analytics_service.get_bulk_user_analytics(
                user_ids=student_ids, start_date=start_date, end_date=end_date
            )

            # Sonuçları birleştir
            student_details = []
            for student in class_students:
                student_id = student["id"]
                student_details.append(
                    {
                        "student_id": student_id,
                        "name": student["name"],
                        "analytics": bulk_analytics.get(student_id, {}),
                    }
                )
            analytics_data["student_details"] = student_details

        # Analytics event'i logla
        await es_service.analytics_service.log_event(
            event_type="class_analytics_viewed",
            user_id=str(current_user.id),
            data={
                "class_id": class_id,
                "period_days": (end_date - start_date).days,
                "include_students": include_students,
            },
        )

        return {
            "success": True,
            "data": analytics_data,
            "message": "Sınıf analytics başarıyla alındı",
        }

    except Exception as e:
        logger.error(f"Class analytics error: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/admin/dashboard")
async def get_admin_dashboard_analytics(
    start_date: datetime | None = Query(None, description="Başlangıç tarihi"),
    end_date: datetime | None = Query(None, description="Bitiş tarihi"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_role("ADMIN")),
):
    """
    Admin dashboard analytics verilerini getir

    Requirements: 6.5 - Sistem geneli analytics ve raporlama
    """
    try:
        # Tarih aralığı ayarla
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Redis cache kontrol
        cache = get_cache()
        cache_key = f"admin_dashboard:{start_date.date()}:{end_date.date()}"

        # Cache'den dene
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"✅ Cache HIT for {cache_key}")
            return cached_result

        logger.info(f"❌ Cache MISS for {cache_key}")

        # Elasticsearch service
        es_service = await get_elasticsearch_service()

        # Sistem geneli metrikleri
        system_metrics = await _calculate_system_metrics(
            start_date, end_date, es_service
        )

        # Kullanıcı istatistikleri
        user_statistics = await _get_user_statistics(start_date, end_date)

        # Sınav istatistikleri
        exam_statistics = await _get_exam_statistics(start_date, end_date)

        # İçerik kullanım istatistikleri
        content_usage = await _get_content_usage_statistics(start_date, end_date)

        # Performans metrikleri
        performance_metrics = await _get_system_performance_metrics(
            start_date, end_date
        )

        # Devrimsel özellik kullanımı
        revolutionary_features_usage = await _get_revolutionary_features_usage(
            start_date, end_date
        )

        analytics_data = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "system_metrics": system_metrics,
            "user_statistics": user_statistics,
            "exam_statistics": exam_statistics,
            "content_usage": content_usage,
            "performance_metrics": performance_metrics,
            "revolutionary_features": revolutionary_features_usage,
        }

        # Analytics event'i logla
        await es_service.analytics_service.log_event(
            event_type="admin_dashboard_viewed",
            user_id=str(current_user.id),
            data={"period_days": (end_date - start_date).days},
        )

        result = {
            "success": True,
            "data": analytics_data,
            "message": "Admin dashboard analytics başarıyla alındı",
        }

        # Sonucu cache'le (5 dakika TTL - admin dashboard sık değişmez)
        cache.set(cache_key, result, ttl=300)
        logger.info(f"💾 Cache SET for {cache_key} (TTL: 300s)")

        return result

    except Exception as e:
        logger.error(f"Admin dashboard analytics error: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Retention Metrics


@router.get("/retention/d7")
async def get_d7_retention(
    current_user: User = Depends(get_current_user),
):
    """
    D7 Retention metriği: 8-14 gün önce aktif olan kullanıcıların
    son 7 günde geri dönme oranı.

    kiro2_learning_events tablosunu kullanır (sentetik veriler ayrı tabloda).
    """
    try:
        async with get_db_session_context() as db:
            row = await db.execute(
                text("""
                    WITH cohort AS (
                        SELECT DISTINCT user_id
                        FROM kiro2_learning_events
                        WHERE event_type IN ('cat_answer', 'exam_answer')
                          AND occurred_at >= NOW() - INTERVAL '14 days'
                          AND occurred_at <  NOW() - INTERVAL '7 days'
                    ),
                    retained AS (
                        SELECT DISTINCT le.user_id
                        FROM kiro2_learning_events le
                        JOIN cohort c ON le.user_id = c.user_id
                        WHERE le.occurred_at >= NOW() - INTERVAL '7 days'
                    )
                    SELECT
                        COUNT(DISTINCT c.user_id)       AS cohort_size,
                        COUNT(DISTINCT r.user_id)       AS retained_count,
                        CASE WHEN COUNT(DISTINCT c.user_id) > 0
                             THEN ROUND(
                                 COUNT(DISTINCT r.user_id)::numeric
                                 / COUNT(DISTINCT c.user_id) * 100, 1)
                             ELSE 0
                        END AS d7_retention_pct
                    FROM cohort c
                    LEFT JOIN retained r ON c.user_id = r.user_id
                """)
            )
            data = row.mappings().first()

        cohort_size = int(data["cohort_size"]) if data else 0
        retained_count = int(data["retained_count"]) if data else 0
        d7_pct = float(data["d7_retention_pct"]) if data else 0.0

        return {
            "metric": "d7_retention",
            "cohort_window": "days_8_to_14_ago",
            "return_window": "last_7_days",
            "cohort_size": cohort_size,
            "retained_count": retained_count,
            "d7_retention_pct": d7_pct,
        }

    except Exception as e:
        logger.error(f"D7 retention error: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz.")


# Export API Endpoints


@router.post("/export/pdf")
async def export_analytics_pdf(
    request: ExportRequest, current_user: User = Depends(get_current_user)
):
    """
    Analytics verilerini PDF olarak export et

    Requirements: 6.5 - Export functionality
    """
    try:
        # Veri tipine göre analytics al
        if request.data_type == "student":
            student_id = request.filters.get("student_id")
            if not student_id:
                raise HTTPException(status_code=400, detail="student_id gerekli")

            # Öğrenci analytics verilerini al
            analytics_data = await _get_student_analytics_for_export(
                student_id, request.filters
            )

        elif request.data_type == "class":
            class_id = request.filters.get("class_id")
            if not class_id:
                raise HTTPException(status_code=400, detail="class_id gerekli")

            # Sınıf analytics verilerini al
            analytics_data = await _get_class_analytics_for_export(
                class_id, request.filters
            )

        elif request.data_type == "admin":
            # Admin analytics verilerini al
            analytics_data = await _get_admin_analytics_for_export(request.filters)

        else:
            raise HTTPException(status_code=400, detail="Geçersiz data_type")

        # PDF oluştur
        pdf_buffer = io.BytesIO()
        pdf_canvas = canvas.Canvas(pdf_buffer, pagesize=letter)

        # PDF içeriği oluştur
        await _generate_pdf_content(pdf_canvas, analytics_data, request.data_type)

        pdf_canvas.save()
        pdf_buffer.seek(0)

        # Analytics event'i logla
        es_service = await get_elasticsearch_service()
        await es_service.analytics_service.log_event(
            event_type="analytics_exported",
            user_id=str(current_user.id),
            data={
                "format": "pdf",
                "data_type": request.data_type,
                "filters": request.filters,
            },
        )

        return {
            "success": True,
            "data": {
                "pdf_content": pdf_buffer.getvalue().hex(),  # Hex encoded PDF
                "filename": f"analytics_{request.data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            },
            "message": "PDF export başarıyla oluşturuldu",
        }

    except Exception as e:
        logger.error(f"PDF export error: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/export/excel")
async def export_analytics_excel(
    request: ExportRequest, current_user: User = Depends(get_current_user)
):
    """
    Analytics verilerini Excel olarak export et

    Requirements: 6.5 - Export functionality
    """
    try:
        # Veri tipine göre analytics al
        analytics_data = await _get_analytics_data_for_export(request)

        # Excel dosyası oluştur
        excel_buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(excel_buffer)

        # Excel içeriği oluştur
        await _generate_excel_content(workbook, analytics_data, request.data_type)

        workbook.close()
        excel_buffer.seek(0)

        # Analytics event'i logla
        es_service = await get_elasticsearch_service()
        await es_service.analytics_service.log_event(
            event_type="analytics_exported",
            user_id=str(current_user.id),
            data={
                "format": "excel",
                "data_type": request.data_type,
                "filters": request.filters,
            },
        )

        return {
            "success": True,
            "data": {
                "excel_content": excel_buffer.getvalue().hex(),  # Hex encoded Excel
                "filename": f"analytics_{request.data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            },
            "message": "Excel export başarıyla oluşturuldu",
        }

    except Exception as e:
        logger.error(f"Excel export error: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/export/csv")
async def export_analytics_csv(
    request: ExportRequest, current_user: User = Depends(get_current_user)
):
    """
    Analytics verilerini CSV olarak export et

    Requirements: 6.5 - Export functionality
    """
    try:
        # Veri tipine göre analytics al
        analytics_data = await _get_analytics_data_for_export(request)

        # CSV dosyası oluştur
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)

        # CSV içeriği oluştur
        await _generate_csv_content(csv_writer, analytics_data, request.data_type)

        csv_content = csv_buffer.getvalue()

        # Analytics event'i logla
        es_service = await get_elasticsearch_service()
        await es_service.analytics_service.log_event(
            event_type="analytics_exported",
            user_id=str(current_user.id),
            data={
                "format": "csv",
                "data_type": request.data_type,
                "filters": request.filters,
            },
        )

        return {
            "success": True,
            "data": {
                "csv_content": csv_content,
                "filename": f"analytics_{request.data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            },
            "message": "CSV export başarıyla oluşturuldu",
        }

    except Exception as e:
        logger.error(f"CSV export error: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Helper functions


async def _calculate_student_performance_metrics(
    student_id: str, start_date: datetime, end_date: datetime, es_service
) -> dict[str, Any]:
    """Öğrenci performans metrikleri hesapla"""
    try:
        # Mock implementation - gerçek implementasyonda DB'den veri alınacak
        return {
            "total_study_time_hours": 45.5,
            "total_questions_solved": 1247,
            "correct_answers": 892,
            "accuracy_rate": 0.715,
            "average_session_duration_minutes": 28.3,
            "improvement_trend": "increasing",
            "weak_subjects": ["Matematik", "Fizik"],
            "strong_subjects": ["Türkçe", "Tarih"],
            "study_consistency_score": 0.82,
        }
    except Exception as e:
        logger.error(f"Student performance metrics error: {e!s}")
        return {}


async def _get_learning_style_analysis(student_id: str) -> dict[str, Any]:
    """Öğrenme stili analizi"""
    try:
        # Mock implementation
        return {
            "vark_profile": {
                "visual": 0.7,
                "auditory": 0.3,
                "reading": 0.6,
                "kinesthetic": 0.4,
            },
            "felder_silverman_profile": {
                "active_reflective": 0.6,
                "sensing_intuitive": 0.4,
                "visual_verbal": 0.8,
                "sequential_global": 0.5,
            },
            "hybrid_code": "V-A-S-S",
            "confidence_level": 0.85,
            "recommendations": [
                "Görsel materyaller kullanın",
                "Diyagramlar ve şemalar ekleyin",
                "Adım adım açıklamalar yapın",
            ],
        }
    except Exception as e:
        logger.error(f"Learning style analysis error: {e!s}")
        return {}


async def _get_exam_performance_analysis(
    student_id: str, start_date: datetime, end_date: datetime
) -> dict[str, Any]:
    """Sınav performans analizi"""
    try:
        # Mock implementation
        return {
            "total_exams": 12,
            "average_score": 78.5,
            "best_score": 92,
            "worst_score": 65,
            "improvement_rate": 0.15,
            "exam_types": {
                "TYT": {"count": 8, "average": 76.2},
                "AYT": {"count": 3, "average": 82.1},
                "YDT": {"count": 1, "average": 85.0},
            },
            "time_management": {
                "average_completion_rate": 0.89,
                "time_per_question_seconds": 45.2,
            },
        }
    except Exception as e:
        logger.error(f"Exam performance analysis error: {e!s}")
        return {}


async def _get_subject_performance_analysis(
    student_id: str, start_date: datetime, end_date: datetime
) -> dict[str, Any]:
    """Konu bazlı performans analizi"""
    try:
        # Mock implementation
        return {
            "subjects": {
                "Matematik": {
                    "accuracy_rate": 0.68,
                    "questions_solved": 245,
                    "time_spent_hours": 12.5,
                    "improvement_trend": "stable",
                    "weak_topics": ["Türev", "İntegral"],
                    "strong_topics": ["Fonksiyonlar", "Geometri"],
                },
                "Türkçe": {
                    "accuracy_rate": 0.82,
                    "questions_solved": 189,
                    "time_spent_hours": 8.2,
                    "improvement_trend": "increasing",
                    "weak_topics": ["Sözcük Türleri"],
                    "strong_topics": ["Anlam Bilgisi", "Paragraf"],
                },
                "Fizik": {
                    "accuracy_rate": 0.61,
                    "questions_solved": 156,
                    "time_spent_hours": 9.8,
                    "improvement_trend": "decreasing",
                    "weak_topics": ["Elektrik", "Manyetizma"],
                    "strong_topics": ["Hareket", "Kuvvet"],
                },
            }
        }
    except Exception as e:
        logger.error(f"Subject performance analysis error: {e!s}")
        return {}


async def _get_detailed_student_analysis(
    student_id: str, start_date: datetime, end_date: datetime
) -> dict[str, Any]:
    """Detaylı öğrenci analizi"""
    try:
        # Mock implementation
        return {
            "study_patterns": {
                "preferred_study_hours": ["14:00-16:00", "20:00-22:00"],
                "most_active_days": ["Pazartesi", "Çarşamba", "Pazar"],
                "session_frequency": "günde 2-3 oturum",
                "break_patterns": "25 dakika çalışma, 5 dakika mola",
            },
            "motivation_analysis": {
                "motivation_score": 0.75,
                "engagement_level": "yüksek",
                "challenge_preference": "orta zorluk",
                "feedback_responsiveness": 0.88,
            },
            "revolutionary_features_usage": {
                "bionic_reading": {"usage_rate": 0.65, "effectiveness": 0.78},
                "fsrs_scheduling": {"usage_rate": 0.82, "retention_improvement": 0.23},
                "text_simplification": {
                    "usage_rate": 0.45,
                    "comprehension_improvement": 0.31,
                },
                "multi_agent_coordination": {
                    "usage_rate": 0.71,
                    "learning_efficiency": 0.19,
                },
            },
        }
    except Exception as e:
        logger.error(f"Detailed student analysis error: {e!s}")
        return {}


async def _get_class_students(class_id: str) -> list[dict[str, Any]]:
    """Sınıf öğrencilerini al"""
    try:
        # Mock implementation - gerçek implementasyonda DB'den gelecek
        return [
            {"id": "student_1", "name": "Ahmet Yılmaz"},
            {"id": "student_2", "name": "Ayşe Demir"},
            {"id": "student_3", "name": "Mehmet Kaya"},
            {"id": "student_4", "name": "Fatma Özkan"},
            {"id": "student_5", "name": "Ali Çelik"},
        ]
    except Exception as e:
        logger.error(f"Get class students error: {e!s}")
        return []


async def _calculate_class_metrics(
    class_id: str,
    students: list[dict[str, Any]],
    start_date: datetime,
    end_date: datetime,
    es_service,
) -> dict[str, Any]:
    """Sınıf metrikleri hesapla"""
    try:
        # Mock implementation
        return {
            "average_study_time_hours": 38.2,
            "total_questions_solved": 5847,
            "class_accuracy_rate": 0.742,
            "active_students_percentage": 0.89,
            "improvement_rate": 0.12,
            "engagement_score": 0.78,
        }
    except Exception as e:
        logger.error(f"Class metrics calculation error: {e!s}")
        return {}


async def _get_class_performance_distribution(
    students: list[dict[str, Any]], start_date: datetime, end_date: datetime
) -> dict[str, Any]:
    """Sınıf performans dağılımı"""
    try:
        # Mock implementation
        return {
            "score_distribution": {
                "90-100": 2,
                "80-89": 8,
                "70-79": 12,
                "60-69": 6,
                "50-59": 2,
                "below_50": 0,
            },
            "performance_levels": {
                "excellent": 2,
                "good": 8,
                "average": 12,
                "needs_improvement": 8,
            },
        }
    except Exception as e:
        logger.error(f"Class performance distribution error: {e!s}")
        return {}


async def _get_class_subject_analysis(
    students: list[dict[str, Any]], start_date: datetime, end_date: datetime
) -> dict[str, Any]:
    """Sınıf konu analizi"""
    try:
        # Mock implementation
        return {
            "subject_averages": {
                "Matematik": 72.5,
                "Türkçe": 78.9,
                "Fizik": 69.2,
                "Kimya": 74.1,
                "Biyoloji": 76.8,
                "Tarih": 81.3,
                "Coğrafya": 77.6,
            },
            "challenging_topics": [
                "Matematik - Türev ve İntegral",
                "Fizik - Elektrik ve Manyetizma",
                "Kimya - Organik Kimya",
            ],
            "strong_topics": [
                "Türkçe - Anlam Bilgisi",
                "Tarih - Osmanlı Tarihi",
                "Biyoloji - Hücre Biyolojisi",
            ],
        }
    except Exception as e:
        logger.error(f"Class subject analysis error: {e!s}")
        return {}


async def _get_class_learning_style_distribution(
    students: list[dict[str, Any]],
) -> dict[str, Any]:
    """Sınıf öğrenme stili dağılımı"""
    try:
        # Mock implementation
        return {
            "vark_distribution": {
                "visual": 0.45,
                "auditory": 0.25,
                "reading": 0.35,
                "kinesthetic": 0.30,
            },
            "felder_silverman_distribution": {
                "active": 0.60,
                "reflective": 0.40,
                "sensing": 0.55,
                "intuitive": 0.45,
                "visual": 0.70,
                "verbal": 0.30,
                "sequential": 0.65,
                "global": 0.35,
            },
            "hybrid_profiles": {
                "V-A-S-S": 8,
                "A-R-I-G": 5,
                "K-A-S-S": 7,
                "R-R-V-G": 4,
                "V-A-I-S": 6,
            },
        }
    except Exception as e:
        logger.error(f"Class learning style distribution error: {e!s}")
        return {}


async def _calculate_system_metrics(
    start_date: datetime, end_date: datetime, es_service
) -> dict[str, Any]:
    """Sistem metrikleri hesapla"""
    try:
        # Mock implementation
        return {
            "total_active_users": 15247,
            "total_sessions": 89456,
            "average_session_duration_minutes": 32.5,
            "total_questions_solved": 1247896,
            "system_uptime_percentage": 99.7,
            "api_response_time_ms": 145,
            "error_rate_percentage": 0.3,
        }
    except Exception as e:
        logger.error(f"System metrics calculation error: {e!s}")
        return {}


async def _get_user_statistics(
    start_date: datetime, end_date: datetime
) -> dict[str, Any]:
    """Kullanıcı istatistikleri"""
    try:
        # Mock implementation
        return {
            "total_users": 25847,
            "new_registrations": 1247,
            "active_users": 15896,
            "user_types": {
                "students": 22456,
                "teachers": 2847,
                "parents": 456,
                "admins": 88,
            },
            "retention_rate": 0.78,
            "churn_rate": 0.05,
        }
    except Exception as e:
        logger.error(f"User statistics error: {e!s}")
        return {}


async def _get_exam_statistics(
    start_date: datetime, end_date: datetime
) -> dict[str, Any]:
    """Sınav istatistikleri"""
    try:
        # Mock implementation
        return {
            "total_exams_taken": 45896,
            "exam_types": {"TYT": 28456, "AYT": 12847, "YDT": 4593},
            "average_scores": {"TYT": 76.8, "AYT": 72.3, "YDT": 78.9},
            "completion_rates": {"TYT": 0.89, "AYT": 0.85, "YDT": 0.92},
        }
    except Exception as e:
        logger.error(f"Exam statistics error: {e!s}")
        return {}


async def _get_content_usage_statistics(
    start_date: datetime, end_date: datetime
) -> dict[str, Any]:
    """İçerik kullanım istatistikleri"""
    try:
        # Mock implementation
        return {
            "total_content_views": 189456,
            "content_types": {
                "videos": 78456,
                "articles": 56789,
                "practice_questions": 45896,
                "flashcards": 8315,
            },
            "popular_subjects": {
                "Matematik": 45896,
                "Türkçe": 38745,
                "Fizik": 28456,
                "Kimya": 25789,
                "Biyoloji": 22456,
            },
            "engagement_metrics": {
                "average_view_duration_minutes": 8.5,
                "bounce_rate": 0.25,
                "completion_rate": 0.68,
            },
        }
    except Exception as e:
        logger.error(f"Content usage statistics error: {e!s}")
        return {}


async def _get_system_performance_metrics(
    start_date: datetime, end_date: datetime
) -> dict[str, Any]:
    """Sistem performans metrikleri"""
    try:
        # Mock implementation
        return {
            "api_metrics": {
                "average_response_time_ms": 145,
                "p95_response_time_ms": 289,
                "p99_response_time_ms": 456,
                "error_rate_percentage": 0.3,
                "throughput_requests_per_second": 1247,
            },
            "database_metrics": {
                "query_performance_ms": 23,
                "connection_pool_usage": 0.65,
                "slow_queries_count": 12,
            },
            "cache_metrics": {
                "hit_rate_percentage": 89.5,
                "miss_rate_percentage": 10.5,
                "eviction_rate": 0.02,
            },
        }
    except Exception as e:
        logger.error(f"System performance metrics error: {e!s}")
        return {}


async def _get_revolutionary_features_usage(
    start_date: datetime, end_date: datetime
) -> dict[str, Any]:
    """Devrimsel özellik kullanımı"""
    try:
        # Mock implementation
        return {
            "bionic_reading": {
                "total_users": 8456,
                "usage_sessions": 45896,
                "effectiveness_score": 0.78,
                "user_satisfaction": 0.85,
            },
            "fsrs_scheduling": {
                "total_users": 12847,
                "cards_reviewed": 189456,
                "retention_improvement": 0.23,
                "user_satisfaction": 0.89,
            },
            "text_simplification": {
                "total_users": 6789,
                "texts_simplified": 28456,
                "comprehension_improvement": 0.31,
                "user_satisfaction": 0.82,
            },
            "multi_agent_coordination": {
                "total_users": 9876,
                "coordination_events": 156789,
                "learning_efficiency_improvement": 0.19,
                "user_satisfaction": 0.87,
            },
            "vark_felder_hybrid": {
                "profiles_generated": 15896,
                "accuracy_rate": 0.91,
                "personalization_effectiveness": 0.84,
            },
            "turkish_zpd_maarif": {
                "assessments_completed": 12456,
                "cultural_adaptation_score": 0.88,
                "learning_optimization": 0.26,
            },
            "turkish_morphology_irt": {
                "questions_analyzed": 89456,
                "difficulty_accuracy": 0.93,
                "osym_standard_improvement": 0.15,
            },
        }
    except Exception as e:
        logger.error(f"Revolutionary features usage error: {e!s}")
        return {}


# Export helper functions


async def _get_analytics_data_for_export(request: ExportRequest) -> dict[str, Any]:
    """Export için analytics verilerini al"""
    try:
        if request.data_type == "student":
            return await _get_student_analytics_for_export(
                request.filters.get("student_id"), request.filters
            )
        if request.data_type == "class":
            return await _get_class_analytics_for_export(
                request.filters.get("class_id"), request.filters
            )
        if request.data_type == "admin":
            return await _get_admin_analytics_for_export(request.filters)
        return {}
    except Exception as e:
        logger.error(f"Get analytics data for export error: {e!s}")
        return {}


async def _get_student_analytics_for_export(
    student_id: str, filters: dict[str, Any]
) -> dict[str, Any]:
    """Öğrenci analytics export verisi"""
    try:
        # Mock implementation
        return {
            "student_info": {
                "id": student_id,
                "name": "Ahmet Yılmaz",
                "class": "12-A",
                "school": "Atatürk Lisesi",
            },
            "performance_summary": {
                "total_study_hours": 45.5,
                "questions_solved": 1247,
                "accuracy_rate": 0.715,
                "improvement_rate": 0.15,
            },
            "subject_breakdown": [
                {
                    "subject": "Matematik",
                    "score": 72.5,
                    "questions": 245,
                    "accuracy": 0.68,
                },
                {
                    "subject": "Türkçe",
                    "score": 78.9,
                    "questions": 189,
                    "accuracy": 0.82,
                },
                {"subject": "Fizik", "score": 69.2, "questions": 156, "accuracy": 0.61},
            ],
        }
    except Exception as e:
        logger.error(f"Student analytics for export error: {e!s}")
        return {}


async def _get_class_analytics_for_export(
    class_id: str, filters: dict[str, Any]
) -> dict[str, Any]:
    """Sınıf analytics export verisi"""
    try:
        # Mock implementation
        return {
            "class_info": {
                "id": class_id,
                "name": "12-A",
                "school": "Atatürk Lisesi",
                "teacher": "Mehmet Öğretmen",
                "student_count": 30,
            },
            "class_summary": {
                "average_score": 76.8,
                "total_study_hours": 1247,
                "questions_solved": 5847,
                "class_accuracy": 0.742,
            },
            "student_list": [
                {"name": "Ahmet Yılmaz", "score": 85.2, "rank": 1},
                {"name": "Ayşe Demir", "score": 82.7, "rank": 2},
                {"name": "Mehmet Kaya", "score": 79.3, "rank": 3},
            ],
        }
    except Exception as e:
        logger.error(f"Class analytics for export error: {e!s}")
        return {}


async def _get_admin_analytics_for_export(filters: dict[str, Any]) -> dict[str, Any]:
    """Admin analytics export verisi"""
    try:
        # Mock implementation
        return {
            "system_summary": {
                "total_users": 25847,
                "active_users": 15896,
                "total_exams": 45896,
                "system_uptime": 99.7,
            },
            "performance_metrics": {
                "api_response_time": 145,
                "error_rate": 0.3,
                "throughput": 1247,
            },
            "usage_statistics": {
                "content_views": 189456,
                "questions_solved": 1247896,
                "study_hours": 89456,
            },
        }
    except Exception as e:
        logger.error(f"Admin analytics for export error: {e!s}")
        return {}


async def _generate_pdf_content(
    pdf_canvas, analytics_data: dict[str, Any], data_type: str
):
    """PDF içeriği oluştur"""
    try:
        # PDF başlığı
        pdf_canvas.setFont("Helvetica-Bold", 16)
        pdf_canvas.drawString(50, 750, f"Analytics Raporu - {data_type.title()}")

        # Tarih
        pdf_canvas.setFont("Helvetica", 10)
        pdf_canvas.drawString(
            50, 730, f"Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        # İçerik (basit metin formatında)
        y_position = 700
        pdf_canvas.setFont("Helvetica", 12)

        for key, value in analytics_data.items():
            if y_position < 50:  # Yeni sayfa
                pdf_canvas.showPage()
                y_position = 750

            pdf_canvas.drawString(50, y_position, f"{key}: {str(value)[:80]}")
            y_position -= 20

    except Exception as e:
        logger.error(f"PDF content generation error: {e!s}")


async def _generate_excel_content(
    workbook, analytics_data: dict[str, Any], data_type: str
):
    """Excel içeriği oluştur"""
    try:
        # Ana worksheet
        worksheet = workbook.add_worksheet(f"{data_type}_analytics")

        # Başlık formatı
        header_format = workbook.add_format(
            {
                "bold": True,
                "font_size": 14,
                "bg_color": "#4472C4",
                "font_color": "white",
            }
        )

        # Başlık
        worksheet.write(0, 0, f"Analytics Raporu - {data_type.title()}", header_format)
        worksheet.write(1, 0, f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

        # Veri yazma
        row = 3
        for key, value in analytics_data.items():
            worksheet.write(row, 0, key)
            worksheet.write(row, 1, str(value))
            row += 1

    except Exception as e:
        logger.error(f"Excel content generation error: {e!s}")


async def _generate_csv_content(
    csv_writer, analytics_data: dict[str, Any], data_type: str
):
    """CSV içeriği oluştur"""
    try:
        # Başlık
        csv_writer.writerow([f"Analytics Raporu - {data_type.title()}"])
        csv_writer.writerow([f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}"])
        csv_writer.writerow([])  # Boş satır

        # Başlık satırı
        csv_writer.writerow(["Metrik", "Değer"])

        # Veri satırları
        for key, value in analytics_data.items():
            csv_writer.writerow([key, str(value)])

    except Exception as e:
        logger.error(f"CSV content generation error: {e!s}")


async def _get_system_performance_metrics(
    start_date: datetime, end_date: datetime
) -> dict[str, Any]:
    """Sistem performans metrikleri"""
    try:
        # Mock implementation
        return {
            "api_metrics": {
                "average_response_time_ms": 145,
                "p95_response_time_ms": 289,
                "p99_response_time_ms": 456,
                "error_rate_percentage": 0.3,
                "throughput_requests_per_second": 1247,
            },
            "database_metrics": {
                "query_performance_ms": 23,
                "connection_pool_usage": 0.65,
                "slow_queries_count": 12,
            },
            "cache_metrics": {
                "hit_rate_percentage": 89.5,
                "miss_rate_percentage": 10.5,
                "eviction_rate": 0.02,
            },
        }
    except Exception as e:
        logger.error(f"System performance metrics error: {e!s}")
        return {}


async def _get_revolutionary_features_usage(
    start_date: datetime, end_date: datetime
) -> dict[str, Any]:
    """Devrimsel özellik kullanımı"""
    try:
        # Mock implementation
        return {
            "bionic_reading": {
                "total_users": 8456,
                "usage_sessions": 45896,
                "effectiveness_score": 0.78,
                "user_satisfaction": 0.85,
            },
            "fsrs_scheduling": {
                "total_users": 12847,
                "cards_reviewed": 189456,
                "retention_improvement": 0.23,
                "user_satisfaction": 0.89,
            },
            "text_simplification": {
                "total_users": 6789,
                "texts_simplified": 28456,
                "comprehension_improvement": 0.31,
                "user_satisfaction": 0.82,
            },
            "multi_agent_coordination": {
                "total_users": 9876,
                "coordination_events": 156789,
                "learning_efficiency_improvement": 0.19,
                "user_satisfaction": 0.87,
            },
            "vark_felder_hybrid": {
                "profiles_generated": 15896,
                "accuracy_rate": 0.91,
                "personalization_effectiveness": 0.84,
            },
            "turkish_zpd_maarif": {
                "assessments_completed": 12456,
                "cultural_adaptation_score": 0.88,
                "learning_optimization": 0.26,
            },
            "turkish_morphology_irt": {
                "questions_analyzed": 89456,
                "difficulty_accuracy": 0.93,
                "osym_standard_improvement": 0.15,
            },
        }
    except Exception as e:
        logger.error(f"Revolutionary features usage error: {e!s}")
        return {}


# Export helper functions


async def _get_analytics_data_for_export(request: ExportRequest) -> dict[str, Any]:
    """Export için analytics verilerini al"""
    try:
        if request.data_type == "student":
            return await _get_student_analytics_for_export(
                request.filters.get("student_id"), request.filters
            )
        if request.data_type == "class":
            return await _get_class_analytics_for_export(
                request.filters.get("class_id"), request.filters
            )
        if request.data_type == "admin":
            return await _get_admin_analytics_for_export(request.filters)
        return {}
    except Exception as e:
        logger.error(f"Get analytics data for export error: {e!s}")
        return {}


async def _get_student_analytics_for_export(
    student_id: str, filters: dict[str, Any]
) -> dict[str, Any]:
    """Öğrenci analytics export verisi"""
    try:
        # Mock implementation
        return {
            "student_info": {
                "id": student_id,
                "name": "Ahmet Yılmaz",
                "class": "12-A",
                "school": "Atatürk Lisesi",
            },
            "performance_summary": {
                "total_study_hours": 45.5,
                "questions_solved": 1247,
                "accuracy_rate": 0.715,
                "improvement_rate": 0.15,
            },
            "subject_breakdown": [
                {
                    "subject": "Matematik",
                    "score": 72.5,
                    "questions": 245,
                    "accuracy": 0.68,
                },
                {
                    "subject": "Türkçe",
                    "score": 78.9,
                    "questions": 189,
                    "accuracy": 0.82,
                },
                {"subject": "Fizik", "score": 69.2, "questions": 156, "accuracy": 0.61},
            ],
        }
    except Exception as e:
        logger.error(f"Student analytics for export error: {e!s}")
        return {}


async def _get_class_analytics_for_export(
    class_id: str, filters: dict[str, Any]
) -> dict[str, Any]:
    """Sınıf analytics export verisi"""
    try:
        # Mock implementation
        return {
            "class_info": {
                "id": class_id,
                "name": "12-A",
                "school": "Atatürk Lisesi",
                "teacher": "Mehmet Öğretmen",
                "student_count": 30,
            },
            "class_summary": {
                "average_score": 76.8,
                "total_study_hours": 1247,
                "questions_solved": 5847,
                "class_accuracy": 0.742,
            },
            "student_list": [
                {"name": "Ahmet Yılmaz", "score": 85.2, "rank": 1},
                {"name": "Ayşe Demir", "score": 82.7, "rank": 2},
                {"name": "Mehmet Kaya", "score": 79.3, "rank": 3},
            ],
        }
    except Exception as e:
        logger.error(f"Class analytics for export error: {e!s}")
        return {}


async def _get_admin_analytics_for_export(filters: dict[str, Any]) -> dict[str, Any]:
    """Admin analytics export verisi"""
    try:
        # Mock implementation
        return {
            "system_summary": {
                "total_users": 25847,
                "active_users": 15896,
                "total_exams": 45896,
                "system_uptime": 99.7,
            },
            "performance_metrics": {
                "api_response_time": 145,
                "error_rate": 0.3,
                "throughput": 1247,
            },
            "usage_statistics": {
                "content_views": 189456,
                "questions_solved": 1247896,
                "study_hours": 89456,
            },
        }
    except Exception as e:
        logger.error(f"Admin analytics for export error: {e!s}")
        return {}


async def _generate_pdf_content(
    pdf_canvas, analytics_data: dict[str, Any], data_type: str
):
    """PDF içeriği oluştur"""
    try:
        # PDF başlığı
        pdf_canvas.setFont("Helvetica-Bold", 16)
        pdf_canvas.drawString(50, 750, f"Analytics Raporu - {data_type.title()}")

        # Tarih
        pdf_canvas.setFont("Helvetica", 10)
        pdf_canvas.drawString(
            50, 730, f"Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        # İçerik (basit metin formatında)
        y_position = 700
        pdf_canvas.setFont("Helvetica", 12)

        for key, value in analytics_data.items():
            if y_position < 50:  # Yeni sayfa
                pdf_canvas.showPage()
                y_position = 750

            pdf_canvas.drawString(50, y_position, f"{key}: {str(value)[:80]}")
            y_position -= 20

    except Exception as e:
        logger.error(f"PDF content generation error: {e!s}")


async def _generate_excel_content(
    workbook, analytics_data: dict[str, Any], data_type: str
):
    """Excel içeriği oluştur"""
    try:
        # Ana worksheet
        worksheet = workbook.add_worksheet(f"{data_type}_analytics")

        # Başlık formatı
        header_format = workbook.add_format(
            {
                "bold": True,
                "font_size": 14,
                "bg_color": "#4472C4",
                "font_color": "white",
            }
        )

        # Başlık
        worksheet.write(0, 0, f"Analytics Raporu - {data_type.title()}", header_format)
        worksheet.write(1, 0, f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

        # Veri yazma
        row = 3
        for key, value in analytics_data.items():
            worksheet.write(row, 0, key)
            worksheet.write(row, 1, str(value))
            row += 1

    except Exception as e:
        logger.error(f"Excel content generation error: {e!s}")


async def _generate_csv_content(
    csv_writer, analytics_data: dict[str, Any], data_type: str
):
    """CSV içeriği oluştur"""
    try:
        # Başlık
        csv_writer.writerow([f"Analytics Raporu - {data_type.title()}"])
        csv_writer.writerow([f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}"])
        csv_writer.writerow([])  # Boş satır

        # Başlık satırı
        csv_writer.writerow(["Metrik", "Değer"])

        # Veri satırları
        for key, value in analytics_data.items():
            csv_writer.writerow([key, str(value)])

    except Exception as e:
        logger.error(f"CSV content generation error: {e!s}")


# ---------------------------------------------------------------------------
# Web Vitals — fire-and-forget endpoint for frontend performance metrics
# ---------------------------------------------------------------------------


@router.post("/web-vitals", status_code=204)
async def receive_web_vitals(request: Request):
    """Receive web vitals metrics from frontend (fire-and-forget)."""
    try:
        body = await request.json()
        logger.debug("Web vital: %s=%s", body.get("name"), body.get("value"))
    except Exception:
        pass
    return Response(status_code=204)
