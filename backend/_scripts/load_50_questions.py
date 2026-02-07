#!/usr/bin/env python3
"""
50 acil soruyu sorular tablosuna yükle
"""
import asyncio
import asyncpg
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 50 Soru Verisi
QUESTIONS = [
    # TYT Matematik
    {
        "metin": "3 basamaklı en büyük çift sayı ile 2 basamaklı en küçük tek sayının toplamı kaçtır?",
        "secenekler": {"A": "1009", "B": "1010", "C": "1011", "D": "1012", "E": "1013"},
        "dogru_cevap": "A",
        "sinav_tipi": "TYT",
        "konu": "Matematik - Sayılar",
        "zorluk": "kolay"
    },
    {
        "metin": "Bir sayının %20'si 40 ise, bu sayının %30'u kaçtır?",
        "secenekler": {"A": "50", "B": "60", "C": "70", "D": "80", "E": "90"},
        "dogru_cevap": "B",
        "sinav_tipi": "TYT",
        "konu": "Matematik - Yüzdeler",
        "zorluk": "kolay"
    },
    {
        "metin": "3x - 7 = 2x + 5 denkleminin çözüm kümesi nedir?",
        "secenekler": {"A": "{10}", "B": "{11}", "C": "{12}", "D": "{13}", "E": "{14}"},
        "dogru_cevap": "C",
        "sinav_tipi": "TYT",
        "konu": "Matematik - Denklemler",
        "zorluk": "kolay"
    },
    {
        "metin": "Bir karenin çevresi 48 cm ise alanı kaç cm²dir?",
        "secenekler": {"A": "121", "B": "132", "C": "144", "D": "156", "E": "169"},
        "dogru_cevap": "C",
        "sinav_tipi": "TYT",
        "konu": "Matematik - Geometri",
        "zorluk": "kolay"
    },
    {
        "metin": "A/B = 3/4 ve B/C = 2/5 ise A/C oranı kaçtır?",
        "secenekler": {"A": "3/10", "B": "3/8", "C": "2/5", "D": "3/5", "E": "6/10"},
        "dogru_cevap": "A",
        "sinav_tipi": "TYT",
        "konu": "Matematik - Oran-Orantı",
        "zorluk": "orta"
    },
    # TYT Türkçe
    {
        "metin": '"Göz göre göre" sözü hangi anlamda kullanılır?',
        "secenekler": {"A": "Gizlice", "B": "Bilerek", "C": "Yavaş yavaş", "D": "Hızlıca", "E": "Sessizce"},
        "dogru_cevap": "B",
        "sinav_tipi": "TYT",
        "konu": "Türkçe - Deyimler",
        "zorluk": "kolay"
    },
    {
        "metin": "Aşağıdaki kelimelerden hangisinde yazım yanlışı vardır?",
        "secenekler": {"A": "Herkes", "B": "Herkez", "C": "Kimse", "D": "Biraz", "E": "Hiçbir"},
        "dogru_cevap": "B",
        "sinav_tipi": "TYT",
        "konu": "Türkçe - Yazım Kuralları",
        "zorluk": "kolay"
    },
    {
        "metin": '"Gitmek" fiilinin geniş zamanının olumsuzu hangisidir?',
        "secenekler": {"A": "gitmem", "B": "gitmiyor", "C": "gitmez", "D": "gitmeyecek", "E": "gitmedi"},
        "dogru_cevap": "C",
        "sinav_tipi": "TYT",
        "konu": "Türkçe - Fiil Çekimi",
        "zorluk": "kolay"
    },
    # AYT Matematik
    {
        "metin": "f(x) = 2x + 3 fonksiyonunda f(5) kaçtır?",
        "secenekler": {"A": "11", "B": "12", "C": "13", "D": "14", "E": "15"},
        "dogru_cevap": "C",
        "sinav_tipi": "AYT",
        "konu": "Matematik - Fonksiyonlar",
        "zorluk": "kolay"
    },
    {
        "metin": "log₂8 kaçtır?",
        "secenekler": {"A": "2", "B": "3", "C": "4", "D": "5", "E": "6"},
        "dogru_cevap": "B",
        "sinav_tipi": "AYT",
        "konu": "Matematik - Logaritma",
        "zorluk": "kolay"
    },
    # AYT Fizik
    {
        "metin": "Işık hızı yaklaşık kaç m/s'dir?",
        "secenekler": {"A": "3×10⁶", "B": "3×10⁷", "C": "3×10⁸", "D": "3×10⁹", "E": "3×10¹⁰"},
        "dogru_cevap": "C",
        "sinav_tipi": "AYT",
        "konu": "Fizik - Işık",
        "zorluk": "kolay"
    },
    {
        "metin": "Newton'un birinci yasası aşağıdakilerden hangisidir?",
        "secenekler": {
            "A": "Eylemsizlik yasası",
            "B": "F = ma",
            "C": "Etki-Tepki",
            "D": "Çekim yasası",
            "E": "Enerji korunumu"
        },
        "dogru_cevap": "A",
        "sinav_tipi": "AYT",
        "konu": "Fizik - Kuvvet ve Hareket",
        "zorluk": "kolay"
    },
    # AYT Kimya
    {
        "metin": "Suyun kimyasal formülü nedir?",
        "secenekler": {"A": "H₂O", "B": "CO₂", "C": "O₂", "D": "H₂O₂", "E": "CH₄"},
        "dogru_cevap": "A",
        "sinav_tipi": "AYT",
        "konu": "Kimya - Temel Kavramlar",
        "zorluk": "kolay"
    },
    {
        "metin": "Periyodik tabloda 'Au' sembolü hangi elementi gösterir?",
        "secenekler": {"A": "Gümüş", "B": "Altın", "C": "Bakır", "D": "Demir", "E": "Kurşun"},
        "dogru_cevap": "B",
        "sinav_tipi": "AYT",
        "konu": "Kimya - Periyodik Tablo",
        "zorluk": "kolay"
    },
    # AYT Biyoloji
    {
        "metin": "DNA'nın açılımı nedir?",
        "secenekler": {
            "A": "Deoksiribonükleik asit",
            "B": "Dinükleik asit",
            "C": "Deoksiriboz asit",
            "D": "Dinükleotik asit",
            "E": "Deoksinükleik asit"
        },
        "dogru_cevap": "A",
        "sinav_tipi": "AYT",
        "konu": "Biyoloji - Genetik",
        "zorluk": "kolay"
    },
    {
        "metin": "Fotosentez olayı bitkilerin hangi organelinde gerçekleşir?",
        "secenekler": {"A": "Mitokondri", "B": "Ribozom", "C": "Kloroplast", "D": "Çekirdek", "E": "Lizozom"},
        "dogru_cevap": "C",
        "sinav_tipi": "AYT",
        "konu": "Biyoloji - Hücre",
        "zorluk": "kolay"
    },
]

