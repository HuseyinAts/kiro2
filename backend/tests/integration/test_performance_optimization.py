"""
Performance Optimization Tests
Performans optimizasyonu testleri
"""

import asyncio
import time
from unittest.mock import Mock

import pytest

# Test edilecek modüller
from core.cache import CacheManager, cache_result
from core.database_optimizer import QueryOptimizer
from core.performance_middleware import RateLimiter, SystemMonitor
from core.revolutionary_optimizer import (
    IRTMorphologyOptimizer,
    VARKFelderOptimizer,
    ZPDMaarifOptimizer,
    revolutionary_optimizer,
)


class TestCacheManager:
    """Cache Manager testleri"""

    @pytest.fixture
    async def cache_manager(self):
        """Test cache manager"""
        manager = CacheManager("redis://localhost:6379")
        await manager.initialize()
        yield manager
        await manager.close()

    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache_manager):
        """Cache set/get işlemleri"""
        # Test verisi
        test_key = "test_key"
        test_value = {"message": "test", "number": 42}

        # Cache'e kaydet
        result = await cache_manager.set(test_key, test_value, expire=60)
        assert result is True

        # Cache'den al
        cached_value = await cache_manager.get(test_key)
        assert cached_value == test_value

    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache_manager):
        """Cache expiration testi"""
        test_key = "expire_test"
        test_value = "expire_value"

        # 1 saniye expire ile kaydet
        await cache_manager.set(test_key, test_value, expire=1)

        # Hemen al - var olmalı
        cached_value = await cache_manager.get(test_key)
        assert cached_value == test_value

        # 2 saniye bekle
        await asyncio.sleep(2)

        # Artık yok olmalı
        cached_value = await cache_manager.get(test_key)
        assert cached_value is None

    @pytest.mark.asyncio
    async def test_cache_hash_operations(self, cache_manager):
        """Hash operasyonları testi"""
        hash_key = "test_hash"
        hash_data = {"field1": "value1", "field2": {"nested": "value"}, "field3": 123}

        # Hash kaydet
        result = await cache_manager.set_hash(hash_key, hash_data, expire=60)
        assert result is True

        # Tek field al
        field_value = await cache_manager.get_hash(hash_key, "field1")
        assert field_value == "value1"

        # Tüm hash'i al
        all_hash = await cache_manager.get_hash(hash_key)
        assert all_hash == hash_data

    @pytest.mark.asyncio
    async def test_cache_list_operations(self, cache_manager):
        """Liste operasyonları testi"""
        list_key = "test_list"
        test_items = ["item1", "item2", {"complex": "item"}]

        # Liste'ye ekle
        for item in test_items:
            result = await cache_manager.add_to_list(list_key, item)
            assert result is True

        # Liste'yi al
        cached_list = await cache_manager.get_list(list_key)
        # Redis LPUSH kullandığı için ters sırada
        assert cached_list == list(reversed(test_items))

    def test_cache_decorator(self):
        """Cache decorator testi"""
        call_count = 0

        @cache_result("test_func", expire=60)
        async def test_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        # İlk çağrı - fonksiyon çalışmalı
        result1 = asyncio.run(test_function(1, 2))
        assert result1 == 3
        assert call_count == 1

        # İkinci çağrı - cache'den dönmeli
        result2 = asyncio.run(test_function(1, 2))
        assert result2 == 3
        assert call_count == 1  # Artmamalı


class TestQueryOptimizer:
    """Database Query Optimizer testleri"""

    def test_query_performance_tracking(self):
        """Query performans takibi"""
        optimizer = QueryOptimizer()

        # Test sorgusu
        query_name = "test_query"
        execution_time = 0.5
        query_sql = "SELECT * FROM test_table"

        # Performans logla
        optimizer.log_query_performance(query_name, execution_time, query_sql)

        # İstatistikleri kontrol et
        stats = optimizer.get_performance_stats()
        assert query_name in stats
        assert stats[query_name]["total_executions"] == 1
        assert stats[query_name]["avg_time"] == execution_time
        assert stats[query_name]["max_time"] == execution_time

    def test_slow_query_detection(self):
        """Yavaş sorgu tespiti"""
        optimizer = QueryOptimizer()
        optimizer.slow_query_threshold = 0.5  # 0.5 saniye threshold

        # Yavaş sorgu
        optimizer.log_query_performance("slow_query", 1.0, "SELECT * FROM big_table")

        # Hızlı sorgu
        optimizer.log_query_performance("fast_query", 0.1, "SELECT id FROM small_table")

        stats = optimizer.get_performance_stats()
        assert stats["slow_query"]["slow_queries"] == 1
        assert stats["fast_query"]["slow_queries"] == 0


