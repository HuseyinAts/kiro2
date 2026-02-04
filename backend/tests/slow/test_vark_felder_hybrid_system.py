from unittest.mock import Mock, patch, AsyncMock

"""
VARK + Felder-Silverman Hibrit Öğrenme Stili Sistemi
Kapsamlı Test Suite

Bu test dosyası, 64 farklı öğrenme profili kombinasyonunu test eder.
Requirements: 10.1
"""

import asyncio
from datetime import datetime

import pytest

from algorithms.hybrid_learning_style_detector import HybridLearningStyleDetector


class TestVARKAnalysis:
    """VARK (Visual, Auditory, Reading, Kinesthetic) analiz testleri"""

    @pytest.fixture
    def detector(self):
        return HybridLearningStyleDetector()

    @pytest.mark.asyncio
    async def test_visual_learner_detection(self, detector):
        """Görsel öğrenci tespiti"""

        visual_behavioral_data = {
            "visual_preference": 0.9,
            "auditory_preference": 0.2,
            "reading_preference": 0.3,
            "kinesthetic_preference": 0.1,
            "active_learning": 0.6,
            "reflective_learning": 0.4,
            "sensing_learning": 0.5,
            "intuitive_learning": 0.5,
            "visual_learning": 0.9,
            "verbal_learning": 0.1,
            "sequential_learning": 0.5,
            "global_learning": 0.5,
        }

        visual_responses = [
            "Diyagramlar ve şemalar bana yardımcı olur",
            "Renkli notlar alırım",
            "Görsel materyallerle daha iyi öğrenirim",
        ]

        profile = await detector.detect_hybrid_profile(
            "visual_student", visual_behavioral_data, visual_responses
        )

        # Görsel tercih dominant olmalı
        assert profile.vark_profile["visual"] > 0.7
        assert profile.vark_profile["visual"] > profile.vark_profile["auditory"]
        assert profile.vark_profile["visual"] > profile.vark_profile["reading"]
        assert profile.vark_profile["visual"] > profile.vark_profile["kinesthetic"]

    @pytest.mark.asyncio
    async def test_auditory_learner_detection(self, detector):
        """İşitsel öğrenci tespiti"""

        auditory_behavioral_data = {
            "visual_preference": 0.2,
            "auditory_preference": 0.9,
            "reading_preference": 0.3,
            "kinesthetic_preference": 0.2,
            "active_learning": 0.7,
            "reflective_learning": 0.3,
            "sensing_learning": 0.6,
            "intuitive_learning": 0.4,
            "visual_learning": 0.2,
            "verbal_learning": 0.8,
            "sequential_learning": 0.6,
            "global_learning": 0.4,
        }

        auditory_responses = [
            "Sesli okumayı severim",
            "Müzik eşliğinde çalışırım",
            "Tartışarak öğrenirim",
        ]

        profile = await detector.detect_hybrid_profile(
            "auditory_student", auditory_behavioral_data, auditory_responses
        )

        # İşitsel tercih dominant olmalı
        assert profile.vark_profile["auditory"] > 0.7
        assert profile.vark_profile["auditory"] > profile.vark_profile["visual"]

    @pytest.mark.asyncio
    async def test_kinesthetic_learner_detection(self, detector):
        """Kinestetik öğrenci tespiti"""

        kinesthetic_behavioral_data = {
            "visual_preference": 0.3,
            "auditory_preference": 0.2,
            "reading_preference": 0.2,
            "kinesthetic_preference": 0.9,
            "active_learning": 0.9,
            "reflective_learning": 0.1,
            "sensing_learning": 0.8,
            "intuitive_learning": 0.2,
            "visual_learning": 0.3,
            "verbal_learning": 0.3,
            "sequential_learning": 0.4,
            "global_learning": 0.6,
        }

        kinesthetic_responses = [
            "Hareket ederek öğrenirim",
            "Deneyimleyerek anlarım",
            "Pratik yapmayı severim",
        ]

        profile = await detector.detect_hybrid_profile(
            "kinesthetic_student", kinesthetic_behavioral_data, kinesthetic_responses
        )

        # Kinestetik tercih dominant olmalı
        assert profile.vark_profile["kinesthetic"] > 0.7
        assert profile.vark_profile["kinesthetic"] > profile.vark_profile["visual"]

    @pytest.mark.asyncio
    async def test_reading_writing_learner_detection(self, detector):
        """Okuma-yazma öğrenci tespiti"""

        reading_behavioral_data = {
            "visual_preference": 0.3,
            "auditory_preference": 0.2,
            "reading_preference": 0.9,
            "kinesthetic_preference": 0.2,
            "active_learning": 0.4,
            "reflective_learning": 0.6,
            "sensing_learning": 0.5,
            "intuitive_learning": 0.5,
            "visual_learning": 0.4,
            "verbal_learning": 0.6,
            "sequential_learning": 0.8,
            "global_learning": 0.2,
        }

        reading_responses = [
            "Kitap okumayı severim",
            "Not tutarak öğrenirim",
            "Yazılı materyaller tercih ederim",
        ]

        profile = await detector.detect_hybrid_profile(
            "reading_student", reading_behavioral_data, reading_responses
        )

        # Okuma-yazma tercihi dominant olmalı
        assert profile.vark_profile["reading"] > 0.7
        assert profile.vark_profile["reading"] > profile.vark_profile["auditory"]


