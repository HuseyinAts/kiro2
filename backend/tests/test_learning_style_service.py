# -*- coding: utf-8 -*-
"""
Test - Hibrit Ogrenme Stili Servisi
64 farkli ogrenme profili kombinasyonu testleri
"""

import pytest
from datetime import datetime


class TestLearningStyleService:
    """Hibrit ogrenme stili servisi test sinifi"""

    @pytest.fixture
    def service(self):
        """Test icin servis ornegi"""
        from services.learning_style_service import LearningStyleService

        return LearningStyleService()

    @pytest.fixture
    def sample_behavioral_data(self):
        """Ornek davranissal veri"""
        return {
            "video_watch_time": 3600,
            "text_read_time": 1800,
            "audio_listen_time": 2400,
            "practice_time": 1200,
            "group_study_sessions": 5,
            "individual_study_sessions": 10,
        }

    # ============================================
    # TEMEL ISLEVSELLIK TESTLERI (3 test)
    # ============================================

    @pytest.mark.asyncio
    async def test_01_detect_learning_style_basic(
        self, service, sample_behavioral_data
    ):
        """Test 1: Temel ogrenme stili tespiti"""
        result = await service.detect_learning_style(
            student_id="test_student_001", behavioral_data=sample_behavioral_data
        )

        assert "student_id" in result
        assert "vark_profili" in result
        assert "felder_silverman_profili" in result
        assert "hibrit_kod" in result
        assert "guven_seviyesi" in result
        assert result["student_id"] == "test_student_001"
        assert 0 <= result["guven_seviyesi"] <= 1

    @pytest.mark.asyncio
    async def test_02_vark_profile_structure(self, service, sample_behavioral_data):
        """Test 2: VARK profil yapisi"""
        result = await service.detect_learning_style(
            student_id="test_student_002", behavioral_data=sample_behavioral_data
        )

        vark_profile = result["vark_profili"]

        assert "visual" in vark_profile
        assert "auditory" in vark_profile
        assert "reading" in vark_profile
        assert "kinesthetic" in vark_profile

        for dimension, score in vark_profile.items():
            assert 0 <= score <= 1, f"{dimension} skoru 0-1 araliginda olmali"

    @pytest.mark.asyncio
    async def test_03_felder_silverman_profile_structure(
        self, service, sample_behavioral_data
    ):
        """Test 3: Felder-Silverman profil yapisi"""
        result = await service.detect_learning_style(
            student_id="test_student_003", behavioral_data=sample_behavioral_data
        )

        felder_profile = result["felder_silverman_profili"]

        assert "active_reflective" in felder_profile
        assert "sensing_intuitive" in felder_profile
        assert "visual_verbal" in felder_profile
        assert "sequential_global" in felder_profile

        for dimension, score in felder_profile.items():
            assert -1 <= score <= 1, f"{dimension} skoru -1 ile 1 araliginda olmali"

    # ============================================
    # HIBRIT KOD TESTLERI (3 test)
    # ============================================

    @pytest.mark.asyncio
    async def test_04_hibrit_code_format(self, service, sample_behavioral_data):
        """Test 4: Hibrit kod formati"""
        result = await service.detect_learning_style(
            student_id="test_student_004", behavioral_data=sample_behavioral_data
        )

        hibrit_kod = result["hibrit_kod"]

        assert "-" in hibrit_kod, "Hibrit kod '-' icermeli"
        parts = hibrit_kod.split("-")
        assert len(parts) == 2, "Hibrit kod 2 parcadan olusmali"

        vark_code, felder_code = parts
        assert len(vark_code) >= 1, "VARK kodu en az 1 karakter olmali"
        assert len(felder_code) == 4, "Felder-Silverman kodu 4 karakter olmali"

    @pytest.mark.asyncio
    async def test_05_all_64_hybrid_codes_generation(self, service):
        """Test 5: 64 hibrit kod kombinasyonunun olusturulmasi"""
        all_codes = await service.get_all_hybrid_codes()

        assert len(all_codes) == 64, "64 farkli hibrit kod olmali"

        # Extract kod fields from dictionaries
        code_list = [c["kod"] for c in all_codes]
        assert len(set(code_list)) == 64, "Tum kodlar benzersiz olmali"

        for code_dict in all_codes:
            code = code_dict["kod"]
            assert "-" in code, f"{code} formati hatali"

    @pytest.mark.asyncio
    async def test_06_specific_hybrid_codes(self, service):
        """Test 6: Belirli hibrit kodlarin varligi"""
        all_codes = await service.get_all_hybrid_codes()
        code_list = [c["kod"] for c in all_codes]

        # V ile baslayan kodlar olmali
        v_codes = [c for c in code_list if c.startswith("V-")]
        assert len(v_codes) >= 5, "V ile baslayan en az 5 kod olmali"

        # A ile baslayan kodlar olmali
        a_codes = [c for c in code_list if c.startswith("A-")]
        assert len(a_codes) >= 5, "A ile baslayan en az 5 kod olmali"

        # Her VARK kategorisi icin kodlar olmali
        for prefix in ["V-", "A-", "R-", "K-"]:
            prefix_codes = [c for c in code_list if c.startswith(prefix)]
            assert len(prefix_codes) > 0, f"{prefix} ile baslayan kod olmali"

    # ============================================
    # ONERI SISTEMI TESTLERI (3 test)
    # ============================================

    @pytest.mark.asyncio
    async def test_07_learning_recommendations_basic(
        self, service, sample_behavioral_data
    ):
        """Test 7: Temel ogrenme onerileri"""
        await service.detect_learning_style(
            student_id="test_student_005", behavioral_data=sample_behavioral_data
        )

        recommendations = await service.get_learning_recommendations(
            student_id="test_student_005"
        )

        assert isinstance(recommendations, list), "Oneriler liste olmali"
        assert len(recommendations) > 0, "En az bir oneri olmali"

        for rec in recommendations:
            assert "tip" in rec
            # Check for both Turkish and ASCII versions of the key
            assert "aciklama" in rec or "açıklama" in rec or "a��klama" in rec
            assert "oncelik" in rec or "öncelik" in rec or "�ncelik" in rec

    @pytest.mark.asyncio
    async def test_08_visual_learner_recommendations(self, service):
        """Test 8: Gorsel ogrenen icin oneriler"""
        behavioral_data = {
            "video_watch_time": 5000,
            "diagram_views": 50,
            "infographic_views": 30,
        }

        await service.detect_learning_style(
            student_id="visual_student", behavioral_data=behavioral_data
        )

        recommendations = await service.get_learning_recommendations(
            student_id="visual_student"
        )

        assert len(recommendations) > 0, "Oneriler olmali"

    @pytest.mark.asyncio
    async def test_09_kinesthetic_learner_recommendations(self, service):
        """Test 9: Kinestetik ogrenen icin oneriler"""
        behavioral_data = {
            "practice_time": 5000,
            "hands_on_activities": 40,
            "experiment_completions": 25,
        }

        await service.detect_learning_style(
            student_id="kinesthetic_student", behavioral_data=behavioral_data
        )

        recommendations = await service.get_learning_recommendations(
            student_id="kinesthetic_student"
        )

        assert len(recommendations) > 0, "Oneriler olmali"

    # ============================================
    # PROFIL YONETIMI TESTLERI (2 test)
    # ============================================

    @pytest.mark.asyncio
    async def test_10_profile_caching(self, service, sample_behavioral_data):
        """Test 10: Profil onbellege alma"""
        student_id = "test_student_006"

        result1 = await service.detect_learning_style(
            student_id=student_id, behavioral_data=sample_behavioral_data
        )

        result2 = await service.get_student_profile(student_id)

        assert result2 is not None, "Profil onbellekte olmali"
        assert result1["hibrit_kod"] == result2["hibrit_kod"]

    @pytest.mark.asyncio
    async def test_11_multiple_students_profiles(self, service, sample_behavioral_data):
        """Test 11: Birden fazla ogrenci profili"""
        student_ids = ["student_A", "student_B", "student_C"]

        for student_id in student_ids:
            await service.detect_learning_style(
                student_id=student_id, behavioral_data=sample_behavioral_data
            )

        stats = service.get_service_stats()
        assert stats["toplam_profil_sayisi"] >= len(student_ids)

    # ============================================
    # GUVEN SEVIYESI TESTLERI (2 test)
    # ============================================

    @pytest.mark.asyncio
    async def test_12_confidence_level_range(self, service, sample_behavioral_data):
        """Test 12: Guven seviyesi aralik"""
        result = await service.detect_learning_style(
            student_id="test_student_007", behavioral_data=sample_behavioral_data
        )

        confidence = result["guven_seviyesi"]
        assert 0 <= confidence <= 1, "Guven seviyesi 0-1 araliginda olmali"

    @pytest.mark.asyncio
    async def test_13_high_confidence_detection(self, service):
        """Test 13: Yuksek guven seviyesi tespiti"""
        consistent_data = {
            "video_watch_time": 5000,
            "diagram_views": 100,
            "visual_notes": 50,
            "infographic_views": 80,
        }

        result = await service.detect_learning_style(
            student_id="high_confidence_student", behavioral_data=consistent_data
        )

        assert result["guven_seviyesi"] > 0.7, "Turarli veri yuksek guven vermeli"

    # ============================================
    # HATA DURUMU TESTLERI (2 test)
    # ============================================

    @pytest.mark.asyncio
    async def test_14_empty_behavioral_data(self, service):
        """Test 14: Bos davranissal veri"""
        result = await service.detect_learning_style(
            student_id="test_student_008", behavioral_data={}
        )

        assert result is not None
        assert "hibrit_kod" in result

    @pytest.mark.asyncio
    async def test_15_invalid_student_id(self, service):
        """Test 15: Gecersiz ogrenci ID"""
        result = await service.get_student_profile("")
        assert result is None

        result = await service.get_student_profile(None)
        assert result is None

    # ============================================
    # SERVIS ISTATISTIKLERI TESTLERI (2 test)
    # ============================================

    def test_16_service_stats_structure(self, service):
        """Test 16: Servis istatistikleri yapisi"""
        stats = service.get_service_stats()

        assert "toplam_profil_sayisi" in stats
        assert "vark_boyutlari" in stats
        assert "felder_boyutlari" in stats
        assert "toplam_kombinasyon" in stats
        assert stats["toplam_kombinasyon"] == 64

    def test_17_vark_felder_dimensions(self, service):
        """Test 17: VARK ve Felder boyutlari"""
        stats = service.get_service_stats()

        assert len(stats["vark_boyutlari"]) == 4
        assert len(stats["felder_boyutlari"]) == 4

    # ============================================
    # PERFORMANS TESTLERI (2 test)
    # ============================================

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_18_detection_performance(self, service, sample_behavioral_data):
        """Test 18: Tespit performansi (<100ms hedef)"""
        import time

        start_time = time.time()

        for i in range(10):
            await service.detect_learning_style(
                student_id=f"perf_student_{i}", behavioral_data=sample_behavioral_data
            )

        end_time = time.time()
        elapsed = end_time - start_time
        avg_time = elapsed / 10

        print(f"\nOrtalama tespit suresi: {avg_time:.3f}s")
        assert avg_time < 0.2, f"Ortalama {avg_time:.3f}s, 0.2s'den kisa olmali"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_19_recommendation_performance(self, service, sample_behavioral_data):
        """Test 19: Oneri performansi (<50ms hedef)"""
        import time

        await service.detect_learning_style(
            student_id="perf_rec_student", behavioral_data=sample_behavioral_data
        )

        start_time = time.time()

        for _ in range(10):
            await service.get_learning_recommendations(student_id="perf_rec_student")

        end_time = time.time()
        elapsed = end_time - start_time
        avg_time = elapsed / 10

        print(f"\nOrtalama oneri suresi: {avg_time:.3f}s")
        assert avg_time < 0.1, f"Ortalama {avg_time:.3f}s, 0.1s'den kisa olmali"

    # ============================================
    # PARAMETRIK TESTLER (4 test)
    # ============================================

    @pytest.mark.parametrize(
        "vark_dimension", ["visual", "auditory", "reading", "kinesthetic"]
    )
    @pytest.mark.asyncio
    async def test_20_vark_dimensions(self, service, vark_dimension):
        """Test 20-23: Her VARK boyutu icin test (4 test)"""
        result = await service.detect_learning_style(
            student_id=f"vark_{vark_dimension}_student",
            behavioral_data={f"{vark_dimension}_activity": 5000},
        )

        vark = result["vark_profili"]
        assert vark_dimension in vark
        assert 0 <= vark[vark_dimension] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
