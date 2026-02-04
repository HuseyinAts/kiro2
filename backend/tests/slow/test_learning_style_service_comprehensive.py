"""
Kapsamlı Learning Style Service Testi
Teknofest 2025 - YKS Hazırlık Platformu
64 Hibrit Öğrenme Profili Sistemi
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Optional

# Test edilecek modülleri import et
try:
    from services.learning_style_service import (
        LearningStyleService,
        learning_style_service,
    )
    from models.learning_style import (
        LearningStyle,
        VARKProfile,
        FelderSilvermanProfile,
        HybridLearningProfile,
    )
except ImportError:
    # Mock classes if imports fail
    class VARKProfile:
        def __init__(self, **kwargs):
            self.visual = kwargs.get("visual", 0.5)
            self.auditory = kwargs.get("auditory", 0.5)
            self.reading = kwargs.get("reading", 0.5)
            self.kinesthetic = kwargs.get("kinesthetic", 0.5)

    class FelderSilvermanProfile:
        def __init__(self, **kwargs):
            self.active_reflective = kwargs.get("active_reflective", 0)
            self.sensing_intuitive = kwargs.get("sensing_intuitive", 0)
            self.visual_verbal = kwargs.get("visual_verbal", 0)
            self.sequential_global = kwargs.get("sequential_global", 0)

    class HybridLearningProfile:
        def __init__(self, **kwargs):
            self.student_id = kwargs.get("student_id")
            self.vark_profile = kwargs.get("vark_profile")
            self.felder_profile = kwargs.get("felder_profile")
            self.hybrid_code = kwargs.get("hybrid_code")
            self.confidence_level = kwargs.get("confidence_level", 0.5)

    class LearningStyleService:
        def __init__(self):
            self.student_profiles = {}
            self.vark_dimensions = ["visual", "auditory", "reading", "kinesthetic"]
            self.felder_dimensions = [
                "active_reflective",
                "sensing_intuitive",
                "visual_verbal",
                "sequential_global",
            ]


class TestLearningStyleServiceComprehensive:
    """Kapsamlı Learning Style Service testleri"""

    @pytest.fixture
    def service(self):
        """Learning style service fixture"""
        return LearningStyleService()

    @pytest.fixture
    def sample_behavioral_data(self):
        """Örnek davranışsal veri"""
        return {
            "video_watch_time": 3600,  # saniye
            "text_read_time": 1800,
            "audio_listen_time": 2400,
            "practice_completion_rate": 0.85,
            "group_study_preference": 0.7,
            "visual_content_interaction": 0.9,
            "note_taking_frequency": 0.6,
            "discussion_participation": 0.4,
        }

    @pytest.fixture
    def sample_questionnaire_responses(self):
        """Örnek anket yanıtları"""
        return [
            {"question_id": "q1", "answer": "visual"},
            {"question_id": "q2", "answer": "active"},
            {"question_id": "q3", "answer": "sequential"},
            {"question_id": "q4", "answer": "sensing"},
        ]

    # ========== Initialization Tests ==========

    def test_service_initialization(self, service):
        """Service başlatma testi"""
        assert service is not None
        assert isinstance(service.student_profiles, dict)
        assert len(service.vark_dimensions) == 4
        assert len(service.felder_dimensions) == 4
        assert "visual" in service.vark_dimensions
        assert "active_reflective" in service.felder_dimensions

    # ========== VARK Profile Tests ==========

    @pytest.mark.asyncio
    async def test_detect_vark_profile(self, service, sample_behavioral_data):
        """VARK profili tespit testi"""
        student_id = "test_student_vark"

        vark_profile = await service.detect_vark_profile(
            student_id=student_id, behavioral_data=sample_behavioral_data
        )

        assert vark_profile is not None
        assert vark_profile.visual >= 0 and vark_profile.visual <= 1
        assert vark_profile.auditory >= 0 and vark_profile.auditory <= 1
        assert vark_profile.reading >= 0 and vark_profile.reading <= 1
        assert vark_profile.kinesthetic >= 0 and vark_profile.kinesthetic <= 1

        # En yüksek boyut visual olmalı (sample data'ya göre)
        assert vark_profile.visual > vark_profile.reading

    @pytest.mark.asyncio
    async def test_vark_dominant_style(self, service):
        """VARK dominant stil testi"""
        vark_profile = VARKProfile(
            visual=0.8, auditory=0.3, reading=0.5, kinesthetic=0.4
        )

        dominant = await service.get_dominant_vark_style(vark_profile)

        assert dominant == "visual"

    # ========== Felder-Silverman Profile Tests ==========

    @pytest.mark.asyncio
    async def test_detect_felder_silverman_profile(
        self, service, sample_behavioral_data
    ):
        """Felder-Silverman profili tespit testi"""
        student_id = "test_student_felder"

        felder_profile = await service.detect_felder_silverman_profile(
            student_id=student_id, behavioral_data=sample_behavioral_data
        )

        assert felder_profile is not None
        assert -1 <= felder_profile.active_reflective <= 1
        assert -1 <= felder_profile.sensing_intuitive <= 1
        assert -1 <= felder_profile.visual_verbal <= 1
        assert -1 <= felder_profile.sequential_global <= 1

    @pytest.mark.asyncio
    async def test_felder_pattern_generation(self, service):
        """Felder-Silverman pattern oluşturma testi"""
        felder_profile = FelderSilvermanProfile(
            active_reflective=0.5,  # Active
            sensing_intuitive=-0.3,  # Intuitive
            visual_verbal=0.7,  # Visual
            sequential_global=-0.2,  # Global
        )

        pattern = await service.generate_felder_pattern(felder_profile)

        assert pattern == "AIVG"  # Active-Intuitive-Visual-Global

    # ========== Hybrid Profile Tests ==========

    @pytest.mark.asyncio
    async def test_detect_hybrid_learning_style(
        self, service, sample_behavioral_data, sample_questionnaire_responses
    ):
        """Hibrit öğrenme stili tespit testi"""
        student_id = "test_hybrid"

        hybrid_profile = await service.detect_learning_style(
            student_id=student_id,
            behavioral_data=sample_behavioral_data,
            questionnaire_responses=sample_questionnaire_responses,
        )

        assert hybrid_profile is not None
        assert hybrid_profile["student_id"] == student_id
        assert "vark_profili" in hybrid_profile
        assert "felder_silverman_profili" in hybrid_profile
        assert "hibrit_kod" in hybrid_profile
        assert "guven_seviyesi" in hybrid_profile
        assert (
            hybrid_profile["guven_seviyesi"] >= 0
            and hybrid_profile["guven_seviyesi"] <= 1
        )

    @pytest.mark.asyncio
    async def test_all_64_hybrid_codes(self, service):
        """64 hibrit kod kombinasyonu testi"""
        all_codes = service.get_all_hybrid_codes()

        assert len(all_codes) == 64

        # VARK x Felder = 4 x 16 = 64
        vark_codes = ["V", "A", "R", "K"]
        felder_patterns = []

        # Tüm Felder kombinasyonları (2^4 = 16)
        for ar in ["A", "R"]:
            for si in ["S", "I"]:
                for vv in ["V", "B"]:
                    for sg in ["S", "G"]:
                        felder_patterns.append(f"{ar}{si}{vv}{sg}")

        assert len(felder_patterns) == 16

        # Her kombinasyon mevcut olmalı
        for vark in vark_codes:
            for felder in felder_patterns:
                expected_code = f"{vark}-{felder}"
                assert expected_code in all_codes

    @pytest.mark.asyncio
    async def test_hybrid_code_generation(self, service):
        """Hibrit kod oluşturma testi"""
        vark_profile = VARKProfile(
            visual=0.8, auditory=0.2, reading=0.3, kinesthetic=0.4
        )
        felder_profile = FelderSilvermanProfile(
            active_reflective=0.5,
            sensing_intuitive=0.3,
            visual_verbal=0.6,
            sequential_global=-0.4,
        )

        hybrid_code = service._generate_hibrit_code(
            vark_profile.__dict__, felder_profile.__dict__
        )

        assert hybrid_code == "V-ASVG"  # Visual - Active-Sensing-Visual-Global

    # ========== Recommendation Tests ==========

    @pytest.mark.asyncio
    async def test_learning_recommendations_visual(self, service):
        """Görsel öğrenci için öneri testi"""
        student_id = "test_visual"

        # Görsel profil oluştur
        service.student_profiles[student_id] = {
            "vark_profili": {
                "visual": 0.9,
                "auditory": 0.2,
                "reading": 0.3,
                "kinesthetic": 0.1,
            },
            "felder_silverman_profili": {"visual_verbal": 0.8},
            "hibrit_kod": "V-ASVS",
        }

        recommendations = await service.get_learning_recommendations(student_id)

        assert len(recommendations) > 0
        assert any("görsel" in r["tip"].lower() for r in recommendations)
        assert recommendations[0]["öncelik"] == "yüksek"

    @pytest.mark.asyncio
    async def test_learning_recommendations_kinesthetic(self, service):
        """Kinestetik öğrenci için öneri testi"""
        student_id = "test_kinesthetic"

        # Kinestetik profil oluştur
        service.student_profiles[student_id] = {
            "vark_profili": {
                "visual": 0.2,
                "auditory": 0.3,
                "reading": 0.1,
                "kinesthetic": 0.9,
            },
            "felder_silverman_profili": {"active_reflective": 0.7},
            "hibrit_kod": "K-ASVS",
        }

        recommendations = await service.get_learning_recommendations(student_id)

        assert len(recommendations) > 0
        assert any("uygulamalı" in r["tip"].lower() for r in recommendations)

    @pytest.mark.asyncio
    async def test_subject_specific_recommendations(self, service):
        """Konu bazlı öneri testi"""
        student_id = "test_subject"

        # Profil oluştur
        await service.detect_learning_style(student_id, {})

        # Matematik için öneriler
        math_recs = await service.get_learning_recommendations(student_id, "matematik")

        # Türkçe için öneriler
        turkish_recs = await service.get_learning_recommendations(student_id, "türkçe")

        # Farklı konular için farklı öneriler olmalı
        assert math_recs != turkish_recs

    # ========== Profile Update Tests ==========

    @pytest.mark.asyncio
    async def test_profile_update_with_new_data(self, service):
        """Yeni veriyle profil güncelleme testi"""
        student_id = "test_update"

        # İlk profil
        initial_profile = await service.detect_learning_style(
            student_id, {"video_watch_time": 1000}
        )
        initial_code = initial_profile["hibrit_kod"]

        # Yeni davranışsal veri ile güncelle
        updated_profile = await service.detect_learning_style(
            student_id, {"video_watch_time": 5000, "text_read_time": 3000}
        )

        # Profil güncellenmiş olabilir
        assert updated_profile["student_id"] == student_id
        # Güven seviyesi değişmiş olmalı
        assert updated_profile["guven_seviyesi"] != initial_profile["guven_seviyesi"]

    @pytest.mark.asyncio
    async def test_confidence_level_calculation(self, service):
        """Güven seviyesi hesaplama testi"""
        # Az veriyle düşük güven
        low_confidence = await service.calculate_confidence_level(
            data_points=10, consistency_score=0.5
        )
        assert low_confidence < 0.6  # LOW

        # Çok veriyle yüksek güven
        high_confidence = await service.calculate_confidence_level(
            data_points=1000, consistency_score=0.9
        )
        assert high_confidence > 0.8  # HIGH

    # ========== Content Personalization Tests ==========

    @pytest.mark.asyncio
    async def test_content_personalization_matrix(self, service):
        """İçerik kişiselleştirme matrisi testi"""
        content_weights = await service.get_content_personalization_weights(
            vark_profile={
                "visual": 0.9,
                "auditory": 0.1,
                "reading": 0.3,
                "kinesthetic": 0.2,
            }
        )

        assert "video_lecture" in content_weights
        assert "audio_podcast" in content_weights
        assert "text_article" in content_weights
        assert "hands_on_exercise" in content_weights

        # Visual profil için video ağırlığı yüksek olmalı
        assert content_weights["video_lecture"] > content_weights["audio_podcast"]

    @pytest.mark.asyncio
    async def test_adaptive_content_selection(self, service):
        """Adaptif içerik seçimi testi"""
        student_id = "test_adaptive"

        # Profil oluştur
        await service.detect_learning_style(
            student_id, {"visual_content_interaction": 0.9}
        )

        # İçerik seç
        selected_content = await service.select_adaptive_content(
            student_id=student_id,
            available_content=[
                {"type": "video", "id": "v1"},
                {"type": "text", "id": "t1"},
                {"type": "audio", "id": "a1"},
            ],
        )

        # Visual profil için video öncelikli olmalı
        assert selected_content[0]["type"] == "video"

    # ========== Performance Tests ==========

    @pytest.mark.asyncio
    async def test_batch_profile_detection(self, service):
        """Toplu profil tespiti performans testi"""
        import time

        start_time = time.time()

        # 100 öğrenci için profil tespit et
        tasks = []
        for i in range(100):
            task = service.detect_learning_style(
                student_id=f"batch_{i}", behavioral_data={"video_watch_time": i * 100}
            )
            tasks.append(task)

        profiles = await asyncio.gather(*tasks)

        elapsed_time = time.time() - start_time

        assert len(profiles) == 100
        assert elapsed_time < 5  # 5 saniyeden az sürmeli

    @pytest.mark.asyncio
    async def test_profile_caching(self, service):
        """Profil cache testi"""
        student_id = "test_cache"

        # İlk tespit
        first_call = await service.detect_learning_style(student_id, {})

        # Cache'den alınmalı (daha hızlı)
        import time

        start = time.time()
        second_call = await service.get_student_profile(student_id)
        elapsed = time.time() - start

        assert elapsed < 0.01  # Cache'den çok hızlı gelmeli
        assert second_call == service.student_profiles[student_id]

    # ========== Analytics Tests ==========

    @pytest.mark.asyncio
    async def test_learning_analytics(self, service):
        """Öğrenme analitiği testi"""
        # Birden fazla profil oluştur
        for i in range(50):
            vark_dominant = ["visual", "auditory", "reading", "kinesthetic"][i % 4]
            await service.detect_learning_style(
                student_id=f"analytics_{i}",
                behavioral_data={f"{vark_dominant}_preference": 0.9},
            )

        # Analitik hesapla
        analytics = await service.calculate_learning_analytics()

        assert "total_profiles" in analytics
        assert analytics["total_profiles"] == 50
        assert "vark_distribution" in analytics
        assert "felder_distribution" in analytics
        assert "most_common_hybrid_code" in analytics

    @pytest.mark.asyncio
    async def test_profile_similarity(self, service):
        """Profil benzerliği testi"""
        # İki benzer profil
        profile1 = await service.detect_learning_style(
            "student1", {"visual_content_interaction": 0.8}
        )
        profile2 = await service.detect_learning_style(
            "student2", {"visual_content_interaction": 0.85}
        )

        similarity = await service.calculate_profile_similarity(
            profile1["hibrit_kod"], profile2["hibrit_kod"]
        )

        assert similarity > 0.7  # Yüksek benzerlik

    # ========== Export/Import Tests ==========

    @pytest.mark.asyncio
    async def test_export_profile(self, service):
        """Profil export testi"""
        student_id = "test_export"

        await service.detect_learning_style(student_id, {})

        exported = await service.export_profile(student_id)

        assert "student_id" in exported
        assert "vark_profili" in exported
        assert "felder_silverman_profili" in exported
        assert "hibrit_kod" in exported
        assert "export_date" in exported

    @pytest.mark.asyncio
    async def test_import_profile(self, service):
        """Profil import testi"""
        profile_data = {
            "student_id": "test_import",
            "vark_profili": {
                "visual": 0.7,
                "auditory": 0.5,
                "reading": 0.8,
                "kinesthetic": 0.3,
            },
            "felder_silverman_profili": {"active_reflective": 0.3},
            "hibrit_kod": "R-ASVS",
            "guven_seviyesi": 0.85,
        }

        success = await service.import_profile(profile_data)

        assert success is True
        assert "test_import" in service.student_profiles

    # ========== Integration Tests ==========

    @pytest.mark.asyncio
    async def test_integration_with_exam_system(self, service):
        """Sınav sistemi entegrasyonu testi"""
        student_id = "test_integration"

        # Profil oluştur
        profile = await service.detect_learning_style(student_id, {})

        # Sınav için özel ayarlar
        exam_settings = await service.get_exam_settings_for_profile(
            student_id, exam_type="TYT"
        )

        assert "question_presentation" in exam_settings
        assert "time_adjustments" in exam_settings
        assert "break_recommendations" in exam_settings

    @pytest.mark.asyncio
    async def test_error_handling(self, service):
        """Hata yönetimi testi"""
        # Geçersiz student_id
        profile = await service.detect_learning_style("", {})
        assert profile["student_id"] == "anonymous_student"

        # Eksik davranışsal veri
        profile = await service.detect_learning_style("test_error", None)
        assert profile is not None

        # Geçersiz anket yanıtları
        profile = await service.detect_learning_style(
            "test_error2", {}, questionnaire_responses="invalid"
        )
        assert profile is not None
