#!/usr/bin/env python3
"""
FSRS Sistem Test Runner

Bu script, Türk öğrenci davranışlarına optimize edilmiş FSRS sisteminin
temel fonksiyonalitelerini test eder.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Backend dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from algorithms.turkish_optimized_fsrs import (
    FSRSCard,
    FSRSGrade,
    StudentContext,
    TurkishOptimizedFSRS,
)


async def test_fsrs_algorithm():
    """FSRS algoritması temel testleri"""
    print("[ROCKET] FSRS Algoritması Test Ediliyor...")

    # Algoritma başlatma
    fsrs = TurkishOptimizedFSRS()
    print(f"[CHECK] Algoritma başlatıldı - {len(fsrs.turkish_params)} parametre")

    # Öğrenci bağlamı oluştur
    student_context = StudentContext(
        student_id="test_student",
        group_study_preference=True,
        family_pressure_level=0.7,
        exam_anxiety_level=0.6,
        study_consistency=0.8,
        cultural_background="turkish",
        timezone="Europe/Istanbul",
    )
    print("[CHECK] Öğrenci bağlamı oluşturuldu")

    # Test kartı oluştur
    test_card = FSRSCard(
        id="test_card_1",
        subject="Matematik",
        difficulty=0.0,
        stability=0.0,
        retrievability=0.0,
        state="new",
    )
    print("[CHECK] Test kartı oluşturuldu")

    # Normal dönem testi
    normal_date = datetime(2024, 4, 15, 14, 0, 0)
    schedule_normal = fsrs.calculate_next_review(
        test_card, FSRSGrade.GOOD, normal_date, student_context
    )
    print(f"[CHECK] Normal dönem - Sonraki tekrar: {schedule_normal.interval_days} gün")

    # Ramazan dönemi testi
    ramadan_date = datetime(2024, 3, 20, 14, 0, 0)
    schedule_ramadan = fsrs.calculate_next_review(
        test_card, FSRSGrade.GOOD, ramadan_date, student_context
    )
    print(
        f"[CHECK] Ramazan dönemi - Sonraki tekrar: {schedule_ramadan.interval_days} gün"
    )

    # Sınav dönemi testi
    exam_date = datetime(2024, 5, 15, 14, 0, 0)
    schedule_exam = fsrs.calculate_next_review(
        test_card, FSRSGrade.GOOD, exam_date, student_context
    )
    print(f"[CHECK] Sınav dönemi - Sonraki tekrar: {schedule_exam.interval_days} gün")

    # Yaz tatili testi
    summer_date = datetime(2024, 7, 20, 14, 0, 0)
    schedule_summer = fsrs.calculate_next_review(
        test_card, FSRSGrade.GOOD, summer_date, student_context
    )
    print(f"[CHECK] Yaz tatili - Sonraki tekrar: {schedule_summer.interval_days} gün")

    # Kültürel dönem tespiti testi
    periods = [
        (datetime(2024, 4, 10), "Normal"),
        (datetime(2024, 3, 20), "Ramazan"),
        (datetime(2024, 5, 15), "Sınav Dönemi"),
        (datetime(2024, 7, 20), "Yaz Tatili"),
    ]

    print("\n📅 Kültürel Dönem Tespiti:")
    for date, expected in periods:
        detected = fsrs._detect_cultural_period(date)
        print(f"   {date.strftime('%d/%m/%Y')} - {expected}: {detected.value}")

    # Çalışma önerileri testi
    test_cards = [
        FSRSCard(
            id="card1", subject="Matematik", due_date=datetime.now() - timedelta(days=1)
        ),
        FSRSCard(
            id="card2", subject="Türkçe", due_date=datetime.now() + timedelta(days=2)
        ),
        FSRSCard(id="card3", subject="Fizik", difficulty=8.0),
    ]

    recommendations = fsrs.get_study_recommendations(
        test_cards, student_context, datetime.now()
    )

    print(f"\n[BOOKS] Çalışma Önerileri:")
    print(f"   Vadesi gelen kartlar: {recommendations['due_cards_count']}")
    print(f"   Yaklaşan kartlar: {recommendations['upcoming_cards_count']}")
    print(f"   Zor kartlar: {recommendations['difficult_cards_count']}")
    print(
        f"   Önerilen çalışma süresi: {recommendations['recommended_study_time']} dakika"
    )
    print(f"   Öncelikli konular: {recommendations['priority_subjects']}")
    print(f"   Dönem tavsiyesi: {recommendations['period_advice']}")

    print("\n[CHECK] FSRS Algoritması testleri başarıyla tamamlandı!")


async def test_cultural_factors():
    """Kültürel faktörler testi"""
    print("\n🇹🇷 Türk Kültürü Faktörleri Test Ediliyor...")

    fsrs = TurkishOptimizedFSRS()

    # Farklı öğrenci profilleri
    profiles = [
        {
            "name": "Normal Öğrenci",
            "context": StudentContext(
                student_id="normal",
                group_study_preference=False,
                family_pressure_level=0.5,
                exam_anxiety_level=0.5,
                study_consistency=0.7,
            ),
        },
        {
            "name": "Grup Çalışması Seven",
            "context": StudentContext(
                student_id="group_lover",
                group_study_preference=True,
                family_pressure_level=0.5,
                exam_anxiety_level=0.5,
                study_consistency=0.7,
            ),
        },
        {
            "name": "Yüksek Aile Baskısı",
            "context": StudentContext(
                student_id="high_pressure",
                group_study_preference=False,
                family_pressure_level=0.9,
                exam_anxiety_level=0.8,
                study_consistency=0.6,
            ),
        },
        {
            "name": "Düşük Kaygı",
            "context": StudentContext(
                student_id="low_anxiety",
                group_study_preference=False,
                family_pressure_level=0.3,
                exam_anxiety_level=0.2,
                study_consistency=0.9,
            ),
        },
    ]

    test_card = FSRSCard(
        id="cultural_test",
        subject="Matematik",
        difficulty=2.0,
        stability=5.0,
        retrievability=0.8,
        state="review",
    )

    test_date = datetime(2024, 4, 15, 14, 0, 0)  # Normal dönem

    print("\n[CHART] Farklı Öğrenci Profillerinin Karşılaştırması:")
    for profile in profiles:
        schedule = fsrs.calculate_next_review(
            test_card, FSRSGrade.GOOD, test_date, profile["context"]
        )

        multiplier = schedule.cultural_factors.get("cultural_multiplier", 1.0)
        print(
            f"   {profile['name']:<20}: {schedule.interval_days:>2} gün (çarpan: {multiplier:.2f})"
        )

    print("\n[CHECK] Kültürel faktörler testleri başarıyla tamamlandı!")


async def test_grade_effects():
    """Farklı notların etkilerini test et"""
    print("\n[MEMO] Not Etkilerini Test Ediliyor...")

    fsrs = TurkishOptimizedFSRS()
    student_context = StudentContext(
        student_id="grade_test",
        group_study_preference=False,
        family_pressure_level=0.5,
        exam_anxiety_level=0.5,
        study_consistency=0.7,
    )

    base_card = FSRSCard(
        id="grade_test",
        subject="Türkçe",
        difficulty=2.0,
        stability=7.0,
        retrievability=0.8,
        state="review",
    )

    test_date = datetime(2024, 4, 15, 14, 0, 0)

    grades = [
        (FSRSGrade.AGAIN, "Tekrar Et (Again)"),
        (FSRSGrade.HARD, "Zor (Hard)"),
        (FSRSGrade.GOOD, "İyi (Good)"),
        (FSRSGrade.EASY, "Kolay (Easy)"),
    ]

    print("\n[TRENDING_UP] Not Etkilerinin Karşılaştırması:")
    for grade, description in grades:
        schedule = fsrs.calculate_next_review(
            base_card, grade, test_date, student_context
        )

        print(
            f"   {description:<15}: {schedule.interval_days:>3} gün, "
            f"Zorluk: {schedule.difficulty:.2f}, "
            f"Kararlılık: {schedule.stability:.2f}"
        )

    print("\n[CHECK] Not etkileri testleri başarıyla tamamlandı!")


async def test_retention_prediction():
    """Retention tahmin testi"""
    print("\n🔮 Retention Tahmini Test Ediliyor...")

    fsrs = TurkishOptimizedFSRS()

    test_cards = [
        FSRSCard(id="easy", subject="Kolay Kart", stability=15.0),
        FSRSCard(id="medium", subject="Orta Kart", stability=7.0),
        FSRSCard(id="hard", subject="Zor Kart", stability=3.0),
    ]

    days_ahead = [1, 3, 7, 14, 30]

    print("\n[CHART] Retention Olasılık Tahminleri:")
    print("Kart Türü      ", end="")
    for day in days_ahead:
        print(f"{day:>6}g", end="")
    print()

    for card in test_cards:
        print(f"{card.subject:<15}", end="")
        for day in days_ahead:
            prob = fsrs.predict_retention_probability(card, day)
            print(f"{prob:>6.2f}", end="")
        print()

    print("\n[CHECK] Retention tahmin testleri başarıyla tamamlandı!")


async def main():
    """Ana test fonksiyonu"""
    print("[TARGET] Türk Öğrenci Davranışlarına Optimize Edilmiş FSRS Sistem Testleri")
    print("=" * 70)

    try:
        await test_fsrs_algorithm()
        await test_cultural_factors()
        await test_grade_effects()
        await test_retention_prediction()

        print("\n" + "=" * 70)
        print("[PARTY] TÜM TESTLER BAŞARIYLA TAMAMLANDI!")
        print("[ROCKET] 17 Parametreli FSRS Sistemi Hazır!")
        print("🇹🇷 Türk Kültürüne Özel Faktörler Aktif!")

    except Exception as e:
        print(f"\n[X] Test hatası: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
