#!/usr/bin/env python3
"""
Database Initialization Script
Teknofest 2025 - Türkiye Üniversite Sınav Hazırlık Platformu

Bu script database'i başlatır, tabloları oluşturur ve örnek verileri ekler.
"""

import asyncio
import logging
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    KullaniciRepository,
    KullaniciRolu,
    OgrenciRepository,
    SinavRepository,
    SinavTipi,
    SoruRepository,
    ZorlukSeviyesi,
    get_async_session_context,
    init_database,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def create_sample_users():
    """Örnek kullanıcılar oluştur"""
    logger.info("[MEMO] Örnek kullanıcılar oluşturuluyor...")

    async with get_async_session_context() as session:
        kullanici_repo = KullaniciRepository(session)
        ogrenci_repo = OgrenciRepository(session)

        # Test öğrencisi
        test_ogrenci = await kullanici_repo.create_kullanici(
            {
                "email": "test.ogrenci@teknofest.edu.tr",
                "ad_soyad": "Test Öğrenci",
                "sifre_hash": "$2b$12$example_hash",  # Gerçek uygulamada bcrypt hash
                "rol": KullaniciRolu.OGRENCI,
                "aktif": True,
                "email_dogrulandi": True,
            }
        )

        # Öğrenci profili
        await ogrenci_repo.create_ogrenci_profili(
            {
                "kullanici_id": test_ogrenci.kullanici_id,
                "sinif": 12,
                "okul_adi": "Teknofest Anadolu Lisesi",
                "hedef_universite": "İTÜ",
                "hedef_bolum": "Bilgisayar Mühendisliği",
                "mevcut_seviye": 6.5,
                "hedef_puan": 450,
            }
        )

        # Test öğretmeni
        test_ogretmen = await kullanici_repo.create_kullanici(
            {
                "email": "test.ogretmen@teknofest.edu.tr",
                "ad_soyad": "Test Öğretmen",
                "sifre_hash": "$2b$12$example_hash",
                "rol": KullaniciRolu.OGRETMEN,
                "aktif": True,
                "email_dogrulandi": True,
            }
        )

        logger.info(
            f"[CHECK] Örnek kullanıcılar oluşturuldu: {test_ogrenci.email}, {test_ogretmen.email}"
        )


async def create_sample_exam_templates():
    """Örnek sınav şablonları oluştur"""
    logger.info("[CLIPBOARD] Sınav şablonları oluşturuluyor...")

    async with get_async_session_context() as session:
        sinav_repo = SinavRepository(session)

        # TYT Şablonu
        tyt_sablon = await sinav_repo.create_sinav_sablonu(
            {
                "ad": "TYT - Temel Yeterlilik Testi",
                "tip": SinavTipi.TYT,
                "aciklama": "YKS TYT sınavı şablonu",
                "sure_dakika": 165,  # 2 saat 45 dakika
                "toplam_soru_sayisi": 120,
                "konu_dagilimi": {
                    "turkce": 40,
                    "matematik": 40,
                    "fen": 20,
                    "sosyal": 20,
                },
                "aktif": True,
            }
        )

        # AYT Şablonu
        ayt_sablon = await sinav_repo.create_sinav_sablonu(
            {
                "ad": "AYT - Alan Yeterlilik Testi",
                "tip": SinavTipi.AYT,
                "aciklama": "YKS AYT sınavı şablonu",
                "sure_dakika": 180,  # 3 saat
                "toplam_soru_sayisi": 80,
                "konu_dagilimi": {
                    "matematik": 40,
                    "fizik": 14,
                    "kimya": 13,
                    "biyoloji": 13,
                },
                "aktif": True,
            }
        )

        # YDT Şablonu
        ydt_sablon = await sinav_repo.create_sinav_sablonu(
            {
                "ad": "YDT - Yabancı Dil Testi",
                "tip": SinavTipi.YDT,
                "aciklama": "YKS YDT İngilizce sınavı şablonu",
                "sure_dakika": 180,  # 3 saat
                "toplam_soru_sayisi": 80,
                "konu_dagilimi": {"ingilizce": 80},
                "aktif": True,
            }
        )

        logger.info(f"[CHECK] Sınav şablonları oluşturuldu: TYT, AYT, YDT")


