"""
Bionic Reading Servisi
Türkçe Bionic Reading algoritmasını servis katmanında sunar
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from algorithms.turkish_bionic_reading import TurkishBionicReading

from .cache import CacheManager

logger = logging.getLogger(__name__)


class BionicReadingService:
    """
    Bionic Reading servisi

    Cache desteği ve performans optimizasyonu ile
    Türkçe Bionic Reading algoritmasını sunar
    """

    def __init__(self, cache_service: CacheManager | None = None):
        self.bionic_reader = TurkishBionicReading()
        self.cache_service = cache_service

        # Cache ayarları
        self.cache_ttl = timedelta(hours=24)  # 24 saat cache
        self.cache_prefix = "bionic_reading:"

        # İstatistikler
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_processing_time_ms": 0,
            "average_processing_time_ms": 0,
        }

    async def process_text(
        self, text: str, user_id: str | None = None, use_cache: bool = True
    ) -> dict[str, Any]:
        """
        Metni Bionic Reading ile işle

        Args:
            text: İşlenecek metin
            user_id: Kullanıcı ID (isteğe bağlı)
            use_cache: Cache kullanılsın mı

        Returns:
            Dict: İşlem sonucu
        """

        self.stats["total_requests"] += 1

        try:
            # Cache kontrolü
            cache_key = None
            if use_cache and self.cache_service:
                cache_key = self._generate_cache_key(text)
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    self.stats["cache_hits"] += 1
                    return cached_result

            self.stats["cache_misses"] += 1

            # Bionic Reading uygula
            result = await self.bionic_reader.apply_bionic_reading(
                text=text, use_cache=use_cache
            )

            # İstatistikleri güncelle
            self.stats["total_processing_time_ms"] += result.processing_time_ms
            self.stats["average_processing_time_ms"] = (
                self.stats["total_processing_time_ms"] / self.stats["total_requests"]
            )

            # Sonucu formatla
            response = {
                "success": result.success,
                "data": {
                    "original_text": result.original_text,
                    "bionic_text": result.bionic_text,
                    "word_count": result.word_count,
                    "bold_ratio": result.bold_ratio,
                    "processing_time_ms": result.processing_time_ms,
                },
                "message": "Bionic Reading başarıyla uygulandı"
                if result.success
                else "İşlem başarısız",
                "timestamp": datetime.now().isoformat(),
            }

            if result.error_message:
                response["error"] = result.error_message

            # Cache'e kaydet
            if use_cache and self.cache_service and cache_key and result.success:
                await self._save_to_cache(cache_key, response)

            return response

        except Exception as e:
            logger.error(f"Bionic Reading servisi hatası: {e}")
            return {
                "success": False,
                "data": None,
                "message": f"Bionic Reading işlemi başarısız: {e!s}",
                "timestamp": datetime.now().isoformat(),
            }

    async def process_multiple_texts(
        self, texts: list[str], user_id: str | None = None, use_cache: bool = True
    ) -> dict[str, Any]:
        """
        Birden fazla metni paralel olarak işle

        Args:
            texts: İşlenecek metinler listesi
            user_id: Kullanıcı ID
            use_cache: Cache kullanılsın mı

        Returns:
            Dict: İşlem sonuçları
        """

        try:
            # Paralel işleme
            tasks = [self.process_text(text, user_id, use_cache) for text in texts]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Sonuçları formatla
            processed_results = []
            successful_count = 0

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(
                        {
                            "index": i,
                            "success": False,
                            "error": str(result),
                            "original_text": texts[i] if i < len(texts) else "",
                        }
                    )
                else:
                    processed_results.append({"index": i, **result})
                    if result.get("success", False):
                        successful_count += 1

            return {
                "success": True,
                "data": {
                    "results": processed_results,
                    "total_texts": len(texts),
                    "successful_count": successful_count,
                    "failed_count": len(texts) - successful_count,
                },
                "message": f"{successful_count}/{len(texts)} metin başarıyla işlendi",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Çoklu metin işleme hatası: {e}")
            return {
                "success": False,
                "data": None,
                "message": f"Çoklu metin işleme başarısız: {e!s}",
                "timestamp": datetime.now().isoformat(),
            }

    async def get_user_preferences(self, user_id: str) -> dict[str, Any]:
        """
        Kullanıcının Bionic Reading tercihlerini getir

        Args:
            user_id: Kullanıcı ID

        Returns:
            Dict: Kullanıcı tercihleri
        """

        try:
            if not self.cache_service:
                return self._get_default_preferences()

            cache_key = f"{self.cache_prefix}preferences:{user_id}"
            preferences = await self.cache_service.get(cache_key)

            if preferences:
                return preferences
            # Varsayılan tercihleri döndür ve cache'e kaydet
            default_prefs = self._get_default_preferences()
            await self.cache_service.set(cache_key, default_prefs, ttl=self.cache_ttl)
            return default_prefs

        except Exception as e:
            logger.error(f"Kullanıcı tercihleri getirme hatası: {e}")
            return self._get_default_preferences()

    async def update_user_preferences(
        self, user_id: str, preferences: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Kullanıcının Bionic Reading tercihlerini güncelle

        Args:
            user_id: Kullanıcı ID
            preferences: Yeni tercihler

        Returns:
            Dict: Güncelleme sonucu
        """

        try:
            # Tercihleri doğrula
            validated_prefs = self._validate_preferences(preferences)

            if self.cache_service:
                cache_key = f"{self.cache_prefix}preferences:{user_id}"
                await self.cache_service.set(
                    cache_key, validated_prefs, ttl=self.cache_ttl
                )

            return {
                "success": True,
                "data": validated_prefs,
                "message": "Tercihler başarıyla güncellendi",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Tercih güncelleme hatası: {e}")
            return {
                "success": False,
                "data": None,
                "message": f"Tercih güncelleme başarısız: {e!s}",
                "timestamp": datetime.now().isoformat(),
            }

    async def get_service_stats(self) -> dict[str, Any]:
        """Servis istatistiklerini getir"""

        cache_stats = {}
        if self.cache_service:
            try:
                cache_stats = await self.cache_service.get_stats()
            except Exception as e:
                logger.warning(f"Cache istatistikleri alınamadı: {e}")

        algorithm_stats = self.bionic_reader.get_cache_stats()

        return {
            "success": True,
            "data": {
                "service_stats": self.stats,
                "cache_stats": cache_stats,
                "algorithm_stats": algorithm_stats,
            },
            "message": "İstatistikler başarıyla alındı",
            "timestamp": datetime.now().isoformat(),
        }

    async def clear_cache(self, user_id: str | None = None) -> dict[str, Any]:
        """Cache'i temizle"""

        try:
            # Algoritma cache'ini temizle
            self.bionic_reader.clear_cache()

            # Servis cache'ini temizle
            if self.cache_service:
                if user_id:
                    # Belirli kullanıcının cache'ini temizle
                    pattern = f"{self.cache_prefix}*:{user_id}"
                    await self.cache_service.delete_pattern(pattern)
                else:
                    # Tüm Bionic Reading cache'ini temizle
                    pattern = f"{self.cache_prefix}*"
                    await self.cache_service.delete_pattern(pattern)

            return {
                "success": True,
                "data": None,
                "message": "Cache başarıyla temizlendi",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Cache temizleme hatası: {e}")
            return {
                "success": False,
                "data": None,
                "message": f"Cache temizleme başarısız: {e!s}",
                "timestamp": datetime.now().isoformat(),
            }

    def _generate_cache_key(self, text: str) -> str:
        """Cache anahtarı oluştur"""
        import hashlib

        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        return f"{self.cache_prefix}text:{text_hash}"

    async def _get_from_cache(self, cache_key: str) -> dict[str, Any] | None:
        """Cache'den veri al"""
        try:
            if self.cache_service:
                return await self.cache_service.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache okuma hatası: {e}")
        return None

    async def _save_to_cache(self, cache_key: str, data: dict[str, Any]):
        """Cache'e veri kaydet"""
        try:
            if self.cache_service:
                await self.cache_service.set(cache_key, data, ttl=self.cache_ttl)
        except Exception as e:
            logger.warning(f"Cache yazma hatası: {e}")

    def _get_default_preferences(self) -> dict[str, Any]:
        """Varsayılan kullanıcı tercihlerini döndür"""
        return {
            "enabled": True,
            "bold_ratio": 0.4,
            "min_word_length": 3,
            "auto_apply": False,
            "font_weight": "bold",
            "highlight_color": "#000000",
        }

    def _validate_preferences(self, preferences: dict[str, Any]) -> dict[str, Any]:
        """Kullanıcı tercihlerini doğrula"""

        default_prefs = self._get_default_preferences()
        validated = default_prefs.copy()

        # Güvenli alanları güncelle
        safe_fields = [
            "enabled",
            "bold_ratio",
            "min_word_length",
            "auto_apply",
            "font_weight",
            "highlight_color",
        ]

        for field in safe_fields:
            if field in preferences:
                if field == "bold_ratio" and isinstance(
                    preferences[field], (int, float)
                ):
                    validated[field] = max(0.1, min(1.0, preferences[field]))
                elif field == "min_word_length" and isinstance(preferences[field], int):
                    validated[field] = max(1, min(10, preferences[field]))
                elif (
                    (field == "enabled" and isinstance(preferences[field], bool))
                    or (field == "auto_apply" and isinstance(preferences[field], bool))
                    or (
                        field in ["font_weight", "highlight_color"]
                        and isinstance(preferences[field], str)
                    )
                ):
                    validated[field] = preferences[field]

        return validated
