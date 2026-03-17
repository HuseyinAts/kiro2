"""
YouTube Module - Configuration
==============================
Static configuration data for YouTube video discovery.

Extracted from youtube_discovery.py
"""

from .types import ExamType

# Genişletilmiş video veritabanı - daha çok çeşitlilik için
QUICK_RECOMMENDATIONS: dict[tuple, list[dict]] = {
    ("matematik", "orta", "TYT"): [
        {
            "video_id": "qsf8ERnJHho",
            "title": "Fonksiyonlar - TYT Matematik",
            "channel": "Matematik Öğretmeni",
            "quality_score": 8.5,
        },
        {
            "video_id": "abc123def",
            "title": "Türev - TYT Matematik",
            "channel": "TonguçAkademi",
            "quality_score": 9.2,
        },
        {
            "video_id": "xyz789ghi",
            "title": "Limit - TYT Matematik",
            "channel": "KAMP Online",
            "quality_score": 8.7,
        },
        {
            "video_id": "math123abc",
            "title": "İntegral - TYT Matematik",
            "channel": "Matematik Öğretmeni",
            "quality_score": 8.9,
        },
        {
            "video_id": "math_new1",
            "title": "Logaritma - TYT Matematik",
            "channel": "Matematikçiler",
            "quality_score": 8.8,
        },
        {
            "video_id": "math_new2",
            "title": "Üçgenler - TYT Matematik",
            "channel": "TonguçAkademi",
            "quality_score": 8.6,
        },
        {
            "video_id": "math_new3",
            "title": "Diziler - TYT Matematik",
            "channel": "KAMP Online",
            "quality_score": 8.4,
        },
        {
            "video_id": "math_new4",
            "title": "Olasılık - TYT Matematik",
            "channel": "Matematik Öğretmeni",
            "quality_score": 8.3,
        },
    ],
    ("matematik", "başlangıç", "TYT"): [
        {
            "video_id": "basic_math1",
            "title": "Temel Matematik - TYT",
            "channel": "TonguçAkademi",
            "quality_score": 8.3,
        },
        {
            "video_id": "basic_math2",
            "title": "Sayılar - TYT Matematik",
            "channel": "Matematik Öğretmeni",
            "quality_score": 8.1,
        },
        {
            "video_id": "basic_math3",
            "title": "İşlemler - TYT Matematik",
            "channel": "Matematikçiler",
            "quality_score": 8.0,
        },
        {
            "video_id": "basic_math4",
            "title": "Kesirler - TYT Matematik",
            "channel": "KAMP Online",
            "quality_score": 7.9,
        },
        {
            "video_id": "basic_math5",
            "title": "Oran-Orantı - TYT Matematik",
            "channel": "TonguçAkademi",
            "quality_score": 8.2,
        },
    ],
    ("matematik", "ileri", "TYT"): [
        {
            "video_id": "adv_math1",
            "title": "Karmaşık Fonksiyonlar - TYT",
            "channel": "İleri Matematik",
            "quality_score": 9.1,
        },
        {
            "video_id": "adv_math2",
            "title": "Analitik Geometri - TYT",
            "channel": "Matematik Öğretmeni",
            "quality_score": 9.0,
        },
        {
            "video_id": "adv_math3",
            "title": "İleri Trigonometri - TYT",
            "channel": "TonguçAkademi",
            "quality_score": 8.9,
        },
    ],
    ("fizik", "başlangıç", "TYT"): [
        {
            "video_id": "2m4xyR1QlIU",
            "title": "Hareket - TYT Fizik",
            "channel": "Fizik Muallimi",
            "quality_score": 8.8,
        },
        {
            "video_id": "def456ghi",
            "title": "Kuvvet - TYT Fizik",
            "channel": "TonguçAkademi",
            "quality_score": 8.9,
        },
        {
            "video_id": "fizik123abc",
            "title": "Enerji - TYT Fizik",
            "channel": "Fizik Öğretmeni",
            "quality_score": 8.7,
        },
        {
            "video_id": "fizik_new1",
            "title": "Basınç - TYT Fizik",
            "channel": "Fizik Akademi",
            "quality_score": 8.5,
        },
        {
            "video_id": "fizik_new2",
            "title": "Isı - TYT Fizik",
            "channel": "Fizik Muallimi",
            "quality_score": 8.4,
        },
    ],
    ("fizik", "orta", "TYT"): [
        {
            "video_id": "fizik_orta1",
            "title": "Elektrik - TYT Fizik",
            "channel": "TonguçAkademi",
            "quality_score": 8.6,
        },
        {
            "video_id": "fizik_orta2",
            "title": "Optik - TYT Fizik",
            "channel": "Fizik Öğretmeni",
            "quality_score": 8.4,
        },
        {
            "video_id": "fizik_orta3",
            "title": "Dalgalar - TYT Fizik",
            "channel": "Fizik Akademi",
            "quality_score": 8.7,
        },
        {
            "video_id": "fizik_orta4",
            "title": "Manyetizma - TYT Fizik",
            "channel": "Fizik Muallimi",
            "quality_score": 8.5,
        },
    ],
    ("fizik", "ileri", "TYT"): [
        {
            "video_id": "fizik_ileri1",
            "title": "Modern Fizik - TYT",
            "channel": "İleri Fizik",
            "quality_score": 9.2,
        },
        {
            "video_id": "fizik_ileri2",
            "title": "Atom Fiziği - TYT",
            "channel": "Fizik Öğretmeni",
            "quality_score": 9.0,
        },
    ],
    ("türkçe", "orta", "TYT"): [
        {
            "video_id": "LKZKJt3u7oA",
            "title": "Sözcük Türleri - TYT Türkçe",
            "channel": "Türkçe Öğretmeni",
            "quality_score": 8.6,
        },
        {
            "video_id": "turkce123",
            "title": "Cümle Bilgisi - TYT Türkçe",
            "channel": "Türkçe Akademi",
            "quality_score": 8.4,
        },
        {
            "video_id": "turkce_new1",
            "title": "Anlam Bilgisi - TYT Türkçe",
            "channel": "Türkçe Öğretmeni",
            "quality_score": 8.5,
        },
        {
            "video_id": "turkce_new2",
            "title": "Paragraf - TYT Türkçe",
            "channel": "Türkçe Akademi",
            "quality_score": 8.3,
        },
    ],
    ("türkçe", "başlangıç", "TYT"): [
        {
            "video_id": "turkce_basic1",
            "title": "Temel Türkçe - TYT",
            "channel": "Türkçe Öğretmeni",
            "quality_score": 8.2,
        },
        {
            "video_id": "turkce_basic2",
            "title": "Yazım Kuralları - TYT",
            "channel": "Türkçe Akademi",
            "quality_score": 8.0,
        },
        {
            "video_id": "turkce_basic3",
            "title": "Noktalama - TYT Türkçe",
            "channel": "Dil Öğretmeni",
            "quality_score": 7.9,
        },
    ],
    ("türkçe", "ileri", "TYT"): [
        {
            "video_id": "turkce_ileri1",
            "title": "Metin Analizi - TYT",
            "channel": "İleri Türkçe",
            "quality_score": 9.1,
        },
        {
            "video_id": "turkce_ileri2",
            "title": "Retorik - TYT Türkçe",
            "channel": "Türkçe Öğretmeni",
            "quality_score": 8.8,
        },
    ],
    ("kimya", "orta", "TYT"): [
        {
            "video_id": "kimya123abc",
            "title": "Atom - TYT Kimya",
            "channel": "Kimya Öğretmeni",
            "quality_score": 8.5,
        },
        {
            "video_id": "kimya_new1",
            "title": "Moleküller - TYT Kimya",
            "channel": "Kimya Akademi",
            "quality_score": 8.4,
        },
        {
            "video_id": "kimya_new2",
            "title": "Bağlar - TYT Kimya",
            "channel": "TonguçAkademi",
            "quality_score": 8.6,
        },
    ],
    ("kimya", "başlangıç", "TYT"): [
        {
            "video_id": "kimya_basic1",
            "title": "Temel Kimya - TYT",
            "channel": "Kimya Öğretmeni",
            "quality_score": 8.1,
        },
        {
            "video_id": "kimya_basic2",
            "title": "Elementler - TYT Kimya",
            "channel": "Kimya Akademi",
            "quality_score": 8.0,
        },
    ],
    ("biyoloji", "orta", "TYT"): [
        {
            "video_id": "bio123abc",
            "title": "Hücre - TYT Biyoloji",
            "channel": "Biyoloji Öğretmeni",
            "quality_score": 8.3,
        },
        {
            "video_id": "bio_new1",
            "title": "DNA - TYT Biyoloji",
            "channel": "Biyoloji Akademi",
            "quality_score": 8.5,
        },
        {
            "video_id": "bio_new2",
            "title": "Metabolizma - TYT Biyoloji",
            "channel": "TonguçAkademi",
            "quality_score": 8.4,
        },
    ],
    ("biyoloji", "başlangıç", "TYT"): [
        {
            "video_id": "bio_basic1",
            "title": "Canlıların Özellikleri - TYT",
            "channel": "Biyoloji Öğretmeni",
            "quality_score": 8.0,
        },
        {
            "video_id": "bio_basic2",
            "title": "Canlı Sınıflandırması - TYT",
            "channel": "Biyoloji Akademi",
            "quality_score": 7.9,
        },
    ],
}