async def create_sample_questions():
    """Örnek sorular oluştur"""
    logger.info("❓ Örnek sorular oluşturuluyor...")

    async with get_async_session_context() as session:
        soru_repo = SoruRepository(session)

        # Matematik soruları
        matematik_sorulari = [
            {
                "konu": "matematik",
                "alt_konu": "fonksiyonlar",
                "zorluk_seviyesi": ZorlukSeviyesi.ORTA,
                "soru_metni": "f(x) = 2x + 3 fonksiyonu için f(5) değeri kaçtır?",
                "secenekler": {"A": "10", "B": "11", "C": "12", "D": "13", "E": "14"},
                "dogru_cevap": "D",
                "aciklama": "f(5) = 2(5) + 3 = 10 + 3 = 13",
                "irt_a_parametresi": 1.2,
                "irt_b_parametresi": 0.5,
                "irt_c_parametresi": 0.2,
                "morfoloji_karmasikligi": 0.3,
                "kok_kelime_sayisi": 8,
                "ek_sayisi": 3,
            },
            {
                "konu": "matematik",
                "alt_konu": "geometri",
                "zorluk_seviyesi": ZorlukSeviyesi.ZOR,
                "soru_metni": "Bir dairenin yarıçapı 5 cm ise, bu dairenin alanı kaç cm² dir?",
                "secenekler": {
                    "A": "25π",
                    "B": "10π",
                    "C": "15π",
                    "D": "20π",
                    "E": "30π",
                },
                "dogru_cevap": "A",
                "aciklama": "Daire alanı = πr² = π(5)² = 25π",
                "irt_a_parametresi": 1.5,
                "irt_b_parametresi": 1.2,
                "irt_c_parametresi": 0.15,
                "morfoloji_karmasikligi": 0.4,
                "kok_kelime_sayisi": 12,
                "ek_sayisi": 5,
            },
        ]

        # Türkçe soruları
        turkce_sorulari = [
            {
                "konu": "turkce",
                "alt_konu": "anlam_bilgisi",
                "zorluk_seviyesi": ZorlukSeviyesi.KOLAY,
                "soru_metni": "Aşağıdaki cümlelerden hangisinde 'baş' kelimesi gerçek anlamında kullanılmıştır?",
                "secenekler": {
                    "A": "Sınıfın başı çok akıllı.",
                    "B": "Başını kaldırıp gökyüzüne baktı.",
                    "C": "Bu işin başı çok zor.",
                    "D": "Başına iş açtı.",
                    "E": "Başından geçenleri anlattı.",
                },
                "dogru_cevap": "B",
                "aciklama": "B seçeneğinde 'baş' kelimesi vücudun bir organı anlamında kullanılmıştır.",
                "irt_a_parametresi": 0.8,
                "irt_b_parametresi": -0.5,
                "irt_c_parametresi": 0.25,
                "morfoloji_karmasikligi": 0.6,
                "kok_kelime_sayisi": 15,
                "ek_sayisi": 8,
            }
        ]

        # Soruları veritabanına ekle
        for soru_data in matematik_sorulari + turkce_sorulari:
            await soru_repo.create_soru(soru_data)

        logger.info(
            f"[CHECK] {len(matematik_sorulari + turkce_sorulari)} örnek soru oluşturuldu"
        )


async def create_sample_educational_content():
    """Örnek eğitim içerikleri oluştur"""
    logger.info("[BOOKS] Eğitim içerikleri oluşturuluyor...")

    async with get_async_session_context() as session:
        from database.repositories import EgitimIcerigiRepository

        icerik_repo = EgitimIcerigiRepository(session)

        icerikler = [
            {
                "baslik": "Fonksiyonlar - Temel Kavramlar",
                "aciklama": "Matematik fonksiyonlarının temel kavramları ve örnekleri",
                "icerik_tipi": "video",
                "konu": "matematik",
                "alt_konu": "fonksiyonlar",
                "zorluk_seviyesi": ZorlukSeviyesi.ORTA,
                "url": "https://www.youtube.com/watch?v=example1",
                "sure_dakika": 25,
                "kalite_skoru": 0.85,
                "erisebilirlik_skoru": 0.90,
                "bionic_reading_destegi": True,
                "basitlestirme_seviyesi": 2,
                "maarif_uyum_skoru": 0.75,
                "uyumlu_degerler": ["sabir", "sorumluluk", "dürüstlük"],
            },
            {
                "baslik": "Türkçe Dil Bilgisi - Anlam Olayları",
                "aciklama": "Türkçede anlam olayları ve örnekleri",
                "icerik_tipi": "metin",
                "konu": "turkce",
                "alt_konu": "anlam_bilgisi",
                "zorluk_seviyesi": ZorlukSeviyesi.KOLAY,
                "dosya_yolu": "/content/turkce/anlam_olaylari.pdf",
                "sure_dakika": 15,
                "kalite_skoru": 0.80,
                "erisebilirlik_skoru": 0.95,
                "bionic_reading_destegi": True,
                "basitlestirme_seviyesi": 1,
                "maarif_uyum_skoru": 0.90,
                "uyumlu_degerler": ["millet", "sevgi", "saygı"],
            },
        ]

        for icerik_data in icerikler:
            await icerik_repo.create_icerik(icerik_data)

        logger.info(f"[CHECK] {len(icerikler)} eğitim içeriği oluşturuldu")


async def main():
    """Ana initialization fonksiyonu"""
    logger.info("[ROCKET] Database initialization başlatılıyor...")

    try:
        # Database'i başlat
        await init_database()

        # Örnek verileri oluştur
        await create_sample_users()
        await create_sample_exam_templates()
        await create_sample_questions()
        await create_sample_educational_content()

        # Database durumunu kontrol et
        from database.connection import database_health_check

        health = await database_health_check()
        logger.info(f"[CHART] Database durumu: {health}")

        logger.info("[CHECK] Database initialization tamamlandı!")

    except Exception as e:
        logger.error(f"[X] Database initialization hatası: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
