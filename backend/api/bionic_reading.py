"""
Bionic Reading API Endpoints
/api/v1/revolutionary-features/bionic-reading/
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from core.bionic_reading_service import BionicReadingService
from core.cache import CacheService
from core.dependencies import AuthenticatedUser, get_cache_service, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bionic-reading", tags=["Bionic Reading"])


# Pydantic modelleri
class BionicReadingRequest(BaseModel):
    """Bionic Reading isteği"""

    text: str = Field(
        ..., min_length=1, max_length=10000, description="İşlenecek metin"
    )
    use_cache: bool = Field(True, description="Cache kullanılsın mı")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Metin boş olamaz")
        return v.strip()


class MultipleBionicReadingRequest(BaseModel):
    """Çoklu Bionic Reading isteği"""

    texts: list[str] = Field(
        ..., min_items=1, max_items=50, description="İşlenecek metinler"
    )
    use_cache: bool = Field(True, description="Cache kullanılsın mı")

    @field_validator("texts")
    @classmethod
    def validate_texts(cls, v):
        if not v:
            raise ValueError("En az bir metin gerekli")

        validated_texts = []
        for text in v:
            if text and text.strip():
                validated_texts.append(text.strip())

        if not validated_texts:
            raise ValueError("Geçerli metin bulunamadı")

        return validated_texts


class UserPreferencesRequest(BaseModel):
    """Kullanıcı tercihleri güncelleme isteği"""

    enabled: bool | None = Field(None, description="Bionic Reading etkin mi")
    bold_ratio: float | None = Field(None, ge=0.1, le=1.0, description="Bold oranı")
    min_word_length: int | None = Field(
        None, ge=1, le=10, description="Minimum kelime uzunluğu"
    )
    auto_apply: bool | None = Field(None, description="Otomatik uygula")
    font_weight: str | None = Field(None, description="Font kalınlığı")
    highlight_color: str | None = Field(None, description="Vurgulama rengi")


# Dependency injection
async def get_bionic_reading_service(
    cache_service: CacheService = Depends(get_cache_service),
) -> BionicReadingService:
    """Bionic Reading servisini al"""
    return BionicReadingService(cache_service=cache_service)


@router.post("/process")
async def process_text(
    request: BionicReadingRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    bionic_service: BionicReadingService = Depends(get_bionic_reading_service),
) -> dict[str, Any]:
    """
    Tek metin için Bionic Reading uygula

    Bu endpoint, verilen metni Türkçe Bionic Reading algoritması ile işler.
    Köklerin %40'ı bold yapılır, ekler hiç bold yapılmaz.
    """

    try:
        logger.info(
            f"Bionic Reading isteği - Kullanıcı: {current_user.id}, Metin uzunluğu: {len(request.text)}"
        )

        result = await bionic_service.process_text(
            text=request.text,
            user_id=current_user.id,
            use_cache=request.use_cache,
        )

        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Bionic Reading işlemi başarısız"),
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bionic Reading API hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bionic Reading işlemi sırasında hata oluştu",
        )


@router.post("/process-multiple")
async def process_multiple_texts(
    request: MultipleBionicReadingRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    bionic_service: BionicReadingService = Depends(get_bionic_reading_service),
) -> dict[str, Any]:
    """
    Birden fazla metin için Bionic Reading uygula

    Bu endpoint, birden fazla metni paralel olarak işler.
    Maksimum 50 metin aynı anda işlenebilir.
    """

    try:
        logger.info(
            f"Çoklu Bionic Reading isteği - Kullanıcı: {current_user.id}, Metin sayısı: {len(request.texts)}"
        )

        result = await bionic_service.process_multiple_texts(
            texts=request.texts,
            user_id=current_user.id,
            use_cache=request.use_cache,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Çoklu Bionic Reading API hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Çoklu Bionic Reading işlemi sırasında hata oluştu",
        )


@router.get("/preferences")
async def get_user_preferences(
    current_user: AuthenticatedUser = Depends(get_current_user),
    bionic_service: BionicReadingService = Depends(get_bionic_reading_service),
) -> dict[str, Any]:
    """
    Kullanıcının Bionic Reading tercihlerini getir

    Kullanıcının kişiselleştirilmiş Bionic Reading ayarlarını döndürür.
    """

    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kullanıcı kimliği gerekli",
            )

        result = await bionic_service.get_user_preferences(user_id)

        return {
            "success": True,
            "data": result,
            "message": "Tercihler başarıyla alındı",
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tercih getirme API hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tercihler alınırken hata oluştu",
        )


@router.put("/preferences")
async def update_user_preferences(
    request: UserPreferencesRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    bionic_service: BionicReadingService = Depends(get_bionic_reading_service),
) -> dict[str, Any]:
    """
    Kullanıcının Bionic Reading tercihlerini güncelle

    Kullanıcının kişiselleştirilmiş Bionic Reading ayarlarını günceller.
    """

    try:
        user_id = current_user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kullanıcı kimliği gerekli",
            )

        # Sadece None olmayan alanları güncelle
        preferences = {}
        for field, value in request.dict().items():
            if value is not None:
                preferences[field] = value

        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Güncellenecek tercih bulunamadı",
            )

        result = await bionic_service.update_user_preferences(user_id, preferences)

        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Tercih güncelleme başarısız"),
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tercih güncelleme API hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tercihler güncellenirken hata oluştu",
        )


@router.get("/stats")
async def get_service_stats(
    current_user: AuthenticatedUser = Depends(get_current_user),
    bionic_service: BionicReadingService = Depends(get_bionic_reading_service),
) -> dict[str, Any]:
    """
    Bionic Reading servis istatistiklerini getir

    Servis performansı ve kullanım istatistiklerini döndürür.
    Sadece admin kullanıcılar erişebilir.
    """

    try:
        # Admin kontrolü
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için admin yetkisi gerekli",
            )

        result = await bionic_service.get_service_stats()
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"İstatistik API hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="İstatistikler alınırken hata oluştu",
        )


@router.delete("/cache")
async def clear_cache(
    current_user: AuthenticatedUser = Depends(get_current_user),
    bionic_service: BionicReadingService = Depends(get_bionic_reading_service),
    clear_all: bool = False,
) -> dict[str, Any]:
    """
    Bionic Reading cache'ini temizle

    Kullanıcının kendi cache'ini veya (admin ise) tüm cache'i temizler.
    """

    try:
        user_id = current_user.id
        user_role = current_user.role.value

        if clear_all and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tüm cache'i temizlemek için admin yetkisi gerekli",
            )

        # Admin tüm cache'i temizleyebilir, normal kullanıcı sadece kendi cache'ini
        target_user_id = None if (clear_all and user_role == "admin") else user_id

        result = await bionic_service.clear_cache(target_user_id)

        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Cache temizleme başarısız"),
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache temizleme API hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cache temizlenirken hata oluştu",
        )


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Bionic Reading servis sağlık kontrolü

    Servisin çalışır durumda olup olmadığını kontrol eder.
    """

    try:
        # Basit test metni ile servis kontrolü
        test_service = BionicReadingService()
        test_result = await test_service.process_text("test metni")

        return {
            "success": True,
            "data": {
                "service_status": "healthy",
                "test_processing": test_result.get("success", False),
                "timestamp": datetime.now().isoformat(),
            },
            "message": "Bionic Reading servisi çalışıyor",
        }

    except Exception as e:
        logger.error(f"Sağlık kontrolü hatası: {e}")
        return {
            "success": False,
            "data": {
                "service_status": "unhealthy",
                "error": "Internal error",
                "timestamp": datetime.now().isoformat(),
            },
            "message": "Bionic Reading servisi çalışmıyor",
        }