# Güvenilir Türk eğitim kanalları — derived from canonical source
# (core.youtube_channels is the single source of truth)
def _build_trusted_channels() -> dict[str, list[dict]]:
    from core.youtube_channels import get_channels_for_subject

    result: dict[str, list[dict]] = {}
    for subject in [
        "matematik",
        "fizik",
        "kimya",
        "biyoloji",
        "türkçe",
        "tarih",
        "coğrafya",
    ]:
        channels = get_channels_for_subject(subject)
        result[subject] = [
            {
                "name": ch["name"],
                "id": ch.get("channel_id", ""),
                "quality": ch["quality_score"],
            }
            for ch in channels
        ]
    return result


TRUSTED_CHANNELS: dict[str, list[dict]] = _build_trusted_channels()


# Arama query şablonları
SEARCH_TEMPLATES: dict[ExamType, list[str]] = {
    ExamType.TYT: [
        "{subject} TYT {difficulty} konu anlatımı 2025",
        "TYT {subject} {difficulty} ders {year}",
        "{subject} temel yeterlilik {difficulty} video",
        "YKS {subject} TYT {difficulty} hazırlık",
    ],
    ExamType.AYT: [
        "{subject} AYT {difficulty} konu anlatımı 2025",
        "AYT {subject} {difficulty} ders {year}",
        "{subject} alan yeterlilik {difficulty} video",
        "YKS {subject} AYT {difficulty} hazırlık",
    ],
}


