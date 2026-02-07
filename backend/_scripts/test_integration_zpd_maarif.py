#!/usr/bin/env python3
"""
Türk ZPD + MEB Maarif Sistemi Entegrasyon Testi
Yeni algoritmanın mevcut sistemle entegrasyonunu test eder
"""
import asyncio
import os
import sys

# Backend dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from algorithms.turkish_zpd_maarif_system import TurkishZPDMaarifSystem


async def test_integration():
    """Entegrasyon testi"""
    print("[ROCKET] Türk ZPD + MEB Maarif Sistemi Entegrasyon Testi Başlatılıyor...")

    # Sistem başlatma
    zpd_system = TurkishZPDMaarifSystem()
    print("[CHECK] ZPD sistemi başlatıldı")

    # Test verisi
    student_id = "test_student_integration"
    behavioral_data = {
        "group_study_sessions": 20,
        "individual_study_sessions": 5,
        "teacher_question_count": 15,
        "peer_interaction_count": 30,
        "help_seeking_frequency": 12,
    }

    family_survey = {
        "involvement_level": 0.9,
        "collective_focus": 0.8,
        "elder_respect": 0.95,
        "harmony_importance": 0.9,
    }

    print("\n[CHART] Test Senaryosu:")
    print(f"   Öğrenci ID: {student_id}")
    print(f"   Grup çalışması oturumları: {behavioral_data['group_study_sessions']}")
    print(
        f"   Bireysel çalışma oturumları: {behavioral_data['individual_study_sessions']}"
    )
    print(f"   Aile katılım seviyesi: {family_survey['involvement_level']}")

    # 1. Kültürel bağlam tespiti
    print("\n[MAG] 1. Kültürel Bağlam Tespiti...")
    cultural_context = await zpd_system.detect_cultural_context(
        student_id=student_id,
        behavioral_data=behavioral_data,
        family_survey=family_survey,
    )

    print(
        f"   [CHECK] Grup öğrenme tercihi: {cultural_context.group_learning_preference:.2f}"
    )
    print(
        f"   [CHECK] Öğretmene saygı seviyesi: {cultural_context.teacher_respect_level:.2f}"
    )
    print(f"   [CHECK] Aile katılımı: {cultural_context.family_involvement:.2f}")
    print(f"   [CHECK] Sosyal uyum: {cultural_context.social_harmony:.2f}")

    # 2. Maarif değerleri uyum analizi
    print("\n[TARGET] 2. MEB Maarif Değerleri Uyum Analizi...")
    subjects = ["matematik", "tarih", "türkçe"]
    content_descriptions = [
        "Dürüst çalışma ile sabırla matematik problemlerini çözme",
        "Türkiye Cumhuriyeti'nin kuruluşu ve vatan sevgisi",
        "Türk dili ve edebiyatı ile millet bilinci",
    ]

    for subject, content in zip(subjects, content_descriptions):
        alignment = await zpd_system.calculate_maarif_alignment(subject, content)
        print(f"   [BOOKS] {subject.upper()}:")
        print(f"      - Genel uyum: {alignment.overall_alignment:.2f}")
        print(f"      - Uyumlu değerler: {[v.value for v in alignment.aligned_values]}")

    # 3. ZPD hesaplama
    print("\n📐 3. Türk Kültürüne Uyarlanmış ZPD Hesaplama...")
    zpd_range = await zpd_system.calculate_turkish_zpd(
        student_id=student_id,
        subject="matematik",
        current_level=6.5,
        cultural_context=cultural_context,
        content_description="Türk matematikçilerin katkıları ve geometri",
    )

    print(f"   [CHECK] Mevcut seviye: {zpd_range.current_level}")
    print(f"   [CHECK] ZPD alt sınır: {zpd_range.lower_bound:.2f}")
    print(f"   [CHECK] ZPD üst sınır: {zpd_range.upper_bound:.2f}")
    print(f"   [CHECK] Optimal zorluk: {zpd_range.optimal_challenge:.2f}")
    print(f"   [CHECK] Grup-bireysel dengesi: {zpd_range.group_individual_balance:.2f}")

    # 4. Öğrenme önerisi oluşturma
    print("\n[BULB] 4. Kişiselleştirilmiş Öğrenme Önerisi...")
    recommendation = await zpd_system.generate_zpd_recommendation(
        zpd_range=zpd_range, learning_objective="Geometri konusunda uzmanlaşma"
    )

    print(f"   [CHECK] Önerilen zorluk: {recommendation.recommended_difficulty:.2f}")
    print(f"   [CHECK] Öğrenme modu: {recommendation.learning_mode}")
    print(f"   [CHECK] İçerik türü: {recommendation.content_type}")
    print(
        f"   [CHECK] Öğretmen rehberliği: {recommendation.teacher_guidance_level:.2f}"
    )
    print(f"   [CHECK] Akran desteği: {recommendation.peer_support_level:.2f}")
    print(f"   [CHECK] Güven skoru: {recommendation.confidence_score:.2f}")
    print(f"   [MEMO] Gerekçe: {recommendation.reasoning}")

    # 5. Kültürel adaptasyon
    print("\n🔄 5. Kültürel Zorluk Adaptasyonu...")
    student_performance = {
        "individual_score": 0.7,
        "group_score": 0.85,
        "teacher_feedback_score": 0.8,
        "homework_score": 0.75,
    }

    adapted_difficulty = await zpd_system.adapt_difficulty_culturally(
        current_difficulty=0.6,
        student_performance=student_performance,
        cultural_context=cultural_context,
    )

    print(f"   [CHECK] Orijinal zorluk: 0.60")
    print(f"   [CHECK] Adapte edilmiş zorluk: {adapted_difficulty:.2f}")
    print(f"   [CHECK] Adaptasyon faktörü: {adapted_difficulty/0.6:.2f}")

    # 6. Öğrenme kalıpları analizi
    print("\n[TRENDING_UP] 6. Kültürel Öğrenme Kalıpları Analizi...")
    learning_sessions = [
        {
            "mode": "group",
            "score": 0.85,
            "teacher_interaction_count": 8,
            "maarif_aligned": True,
        },
        {
            "mode": "group",
            "score": 0.90,
            "teacher_interaction_count": 10,
            "maarif_aligned": True,
        },
        {
            "mode": "individual",
            "score": 0.70,
            "teacher_interaction_count": 3,
            "maarif_aligned": False,
        },
        {
            "mode": "individual",
            "score": 0.75,
            "teacher_interaction_count": 4,
            "maarif_aligned": False,
        },
        {
            "mode": "mixed",
            "score": 0.80,
            "teacher_interaction_count": 6,
            "maarif_aligned": True,
        },
    ]

    patterns = await zpd_system.monitor_cultural_learning_patterns(
        student_id=student_id, learning_sessions=learning_sessions
    )

    print(f"   [CHECK] Grup vs bireysel performans:")
    if patterns["group_vs_individual_performance"]:
        gvip = patterns["group_vs_individual_performance"]
        print(f"      - Grup ortalaması: {gvip['group_average']:.2f}")
        print(f"      - Bireysel ortalama: {gvip['individual_average']:.2f}")
        print(f"      - Grup tercihi doğrulandı: {gvip['group_preference_confirmed']}")

    print(
        f"   [CHECK] Öğretmen etkileşimi korelasyonu: {patterns['teacher_interaction_correlation']:.2f}"
    )
    print(
        f"   [CHECK] Maarif içerik katılımı: {patterns['maarif_content_engagement']:.2f}"
    )

    print("\n[PARTY] Entegrasyon Testi Başarıyla Tamamlandı!")
    print("\n[CLIPBOARD] SONUÇ ÖZETİ:")
    print("=" * 60)
    print(f"[TARGET] Öğrenci Profili: Grup odaklı, yüksek aile desteği")
    print(f"[CHART] Optimal Zorluk: {zpd_range.optimal_challenge:.2f}/10")
    print(f"🤝 Önerilen Mod: {recommendation.learning_mode}")
    print(f"[BOOKS] İçerik Türü: {recommendation.content_type}")
    print(f"🔄 Kültürel Adaptasyon: %{((adapted_difficulty/0.6-1)*100):+.1f}")
    print(f"[CHECK] Sistem Güveni: {recommendation.confidence_score:.1%}")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_integration())
        if result:
            print("\n[CHECK] TÜM TESTLER BAŞARILI!")
            sys.exit(0)
        else:
            print("\n[X] TESTLER BAŞARISIZ!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 ENTEGRASYON TESTI HATASI: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