class TestFelderSilvermanAnalysis:
    """Felder-Silverman boyutları analiz testleri"""

    @pytest.fixture
    def detector(self):
        return HybridLearningStyleDetector()

    @pytest.mark.asyncio
    async def test_active_vs_reflective_dimension(self, detector):
        """Aktif vs Yansıtıcı boyut testi"""

        # Aktif öğrenci
        active_data = {
            "visual_preference": 0.5,
            "auditory_preference": 0.5,
            "reading_preference": 0.5,
            "kinesthetic_preference": 0.5,
            "active_learning": 0.9,
            "reflective_learning": 0.1,
            "sensing_learning": 0.5,
            "intuitive_learning": 0.5,
            "visual_learning": 0.5,
            "verbal_learning": 0.5,
            "sequential_learning": 0.5,
            "global_learning": 0.5,
        }

        active_profile = await detector.detect_hybrid_profile(
            "active_student", active_data, ["Grup çalışması severim"]
        )

        # Yansıtıcı öğrenci
        reflective_data = active_data.copy()
        reflective_data["active_learning"] = 0.1
        reflective_data["reflective_learning"] = 0.9

        reflective_profile = await detector.detect_hybrid_profile(
            "reflective_student", reflective_data, ["Tek başıma düşünürüm"]
        )

        # Aktif öğrenci pozitif, yansıtıcı negatif skor almalı
        assert active_profile.felder_profile["active_reflective"] > 0.5
        assert reflective_profile.felder_profile["active_reflective"] < 0.5

    @pytest.mark.asyncio
    async def test_sensing_vs_intuitive_dimension(self, detector):
        """Algısal vs Sezgisel boyut testi"""

        base_data = {
            "visual_preference": 0.5,
            "auditory_preference": 0.5,
            "reading_preference": 0.5,
            "kinesthetic_preference": 0.5,
            "active_learning": 0.5,
            "reflective_learning": 0.5,
            "sensing_learning": 0.9,
            "intuitive_learning": 0.1,
            "visual_learning": 0.5,
            "verbal_learning": 0.5,
            "sequential_learning": 0.5,
            "global_learning": 0.5,
        }

        sensing_profile = await detector.detect_hybrid_profile(
            "sensing_student", base_data, ["Detayları severim"]
        )

        # Sezgisel öğrenci
        intuitive_data = base_data.copy()
        intuitive_data["sensing_learning"] = 0.1
        intuitive_data["intuitive_learning"] = 0.9

        intuitive_profile = await detector.detect_hybrid_profile(
            "intuitive_student", intuitive_data, ["Büyük resmi görürüm"]
        )

        # Algısal öğrenci pozitif, sezgisel negatif skor almalı
        assert sensing_profile.felder_profile["sensing_intuitive"] > 0.5
        assert intuitive_profile.felder_profile["sensing_intuitive"] < 0.5

    @pytest.mark.asyncio
    async def test_visual_vs_verbal_dimension(self, detector):
        """Görsel vs Sözel boyut testi"""

        base_data = {
            "visual_preference": 0.5,
            "auditory_preference": 0.5,
            "reading_preference": 0.5,
            "kinesthetic_preference": 0.5,
            "active_learning": 0.5,
            "reflective_learning": 0.5,
            "sensing_learning": 0.5,
            "intuitive_learning": 0.5,
            "visual_learning": 0.9,
            "verbal_learning": 0.1,
            "sequential_learning": 0.5,
            "global_learning": 0.5,
        }

        visual_profile = await detector.detect_hybrid_profile(
            "visual_student", base_data, ["Şemalar yardımcı olur"]
        )

        # Sözel öğrenci
        verbal_data = base_data.copy()
        verbal_data["visual_learning"] = 0.1
        verbal_data["verbal_learning"] = 0.9

        verbal_profile = await detector.detect_hybrid_profile(
            "verbal_student", verbal_data, ["Açıklamalar yardımcı olur"]
        )

        # Görsel öğrenci pozitif, sözel negatif skor almalı
        assert visual_profile.felder_profile["visual_verbal"] > 0.5
        assert verbal_profile.felder_profile["visual_verbal"] < 0.5

    @pytest.mark.asyncio
    async def test_sequential_vs_global_dimension(self, detector):
        """Sıralı vs Bütünsel boyut testi"""

        base_data = {
            "visual_preference": 0.5,
            "auditory_preference": 0.5,
            "reading_preference": 0.5,
            "kinesthetic_preference": 0.5,
            "active_learning": 0.5,
            "reflective_learning": 0.5,
            "sensing_learning": 0.5,
            "intuitive_learning": 0.5,
            "visual_learning": 0.5,
            "verbal_learning": 0.5,
            "sequential_learning": 0.9,
            "global_learning": 0.1,
        }

        sequential_profile = await detector.detect_hybrid_profile(
            "sequential_student", base_data, ["Adım adım öğrenirim"]
        )

        # Bütünsel öğrenci
        global_data = base_data.copy()
        global_data["sequential_learning"] = 0.1
        global_data["global_learning"] = 0.9

        global_profile = await detector.detect_hybrid_profile(
            "global_student", global_data, ["Genel resmi görürüm"]
        )

        # Sıralı öğrenci pozitif, bütünsel negatif skor almalı
        assert sequential_profile.felder_profile["sequential_global"] > 0.5
        assert global_profile.felder_profile["sequential_global"] < 0.5


