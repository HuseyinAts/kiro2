"""
Performance Monitoring API
Real-time metrics for LLM pool, vector store, cache, and RAG pipeline

Endpoints:
- GET /api/v1/performance/metrics - Comprehensive performance metrics
- GET /api/v1/performance/llm-pool - LLM connection pool stats
- GET /api/v1/performance/vector-store - Vector store optimization stats
- GET /api/v1/performance/cache - Cache statistics (L1 + L2)
- DELETE /api/v1/performance/cache/clear/{tag} - Clear cache by tag
- GET /api/v1/performance/rag-pipeline - RAG pipeline stats
"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.dependencies import get_current_user, AuthenticatedUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/performance-monitoring", tags=["Performance Monitoring"])


# ==================== RESPONSE MODELS ====================


class LLMPoolMetrics(BaseModel):
    """LLM connection pool metrics"""

    total_requests: int = 0
    active_connections: int = 0
    avg_response_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    errors: int = 0


class VectorStoreMetrics(BaseModel):
    """Vector store optimization metrics"""

    total_searches: int = 0
    avg_search_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    index_size: int = 0
    hnsw_enabled: bool = False


class CacheMetrics(BaseModel):
    """Multi-layer cache metrics"""

    l1_hits: int = 0
    l2_hits: int = 0
    misses: int = 0
    hit_ratio: float = 0.0
    total_keys: int = 0
    l1_size: int = 0
    l2_size: int = 0
    evictions: int = 0


class RAGPipelineMetrics(BaseModel):
    """RAG pipeline performance metrics"""

    total_queries: int = 0
    avg_query_time_ms: float = 0.0
    parallel_speedup: float = 1.0
    avg_documents_retrieved: float = 0.0
    reranking_enabled: bool = True
    query_expansion_enabled: bool = True


class PerformanceMetrics(BaseModel):
    """Comprehensive performance metrics"""

    llm_pool: Optional[LLMPoolMetrics] = None
    vector_store: Optional[VectorStoreMetrics] = None
    cache: Optional[CacheMetrics] = None
    rag_pipeline: Optional[RAGPipelineMetrics] = None


# ==================== ENDPOINTS ====================


@router.get("/metrics", response_model=PerformanceMetrics)
async def get_comprehensive_metrics(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get comprehensive performance metrics

    Returns metrics for:
    - LLM connection pool
    - Vector store optimization
    - Multi-layer cache
    - RAG pipeline
    """
    try:
        metrics = PerformanceMetrics()

        # LLM Pool metrics
        try:
            from core.llm_pool import get_global_llm_pool

            llm_pool = get_global_llm_pool()
            if llm_pool:
                pool_metrics = llm_pool.get_metrics()
                metrics.llm_pool = LLMPoolMetrics(**pool_metrics)
        except Exception as e:
            logger.warning(f"Failed to get LLM pool metrics: {e}")

        # Vector Store metrics
        try:
            from core.vector_optimizations import get_vector_store

            vector_store = await get_vector_store()
            if vector_store:
                vector_metrics = vector_store.get_metrics()
                metrics.vector_store = VectorStoreMetrics(**vector_metrics)
        except Exception as e:
            logger.warning(f"Failed to get vector store metrics: {e}")

        # Cache metrics
        try:
            from core.advanced_cache import get_cache_manager

            cache_manager = get_cache_manager()
            if cache_manager:
                cache_stats = cache_manager.get_metrics()
                metrics.cache = CacheMetrics(**cache_stats)
        except Exception as e:
            logger.warning(f"Failed to get cache metrics: {e}")

        # RAG Pipeline metrics
        try:
            from core.parallel_rag import get_rag_pipeline_stats

            rag_stats = get_rag_pipeline_stats()
            if rag_stats:
                metrics.rag_pipeline = RAGPipelineMetrics(**rag_stats)
        except Exception as e:
            logger.warning(f"Failed to get RAG pipeline metrics: {e}")

        return metrics

    except Exception as e:
        logger.error(f"Get comprehensive metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm-pool", response_model=LLMPoolMetrics)