# Konu anahtar kelimeleri
SUBJECT_KEYWORDS: dict[str, list[str]] = {
    "matematik": [
        "matematik",
        "geometri",
        "analiz",
        "trigonometri",
        "fonksiyon",
        "türev",
        "integral",
    ],
    "fizik": [
        "fizik",
        "mekanik",
        "elektrik",
        "manyetizma",
        "optik",
        "termodinamik",
        "hareket",
    ],
    "kimya": [
        "kimya",
        "atom",
        "molekül",
        "reaksiyon",
        "element",
        "periyodik",
        "organik",
    ],
    "biyoloji": [
        "biyoloji",
        "hücre",
        "dna",
        "protein",
        "metabolizma",
        "ekosistem",
        "evrim",
    ],
    "türkçe": [
        "türkçe",
        "dil",
        "gramer",
        "yazım",
        "sözcük",
        "cümle",
        "paragraf",
    ],
    "edebiyat": [
        "edebiyat",
        "şiir",
        "roman",
        "hikaye",
        "yazar",
        "eser",
        "dönem",
    ],
    "tarih": [
        "tarih",
        "osmanlı",
        "cumhuriyet",
        "savaş",
        "devrim",
        "medeniyet",
        "kültür",
    ],
    "coğrafya": [
        "coğrafya",
        "harita",
        "iklim",
        "nüfus",
        "ekonomi",
        "bölge",
        "şehir",
    ],
    "sosyal": [
        "sosyal",
        "toplum",
        "ekonomi",
        "siyaset",
        "hukuk",
        "sosyoloji",
        "felsefe",
    ],
    "ingilizce": [
        "ingilizce",
        "english",
        "grammar",
        "vocabulary",
        "tense",
        "kelime",
    ],
}


__all__ = [
    "QUICK_RECOMMENDATIONS",
    "SEARCH_TEMPLATES",
    "SUBJECT_KEYWORDS",
    "TRUSTED_CHANNELS",
]
