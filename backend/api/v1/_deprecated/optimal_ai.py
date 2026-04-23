"""
Optimal Hybrid AI API Endpoints
FastAPI entegrasyonu
"""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

try:
    from optimal_hybrid_system import OptimalHybridSystem, SmartRouter
except ImportError:
    OptimalHybridSystem = None
    SmartRouter = None

logger = structlog.get_logger()

# Router
router = APIRouter(prefix="/api/v1/ai", tags=["Optimal AI"])

# Global sistem instance
_system_instance: OptimalHybridSystem | None = None


def get_system() -> OptimalHybridSystem:
    """Sistem instance'ını al (singleton)"""
    global _system_instance
    if _system_instance is None:
        _system_instance = OptimalHybridSystem()
    return _system_instance


# Request/Response modelleri
class AIQueryRequest(BaseModel):
    """AI sorgu isteği"""
    query: str = Field(..., description="Kullanıcı sorusu", min_length=1, max_length=10000)
    context: dict[str, Any] | None = Field(None, description="Ek bağlam bilgisi")
    use_cache: bool = Field(True, description="Cache kullan")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "query": "Python'da async/await nasıl kullanılır?",
            "context": {
                "language": "python",
                "level": "intermediate"
            },
            "use_cache": True
        }
    })


class AIQueryResponse(BaseModel):
    """AI sorgu yanıtı"""
    success: bool
    response: str
    model: str
    cached: bool
    duration: float
    cost: float
    routing_info: dict[str, Any]


class RoutingInfoRequest(BaseModel):
    """Routing bilgi isteği"""
    query: str = Field(..., description="Analiz edilecek sorgu")
    context: dict[str, Any] | None = Field(None, description="Ek bağlam")


class RoutingInfoResponse(BaseModel):
    """Routing bilgi yanıtı"""
    complexity: int
    model_type: str
    estimated_time: float
    estimated_cost: float


class SystemMetricsResponse(BaseModel):
    """Sistem metrikleri yanıtı"""
    total_requests: int
    total_cost: float
    total_time: float
    avg_time: float
    avg_cost: float
    cache_hit_rate: dict[str, float]


# Endpoints
@router.post("/query", response_model=AIQueryResponse)
async def ai_query(
    request: AIQueryRequest,
    system: OptimalHybridSystem = Depends(get_system)
):
    """
    AI sorgusu gönder
    
    Sistem otomatik olarak en uygun modeli seçer:
    - Basit sorular → Claude Only
    - Orta seviye → Gemini Assist
    - Karmaşık → Gemini Thinking
    """
    try:
        result = await system.process_query(
            query=request.query,
            context=request.context,
            use_cache=request.use_cache
        )

        return AIQueryResponse(
            success=True,
            response=result["response"],
            model=result["model"],
            cached=result["cached"],
            duration=result["duration"],
            cost=result["cost"],
            routing_info=result["routing_info"]
        )

    except ValueError as e:
        logger.error("api_key_missing", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin."
        )

    except Exception as e:
        logger.error("query_failed", error=str(e), query=request.query[:100])
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/routing-info", response_model=RoutingInfoResponse)
async def get_routing_info(request: RoutingInfoRequest):
    """
    Sorgu için routing bilgisi al
    
    Hangi modelin kullanılacağını ve tahmini maliyet/süreyi gösterir.
    """
    try:
        router = SmartRouter()
        info = router.get_routing_info(request.query, request.context)

        return RoutingInfoResponse(**info)

    except Exception as e:
        logger.error("routing_info_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/metrics", response_model=SystemMetricsResponse)
async def get_metrics(system: OptimalHybridSystem = Depends(get_system)):
    """
    Sistem metriklerini al
    
    Toplam istek sayısı, maliyet, cache hit rate vb.
    """
    try:
        metrics = system.get_metrics()
        return SystemMetricsResponse(**metrics)

    except Exception as e:
        logger.error("metrics_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/health")
async def health_check():
    """
    Sistem sağlık kontrolü
    """
    import os

    gemini_key = os.getenv("GOOGLE_API_KEY")
    claude_key = os.getenv("ANTHROPIC_API_KEY")

    return {
        "status": "healthy",
        "gemini_configured": bool(gemini_key),
        "claude_configured": bool(claude_key and claude_key != "your_anthropic_api_key_here"),
        "system_ready": bool(gemini_key and claude_key)
    }