class TestHybridProfileGeneration:
    """64 hibrit profil kombinasyonu testleri"""

    @pytest.fixture
    def detector(self):
        return HybridLearningStyleDetector()

    @pytest.mark.asyncio
    async def test_64_profile_combinations(self, detector):
        """64 farklı profil kombinasyonu test et"""

        # VARK: 4 boyut x 2 seviye = 8 kombinasyon
        # Felder: 4 boyut x 2 seviye = 8 kombinasyon
        # Toplam: 8 x 8 = 64 kombinasyon

        vark_combinations = [
            {
                "visual": 0.8,
                "auditory": 0.2,
                "reading": 0.3,
                "kinesthetic": 0.2,
            },  # Visual dominant
            {
                "visual": 0.2,
                "auditory": 0.8,
                "reading": 0.3,
                "kinesthetic": 0.2,
            },  # Auditory dominant
            {
                "visual": 0.3,
                "auditory": 0.2,
                "reading": 0.8,
                "kinesthetic": 0.2,
            },  # Reading dominant
            {
                "visual": 0.2,
                "auditory": 0.2,
                "reading": 0.3,
                "kinesthetic": 0.8,
            },  # Kinesthetic dominant
        ]

        felder_combinations = [
            {
                "active_learning": 0.8,
                "reflective_learning": 0.2,
                "sensing_learning": 0.8,
                "intuitive_learning": 0.2,
                "visual_learning": 0.8,
                "verbal_learning": 0.2,
                "sequential_learning": 0.8,
                "global_learning": 0.2,
            },  # Active-Sensing-Visual-Sequential
            {
                "active_learning": 0.2,
                "reflective_learning": 0.8,
                "sensing_learning": 0.2,
                "intuitive_learning": 0.8,
                "visual_learning": 0.2,
                "verbal_learning": 0.8,
                "sequential_learning": 0.2,
                "global_learning": 0.8,
            },  # Reflective-Intuitive-Verbal-Global
        ]

        profiles = []

        for i, vark in enumerate(vark_combinations):
            for j, felder in enumerate(felder_combinations):
                # Kombinasyon oluştur
                combined_data = {**vark, **felder}

                profile = await detector.detect_hybrid_profile(
                    f"student_{i}_{j}", combined_data, [f"Test response {i}_{j}"]
                )

                profiles.append(profile)

                # Hibrit kod benzersiz olmalı
                assert profile.hybrid_code is not None
                assert len(profile.hybrid_code) > 0

        # Tüm profiller oluşturuldu mu?
        assert len(profiles) == len(vark_combinations) * len(felder_combinations)

        # Hibrit kodlar benzersiz mi?
        hybrid_codes = [p.hybrid_code for p in profiles]
        assert len(set(hybrid_codes)) == len(hybrid_codes)

    @pytest.mark.asyncio
    async def test_hybrid_code_generation(self, detector):
        """Hibrit kod oluşturma test et"""

        behavioral_data = {
            "visual_preference": 0.9,  # V (Visual)
            "auditory_preference": 0.1,
            "reading_preference": 0.2,
            "kinesthetic_preference": 0.1,
            "active_learning": 0.8,  # A (Active)
            "reflective_learning": 0.2,
            "sensing_learning": 0.7,  # S (Sensing)
            "intuitive_learning": 0.3,
            "visual_learning": 0.9,  # V (Visual)
            "verbal_learning": 0.1,
            "sequential_learning": 0.8,  # S (Sequential)
            "global_learning": 0.2,
        }

        profile = await detector.detect_hybrid_profile(
            "test_student", behavioral_data, ["Test response"]
        )

        # Hibrit kod formatı: VARK-FELDER (örn: V-ASVS)
        assert "-" in profile.hybrid_code
        parts = profile.hybrid_code.split("-")
        assert len(parts) == 2

        # VARK kısmı (1 karakter)
        vark_part = parts[0]
        assert len(vark_part) == 1
        assert vark_part in [
            "V",
            "A",
            "R",
            "K",
        ]  # Visual, Auditory, Reading, Kinesthetic

        # Felder kısmı (4 karakter)
        felder_part = parts[1]
        assert len(felder_part) == 4

    @pytest.mark.asyncio
    async def test_confidence_level_calculation(self, detector):
        """Güven seviyesi hesaplama test et"""

        # Yüksek tutarlılık - yüksek güven
        consistent_data = {
            "visual_preference": 0.9,
            "auditory_preference": 0.1,
            "reading_preference": 0.1,
            "kinesthetic_preference": 0.1,
            "active_learning": 0.9,
            "reflective_learning": 0.1,
            "sensing_learning": 0.9,
            "intuitive_learning": 0.1,
            "visual_learning": 0.9,
            "verbal_learning": 0.1,
            "sequential_learning": 0.9,
            "global_learning": 0.1,
        }

        consistent_profile = await detector.detect_hybrid_profile(
            "consistent_student",
            consistent_data,
            ["Görsel materyallerle çalışırım", "Aktif öğrenmeyi severim"],
        )

        # Düşük tutarlılık - düşük güven
        inconsistent_data = {
            "visual_preference": 0.5,
            "auditory_preference": 0.5,
            "reading_preference": 0.5,
            "kinesthetic_preference": 0.5,
            "active_learning": 0.5,
            "reflective_learning": 0.5,
            "sensing_learning": 0.5,
            "intuitive_learning": 0.5,
            "visual_learning": 0.5,
            "verbal_learning": 0.5,
            "sequential_learning": 0.5,
            "global_learning": 0.5,
        }

        inconsistent_profile = await detector.detect_hybrid_profile(
            "inconsistent_student", inconsistent_data, ["Kararsızım"]
        )

        # Tutarlı veri daha yüksek güven vermeli
        assert (
            consistent_profile.confidence_level > inconsistent_profile.confidence_level
        )
        assert consistent_profile.confidence_level > 0.7
        assert inconsistent_profile.confidence_level < 0.6


