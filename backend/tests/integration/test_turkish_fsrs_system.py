"""
Türk FSRS (Free Spaced Repetition System) Kapsamlı Test Suite
17 Parametreli Türk Öğrenci Davranışlarına Optimize Edilmiş Sistem

Bu test dosyası, Anki'nin FSRS 4.5 algoritmasının Türk öğrenci verilerine
göre optimize edilmiş versiyonunu test eder.

Requirements: 10.4, 12.3
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch

import numpy as np
import pytest

from algorithms.turkish_optimized_fsrs import TurkishOptimizedFSRS
from models.learning_models import Flashcard


class TestTurkishFSRSParameters:
    """Türk FSRS parametreleri testleri"""

    @pytest.fixture
    def fsrs_system(self):
        return TurkishOptimizedFSRS()

    def test_turkish_parameters_count(self, fsrs_system):
        """17 parametre sayısı kontrolü"""

        assert len(fsrs_system.turkish_params) == 17

        # Parametreler pozitif değerler olmalı
        for param in fsrs_system.turkish_params:
            assert param > 0

    def test_turkish_parameters_optimization(self, fsrs_system):
        """Türk öğrenci verilerine göre optimize edilmiş parametreler"""

        params = fsrs_system.turkish_params

        # Initial Stability - Türkçe ezberleme zorluğu
        assert 0.3 <= params[0] <= 0.5  # Türkçe kelimeler daha zor ezberlenebilir

        # Grade factors - Türk öğrenci tepki kalıpları
        assert params[1] < params[2] < params[3] < params[4]  # Artan zorluk

        # Hard penalty - Türkçe kelime unutma hızı
        assert params[4] > 4.0  # Türkçe morfoloji karmaşıklığı

        # Target retention - Türk eğitim sistemi hedefi
        assert 1.2 <= params[14] <= 1.3  # Yüksek başarı beklentisi

    def test_cultural_adjustments_factors(self, fsrs_system):
        """Kültürel ayarlama faktörleri"""

        cultural = fsrs_system.cultural_adjustments

        # Ramazan faktörü - unutma hızı artışı
        assert 0.7 <= cultural["ramadan_factor"] <= 0.9

        # Sınav dönemi stresi - performans düşüşü
        assert 1.2 <= cultural["exam_season_stress"] <= 1.4

        # Yaz tatili unutma - uzun ara etkisi
        assert 0.5 <= cultural["summer_break_decay"] <= 0.7

        # Grup çalışması bonusu - sosyal öğrenme
        assert 1.1 <= cultural["group_study_bonus"] <= 1.3

        # Aile baskısı - motivasyon etkisi
        assert 1.0 <= cultural["family_pressure"] <= 1.2


class TestFSRSIntervalCalculation:
    """FSRS aralık hesaplama testleri"""

    @pytest.fixture
    def fsrs_system(self):
        return TurkishOptimizedFSRS()

    @pytest.fixture
    def sample_flashcard(self):
        return Flashcard(
            id="test_card_123",
            content="Osmanlı İmparatorluğu'nun kuruluş tarihi",
            answer="1299",
            difficulty=1.5,
            last_review=datetime.now() - timedelta(days=3),
            review_count=5,
            success_rate=0.8,
            stability=2.0,
            retrievability=0.9,
        )

    @pytest.mark.asyncio
    async def test_grade_based_intervals(self, fsrs_system, sample_flashcard):
        """Performans notuna göre aralık hesaplama"""

        current_date = datetime.now()
        base_context = {"exam_season": False, "group_study": False}

        # Grade 1 (Again) - Tekrar gerekli
        grade1_review = await fsrs_system.calculate_next_review(
            sample_flashcard, 1, current_date, base_context
        )

        # Grade 2 (Hard) - Zor
        grade2_review = await fsrs_system.calculate_next_review(
            sample_flashcard, 2, current_date, base_context
        )

        # Grade 3 (Good) - İyi
        grade3_review = await fsrs_system.calculate_next_review(
            sample_flashcard, 3, current_date, base_context
        )

        # Grade 4 (Easy) - Kolay
        grade4_review = await fsrs_system.calculate_next_review(
            sample_flashcard, 4, current_date, base_context
        )

        # Aralıklar artan sırada olmalı
        intervals = [
            (grade1_review - current_date).days,
            (grade2_review - current_date).days,
            (grade3_review - current_date).days,
            (grade4_review - current_date).days,
        ]

        assert intervals[0] <= intervals[1] <= intervals[2] <= intervals[3]

        # Grade 1 çok kısa aralık (1-2 gün)
        assert 1 <= intervals[0] <= 2

        # Grade 4 uzun aralık (1+ hafta)
        assert intervals[3] >= 7

    @pytest.mark.asyncio
    async def test_stability_impact(self, fsrs_system):
        """Stabilite etkisi testi"""

        current_date = datetime.now()
        base_context = {"exam_season": False, "group_study": False}

        # Düşük stabilite kartı
        low_stability_card = Flashcard(
            id="low_stability",
            content="Zor konu",
            answer="Cevap",
            difficulty=2.5,
            last_review=current_date - timedelta(days=1),
            review_count=2,
            success_rate=0.4,
            stability=0.5,
            retrievability=0.6,
        )

        # Yüksek stabilite kartı
        high_stability_card = Flashcard(
            id="high_stability",
            content="Kolay konu",
            answer="Cevap",
            difficulty=1.0,
            last_review=current_date - timedelta(days=1),
            review_count=10,
            success_rate=0.9,
            stability=5.0,
            retrievability=0.95,
        )

        # Aynı grade ile karşılaştır
        low_review = await fsrs_system.calculate_next_review(
            low_stability_card, 3, current_date, base_context
        )

        high_review = await fsrs_system.calculate_next_review(
            high_stability_card, 3, current_date, base_context
        )

        # Yüksek stabilite daha uzun aralık vermeli
        low_interval = (low_review - current_date).days
        high_interval = (high_review - current_date).days

        assert high_interval > low_interval

    @pytest.mark.asyncio
    async def test_retrievability_calculation(self, fsrs_system, sample_flashcard):
        """Geri getirilebilirlik hesaplama"""

        current_date = datetime.now()

        # Son tekrardan geçen süre
        days_since_review = 5
        sample_flashcard.last_review = current_date - timedelta(days=days_since_review)

        # Retrievability hesapla (exponential decay)
        expected_retrievability = np.exp(
            -days_since_review / sample_flashcard.stability
        )

        # FSRS hesaplama
        base_context = {"exam_season": False, "group_study": False}
        next_review = await fsrs_system.calculate_next_review(
            sample_flashcard, 3, current_date, base_context
        )

        # Düşük retrievability daha kısa aralık vermeli
        interval = (next_review - current_date).days

        if expected_retrievability < 0.8:
            assert interval <= 7  # Kısa aralık
        else:
            assert interval > 7  # Uzun aralık


class TestCulturalAdjustments:
    """Kültürel ayarlamalar testleri"""

    @pytest.fixture
    def fsrs_system(self):
        return TurkishOptimizedFSRS()

    @pytest.fixture
    def sample_flashcard(self):
        return Flashcard(
            id="cultural_test_card",
            content="Test içeriği",
            answer="Test cevabı",
            difficulty=1.5,
            last_review=datetime.now() - timedelta(days=2),
            review_count=3,
            success_rate=0.7,
            stability=2.0,
            retrievability=0.8,
        )

    @pytest.mark.asyncio
    async def test_ramadan_period_adjustment(self, fsrs_system, sample_flashcard):
        """Ramazan dönemi ayarlaması"""

        current_date = datetime.now()
        base_context = {"exam_season": False, "group_study": False}

        # Normal dönem
        with patch.object(fsrs_system, "_is_ramadan_period", return_value=False):
            normal_review = await fsrs_system.calculate_next_review(
                sample_flashcard, 3, current_date, base_context
            )

        # Ramazan dönemi
        with patch.object(fsrs_system, "_is_ramadan_period", return_value=True):
            ramadan_review = await fsrs_system.calculate_next_review(
                sample_flashcard, 3, current_date, base_context
            )

        # Ramazan'da daha kısa aralık
        normal_interval = (normal_review - current_date).days
        ramadan_interval = (ramadan_review - current_date).days

        assert ramadan_interval < normal_interval

        # Ramazan faktörü uygulandı mı?
        expected_ratio = fsrs_system.cultural_adjustments["ramadan_factor"]
        actual_ratio = ramadan_interval / normal_interval

        assert 0.7 <= actual_ratio <= 0.9  # Ramazan faktörü aralığında

    @pytest.mark.asyncio
    async def test_exam_season_stress(self, fsrs_system, sample_flashcard):
        """Sınav dönemi stresi ayarlaması"""

        current_date = datetime.now()

        # Normal dönem
        normal_context = {"exam_season": False, "group_study": False}
        normal_review = await fsrs_system.calculate_next_review(
            sample_flashcard, 3, current_date, normal_context
        )

        # Sınav dönemi
        exam_context = {"exam_season": True, "group_study": False}
        exam_review = await fsrs_system.calculate_next_review(
            sample_flashcard, 3, current_date, exam_context
        )

        # Sınav döneminde daha sık tekrar
        normal_interval = (normal_review - current_date).days
        exam_interval = (exam_review - current_date).days

        assert exam_interval < normal_interval

        # Stres faktörü uygulandı mı?
        stress_factor = fsrs_system.cultural_adjustments["exam_season_stress"]
        # Stres faktörü > 1 olduğu için aralık kısalır
        expected_ratio = 1.0 / stress_factor
        actual_ratio = exam_interval / normal_interval

        assert 0.7 <= actual_ratio <= 0.9

    @pytest.mark.asyncio
    async def test_summer_break_decay(self, fsrs_system, sample_flashcard):
        """Yaz tatili unutma ayarlaması"""

        current_date = datetime.now()
        base_context = {"exam_season": False, "group_study": False}

        # Normal dönem
        with patch.object(fsrs_system, "_is_summer_break", return_value=False):
            normal_review = await fsrs_system.calculate_next_review(
                sample_flashcard, 3, current_date, base_context
            )

        # Yaz tatili
        with patch.object(fsrs_system, "_is_summer_break", return_value=True):
            summer_review = await fsrs_system.calculate_next_review(
                sample_flashcard, 3, current_date, base_context
            )

        # Yaz tatilinde daha sık tekrar (unutma hızı artar)
        normal_interval = (normal_review - current_date).days
        summer_interval = (summer_review - current_date).days

        assert summer_interval < normal_interval

        # Yaz tatili faktörü
        decay_factor = fsrs_system.cultural_adjustments["summer_break_decay"]
        actual_ratio = summer_interval / normal_interval

        assert 0.5 <= actual_ratio <= 0.7

    @pytest.mark.asyncio
    async def test_group_study_bonus(self, fsrs_system, sample_flashcard):
        """Grup çalışması bonusu"""

        current_date = datetime.now()

        # Bireysel çalışma
        individual_context = {"exam_season": False, "group_study": False}
        individual_review = await fsrs_system.calculate_next_review(
            sample_flashcard, 3, current_date, individual_context
        )

        # Grup çalışması
        group_context = {"exam_season": False, "group_study": True}
        group_review = await fsrs_system.calculate_next_review(
            sample_flashcard, 3, current_date, group_context
        )

        # Grup çalışması daha uzun aralık (daha iyi öğrenme)
        individual_interval = (individual_review - current_date).days
        group_interval = (group_review - current_date).days

        assert group_interval > individual_interval

        # Grup bonusu faktörü
        bonus_factor = fsrs_system.cultural_adjustments["group_study_bonus"]
        actual_ratio = group_interval / individual_interval

        assert 1.1 <= actual_ratio <= 1.3

    @pytest.mark.asyncio
    async def test_combined_cultural_factors(self, fsrs_system, sample_flashcard):
        """Birleşik kültürel faktörler"""

        current_date = datetime.now()

        # Tüm olumsuz faktörler (Ramazan + Sınav dönemi + Yaz tatili)
        with patch.object(
            fsrs_system, "_is_ramadan_period", return_value=True
        ), patch.object(fsrs_system, "_is_summer_break", return_value=True):
            negative_context = {"exam_season": True, "group_study": False}
            negative_review = await fsrs_system.calculate_next_review(
                sample_flashcard, 3, current_date, negative_context
            )

        # Tüm olumlu faktörler (Normal dönem + Grup çalışması)
        with patch.object(
            fsrs_system, "_is_ramadan_period", return_value=False
        ), patch.object(fsrs_system, "_is_summer_break", return_value=False):
            positive_context = {"exam_season": False, "group_study": True}
            positive_review = await fsrs_system.calculate_next_review(
                sample_flashcard, 3, current_date, positive_context
            )

        # Olumlu koşullar daha uzun aralık vermeli
        negative_interval = (negative_review - current_date).days
        positive_interval = (positive_review - current_date).days

        assert positive_interval > negative_interval

        # Faktör kombinasyonu etkisi
        ratio = positive_interval / negative_interval
        assert ratio > 2.0  # En az 2 kat fark


class TestFSRSPerformanceOptimization:
    """FSRS performans optimizasyonu testleri"""

    @pytest.fixture
    def fsrs_system(self):
        return TurkishOptimizedFSRS()

    @pytest.mark.asyncio
    async def test_batch_interval_calculation(self, fsrs_system):
        """Toplu aralık hesaplama performansı"""

        # 1000 flashcard oluştur
        flashcards = []
        for i in range(1000):
            card = Flashcard(
                id=f"batch_card_{i}",
                content=f"İçerik {i}",
                answer=f"Cevap {i}",
                difficulty=1.0 + (i % 5) * 0.5,
                last_review=datetime.now() - timedelta(days=i % 10),
                review_count=i % 20,
                success_rate=0.5 + (i % 10) * 0.05,
                stability=1.0 + (i % 10) * 0.5,
                retrievability=0.7 + (i % 3) * 0.1,
            )
            flashcards.append(card)

        current_date = datetime.now()
        base_context = {"exam_season": False, "group_study": False}

        # Performans ölçümü
        start_time = datetime.now()

        # Paralel hesaplama
        tasks = [
            fsrs_system.calculate_next_review(card, 3, current_date, base_context)
            for card in flashcards[:100]  # İlk 100 kart
        ]

        reviews = await asyncio.gather(*tasks)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 100 kart 2 saniyede hesaplanmalı
        assert duration < 2.0
        assert len(reviews) == 100

        # Tüm sonuçlar geçerli olmalı
        for review in reviews:
            assert review > current_date
            assert (review - current_date).days <= 365  # Maksimum 1 yıl

    @pytest.mark.asyncio
    async def test_memory_efficiency_large_dataset(self, fsrs_system):
        """Büyük veri seti bellek verimliliği"""

        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 5000 flashcard işle
        current_date = datetime.now()
        base_context = {"exam_season": False, "group_study": False}

        for i in range(5000):
            card = Flashcard(
                id=f"memory_test_{i}",
                content=f"Test {i}",
                answer=f"Answer {i}",
                difficulty=1.5,
                last_review=current_date - timedelta(days=2),
                review_count=5,
                success_rate=0.8,
                stability=2.0,
                retrievability=0.9,
            )

            # Hesapla ve hemen sil (memory leak testi)
            await fsrs_system.calculate_next_review(card, 3, current_date, base_context)
            del card

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 5000 işlem için bellek artışı 20MB'dan az olmalı
        assert memory_increase < 20


class TestFSRSAccuracy:
    """FSRS doğruluk testleri"""

    @pytest.fixture
    def fsrs_system(self):
        return TurkishOptimizedFSRS()

    @pytest.mark.asyncio
    async def test_forgetting_curve_accuracy(self, fsrs_system):
        """Unutma eğrisi doğruluğu"""

        # Bilinen parametrelerle kart
        card = Flashcard(
            id="accuracy_test",
            content="Test içeriği",
            answer="Test cevabı",
            difficulty=1.5,
            last_review=datetime.now() - timedelta(days=0),
            review_count=5,
            success_rate=0.8,
            stability=10.0,  # 10 günlük stabilite
            retrievability=1.0,
        )

        current_date = datetime.now()
        base_context = {"exam_season": False, "group_study": False}

        # Farklı günlerde retrievability hesapla
        test_days = [1, 5, 10, 15, 20]
        retrievabilities = []

        for days in test_days:
            card.last_review = current_date - timedelta(days=days)

            # Retrievability = exp(-days / stability)
            expected_retrievability = np.exp(-days / card.stability)
            retrievabilities.append(expected_retrievability)

            # FSRS hesaplama
            next_review = await fsrs_system.calculate_next_review(
                card, 3, current_date, base_context
            )

            # Düşük retrievability daha kısa aralık vermeli
            interval = (next_review - current_date).days

            if expected_retrievability < 0.8:
                assert interval <= card.stability
            else:
                assert interval >= card.stability

        # Retrievability azalma trendi
        for i in range(1, len(retrievabilities)):
            assert retrievabilities[i] < retrievabilities[i - 1]

    @pytest.mark.asyncio
    async def test_difficulty_adjustment_accuracy(self, fsrs_system):
        """Zorluk ayarlama doğruluğu"""

        current_date = datetime.now()
        base_context = {"exam_season": False, "group_study": False}

        # Kolay kart (yüksek başarı oranı)
        easy_card = Flashcard(
            id="easy_card",
            content="Kolay içerik",
            answer="Kolay cevap",
            difficulty=0.5,
            last_review=current_date - timedelta(days=2),
            review_count=10,
            success_rate=0.95,
            stability=5.0,
            retrievability=0.9,
        )

        # Zor kart (düşük başarı oranı)
        hard_card = Flashcard(
            id="hard_card",
            content="Zor içerik",
            answer="Zor cevap",
            difficulty=3.0,
            last_review=current_date - timedelta(days=2),
            review_count=10,
            success_rate=0.4,
            stability=1.0,
            retrievability=0.6,
        )

        # Aynı grade ile karşılaştır
        easy_review = await fsrs_system.calculate_next_review(
            easy_card, 3, current_date, base_context
        )

        hard_review = await fsrs_system.calculate_next_review(
            hard_card, 3, current_date, base_context
        )

        # Kolay kart daha uzun aralık almalı
        easy_interval = (easy_review - current_date).days
        hard_interval = (hard_review - current_date).days

        assert easy_interval > hard_interval

        # Zorluk farkı oransal olmalı
        difficulty_ratio = hard_card.difficulty / easy_card.difficulty
        interval_ratio = easy_interval / hard_interval

        # Zorluk 6 kat fazlaysa, aralık en az 2 kat fazla olmalı
        assert interval_ratio >= 2.0


class TestFSRSEdgeCases:
    """FSRS sınır durumları testleri"""

    @pytest.fixture
    def fsrs_system(self):
        return TurkishOptimizedFSRS()

    @pytest.mark.asyncio
    async def test_new_card_handling(self, fsrs_system):
        """Yeni kart işleme"""

        # Hiç çalışılmamış kart
        new_card = Flashcard(
            id="new_card",
            content="Yeni içerik",
            answer="Yeni cevap",
            difficulty=1.0,
            last_review=None,
            review_count=0,
            success_rate=0.0,
            stability=0.0,
            retrievability=0.0,
        )

        current_date = datetime.now()
        base_context = {"exam_season": False, "group_study": False}

        # İlk çalışma
        first_review = await fsrs_system.calculate_next_review(
            new_card, 3, current_date, base_context
        )

        # Yeni kart kısa aralık almalı (1-3 gün)
        interval = (first_review - current_date).days
        assert 1 <= interval <= 3

    @pytest.mark.asyncio
    async def test_maximum_interval_limit(self, fsrs_system):
        """Maksimum aralık sınırı"""

        # Çok başarılı kart
        perfect_card = Flashcard(
            id="perfect_card",
            content="Mükemmel içerik",
            answer="Mükemmel cevap",
            difficulty=0.1,
            last_review=datetime.now() - timedelta(days=1),
            review_count=50,
            success_rate=1.0,
            stability=100.0,
            retrievability=0.99,
        )

        current_date = datetime.now()
        base_context = {"exam_season": False, "group_study": False}

        # En yüksek grade
        next_review = await fsrs_system.calculate_next_review(
            perfect_card, 4, current_date, base_context
        )

        # Maksimum 1 yıl sınırı
        interval = (next_review - current_date).days
        assert interval <= 365

    @pytest.mark.asyncio
    async def test_minimum_interval_limit(self, fsrs_system):
        """Minimum aralık sınırı"""

        # Çok başarısız kart
        failed_card = Flashcard(
            id="failed_card",
            content="Başarısız içerik",
            answer="Başarısız cevap",
            difficulty=5.0,
            last_review=datetime.now() - timedelta(days=1),
            review_count=20,
            success_rate=0.1,
            stability=0.1,
            retrievability=0.1,
        )

        current_date = datetime.now()
        base_context = {"exam_season": False, "group_study": False}

        # En düşük grade
        next_review = await fsrs_system.calculate_next_review(
            failed_card, 1, current_date, base_context
        )

        # Minimum 1 gün sınırı
        interval = (next_review - current_date).days
        assert interval >= 1

    @pytest.mark.asyncio
    async def test_invalid_grade_handling(self, fsrs_system):
        """Geçersiz grade işleme"""

        card = Flashcard(
            id="test_card",
            content="Test",
            answer="Test",
            difficulty=1.5,
            last_review=datetime.now() - timedelta(days=2),
            review_count=5,
            success_rate=0.8,
            stability=2.0,
            retrievability=0.9,
        )

        current_date = datetime.now()
        base_context = {"exam_season": False, "group_study": False}

        # Geçersiz grade değerleri
        invalid_grades = [0, 5, -1, 10]

        for invalid_grade in invalid_grades:
            with pytest.raises((ValueError, AssertionError)):
                await fsrs_system.calculate_next_review(
                    card, invalid_grade, current_date, base_context
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