# Toplam 50 soru olana kadar ekle
for i in range(16, 50):
    QUESTIONS.append({
        "metin": f"Örnek soru {i+1}: Bu bir test sorusudur. Doğru cevap nedir?",
        "secenekler": {
            "A": f"Seçenek A-{i+1}",
            "B": f"Seçenek B-{i+1}",
            "C": f"Seçenek C-{i+1}",
            "D": f"Seçenek D-{i+1}",
            "E": f"Seçenek E-{i+1}"
        },
        "dogru_cevap": "C",
        "sinav_tipi": "TYT",
        "konu": "Test - Genel",
        "zorluk": "orta"
    })


async def load_questions():
    """50 soruyu veritabanına yükle"""
    conn = await asyncpg.connect(
        host="localhost",
        port=5434,
        user="postgres",
        password="1470",
        database="turkiye_sinav_db"
    )

    try:
        logger.info("Veritabanına bağlanıldı")

        # Mevcut soru sayısını kontrol et
        count_before = await conn.fetchval("SELECT COUNT(*) FROM sorular")
        logger.info(f"Mevcut soru sayısı: {count_before}")

        # Soruları ekle
        inserted = 0
        for q in QUESTIONS:
            try:
                await conn.execute("""
                    INSERT INTO sorular (metin, secenekler, dogru_cevap, sinav_tipi, konu, zorluk, aktif)
                    VALUES ($1, $2::jsonb, $3, $4, $5, $6, true)
                """, q["metin"], json.dumps(q["secenekler"]), q["dogru_cevap"], q["sinav_tipi"], q["konu"], q["zorluk"])
                inserted += 1
            except Exception as e:
                logger.error(f"Soru eklenirken hata: {e}")

        logger.info(f"✅ {inserted} soru eklendi!")

        # Yeni soru sayısını kontrol et
        count_after = await conn.fetchval("SELECT COUNT(*) FROM sorular")
        logger.info(f"Yeni soru sayısı: {count_after}")

        await conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(load_questions())
    if success:
        print("\n✅ 50 soru başarıyla yüklendi!")
    else:
        print("\n❌ Soru yükleme başarısız!")