class TestRevolutionaryOptimizer:
    """Revolutionary Features Optimizer testleri"""

    @pytest.mark.asyncio
    async def test_vark_felder_optimization(self):
        """VARK + Felder-Silverman optimizasyon testi"""
        optimizer = VARKFelderOptimizer()

        # Test verisi
        student_id = "test_student"
        behavioral_data = {
            "video_watch_time": 100,
            "audio_content_time": 50,
            "text_reading_time": 80,
            "interactive_time": 120,
        }
        questionnaire_responses = [
            "Görsel materyalleri tercih ederim",
            "Dinleyerek öğrenirim",
            "Okuyarak anlıyorum",
        ]

        # Hibrit profil hesapla
        start_time = time.time()
        profile = await optimizer.calculate_hybrid_profile_optimized(
            student_id, behavioral_data, questionnaire_responses
        )
        execution_time = time.time() - start_time

        # Sonuçları kontrol et
        assert profile["student_id"] == student_id
        assert "vark_profile" in profile
        assert "felder_profile" in profile
        assert "hybrid_code" in profile
        assert "confidence_level" in profile

        # Performans kontrolü (1 saniyeden az olmalı)
        assert execution_time < 1.0

        # VARK skorları toplamı 1'e yakın olmalı
        vark_total = sum(profile["vark_profile"].values())
        assert 0.9 <= vark_total <= 1.1

    @pytest.mark.asyncio
    async def test_zpd_maarif_optimization(self):
        """ZPD + Maarif optimizasyon testi"""
        optimizer = ZPDMaarifOptimizer()

        # Test verisi
        student_current_level = 0.6
        subject = "matematik"
        cultural_context = {
            "group_learning_preference": 0.8,
            "teacher_respect_level": 0.9,
            "family_involvement": 0.7,
            "peer_competition": 0.6,
            "authority_acceptance": 0.8,
        }

        # ZPD hesapla
        start_time = time.time()
        zpd_result = await optimizer.calculate_turkish_zpd_optimized(
            student_current_level, subject, cultural_context
        )
        execution_time = time.time() - start_time

        # Sonuçları kontrol et
        assert zpd_result["lower_bound"] == student_current_level
        assert zpd_result["upper_bound"] > student_current_level
        assert zpd_result["optimal_challenge"] > student_current_level
        assert "cultural_factors" in zpd_result
        assert "maarif_alignment" in zpd_result

        # Performans kontrolü
        assert execution_time < 0.5

    @pytest.mark.asyncio
    async def test_irt_morphology_optimization(self):
        """IRT + Morfoloji optimizasyon testi"""
        optimizer = IRTMorphologyOptimizer()

        # Test verisi
        question_text = "Çekoslovakyalılaştıramadıklarımızdanmısınız kelimesinin morfolojik yapısını analiz ediniz."
        student_ability = 0.5
        question_difficulty = 0.3
        question_discrimination = 1.2

        # IRT hesapla
        start_time = time.time()
        irt_result = await optimizer.calculate_turkish_irt_optimized(
            question_text, student_ability, question_difficulty, question_discrimination
        )
        execution_time = time.time() - start_time

        # Sonuçları kontrol et
        assert 0.0 <= irt_result["probability"] <= 1.0
        assert irt_result["morphological_complexity"] > 0
        assert irt_result["adjusted_difficulty"] >= question_difficulty
        assert "morphology_impact" in irt_result

        # Performans kontrolü
        assert execution_time < 0.3

    def test_performance_tracking_decorator(self):
        """Performans takip decorator testi"""

        @revolutionary_optimizer.track_performance("test_algorithm")
        async def test_algorithm(x, y):
            await asyncio.sleep(0.1)  # Simüle edilmiş işlem
            return x * y

        # İlk çağrı
        result1 = asyncio.run(test_algorithm(2, 3))
        assert result1 == 6

        # İkinci çağrı (cache'den dönmeli)
        result2 = asyncio.run(test_algorithm(2, 3))
        assert result2 == 6

        # Metrikleri kontrol et
        metrics = revolutionary_optimizer.metrics
        assert "test_algorithm" in metrics
        assert metrics["test_algorithm"]["total_executions"] == 2
        assert metrics["test_algorithm"]["cache_hits"] == 1


