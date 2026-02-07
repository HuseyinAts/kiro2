"""
Zone of Proximal Development + MEB Maarif Modeli Test - DEVRİMSEL
Türk eğitim kültürüne uyarlanmış ZPD sistemi test dosyası

Bu test dosyası devrimsel ZPD + Maarif sisteminin tüm özelliklerini test eder.
"""

import asyncio
import logging

import pytest

# Test edilecek modüller
from algorithms.turkish_zpd_maarif_system import (
    MaarifValue,
    TurkishCulturalFactor,
    TurkishZPDMaarifSystem,
)
from services.zpd_maarif_service import ZPDMaarifService

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestTurkishZPDMaarifSystem:
    """DEVRİMSEL ZPD + Maarif sistemi test sınıfı"""

    def setup_method(self):
        """Test öncesi hazırlık"""
        self.zpd_system = TurkishZPDMaarifSystem()
        self.zpd_service = ZPDMaarifService()

        # Test verileri
        self.sample_student_id = "test_student_001"
        self.sample_behavioral_data = {
            "group_study_sessions": 15,
            "individual_study_sessions": 8,
            "teacher_question_count": 12,
            "peer_interaction_count": 25,
            "help_seeking_frequency": 10,
            "video_watch_time": 120,
            "text_reading_time": 90,
            "interactive_engagement": 35,
            "quiz_completion_rate": 0.85,
            "hands_on_performance": 0.78,
            "visual_content_performance": 0.82,
            "auditory_content_performance": 0.75,
            "text_content_performance": 0.80,
            "note_taking_frequency": 8,
        }

        self.sample_family_survey = {
            "involvement_level": 0.8,
            "collective_focus": 0.7,
            "elder_respect": 0.9,
            "harmony_importance": 0.85,
        }

    @pytest.mark.asyncio
    async def test_cultural_context_detection(self):
        """Kültürel bağlam tespiti testi"""
        logger.info("🧪 Kültürel bağlam tespiti testi başlatıldı")

        cultural_context = await self.zpd_system.detect_cultural_context(
            student_id=self.sample_student_id,
            behavioral_data=self.sample_behavioral_data,
            family_survey=self.sample_family_survey,
        )

        # Assertions
        assert cultural_context.student_id == self.sample_student_id
        assert 0.0 <= cultural_context.group_learning_preference <= 1.0
        assert 0.0 <= cultural_context.teacher_respect_level <= 1.0
        assert 0.0 <= cultural_context.family_involvement <= 1.0
        assert cultural_context.detected_at is not None

        # Türk kültürü beklentileri
        assert (
            cultural_context.group_learning_preference > 0.5
        )  # Grup çalışması tercihi yüksek
        assert cultural_context.teacher_respect_level > 0.3  # Öğretmene saygı var

        logger.info(
            f"[CHECK] Kültürel bağlam tespit edildi - Grup tercihi: {cultural_context.group_learning_preference:.2f}"
        )

    @pytest.mark.asyncio
    async def test_maarif_alignment_calculation(self):
        """MEB Maarif değerleri uyum hesaplama testi"""
        logger.info("🧪 Maarif uyum hesaplama testi başlatıldı")

        # Tarih konusu - milli değerler yüksek olmalı
        alignment_tarih = await self.zpd_system.calculate_maarif_alignment(
            subject="tarih",
            content_description="Türk tarihinde önemli olaylar, vatan sevgisi ve millet bilinci",
        )

        # Matematik konusu - evrensel değerler yüksek olmalı
        alignment_matematik = await self.zpd_system.calculate_maarif_alignment(
            subject="matematik",
            content_description="Geometri ve sayılar, dürüstlük ve sabır gerektiren problemler",
        )

        # Assertions
        assert alignment_tarih.subject == "tarih"
        assert 0.0 <= alignment_tarih.overall_alignment <= 1.0
        assert len(alignment_tarih.aligned_values) > 0

        assert alignment_matematik.subject == "matematik"
        assert 0.0 <= alignment_matematik.overall_alignment <= 1.0

        # Tarih konusunda milli değerler daha yüksek olmalı
        assert (
            alignment_tarih.national_values_alignment
            >= alignment_matematik.national_values_alignment
        )

        logger.info(
            f"[CHECK] Maarif uyumu hesaplandı - Tarih: {alignment_tarih.overall_alignment:.2f}, "
            f"Matematik: {alignment_matematik.overall_alignment:.2f}"
        )

    @pytest.mark.asyncio
    async def test_turkish_zpd_calculation(self):
        """Türk ZPD hesaplama testi"""
        logger.info("🧪 Türk ZPD hesaplama testi başlatıldı")

        # Kültürel bağlam tespit et
        cultural_context = await self.zpd_system.detect_cultural_context(
            student_id=self.sample_student_id,
            behavioral_data=self.sample_behavioral_data,
            family_survey=self.sample_family_survey,
        )

        # ZPD hesapla
        zpd_range = await self.zpd_system.calculate_turkish_zpd(
            student_id=self.sample_student_id,
            subject="matematik",
            current_level=6.5,
            cultural_context=cultural_context,
            content_description="Türk matematikçilerin katkıları ve geometri",
        )

        # Assertions
        assert zpd_range.student_id == self.sample_student_id
        assert zpd_range.subject == "matematik"
        assert zpd_range.current_level == 6.5
        assert zpd_range.lower_bound <= zpd_range.current_level
        assert (
            zpd_range.current_level
            <= zpd_range.optimal_challenge
            <= zpd_range.upper_bound
        )
        assert 0.0 <= zpd_range.group_individual_balance <= 1.0
        assert zpd_range.calculated_at is not None

        # Türk kültürü etkisi - grup tercihi yüksekse denge grup yönünde olmalı
        if cultural_context.group_learning_preference > 0.7:
            assert zpd_range.group_individual_balance > 0.5

        logger.info(
            f"[CHECK] Türk ZPD hesaplandı - Optimal zorluk: {zpd_range.optimal_challenge:.2f}, "
            f"Grup-bireysel dengesi: {zpd_range.group_individual_balance:.2f}"
        )

    @pytest.mark.asyncio
    async def test_zpd_recommendation_generation(self):
        """ZPD önerisi oluşturma testi"""
        logger.info("🧪 ZPD önerisi oluşturma testi başlatıldı")

        # Kültürel bağlam ve ZPD hesapla
        cultural_context = await self.zpd_system.detect_cultural_context(
            student_id=self.sample_student_id,
            behavioral_data=self.sample_behavioral_data,
            family_survey=self.sample_family_survey,
        )

        zpd_range = await self.zpd_system.calculate_turkish_zpd(
            student_id=self.sample_student_id,
            subject="matematik",
            current_level=6.5,
            cultural_context=cultural_context,
            content_description="Geometri ve problem çözme",
        )

        # Öneri oluştur
        recommendation = await self.zpd_system.generate_zpd_recommendation(
            zpd_range=zpd_range, learning_objective="Geometri konusunda uzmanlaşma"
        )

        # Assertions
        assert recommendation.student_id == self.sample_student_id
        assert recommendation.subject == "matematik"
        assert 0.0 <= recommendation.recommended_difficulty <= 10.0
        assert recommendation.learning_mode in ["individual", "group", "mixed"]
        assert recommendation.content_type in [
            "visual",
            "textual",
            "interactive",
            "mixed",
        ]
        assert 0.0 <= recommendation.teacher_guidance_level <= 1.0
        assert 0.0 <= recommendation.peer_support_level <= 1.0
        assert 0.0 <= recommendation.confidence_score <= 1.0
        assert len(recommendation.reasoning) > 0

        # Türk kültürü beklentileri
        if cultural_context.group_learning_preference > 0.7:
            assert recommendation.learning_mode in ["group", "mixed"]

        logger.info(
            f"[CHECK] ZPD önerisi oluşturuldu - Mod: {recommendation.learning_mode}, "
            f"Zorluk: {recommendation.recommended_difficulty:.2f}, "
            f"Güven: {recommendation.confidence_score:.2f}"
        )

    @pytest.mark.asyncio
    async def test_cultural_difficulty_adaptation(self):
        """Kültürel zorluk adaptasyonu testi"""
        logger.info("🧪 Kültürel zorluk adaptasyonu testi başlatıldı")

        # Kültürel bağlam tespit et
        cultural_context = await self.zpd_system.detect_cultural_context(
            student_id=self.sample_student_id,
            behavioral_data=self.sample_behavioral_data,
            family_survey=self.sample_family_survey,
        )

        # Örnek performans verileri
        student_performance = {
            "individual_score": 0.6,
            "group_score": 0.8,
            "teacher_feedback_score": 0.7,
            "homework_score": 0.75,
        }

        # Zorluk adaptasyonu
        original_difficulty = 6.0
        adapted_difficulty = await self.zpd_system.adapt_difficulty_culturally(
            current_difficulty=original_difficulty,
            student_performance=student_performance,
            cultural_context=cultural_context,
        )

        # Assertions
        assert 0.1 <= adapted_difficulty <= 10.0
        assert adapted_difficulty != original_difficulty  # Bir değişiklik olmalı

        # Grup başarısı bireysel başarıdan yüksekse ve kolektif odak varsa artış beklenir
        if (
            student_performance["group_score"] > student_performance["individual_score"]
            and cultural_context.collective_success > 0.7
        ):
            assert adapted_difficulty >= original_difficulty

        logger.info(
            f"[CHECK] Kültürel zorluk adaptasyonu: {original_difficulty:.2f} → {adapted_difficulty:.2f}"
        )

    @pytest.mark.asyncio
    async def test_cultural_learning_patterns(self):
        """Kültürel öğrenme kalıpları analizi testi"""
        logger.info("🧪 Kültürel öğrenme kalıpları analizi testi başlatıldı")

        # Örnek öğrenme oturumları
        learning_sessions = [
            {
                "mode": "group",
                "score": 0.8,
                "teacher_interaction_count": 5,
                "maarif_aligned": True,
            },
            {
                "mode": "individual",
                "score": 0.6,
                "teacher_interaction_count": 2,
                "maarif_aligned": False,
            },
            {
                "mode": "group",
                "score": 0.85,
                "teacher_interaction_count": 7,
                "maarif_aligned": True,
            },
            {
                "mode": "individual",
                "score": 0.65,
                "teacher_interaction_count": 1,
                "maarif_aligned": False,
            },
        ]

        # Kalıp analizi
        patterns = await self.zpd_system.monitor_cultural_learning_patterns(
            student_id=self.sample_student_id, learning_sessions=learning_sessions
        )

        # Assertions
        assert "group_vs_individual_performance" in patterns
        assert "teacher_interaction_correlation" in patterns
        assert "maarif_content_engagement" in patterns

        # Grup vs bireysel performans analizi
        if "group_preference_confirmed" in patterns["group_vs_individual_performance"]:
            group_confirmed = patterns["group_vs_individual_performance"][
                "group_preference_confirmed"
            ]
            assert isinstance(group_confirmed, bool)

        logger.info(
            f"[CHECK] Kültürel kalıp analizi tamamlandı - {len(patterns)} kalıp tespit edildi"
        )

    @pytest.mark.asyncio
    async def test_service_integration(self):
        """Servis entegrasyonu testi"""
        logger.info("🧪 Servis entegrasyonu testi başlatıldı")

        # Devrimsel ZPD hesaplama
        zpd_range = await self.zpd_service.calculate_revolutionary_zpd(
            student_id=self.sample_student_id,
            subject="türkçe",
            current_level=7.0,
            behavioral_data=self.sample_behavioral_data,
            content_description="Türk edebiyatı ve dil bilgisi",
            family_survey=self.sample_family_survey,
        )

        # Assertions
        assert zpd_range.student_id == self.sample_student_id
        assert zpd_range.subject == "türkçe"
        assert zpd_range.current_level == 7.0

        # Devrimsel öneri oluşturma
        recommendation = await self.zpd_service.generate_revolutionary_recommendation(
            student_id=self.sample_student_id,
            subject="türkçe",
            current_level=7.0,
            behavioral_data=self.sample_behavioral_data,
            learning_objective="Türk edebiyatında uzmanlaşma",
            content_description="Türk edebiyatı ve dil bilgisi",
            family_survey=self.sample_family_survey,
        )

        # Assertions
        assert recommendation.student_id == self.sample_student_id
        assert recommendation.subject == "türkçe"

        logger.info(
            f"[CHECK] Servis entegrasyonu başarılı - ZPD: {zpd_range.optimal_challenge:.2f}, "
            f"Öneri: {recommendation.learning_mode}"
        )

    def test_maarif_values_enum(self):
        """MEB Maarif değerleri enum testi"""
        logger.info("🧪 Maarif değerleri enum testi başlatıldı")

        # Milli değerler
        assert MaarifValue.VATAN in MaarifValue
        assert MaarifValue.MILLET in MaarifValue
        assert MaarifValue.AILE in MaarifValue

        # Evrensel değerler
        assert MaarifValue.ADALET in MaarifValue
        assert MaarifValue.DOSTLUK in MaarifValue
        assert MaarifValue.DÜRÜSTLÜK in MaarifValue

        # Kök değerler
        assert MaarifValue.SABIR in MaarifValue
        assert MaarifValue.MERHAMET in MaarifValue
        assert MaarifValue.HOŞGÖRÜ in MaarifValue

        logger.info("[CHECK] Maarif değerleri enum testi başarılı")

    def test_cultural_factors_enum(self):
        """Türk kültürü faktörleri enum testi"""
        logger.info("🧪 Kültürel faktörler enum testi başlatıldı")

        # Temel faktörler
        assert TurkishCulturalFactor.GROUP_LEARNING_PREFERENCE in TurkishCulturalFactor
        assert TurkishCulturalFactor.TEACHER_RESPECT_LEVEL in TurkishCulturalFactor
        assert TurkishCulturalFactor.FAMILY_INVOLVEMENT in TurkishCulturalFactor
        assert TurkishCulturalFactor.PEER_COMPETITION in TurkishCulturalFactor

        logger.info("[CHECK] Kültürel faktörler enum testi başarılı")


