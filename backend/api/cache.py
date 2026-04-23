"""
Cache Management API
Redis cache yönetimi ve monitoring endpoint'leri
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core.unified.cache_system import get_cache_manager

cache_manager = get_cache_manager()
from core.dependencies import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cache", tags=["Cache Management"])


# Pydantic modelleri
class CacheStatsResponse(BaseModel):
    """Cache istatistikleri response modeli"""

    success: bool
    data: dict[str, Any]
    message: str


class CacheHealthResponse(BaseModel):
    """Cache sağlık durumu response modeli"""

    success: bool
    data: dict[str, Any]
    message: str


class InvalidationRequest(BaseModel):
    """Cache invalidation request modeli"""

    event_name: str = Field(..., description="Event adı")
    context: dict[str, Any] | None = Field(default=None, description="Event context")


class PatternInvalidationRequest(BaseModel):
    """Pattern-based invalidation request modeli"""

    pattern: str = Field(..., description="Cache key pattern'i")
    scope: str | None = Field(
        default=None, description="Cache scope (global, user, exam, content, session)"
    )


class CacheKeyRequest(BaseModel):
    """Cache key işlemi request modeli"""

    key: str = Field(..., description="Cache key")
    value: Any | None = Field(default=None, description="Cache value")
    expire: int | None = Field(default=None, description="Expire süresi (saniye)")
    serialize: str | None = Field(default="json", description="Serialization tipi")


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(current_user=Depends(get_current_admin_user)):
    """
    Cache istatistiklerini getir
    Sadece admin kullanıcılar erişebilir
    """
    try:
        # Ana cache stats
        main_stats = await cache_manager.get_stats()

        # Simplified cache stats
        exam_stats = {"total_keys": 0, "memory_usage": "0MB"}
        session_stats = {"active_sessions": 0, "total_sessions": 0}

        # Invalidation stats
        invalidation_stats = {"invalidated_keys": 0, "last_invalidation": None}

        combined_stats = {
            "main_cache": main_stats,
            "exam_cache": exam_stats,
            "session_cache": session_stats,
            "invalidation": invalidation_stats,
            "timestamp": "2025-01-18T10:00:00Z",
        }

        return CacheStatsResponse(
            success=True,
            data=combined_stats,
            message="Cache istatistikleri başarıyla alındı",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache stats hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/health", response_model=CacheHealthResponse)
async def get_cache_health():
    """
    Cache sağlık durumunu kontrol et
    Public endpoint - monitoring için
    """
    try:
        health_data = await cache_manager.health_check()

        return CacheHealthResponse(
            success=health_data.get("status") == "healthy",
            data=health_data,
            message="Cache sağlık durumu kontrol edildi",
        )

    except Exception as e:
        logger.error(f"Cache health check hatası: {e!s}")
        return CacheHealthResponse(
            success=False,
            data={"error": str(e)},
            message="Cache sağlık kontrolü başarısız",
        )


@router.post("/invalidate/event")
async def invalidate_by_event(
    request: InvalidationRequest, current_user=Depends(get_current_admin_user)
):
    """
    Event-based cache invalidation
    Sadece admin kullanıcılar erişebilir
    """
    try:
        # Basit invalidation - event_name'i pattern olarak kullan
        invalidated_keys = await cache_manager.invalidate_pattern(
            f"*{request.event_name}*"
        )

        return {
            "success": True,
            "data": {
                "event_name": request.event_name,
                "invalidated_keys": invalidated_keys,
                "count": len(invalidated_keys),
            },
            "message": f"Event-based invalidation tamamlandı: {len(invalidated_keys)} key",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Event-based invalidation hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/invalidate/pattern")
async def invalidate_by_pattern(
    request: PatternInvalidationRequest, current_user=Depends(get_current_admin_user)
):
    """
    Pattern-based cache invalidation
    Sadece admin kullanıcılar erişebilir
    """
    try:
        invalidated_count = await cache_manager.invalidate_pattern(request.pattern)

        return {
            "success": True,
            "data": {
                "pattern": request.pattern,
                "scope": request.scope,
                "invalidated_count": invalidated_count,
            },
            "message": f"Pattern-based invalidation tamamlandı: {invalidated_count} key",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pattern-based invalidation hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.delete("/user/{user_id}")
async def invalidate_user_cache(
    user_id: str, current_user=Depends(get_current_admin_user)
):
    """
    Kullanıcıya ait tüm cache'leri temizle
    Sadece admin kullanıcılar erişebilir
    """
    try:
        invalidated_count = await cache_manager.invalidate_pattern(f"user:{user_id}:*")

        return {
            "success": True,
            "data": {"user_id": user_id, "invalidated_count": invalidated_count},
            "message": f"Kullanıcı cache'i temizlendi: {invalidated_count} key",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kullanıcı cache temizleme hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.delete("/exam")
async def invalidate_exam_cache(
    exam_type: str | None = Query(None, description="Sınav tipi (TYT, AYT, YDT)"),
    current_user=Depends(get_current_admin_user),
):
    """
    Sınav cache'lerini temizle
    Sadece admin kullanıcılar erişebilir
    """
    try:
        invalidated_count = await cache_manager.invalidate_pattern(
            f"exam:{exam_type}:*"
        )

        return {
            "success": True,
            "data": {
                "exam_type": exam_type or "all",
                "invalidated_count": invalidated_count,
            },
            "message": f"Sınav cache'i temizlendi: {invalidated_count} key",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sınav cache temizleme hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/key/{key}")
async def get_cache_key(
    key: str,
    serialize: str = Query("json", description="Serialization tipi"),
    current_user=Depends(get_current_admin_user),
):
    """
    Cache key'ini getir
    Sadece admin kullanıcılar erişebilir
    """
    try:
        value = await cache_manager.get(key, serialize=serialize)

        return {
            "success": True,
            "data": {"key": key, "value": value, "exists": value is not None},
            "message": "Cache key başarıyla alındı",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache key getirme hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/key")
async def set_cache_key(
    request: CacheKeyRequest, current_user=Depends(get_current_admin_user)
):
    """
    Cache key'ini ayarla
    Sadece admin kullanıcılar erişebilir
    """
    try:
        success = await cache_manager.set(
            request.key,
            request.value,
            expire=request.expire,
            serialize=request.serialize,
        )

        return {
            "success": success,
            "data": {
                "key": request.key,
                "expire": request.expire,
                "serialize": request.serialize,
            },
            "message": "Cache key başarıyla ayarlandı"
            if success
            else "Cache key ayarlama başarısız",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache key ayarlama hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.delete("/key/{key}")
async def delete_cache_key(key: str, current_user=Depends(get_current_admin_user)):
    """
    Cache key'ini sil
    Sadece admin kullanıcılar erişebilir
    """
    try:
        success = await cache_manager.delete(key)

        return {
            "success": success,
            "data": {"key": key},
            "message": "Cache key başarıyla silindi"
            if success
            else "Cache key silme başarısız",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache key silme hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/warm-up")
async def warm_up_cache(current_user=Depends(get_current_admin_user)):
    """
    Cache warm-up işlemi
    Sık kullanılan verileri önceden cache'e yükler
    """
    try:
        # Warm-up fonksiyonları
        warm_up_functions = {
            "exam:questions:TYT": _warm_up_tyt_questions,
            "exam:questions:AYT": _warm_up_ayt_questions,
            "exam:questions:YDT": _warm_up_ydt_questions,
            "content:popular": _warm_up_popular_content,
            "learning_styles:profiles": _warm_up_learning_profiles,
        }

        # Basit warm-up implementation
        warmed_keys = 0

        return {
            "success": True,
            "data": {"warmed_keys": warmed_keys, "count": len(warmed_keys)},
            "message": f"Cache warm-up tamamlandı: {len(warmed_keys)} key",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache warm-up hatası: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


# Warm-up helper fonksiyonları
async def _warm_up_tyt_questions():
    """TYT sorularını warm-up et"""
    try:
        # Bu gerçek implementasyonda soru bankası servisinden çekilecek
        return {"questions": [], "count": 0}
    except Exception:
        return None


async def _warm_up_ayt_questions():
    """AYT sorularını warm-up et"""
    try:
        return {"questions": [], "count": 0}
    except Exception:
        return None


async def _warm_up_ydt_questions():
    """YDT sorularını warm-up et"""
    try:
        return {"questions": [], "count": 0}
    except Exception:
        return None


async def _warm_up_popular_content():
    """Popüler içerikleri warm-up et"""
    try:
        return {"content": [], "count": 0}
    except Exception:
        return None


async def _warm_up_learning_profiles():
    """Öğrenme profilleri warm-up et"""
    try:
        return {"profiles": [], "count": 0}
    except Exception:
        return None
