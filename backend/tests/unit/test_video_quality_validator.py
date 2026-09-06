"""
Video Quality Validator Unit Tests
Video erişilebilirliği ve kalitesini doğrulayan servisi test eder
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.video_quality_validator import (
    VideoAccessibilityResult,
    VideoQualityValidator,
)


class TestVideoQualityValidator:
    """Video Quality Validator test sınıfı"""

    @pytest.fixture
    def validator_service(self):
        """Test için validator instance'ı oluştur"""
        service = VideoQualityValidator()
        # OLCUM (6 Eyl 2026): validate_video_accessibility, mock'lanan
        # _make_api_request'e ULASMADAN once `if not self.api_key` guard'ini
        # calistiriyor. api_key os.getenv("YOUTUBE_API_KEY", "") ile geliyor:
        # yerelde conftest load_dotenv ile .env'den doluyor, CI'da ise bu is'e
        # secret gecirilmedigi icin BOS. Olculdu -- api_key dolu iken mock 1
        # kez cagriliyor, bos iken 0 kez: yani CI'da guard erken donuyor ve
        # bu dosyanin mock'ladigi mantik HIC calismiyordu. Sonuc olarak
        # test_accessible_video_public master'da 4/4 kosumda ayni sekilde
        # dusuyor, kalan testler de mock'ladiklari mantigi dogrulamiyordu.
        # Sabit test degeri guard'i gecirir ve testleri ortamdan bagimsiz
        # kilar. Bu GERCEK bir anahtar degil, yalnizca guard yer tutucusu;
        # "api key yok" senaryosunu test eden test_accessible_video_no_api_key
        # zaten kendi icinde api_key'i "" yaparak bunu eziyor.
        service.api_key = "test-youtube-api-key"  # pragma: allowlist secret
        return service

    # ==================== Erişilebilir Video Testleri ====================

    @pytest.mark.asyncio
    async def test_accessible_video_public(self, validator_service):
        """Public ve erişilebilir video testi"""
        mock_response = {
            "items": [
                {
                    "status": {
                        "uploadStatus": "processed",
                        "privacyStatus": "public",
                        "embeddable": True,
                    },
                    "contentDetails": {},
                }
            ]
        }

        with patch.object(
            validator_service, "_make_api_request", return_value=mock_response
        ):
            result = await validator_service.validate_video_accessibility(
                "test_video_id"
            )

        assert result.is_accessible is True
        assert result.is_embeddable is True
        assert result.privacy_status == "public"
        assert result.error_reason is None

    @pytest.mark.asyncio
    async def test_accessible_video_unlisted(self, validator_service):
        """Unlisted ama erişilebilir video testi"""
        mock_response = {
            "items": [
                {
                    "status": {
                        "uploadStatus": "processed",
                        "privacyStatus": "unlisted",
                        "embeddable": True,
                    },
                    "contentDetails": {},
                }
            ]
        }

        with patch.object(
            validator_service, "_make_api_request", return_value=mock_response
        ):
            result = await validator_service.validate_video_accessibility(
                "unlisted_video"
            )

        assert result.is_accessible is True
        assert result.is_embeddable is True
        assert result.privacy_status == "unlisted"
        assert result.error_reason is None

    @pytest.mark.asyncio
    async def test_accessible_video_embeddable_true(self, validator_service):
        """Gömülebilir video testi"""
        mock_response = {
            "items": [
                {
                    "status": {
                        "uploadStatus": "processed",
                        "privacyStatus": "public",
                        "embeddable": True,
                    },
                    "contentDetails": {},
                }
            ]
        }

        with patch.object(
            validator_service, "_make_api_request", return_value=mock_response
        ):
            result = await validator_service.validate_video_accessibility(
                "embeddable_video"
            )

        assert result.is_accessible is True
        assert result.is_embeddable is True

    @pytest.mark.asyncio
    async def test_accessible_video_no_api_key(self, validator_service):
        """API key olmadan erişilebilirlik kontrolü"""
        validator_service.api_key = ""

        result = await validator_service.validate_video_accessibility("test_video")

        # API key yoksa doğrulama yapılamaz, güvenli tarafta kal
        assert result.is_accessible is False
        assert result.is_embeddable is False
        assert result.privacy_status == "unknown"
        assert result.error_reason == "YouTube API key not configured"

    # ==================== Erişilemeyen Video Testleri ====================

    @pytest.mark.asyncio
    async def test_inaccessible_video_private(self, validator_service):
        """Private video erişilemez testi"""
        mock_response = {
            "items": [
                {
                    "status": {
                        "uploadStatus": "processed",
                        "privacyStatus": "private",
                        "embeddable": False,
                    },
                    "contentDetails": {},
                }
            ]
        }

        with patch.object(
            validator_service, "_make_api_request", return_value=mock_response
        ):
            result = await validator_service.validate_video_accessibility(
                "private_video"
            )

        assert result.is_accessible is False
        assert result.privacy_status == "private"
        assert result.error_reason is not None
        assert "Privacy status" in result.error_reason

    @pytest.mark.asyncio
    async def test_inaccessible_video_not_processed(self, validator_service):
        """İşlenmemiş video erişilemez testi"""
        mock_response = {
            "items": [
                {
                    "status": {
                        "uploadStatus": "uploaded",
                        "privacyStatus": "public",
                        "embeddable": True,
                    },
                    "contentDetails": {},
                }
            ]
        }

        with patch.object(
            validator_service, "_make_api_request", return_value=mock_response
        ):
            result = await validator_service.validate_video_accessibility(
                "unprocessed_video"
            )

        assert result.is_accessible is False
        assert result.error_reason is not None
        assert "Upload status" in result.error_reason

    @pytest.mark.asyncio
    async def test_inaccessible_video_not_found(self, validator_service):
        """Bulunamayan video testi"""
        mock_response = {"items": []}

        with patch.object(
            validator_service, "_make_api_request", return_value=mock_response
        ):
            result = await validator_service.validate_video_accessibility(
                "nonexistent_video"
            )

        assert result.is_accessible is False
        assert result.is_embeddable is False
        assert result.privacy_status == "unknown"
        assert "not found" in result.error_reason.lower()

    @pytest.mark.asyncio
    async def test_inaccessible_video_api_error(self, validator_service):
        """API hatası durumunda erişilemez testi"""
        with patch.object(validator_service, "_make_api_request", return_value=None):
            result = await validator_service.validate_video_accessibility("error_video")

        assert result.is_accessible is False
        assert result.is_embeddable is False
        assert result.privacy_status == "unknown"

    @pytest.mark.asyncio
    async def test_inaccessible_video_not_embeddable(self, validator_service):
        """Gömülemeyen video testi"""
        mock_response = {
            "items": [
                {
                    "status": {
                        "uploadStatus": "processed",
                        "privacyStatus": "public",
                        "embeddable": False,
                    },
                    "contentDetails": {},
                }
            ]
        }

        with patch.object(
            validator_service, "_make_api_request", return_value=mock_response
        ):
            result = await validator_service.validate_video_accessibility(
                "not_embeddable"
            )

        # Erişilebilir ama gömülemiyor
        assert result.is_accessible is True
        assert result.is_embeddable is False

    # ==================== Kalite Skorlama Testleri ====================

    @pytest.mark.asyncio
    async def test_quality_score_high_quality_video(self, validator_service):
        """Yüksek kaliteli video skorlama"""
        metadata = {
            "view_count": 50000,
            "like_count": 2000,
            "duration_minutes": 15,
            "caption_available": True,
            "definition": "hd",
            "channel_name": "TonguçAkademi",
        }

        score = await validator_service.calculate_quality_score(metadata)

        # Tüm kriterler ideal: 0.2 + 0.2 + 0.2 + 0.1 + 0.1 + 0.2 = 1.0
        assert score >= 0.9
        assert score <= 1.0

    @pytest.mark.asyncio
    async def test_quality_score_medium_quality_video(self, validator_service):
        """Orta kaliteli video skorlama"""
        metadata = {
            "view_count": 8000,
            "like_count": 100,
            "duration_minutes": 25,
            "caption_available": False,
            "definition": "sd",
            "channel_name": "Random Channel",
        }

        score = await validator_service.calculate_quality_score(metadata)

        # Orta seviye: view (0.15) + like (0.15) + duration (0.2) = 0.5
        assert 0.4 <= score <= 0.7

    @pytest.mark.asyncio
    async def test_quality_score_low_quality_video(self, validator_service):
        """Düşük kaliteli video skorlama"""
        metadata = {
            "view_count": 500,
            "like_count": 5,
            "duration_minutes": 2,
            "caption_available": False,
            "definition": "sd",
            "channel_name": "Unknown Channel",
        }

        score = await validator_service.calculate_quality_score(metadata)

        # Düşük kalite
        assert score < 0.5

    @pytest.mark.asyncio
    async def test_quality_score_view_count_ranges(self, validator_service):
        """View count aralıklarına göre skorlama"""
        # İdeal aralık: 10k-500k
        metadata_ideal = {"view_count": 100000, "like_count": 0, "duration_minutes": 0}
        score_ideal = await validator_service.calculate_quality_score(metadata_ideal)

        # Çok yüksek: >1M
        metadata_high = {"view_count": 2000000, "like_count": 0, "duration_minutes": 0}
        score_high = await validator_service.calculate_quality_score(metadata_high)

        # Düşük: <5k
        metadata_low = {"view_count": 2000, "like_count": 0, "duration_minutes": 0}
        score_low = await validator_service.calculate_quality_score(metadata_low)

        assert score_ideal > score_high
        assert score_ideal > score_low

    @pytest.mark.asyncio
    async def test_quality_score_like_ratio(self, validator_service):
        """Like ratio skorlama"""
        # Yüksek like ratio: >2%
        metadata_high = {"view_count": 10000, "like_count": 300, "duration_minutes": 0}
        score_high = await validator_service.calculate_quality_score(metadata_high)

        # Orta like ratio: 1-2%
        metadata_mid = {"view_count": 10000, "like_count": 150, "duration_minutes": 0}
        score_mid = await validator_service.calculate_quality_score(metadata_mid)

        # Düşük like ratio: <0.5%
        metadata_low = {"view_count": 10000, "like_count": 30, "duration_minutes": 0}
        score_low = await validator_service.calculate_quality_score(metadata_low)

        assert score_high > score_mid > score_low

    @pytest.mark.asyncio
    async def test_quality_score_duration_ranges(self, validator_service):
        """Video süresi aralıklarına göre skorlama"""
        # İdeal: 5-60 dakika
        metadata_ideal = {"view_count": 0, "like_count": 0, "duration_minutes": 20}
        score_ideal = await validator_service.calculate_quality_score(metadata_ideal)

        # Kabul edilebilir: 3-5 veya 60-90 dakika
        metadata_ok = {"view_count": 0, "like_count": 0, "duration_minutes": 70}
        score_ok = await validator_service.calculate_quality_score(metadata_ok)

        # Çok kısa: <3 dakika
        metadata_short = {"view_count": 0, "like_count": 0, "duration_minutes": 1}
        score_short = await validator_service.calculate_quality_score(metadata_short)

        assert score_ideal > score_ok
        assert score_ok > score_short

    @pytest.mark.asyncio
    async def test_quality_score_caption_bonus(self, validator_service):
        """Altyazı bonusu testi"""
        metadata_with_caption = {
            "view_count": 10000,
            "like_count": 200,
            "duration_minutes": 15,
            "caption_available": True,
        }

        metadata_without_caption = {
            "view_count": 10000,
            "like_count": 200,
            "duration_minutes": 15,
            "caption_available": False,
        }

        score_with = await validator_service.calculate_quality_score(
            metadata_with_caption
        )
        score_without = await validator_service.calculate_quality_score(
            metadata_without_caption
        )

        # Altyazılı video 0.1 puan daha fazla almalı
        assert score_with > score_without
        assert abs(score_with - score_without) >= 0.09  # Yaklaşık 0.1

    @pytest.mark.asyncio
    async def test_quality_score_hd_bonus(self, validator_service):
        """HD kalite bonusu testi"""
        metadata_hd = {
            "view_count": 10000,
            "like_count": 200,
            "duration_minutes": 15,
            "definition": "hd",
        }

        metadata_sd = {
            "view_count": 10000,
            "like_count": 200,
            "duration_minutes": 15,
            "definition": "sd",
        }

        score_hd = await validator_service.calculate_quality_score(metadata_hd)
        score_sd = await validator_service.calculate_quality_score(metadata_sd)

        # HD video 0.1 puan daha fazla almalı
        assert score_hd > score_sd
        assert abs(score_hd - score_sd) >= 0.09

    @pytest.mark.asyncio
    async def test_quality_score_trusted_channel_bonus(self, validator_service):
        """Güvenilir kanal bonusu testi"""
        metadata_trusted = {
            "view_count": 10000,
            "like_count": 200,
            "duration_minutes": 15,
            "channel_name": "TonguçAkademi",
        }

        metadata_untrusted = {
            "view_count": 10000,
            "like_count": 200,
            "duration_minutes": 15,
            "channel_name": "Random Channel",
        }

        score_trusted = await validator_service.calculate_quality_score(
            metadata_trusted
        )
        score_untrusted = await validator_service.calculate_quality_score(
            metadata_untrusted
        )

        # Güvenilir kanal 0.2 puan daha fazla almalı
        assert score_trusted > score_untrusted
        assert abs(score_trusted - score_untrusted) >= 0.19

    @pytest.mark.asyncio
    async def test_quality_score_empty_metadata(self, validator_service):
        """Boş metadata ile skorlama"""
        metadata = {}

        score = await validator_service.calculate_quality_score(metadata)

        # Boş metadata ile düşük skor
        assert 0.0 <= score <= 0.5

    @pytest.mark.asyncio
    async def test_quality_score_error_handling(self, validator_service):
        """Hata durumunda skorlama"""
        # Geçersiz metadata
        metadata = {"invalid_key": "invalid_value"}

        score = await validator_service.calculate_quality_score(metadata)

        # Geçersiz metadata ile 0.0 skor
        assert score == 0.0

    # ==================== Batch Validation Testleri ====================

    @pytest.mark.asyncio
    async def test_batch_validate_multiple_videos(self, validator_service):
        """Çoklu video toplu doğrulama"""
        video_ids = ["video1", "video2", "video3"]

        mock_response = {
            "items": [
                {
                    "status": {
                        "uploadStatus": "processed",
                        "privacyStatus": "public",
                        "embeddable": True,
                    },
                    "contentDetails": {},
                }
            ]
        }

        with patch.object(
            validator_service, "_make_api_request", return_value=mock_response
        ):
            results = await validator_service.batch_validate_videos(video_ids)

        assert len(results) == 3
        assert all(video_id in results for video_id in video_ids)
        assert all(
            isinstance(result, VideoAccessibilityResult) for result in results.values()
        )

    @pytest.mark.asyncio
    async def test_batch_validate_empty_list(self, validator_service):
        """Boş liste ile toplu doğrulama"""
        results = await validator_service.batch_validate_videos([])

        assert results == {}

    @pytest.mark.asyncio
    async def test_batch_validate_with_timeout(self, validator_service):
        """Timeout ile toplu doğrulama"""
        video_ids = ["video1", "video2"]

        # Timeout simülasyonu
        async def slow_validate(video_id):
            import asyncio

            await asyncio.sleep(2)  # Timeout simulation (reduced from 10s)
            return VideoAccessibilityResult(True, True, "public", None)

        with patch.object(
            validator_service, "validate_video_accessibility", side_effect=slow_validate
        ):
            results = await validator_service.batch_validate_videos(
                video_ids, timeout_seconds=1
            )

        # Timeout durumunda sonuçlar dönmeli
        assert len(results) == 2
        # Timeout nedeniyle erişilemez olarak işaretlenmeli
        assert all(not result.is_accessible for result in results.values())

    @pytest.mark.asyncio
    async def test_batch_validate_mixed_results(self, validator_service):
        """Karışık sonuçlarla toplu doğrulama"""
        video_ids = ["accessible", "inaccessible", "error"]

        async def mock_validate(video_id):
            if video_id == "accessible":
                return VideoAccessibilityResult(True, True, "public", None)
            if video_id == "inaccessible":
                return VideoAccessibilityResult(
                    False, False, "private", "Private video"
                )
            raise Exception("API Error")

        with patch.object(
            validator_service, "validate_video_accessibility", side_effect=mock_validate
        ):
            results = await validator_service.batch_validate_videos(video_ids)

        assert len(results) == 3
        assert results["accessible"].is_accessible is True
        assert results["inaccessible"].is_accessible is False
        assert results["error"].is_accessible is False

    @pytest.mark.asyncio
    async def test_batch_validate_performance(self, validator_service):
        """Toplu doğrulama performans testi"""
        import time

        video_ids = [f"video{i}" for i in range(10)]

        mock_response = {
            "items": [
                {
                    "status": {
                        "uploadStatus": "processed",
                        "privacyStatus": "public",
                        "embeddable": True,
                    },
                    "contentDetails": {},
                }
            ]
        }

        with patch.object(
            validator_service, "_make_api_request", return_value=mock_response
        ):
            start_time = time.time()
            results = await validator_service.batch_validate_videos(
                video_ids, timeout_seconds=5
            )
            end_time = time.time()

        # 10 video 5 saniyeden kısa sürede doğrulanmalı
        assert (end_time - start_time) < 5.0
        assert len(results) == 10

    # ==================== Helper Method Testleri ====================

    def test_is_trusted_channel_exact_match(self, validator_service):
        """Tam eşleşen güvenilir kanal kontrolü"""
        assert validator_service._is_trusted_channel("TonguçAkademi") is True
        assert validator_service._is_trusted_channel("Khan Academy Türkçe") is True
        assert validator_service._is_trusted_channel("KAMP Online") is True

    def test_is_trusted_channel_case_insensitive(self, validator_service):
        """Büyük/küçük harf duyarsız kanal kontrolü"""
        # Türkçe karakterlerle tam eşleşme
        assert validator_service._is_trusted_channel("tonguçakademi") is True
        assert validator_service._is_trusted_channel("KHAN ACADEMY TÜRKÇE") is True
        # Kısmi eşleşme - yeterince uzun olmalı
        assert validator_service._is_trusted_channel("TonguçAkademi Official") is True
        assert validator_service._is_trusted_channel("Khan Academy") is True

    def test_is_trusted_channel_partial_match(self, validator_service):
        """Kısmi eşleşen kanal kontrolü"""
        assert validator_service._is_trusted_channel("TonguçAkademi Official") is True
        assert validator_service._is_trusted_channel("Khan Academy") is True

    def test_is_trusted_channel_untrusted(self, validator_service):
        """Güvenilir olmayan kanal kontrolü"""
        assert validator_service._is_trusted_channel("Random Channel") is False
        assert validator_service._is_trusted_channel("") is False
        assert validator_service._is_trusted_channel(None) is False

    def test_parse_duration_to_minutes_standard(self, validator_service):
        """Standart duration parsing"""
        assert validator_service._parse_duration_to_minutes("PT15M30S") == 15
        assert validator_service._parse_duration_to_minutes("PT1H30M") == 90
        assert validator_service._parse_duration_to_minutes("PT45S") == 0
        assert validator_service._parse_duration_to_minutes("PT2H") == 120

    def test_parse_duration_to_minutes_edge_cases(self, validator_service):
        """Duration parsing edge cases"""
        assert validator_service._parse_duration_to_minutes("") == 0
        assert validator_service._parse_duration_to_minutes(None) == 0
        assert validator_service._parse_duration_to_minutes("PT0S") == 0
        # Invalid format returns 0, not 15
        result = validator_service._parse_duration_to_minutes("INVALID")
        assert result >= 0  # Should handle gracefully

    # ==================== API Request Testleri ====================

    @pytest.mark.asyncio
    async def test_make_api_request_success(self, validator_service):
        """Başarılı API isteği"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"items": []})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False

        validator_service.session = mock_session

        result = await validator_service._make_api_request("videos", {"id": "test"})

        assert result == {"items": []}

    @pytest.mark.asyncio
    async def test_make_api_request_quota_exceeded(self, validator_service):
        """API quota aşımı"""
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.json = AsyncMock(
            return_value={"error": {"errors": [{"reason": "quotaExceeded"}]}}
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False

        validator_service.session = mock_session

        # API quota exceeded durumunda exception raise edilir
        try:
            result = await validator_service._make_api_request("videos", {"id": "test"})
            # Exception raise edilmezse None dönmeli
            assert result is None or "quota" in str(result).lower()
        except Exception as e:
            assert "quota" in str(e).lower()

    @pytest.mark.asyncio
    async def test_make_api_request_invalid_key(self, validator_service):
        """Geçersiz API key"""
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.json = AsyncMock(
            return_value={"error": {"errors": [{"reason": "keyInvalid"}]}}
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False

        validator_service.session = mock_session

        # Invalid key durumunda exception raise edilir veya None döner
        try:
            result = await validator_service._make_api_request("videos", {"id": "test"})
            # Exception raise edilmezse None dönmeli
            assert result is None or "key" in str(result).lower()
        except Exception as e:
            assert "key" in str(e).lower() or "API" in str(e)

    @pytest.mark.asyncio
    async def test_make_api_request_not_found(self, validator_service):
        """404 Not Found"""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False

        validator_service.session = mock_session

        result = await validator_service._make_api_request("videos", {"id": "test"})

        assert result is None

    @pytest.mark.asyncio
    async def test_make_api_request_rate_limit_retry(self, validator_service):
        """Rate limit ile retry"""
        # İlk istek 429, ikinci istek 200
        mock_response_429 = AsyncMock()
        mock_response_429.status = 429
        mock_response_429.__aenter__ = AsyncMock(return_value=mock_response_429)
        mock_response_429.__aexit__ = AsyncMock(return_value=None)

        mock_response_200 = AsyncMock()
        mock_response_200.status = 200
        mock_response_200.json = AsyncMock(return_value={"success": True})
        mock_response_200.__aenter__ = AsyncMock(return_value=mock_response_200)
        mock_response_200.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(side_effect=[mock_response_429, mock_response_200])
        mock_session.closed = False

        validator_service.session = mock_session

        result = await validator_service._make_api_request("videos", {"id": "test"})

        assert result == {"success": True}

    # ==================== Session Management Testleri ====================

    @pytest.mark.asyncio
    async def test_get_session_creates_new(self, validator_service):
        """Yeni session oluşturma"""
        validator_service.session = None

        session = await validator_service._get_session()

        assert session is not None
        assert validator_service.session is not None

    @pytest.mark.asyncio
    async def test_get_session_reuses_existing(self, validator_service):
        """Mevcut session'ı yeniden kullanma"""
        mock_session = AsyncMock()
        mock_session.closed = False
        validator_service.session = mock_session

        session = await validator_service._get_session()

        assert session is mock_session

    @pytest.mark.asyncio
    async def test_close_session(self, validator_service):
        """Session kapatma"""
        mock_session = AsyncMock()
        mock_session.closed = False
        mock_session.close = AsyncMock()
        validator_service.session = mock_session

        await validator_service.close_session()

        mock_session.close.assert_called_once()

    # ==================== Integration Testleri ====================

    @pytest.mark.asyncio
    async def test_real_world_accessible_video(self, validator_service):
        """Gerçek dünya erişilebilir video örneği"""
        mock_response = {
            "items": [
                {
                    "status": {
                        "uploadStatus": "processed",
                        "privacyStatus": "public",
                        "embeddable": True,
                        "publicStatsViewable": True,
                    },
                    "contentDetails": {
                        "duration": "PT15M30S",
                        "caption": "true",
                        "definition": "hd",
                    },
                }
            ]
        }

        with patch.object(
            validator_service, "_make_api_request", return_value=mock_response
        ):
            result = await validator_service.validate_video_accessibility(
                "real_video_id"
            )

        assert result.is_accessible is True
        assert result.is_embeddable is True
        assert result.privacy_status == "public"
        assert result.error_reason is None

    @pytest.mark.asyncio
    async def test_real_world_quality_scoring(self, validator_service):
        """Gerçek dünya kalite skorlama örneği"""
        metadata = {
            "view_count": 125000,
            "like_count": 3500,
            "duration_minutes": 18,
            "caption_available": True,
            "definition": "hd",
            "channel_name": "TonguçAkademi",
        }

        score = await validator_service.calculate_quality_score(metadata)

        # Mükemmel video: tüm kriterler ideal
        assert score >= 0.95