async def get_llm_pool_stats(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Get LLM connection pool statistics

    Metrics:
    - Total requests processed
    - Active HTTP/2 connections
    - Average response time
    - Cache hit rate
    - Error count
    """
    try:
        from core.llm_pool import get_global_llm_pool

        llm_pool = get_global_llm_pool()
        if not llm_pool:
            return LLMPoolMetrics()

        pool_metrics = llm_pool.get_metrics()
        return LLMPoolMetrics(**pool_metrics)

    except Exception as e:
        logger.error(f"Get LLM pool stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector-store", response_model=VectorStoreMetrics)
async def get_vector_store_stats(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get vector store optimization statistics

    Metrics:
    - Total searches performed
    - Average search time (HNSW: O(log N))
    - Query cache hits/misses
    - Index size
    - HNSW optimization status
    """
    try:
        from core.vector_optimizations import get_vector_store

        vector_store = await get_vector_store()
        if not vector_store:
            return VectorStoreMetrics()

        vector_metrics = vector_store.get_metrics()
        return VectorStoreMetrics(**vector_metrics)

    except Exception as e:
        logger.error(f"Get vector store stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache", response_model=CacheMetrics)
async def get_cache_stats(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Get multi-layer cache statistics

    Metrics:
    - L1 (memory) hits
    - L2 (Redis) hits
    - Cache misses
    - Overall hit ratio
    - Total cached keys
    - Cache sizes (L1 + L2)
    - Eviction count
    """
    try:
        from core.advanced_cache import get_cache_manager

        cache_manager = get_cache_manager()
        if not cache_manager:
            return CacheMetrics()

        cache_stats = cache_manager.get_metrics()
        return CacheMetrics(**cache_stats)

    except Exception as e:
        logger.error(f"Get cache stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/clear/{tag}")
async def clear_cache_by_tag(
    tag: str, current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Clear cache entries by tag

    Common tags:
    - user - User-related data
    - session - Session data
    - question - Question cache
    - exam - Exam results
    - rag - RAG query results
    """
    try:
        from core.advanced_cache import get_cache_manager

        cache_manager = get_cache_manager()
        if not cache_manager:
            raise HTTPException(status_code=503, detail="Cache manager not available")

        await cache_manager.invalidate_by_tag(tag)

        return {"success": True, "message": f"Cache cleared for tag: {tag}", "tag": tag}

    except Exception as e:
        logger.error(f"Clear cache by tag error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag-pipeline", response_model=RAGPipelineMetrics)
async def get_rag_pipeline_stats(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get RAG pipeline performance statistics

    Metrics:
    - Total queries processed
    - Average query time (parallel optimization)
    - Parallel speedup factor (2-4x typical)
    - Average documents retrieved per query
    - Cross-encoder reranking status
    - Query expansion status
    """
    try:
        from core.parallel_rag import get_rag_pipeline_stats

        rag_stats = get_rag_pipeline_stats()
        if not rag_stats:
            return RAGPipelineMetrics()

        return RAGPipelineMetrics(**rag_stats)

    except Exception as e:
        logger.error(f"Get RAG pipeline stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for performance monitoring API"""
    return {
        "success": True,
        "data": {
            "service": "Performance Monitoring API",
            "status": "healthy",
            "features": [
                "LLM Connection Pool Metrics",
                "Vector Store HNSW Optimization",
                "Multi-layer Cache (L1 + L2)",
                "RAG Pipeline Parallelization",
                "Tag-based Cache Invalidation",
            ],
            "targets": {
                "chat_response_ms": "<200ms",
                "llm_generation_s": "<2s",
                "vector_search_ms": "<100ms",
                "rag_query_s": "<2s",
                "cache_hit_rate": ">85%",
                "parallel_speedup": ">2x",
            },
        },
        "message": "Performance Monitoring API çalışıyor",
    }


# ==================== UTILITY FUNCTIONS ====================


def _calculate_hit_rate(hits: int, total: int) -> float:
    """Calculate cache hit rate"""
    if total == 0:
        return 0.0
    return hits / total


def _calculate_speedup(parallel_time: float, sequential_time: float) -> float:
    """Calculate parallel speedup factor"""
    if parallel_time == 0:
        return 1.0
    return sequential_time / parallel_time