class TestPerformanceMiddleware:
    """Performance Middleware testleri"""

    def test_system_monitor(self):
        """Sistem monitör testi"""
        monitor = SystemMonitor()

        # Monitoring başlat
        monitor.start_monitoring(interval=1)
        assert monitor.monitoring is True

        # Kısa süre bekle
        time.sleep(2)

        # Metrikleri kontrol et
        current_metrics = monitor.get_current_metrics()
        assert "cpu_percent" in current_metrics
        assert "memory_percent" in current_metrics

        # Monitoring durdur
        monitor.stop_monitoring()
        assert monitor.monitoring is False

    @pytest.mark.asyncio
    async def test_rate_limiter(self):
        """Rate limiter testi"""
        rate_limiter = RateLimiter(requests_per_minute=5)  # 5 req/min

        # Mock request
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        # Mock call_next
        async def mock_call_next(request):
            return Mock(status_code=200)

        # 5 request gönder - hepsi geçmeli
        for i in range(5):
            response = await rate_limiter(mock_request, mock_call_next)
            assert response.status_code == 200

        # 6. request - rate limit'e takılmalı
        response = await rate_limiter(mock_request, mock_call_next)
        assert response.status_code == 429


class TestPerformanceIntegration:
    """Entegrasyon performans testleri"""

    @pytest.mark.asyncio
    async def test_full_optimization_pipeline(self):
        """Tam optimizasyon pipeline testi"""

        # Cache manager
        cache_manager = CacheManager()
        await cache_manager.initialize()

        # Revolutionary optimizer
        vark_optimizer = VARKFelderOptimizer()

        try:
            # Test verisi
            student_id = "integration_test_student"
            behavioral_data = {
                "video_watch_time": 150,
                "audio_content_time": 75,
                "text_reading_time": 100,
                "interactive_time": 200,
            }
            questionnaire_responses = [
                "Görsel öğrenmeyi tercih ederim",
                "Pratik yaparak öğrenirim",
            ]

            # İlk hesaplama - cache miss
            start_time = time.time()
            profile1 = await vark_optimizer.calculate_hybrid_profile_optimized(
                student_id, behavioral_data, questionnaire_responses
            )
            first_execution_time = time.time() - start_time

            # İkinci hesaplama - cache hit olmalı
            start_time = time.time()
            profile2 = await vark_optimizer.calculate_hybrid_profile_optimized(
                student_id, behavioral_data, questionnaire_responses
            )
            second_execution_time = time.time() - start_time

            # Sonuçlar aynı olmalı
            assert profile1 == profile2

            # İkinci çağrı daha hızlı olmalı (cache hit)
            assert second_execution_time < first_execution_time

            # Cache performansı
            assert second_execution_time < 0.1  # 100ms'den az

        finally:
            await cache_manager.close()

    def test_memory_usage_optimization(self):
        """Memory kullanım optimizasyonu testi"""
        import gc

        import psutil

        # Başlangıç memory kullanımı
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Büyük veri yapıları oluştur
        large_data = []
        for i in range(10000):
            large_data.append(
                {"id": i, "data": f"test_data_{i}" * 100, "nested": {"value": i * 2}}
            )

        # Memory kullanımı artmış olmalı
        after_creation_memory = process.memory_info().rss
        assert after_creation_memory > initial_memory

        # Veriyi temizle
        del large_data
        gc.collect()

        # Memory kullanımı azalmış olmalı
        after_cleanup_memory = process.memory_info().rss
        assert after_cleanup_memory < after_creation_memory

    @pytest.mark.asyncio
    async def test_concurrent_performance(self):
        """Eşzamanlı işlem performansı testi"""

        async def mock_heavy_operation(delay: float):
            """Ağır işlem simülasyonu"""
            await asyncio.sleep(delay)
            return f"result_{delay}"

        # Sıralı işlem
        start_time = time.time()
        sequential_results = []
        for i in range(5):
            result = await mock_heavy_operation(0.1)
            sequential_results.append(result)
        sequential_time = time.time() - start_time

        # Paralel işlem
        start_time = time.time()
        tasks = [mock_heavy_operation(0.1) for _ in range(5)]
        parallel_results = await asyncio.gather(*tasks)
        parallel_time = time.time() - start_time

        # Paralel işlem daha hızlı olmalı
        assert parallel_time < sequential_time
        assert len(parallel_results) == len(sequential_results)

        # Performans iyileştirmesi en az %50 olmalı
        improvement = (sequential_time - parallel_time) / sequential_time
        assert improvement > 0.5


if __name__ == "__main__":
    # Test'leri çalıştır
    pytest.main([__file__, "-v", "--tb=short"])