async def run_comprehensive_test():
    """Kapsamlı test çalıştırma"""
    logger.info("[ROCKET] DEVRİMSEL ZPD + MEB MAAİF SİSTEMİ KAPSAMLI TEST BAŞLATIYOR")

    test_instance = TestTurkishZPDMaarifSystem()
    test_instance.setup_method()

    try:
        # Tüm testleri sırayla çalıştır
        await test_instance.test_cultural_context_detection()
        await test_instance.test_maarif_alignment_calculation()
        await test_instance.test_turkish_zpd_calculation()
        await test_instance.test_zpd_recommendation_generation()
        await test_instance.test_cultural_difficulty_adaptation()
        await test_instance.test_cultural_learning_patterns()
        await test_instance.test_service_integration()
        test_instance.test_maarif_values_enum()
        test_instance.test_cultural_factors_enum()

        logger.info("[PARTY] TÜM TESTLER BAŞARIYLA TAMAMLANDI!")
        logger.info("[ROCKET] DEVRİMSEL ZPD + MEB MAAİF SİSTEMİ TAM ÇALIŞIR DURUMDA!")

        return True

    except Exception as e:
        logger.error(f"[X] Test hatası: {str(e)}")
        return False


if __name__ == "__main__":
    # Test çalıştırma
    success = asyncio.run(run_comprehensive_test())

    if success:
        print("\n" + "=" * 80)
        print("[ROCKET] DEVRİMSEL ZPD + MEB MAAİF SİSTEMİ TEST RAPORU")
        print("=" * 80)
        print("[CHECK] Kültürel bağlam tespiti: BAŞARILI")
        print("[CHECK] MEB Maarif değerleri uyumu: BAŞARILI")
        print("[CHECK] Türk ZPD hesaplama: BAŞARILI")
        print("[CHECK] ZPD önerisi oluşturma: BAŞARILI")
        print("[CHECK] Kültürel zorluk adaptasyonu: BAŞARILI")
        print("[CHECK] Kültürel öğrenme kalıpları: BAŞARILI")
        print("[CHECK] Servis entegrasyonu: BAŞARILI")
        print("[CHECK] Enum yapıları: BAŞARILI")
        print("=" * 80)
        print("[PARTY] SİSTEM HAZIR VE ÇALIŞIR DURUMDA!")
        print("🇹🇷 TÜRKİYE'YE ÖZEL DEVRİMSEL EĞİTİM TEKNOLOJİSİ AKTİF!")
    else:
        print("\n[X] TESTLERDE HATA OLUŞTU - LÜTFEN LOGLARI KONTROL EDİN")
