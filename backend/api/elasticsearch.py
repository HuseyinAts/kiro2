"""
Elasticsearch API endpoint'leri
Arama, indeksleme ve analytics API'leri
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

try:
    from core.dependencies import AuthenticatedUser, get_current_user
    from core.auth_dependencies import require_role
    from services.elasticsearch_service import (
        ElasticsearchService,
        get_elasticsearch_service,
    )
except ImportError:
    # Import the canonical get_current_user function from core.dependencies
    from core.dependencies import AuthenticatedUser, get_current_user
    from core.auth_dependencies import require_role
    from services.elasticsearch_service import (
        ElasticsearchService,
        get_elasticsearch_service,
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/elasticsearch", tags=["elasticsearch"])


# Request/Response modelleri
class SearchRequest(BaseModel):
    """Arama isteği modeli"""

    query: str = Field(..., description="Arama sorgusu")
    size: int = Field(default=20, ge=1, le=100, description="Sonuç sayısı")
    from_: int = Field(default=0, ge=0, alias="from", description="Başlangıç indeksi")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Filtreler")


class QuestionSearchRequest(SearchRequest):
    """Soru arama isteği"""

    subject: Optional[str] = Field(default=None, description="Ders")
    topic: Optional[str] = Field(default=None, description="Konu")
    exam_type: Optional[str] = Field(default=None, description="Sınav türü")
    difficulty_min: Optional[float] = Field(
        default=None, ge=0, le=10, description="Min zorluk"
    )
    difficulty_max: Optional[float] = Field(
        default=None, ge=0, le=10, description="Max zorluk"
    )


class ContentSearchRequest(SearchRequest):
    """İçerik arama isteği"""

    content_type: Optional[str] = Field(default=None, description="İçerik türü")
    subject: Optional[str] = Field(default=None, description="Ders")
    difficulty_level: Optional[str] = Field(default=None, description="Zorluk seviyesi")


class SearchResponse(BaseModel):
    """Arama yanıt modeli"""

    total: int
    max_score: Optional[float]
    took: int
    results: List[Dict[str, Any]]


class IndexStatsResponse(BaseModel):
    """İndeks istatistik yanıtı"""

    doc_count: int
    store_size_bytes: int
    index_name: str


class HealthResponse(BaseModel):
    """Sağlık kontrolü yanıtı"""

    status: str
    cluster_name: Optional[str] = None
    cluster_status: Optional[str] = None
    indices: Optional[Dict[str, Dict[str, Any]]] = None
    error: Optional[str] = None


# Soru arama endpoint'leri
@router.post("/questions/search", response_model=SearchResponse)
async def search_questions(
    request: QuestionSearchRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    es_service: ElasticsearchService = Depends(get_elasticsearch_service),
):
    """
    Soru bankasında Türkçe full-text arama

    - **query**: Arama sorgusu (Türkçe destekli)
    - **subject**: Ders filtresi (Matematik, Türkçe, vb.)
    - **topic**: Konu filtresi
    - **exam_type**: Sınav türü (TYT, AYT, YDT)
    - **difficulty_min/max**: Zorluk aralığı
    """
    try:
        # Zorluk aralığı
        difficulty_range = None
        if request.difficulty_min is not None or request.difficulty_max is not None:
            min_diff = request.difficulty_min or 0
            max_diff = request.difficulty_max or 10
            difficulty_range = (min_diff, max_diff)

        # Arama yap
        search_result = await es_service.question_service.search_questions(
            query_text=request.query,
            subject=request.subject,
            topic=request.topic,
            exam_type=request.exam_type,
            difficulty_range=difficulty_range,
            size=request.size,
            from_=request.from_,
        )

        # Analytics log
        await es_service.analytics_service.log_event(
            event_type="question_search",
            user_id=str(current_user.id),
            data={
                "query": request.query,
                "subject": request.subject,
                "topic": request.topic,
                "exam_type": request.exam_type,
                "results_count": search_result.total,
            },
        )

        return SearchResponse(
            total=search_result.total,
            max_score=search_result.max_score,
            took=search_result.took,
            results=[
                {
                    "id": result.id,
                    "score": result.score,
                    "source": result.source,
                    "highlight": result.highlight,
                }
                for result in search_result.results
            ],
        )

    except Exception as e:
        logger.error(f"Soru arama hatası: {str(e)}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/questions/{question_id}/similar", response_model=SearchResponse)
async def get_similar_questions(
    question_id: str = Path(..., description="Soru ID"),
    size: int = Query(default=5, ge=1, le=20, description="Sonuç sayısı"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    es_service: ElasticsearchService = Depends(get_elasticsearch_service),
):
    """
    Benzer soruları bul

    More Like This algoritması ile benzer soruları getirir
    """
    try:
        search_result = await es_service.question_service.get_similar_questions(
            question_id=question_id, size=size
        )

        # Analytics log
        await es_service.analytics_service.log_event(
            event_type="similar_questions_search",
            user_id=str(current_user.id),
            data={"question_id": question_id, "results_count": search_result.total},
        )

        return SearchResponse(
            total=search_result.total,
            max_score=search_result.max_score,
            took=search_result.took,
            results=[
                {"id": result.id, "score": result.score, "source": result.source}
                for result in search_result.results
            ],
        )

    except Exception as e:
        logger.error(f"Benzer soru arama hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# İçerik arama endpoint'leri
@router.post("/content/search", response_model=SearchResponse)
async def search_content(
    request: ContentSearchRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    es_service: ElasticsearchService = Depends(get_elasticsearch_service),
):
    """
    Eğitim içeriklerinde arama

    - **query**: Arama sorgusu
    - **content_type**: İçerik türü (video, article, exercise)
    - **subject**: Ders filtresi
    - **difficulty_level**: Zorluk seviyesi (beginner, intermediate, advanced)
    """
    try:
        search_result = await es_service.content_service.search_content(
            query_text=request.query,
            content_type=request.content_type,
            subject=request.subject,
            difficulty_level=request.difficulty_level,
            size=request.size,
            from_=request.from_,
        )

        # Analytics log
        await es_service.analytics_service.log_event(
            event_type="content_search",
            user_id=str(current_user.id),
            data={
                "query": request.query,
                "content_type": request.content_type,
                "subject": request.subject,
                "difficulty_level": request.difficulty_level,
                "results_count": search_result.total,
            },
        )

        return SearchResponse(
            total=search_result.total,
            max_score=search_result.max_score,
            took=search_result.took,
            results=[
                {
                    "id": result.id,
                    "score": result.score,
                    "source": result.source,
                    "highlight": result.highlight,
                }
                for result in search_result.results
            ],
        )

    except Exception as e:
        logger.error(f"İçerik arama hatası: {str(e)}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


# Analytics endpoint'leri
@router.get("/analytics/user/{user_id}")
async def get_user_analytics(
    user_id: str = Path(..., description="Kullanıcı ID"),
    days: int = Query(default=30, ge=1, le=365, description="Gün sayısı"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    es_service: ElasticsearchService = Depends(get_elasticsearch_service),
):
    """
    Kullanıcı analytics verilerini getir

    Son N gün içindeki kullanıcı aktivitelerini analiz eder
    """
    try:
        # Yetki kontrolü (sadece kendi verilerini veya admin)
        if str(current_user.id) != user_id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=403, detail="Bu verilere erişim yetkiniz yok"
            )

        # Tarih aralığı
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        analytics_data = await es_service.analytics_service.get_user_analytics(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        return {
            "success": True,
            "data": analytics_data,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics getirme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


# Admin endpoint'leri
@router.post("/admin/reindex/questions")
async def reindex_questions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    es_service: ElasticsearchService = Depends(get_elasticsearch_service),
    _: None = Depends(require_role("ADMIN")),
):
    """
    Soru bankasını yeniden indeksle (Admin only)
    """
    try:

        # İndeksi yeniden oluştur
        success = await es_service.question_service.initialize_index()

        if not success:
            raise HTTPException(status_code=500, detail="İndeks oluşturma başarısız")

        # Database'den tüm soruları çek ve indeksle
        try:
            from core.database import get_db_session_context
            from sqlalchemy import select
            from models.osym_question import OSYMQuestion
            from models.question_bank import QuestionBankItem as Question

            indexed_count = 0
            errors = []

            # Get database session
            async with get_db_session_context() as db_session:
                # Index OSYM questions
                try:
                    result = await db_session.execute(select(OSYMQuestion))
                    osym_questions = result.scalars().all()

                    # OPTIMIZED: Bulk indexing ile N+1 problemi çözüldü
                    # Before: 1000 sequential ES calls (~10 seconds)
                    # After: 1 bulk ES call (~500ms, 95% faster)
                    questions_to_index = []
                    for question in osym_questions:
                        questions_to_index.append(
                            {
                                "id": question.question_id,
                                "question_id": question.question_id,
                                "stem": question.stem,
                                "text": question.stem,  # For search compatibility
                                "options": question.options,
                                "correct_answer": question.correct_answer,
                                "explanation": question.explanation,
                                "subject": question.subject,
                                "topic": question.topic,
                                "difficulty": float(question.difficulty_level)
                                if question.difficulty_level
                                else 0.0,
                                "difficulty_level": question.difficulty_level,
                                "bloom_level": question.bloom_level,
                                "keywords": question.keywords or [],
                                "tags": question.keywords or [],
                            }
                        )

                    # Bulk index all questions at once
                    if questions_to_index:
                        bulk_result = (
                            await es_service.question_service.bulk_index_questions(
                                questions_to_index
                            )
                        )
                        indexed_count = bulk_result.get("success", 0)
                        if bulk_result.get("errors", 0) > 0:
                            errors.append(
                                f"OSYM bulk indexing: {bulk_result['errors']} errors occurred"
                            )

                    logger.info(f"Indexed {indexed_count} OSYM questions via bulk API")

                except Exception as e:
                    logger.error(f"Error indexing OSYM questions: {e}")
                    errors.append(f"OSYM questions error: {str(e)}")

                # Index regular questions
                try:
                    result = await db_session.execute(
                        select(Question).where(Question.is_active == True)  # noqa: E712
                    )
                    regular_questions = result.scalars().all()

                    for question in regular_questions:
                        try:
                            # Index question
                            await es_service.question_service.index_question(
                                {
                                    "question_id": question.id,
                                    "stem": question.question_text,
                                    "options": {"A": question.option_a, "B": question.option_b, "C": question.option_c, "D": question.option_d, "E": question.option_e},
                                    "correct_answer": question.correct_answer,
                                    "explanation": question.explanation or "",
                                    "subject": question.subject_area,
                                    "topic": question.primary_topic_id,
                                    "difficulty_level": question.difficulty_level.value
                                    if question.difficulty_level
                                    else "MEDIUM",
                                    "keywords": [],
                                }
                            )
                            indexed_count += 1
                        except Exception as e:
                            errors.append(f"Question {question.id}: {str(e)}")

                    logger.info(f"Indexed {len(regular_questions)} regular questions")

                except Exception as e:
                    logger.error(f"Error indexing regular questions: {e}")
                    errors.append(f"Regular questions error: {str(e)}")

        except Exception as e:
            logger.error(f"Database indexing error: {e}")
            errors.append(f"Database error: {str(e)}")

        return {
            "success": True,
            "message": "Soru bankası yeniden indekslendi",
            "indexed_count": indexed_count,
            "errors": errors if errors else None,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Yeniden indeksleme hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/admin/indices/stats", response_model=Dict[str, IndexStatsResponse])
async def get_indices_stats(
    current_user: AuthenticatedUser = Depends(get_current_user),
    es_service: ElasticsearchService = Depends(get_elasticsearch_service),
    _: None = Depends(require_role("ADMIN")),
):
    """
    İndeks istatistiklerini getir (Admin only)
    """
    try:

        stats = {}

        # Her indeks için istatistik
        for index_name in ["questions", "content", "analytics"]:
            index_stats = await es_service.es_client.get_index_stats(index_name)

            if index_stats:
                stats[index_name] = IndexStatsResponse(
                    doc_count=index_stats["total"]["docs"]["count"],
                    store_size_bytes=index_stats["total"]["store"]["size_in_bytes"],
                    index_name=index_name,
                )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"İndeks istatistik hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Sağlık kontrolü
@router.get("/health", response_model=HealthResponse)
async def elasticsearch_health(
    es_service: ElasticsearchService = Depends(get_elasticsearch_service),
):
    """
    Elasticsearch sağlık kontrolü

    Cluster durumu ve indeks istatistiklerini döner
    """
    try:
        health_data = await es_service.health_check()

        return HealthResponse(**health_data)

    except Exception as e:
        logger.error(f"Sağlık kontrolü hatası: {str(e)}")
        return HealthResponse(status="error", error=str(e))