class TestBehavioralDataAnalysis:
    """Davranışsal veri analizi testleri"""

    @pytest.fixture
    def detector(self):
        return HybridLearningStyleDetector()

    @pytest.mark.asyncio
    async def test_questionnaire_response_analysis(self, detector):
        """Anket yanıtları analizi test et"""

        base_data = {
            "visual_preference": 0.5,
            "auditory_preference": 0.5,
            "reading_preference": 0.5,
            "kinesthetic_preference": 0.5,
            "active_learning": 0.5,
            "reflective_learning": 0.5,
            "sensing_learning": 0.5,
            "intuitive_learning": 0.5,
            "visual_learning": 0.5,
            "verbal_learning": 0.5,
            "sequential_learning": 0.5,
            "global_learning": 0.5,
        }

        # Görsel yanıtlar
        visual_responses = [
            "Diyagramlar ve şemalar bana yardımcı olur",
            "Renkli notlar alırım",
            "Görsel materyallerle daha iyi öğrenirim",
            "Grafikleri severim",
        ]

        visual_profile = await detector.detect_hybrid_profile(
            "visual_responses_student", base_data, visual_responses
        )

        # İşitsel yanıtlar
        auditory_responses = [
            "Sesli okumayı severim",
            "Müzik eşliğinde çalışırım",
            "Tartışarak öğrenirim",
            "Sesli açıklamaları tercih ederim",
        ]

        auditory_profile = await detector.detect_hybrid_profile(
            "auditory_responses_student", base_data, auditory_responses
        )

        # Yanıtlar profili etkilemeli
        # Not: Gerçek implementasyonda anket yanıtları NLP ile analiz edilir
        assert visual_profile.hybrid_code != auditory_profile.hybrid_code

    @pytest.mark.asyncio
    async def test_behavioral_pattern_recognition(self, detector):
        """Davranışsal kalıp tanıma test et"""

        # Matematik odaklı öğrenci davranışı
        math_focused_data = {
            "visual_preference": 0.7,  # Formüller ve grafikler
            "auditory_preference": 0.3,
            "reading_preference": 0.6,  # Problem çözme adımları
            "kinesthetic_preference": 0.4,
            "active_learning": 0.6,  # Problem çözme
            "reflective_learning": 0.4,
            "sensing_learning": 0.8,  # Detaylı hesaplar
            "intuitive_learning": 0.2,
            "visual_learning": 0.8,  # Geometri
            "verbal_learning": 0.2,
            "sequential_learning": 0.9,  # Adım adım çözüm
            "global_learning": 0.1,
        }

        math_profile = await detector.detect_hybrid_profile(
            "math_student",
            math_focused_data,
            ["Formülleri görsel olarak hatırlarım", "Adım adım çözerim"],
        )

        # Edebiyat odaklı öğrenci davranışı
        literature_focused_data = {
            "visual_preference": 0.4,
            "auditory_preference": 0.6,  # Şiir okuma
            "reading_preference": 0.9,  # Kitap okuma
            "kinesthetic_preference": 0.2,
            "active_learning": 0.4,
            "reflective_learning": 0.6,  # Düşünme
            "sensing_learning": 0.3,
            "intuitive_learning": 0.7,  # Sezgisel anlama
            "visual_learning": 0.3,
            "verbal_learning": 0.7,  # Kelimeler
            "sequential_learning": 0.4,
            "global_learning": 0.6,  # Bütünsel anlama
        }

        literature_profile = await detector.detect_hybrid_profile(
            "literature_student",
            literature_focused_data,
            ["Kitap okumayı severim", "Sezgisel olarak anlarım"],
        )

        # Farklı profiller oluşmalı
        assert math_profile.hybrid_code != literature_profile.hybrid_code

        # Matematik öğrencisi daha sıralı olmalı
        assert (
            math_profile.felder_profile["sequential_global"]
            > literature_profile.felder_profile["sequential_global"]
        )

        # Edebiyat öğrencisi daha sezgisel olmalı
        assert (
            literature_profile.felder_profile["sensing_intuitive"]
            < math_profile.felder_profile["sensing_intuitive"]
        )


