"""
YouTube Module - Configuration
==============================
Static configuration data for YouTube video discovery.

Extracted from youtube_discovery.py
"""

from typing import Dict, List

from .types import ExamType

# Genişletilmiş video veritabanı - daha çok çeşitlilik için
QUICK_RECOMMENDATIONS: Dict[tuple, List[Dict]] = {
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


# Güvenilir Türk eğitim kanalları
TRUSTED_CHANNELS: Dict[str, List[Dict]] = {
    "matematik": [
        {"name": "Matematik Öğretmeni", "id": "UCxxxxxx", "quality": 9.2},
        {
            "name": "TonguçAkademi",
            "id": "UC5Bu5lNaUYBYG-ZW-bMeXWA",
            "quality": 8.8,
        },
        {"name": "KAMP Online", "id": "UCyyyyyy", "quality": 8.5},
        {"name": "Matematikciler", "id": "UCzzzzzz", "quality": 8.3},
    ],
    "fizik": [
        {"name": "Fizik Öğretmeni", "id": "UCaaaaaa", "quality": 9.0},
        {
            "name": "TonguçAkademi",
            "id": "UC5Bu5lNaUYBYG-ZW-bMeXWA",
            "quality": 8.8,
        },
    ],
    "türkçe": [
        {"name": "Türkçe Öğretmeni", "id": "UCbbbbbbb", "quality": 9.1},
        {"name": "Hocawebde", "id": "UCcccccc", "quality": 8.7},
    ],
    "sosyal": [
        {"name": "TRT EBA TV", "id": "UCddddddd", "quality": 8.9},
        {"name": "Tarih Öğretmeni", "id": "UCeeeeeee", "quality": 8.4},
    ],
}


# Arama query şablonları
SEARCH_TEMPLATES: Dict[ExamType, List[str]] = {
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
SUBJECT_KEYWORDS: Dict[str, List[str]] = {
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
    "TRUSTED_CHANNELS",
    "SEARCH_TEMPLATES",
    "SUBJECT_KEYWORDS",
]