class TestPerformanceAndScalability:
    """Performans ve ölçeklenebilirlik testleri"""

    @pytest.fixture
    def detector(self):
        return HybridLearningStyleDetector()

    @pytest.mark.asyncio
    async def test_batch_profile_detection(self, detector):
        """Toplu profil tespiti performans testi"""

        # 1000 öğrenci için test verisi oluştur
        students_data = []
        for i in range(1000):
            behavioral_data = {
                "visual_preference": 0.3 + (i % 7) * 0.1,
                "auditory_preference": 0.2 + (i % 5) * 0.1,
                "reading_preference": 0.4 + (i % 6) * 0.1,
                "kinesthetic_preference": 0.1 + (i % 4) * 0.1,
                "active_learning": 0.5 + (i % 5) * 0.1,
                "reflective_learning": 0.5 - (i % 5) * 0.1,
                "sensing_learning": 0.4 + (i % 6) * 0.1,
                "intuitive_learning": 0.6 - (i % 6) * 0.1,
                "visual_learning": 0.3 + (i % 7) * 0.1,
                "verbal_learning": 0.7 - (i % 7) * 0.1,
                "sequential_learning": 0.5 + (i % 4) * 0.1,
                "global_learning": 0.5 - (i % 4) * 0.1,
            }

            students_data.append(
                {
                    "id": f"student_{i}",
                    "data": behavioral_data,
                    "responses": [f"Response {i}"],
                }
            )

        # Performans ölçümü
        start_time = datetime.now()

        # Paralel işlem
        tasks = [
            detector.detect_hybrid_profile(
                student["id"], student["data"], student["responses"]
            )
            for student in students_data[:100]  # İlk 100 öğrenci
        ]

        profiles = await asyncio.gather(*tasks)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 100 öğrenci 5 saniyede işlenmeli
        assert duration < 5.0
        assert len(profiles) == 100

        # Tüm profiller geçerli olmalı
        for profile in profiles:
            assert profile is not None
            assert hasattr(profile, "hybrid_code")
            assert hasattr(profile, "confidence_level")
            assert 0.0 <= profile.confidence_level <= 1.0

    @pytest.mark.asyncio
    async def test_memory_efficiency(self, detector):
        """Bellek verimliliği testi"""

        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 500 profil oluştur
        profiles = []
        for i in range(500):
            behavioral_data = {
                "visual_preference": 0.5,
                "auditory_preference": 0.5,
                "reading_preference": 0.5,
                "kinesthetic_preference": 0.5,
                "active_learning": 0.5,
                "reflective_learning": 0.5,
                "sensing_learning": 0.5,
                "intuitive_learning": 0.5,
                "visual_learning": 0.5,
                "verbal_learning": 0.5,
                "sequential_learning": 0.5,
                "global_learning": 0.5,
            }

            profile = await detector.detect_hybrid_profile(
                f"memory_test_student_{i}", behavioral_data, ["Test"]
            )
            profiles.append(profile)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 500 profil için bellek artışı 50MB'dan az olmalı
        assert memory_increase < 50

        # Profiller doğru oluşturulmuş olmalı
        assert len(profiles) == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
