"""
ESKİ YouTube Video Keşif Sistemi - DEVRE DIŞI
Advanced YouTube Search sistemi kullanıyor artık
"""

import asyncio
import hashlib
import json
import logging
import random
import re
import sqlite3
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SubjectType(Enum):
    """TYT/AYT Konu türleri"""

    MATEMATIK = "matematik"
    TURKCE = "türkçe"
    FIZIK = "fizik"
    KIMYA = "kimya"
    BIYOLOJI = "biyoloji"
    SOSYAL = "sosyal"
    TARIH = "tarih"
    COGRAFYA = "coğrafya"
    FELSEFE = "felsefe"
    INGILIZCE = "ingilizce"
    EDEBIYAT = "edebiyat"


class DifficultyLevel(Enum):
    """Zorluk seviyeleri"""

    BASLANGIC = "başlangıç"
    ORTA = "orta"
    ILERI = "ileri"
    SINAVA_OZEL = "sınava özel"


class ExamType(Enum):
    """Sınav türleri"""

    TYT = "TYT"
    AYT = "AYT"
    YDT = "YDT"
    MSU = "MSÜ"


@dataclass
class VideoMetadata:
    """Video metadata"""

    video_id: str
    title: str
    channel: str
    channel_id: str
    duration: str
    view_count: int
    upload_date: str
    thumbnail: str
    description: str
    quality_score: float
    subject: SubjectType
    difficulty: DifficultyLevel
    exam_type: ExamType
    language: str = "tr"


class YouTubeDiscovery:
    """Gelişmiş YouTube video keşif sistemi"""

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.db_path = self.cache_dir / "youtube_cache.db"
        self.session: Optional[aiohttp.ClientSession] = None

        # Genişletilmiş video veritabanı - daha çok çeşitlilik için
        self.quick_recommendations = {
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
        self.trusted_channels = {
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
        self.search_templates = {
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

        self._init_database()

    def _init_database(self):
        """Cache veritabanını başlat"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS video_cache (
                    video_id TEXT PRIMARY KEY,
                    title TEXT,
                    channel TEXT,
                    channel_id TEXT,
                    duration TEXT,
                    view_count INTEGER,
                    upload_date TEXT,
                    thumbnail TEXT,
                    description TEXT,
                    quality_score REAL,
                    subject TEXT,
                    difficulty TEXT,
                    exam_type TEXT,
                    language TEXT,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS channel_rss (
                    channel_id TEXT PRIMARY KEY,
                    channel_name TEXT,
                    rss_url TEXT,
                    last_check TIMESTAMP,
                    video_count INTEGER DEFAULT 0,
                    quality_rating REAL DEFAULT 0.0
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS search_cache (
                    query_hash TEXT PRIMARY KEY,
                    query TEXT,
                    results TEXT,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

    async def start_session(self):
        """HTTP session başlat"""
        if not self.session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            self.session = aiohttp.ClientSession(
                headers=headers, timeout=aiohttp.ClientTimeout(total=30)
            )

    async def close_session(self):
        """HTTP session kapat"""
        if self.session:
            await self.session.close()
            self.session = None

    def _generate_search_queries(
        self,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        year: int = 2025,
    ) -> List[str]:
        """Akıllı arama sorguları oluştur"""
        templates = self.search_templates.get(exam_type, [])
        queries = []

        for template in templates:
            query = template.format(
                subject=subject.value, difficulty=difficulty.value, year=year
            )
            queries.append(query)

        # Ek varyasyonlar ekle
        base_terms = [
            f"{subject.value} {exam_type.value}",
            f"{exam_type.value} {subject.value} {difficulty.value}",
            f"{subject.value} konu anlatımı {exam_type.value}",
            f"{subject.value} ders {exam_type.value} {year}",
        ]

        queries.extend(base_terms)
        return list(set(queries))  # Duplikatları kaldır

    async def _search_youtube_concurrent(
        self,
        query: str,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        max_results: int = 10,
    ) -> List[VideoMetadata]:
        """Concurrent YouTube arama ve işleme"""
        try:
            results = await self._search_youtube_direct(query, max_results)
            videos = []

            for video_data in results:
                # Hızlı kalite kontrolü
                quality_score = self._calculate_quality_score_fast(
                    video_data, subject, exam_type
                )

                # Minimum kalite eşiği
                if quality_score < 6.0:
                    continue

                video_metadata = VideoMetadata(
                    video_id=video_data["video_id"],
                    title=video_data["title"],
                    channel=video_data["channel"],
                    channel_id=video_data["channel_id"],
                    duration=video_data["duration"],
                    view_count=video_data["view_count"],
                    upload_date=video_data["upload_date"],
                    thumbnail=video_data["thumbnail"],
                    description="",
                    quality_score=quality_score,
                    subject=subject,
                    difficulty=difficulty,
                    exam_type=exam_type,
                )

                videos.append(video_metadata)

            return videos

        except Exception as e:
            logger.error(f"Concurrent search error for '{query}': {e}")
            return []

    async def _search_youtube_direct(
        self, query: str, max_results: int = 20
    ) -> List[Dict]:
        """YouTube'da doğrudan arama (API olmadan)"""
        # Session lazy loading kaldırıldı - direkt mock veri döndür
        if not hasattr(self, "_mock_data_returned"):
            logger.info("YouTube search mock mode - returning cached data")
            self._mock_data_returned = True
            return []

        # Query hash kontrol et
        query_hash = hashlib.md5(query.encode()).hexdigest()
        cached_result = self._get_cached_search(query_hash)
        if cached_result:
            return cached_result

        try:
            # YouTube arama URL'i
            search_url = f"https://www.youtube.com/results?search_query={query}"

            async with self.session.get(search_url) as response:
                html = await response.text()

            soup = BeautifulSoup(html, "html.parser")

            # Video verilerini çıkar
            videos = []
            scripts = soup.find_all("script")

            for script in scripts:
                if "ytInitialData" in script.text:
                    # JSON verisini çıkar
                    json_text = script.text
                    start = json_text.find("ytInitialData") + 14
                    end = json_text.find(";</script>", start)

                    if start > 14 and end > start:
                        try:
                            json_str = json_text[start:end].strip()
                            if json_str.startswith("="):
                                json_str = json_str[1:].strip()

                            data = json.loads(json_str)
                            videos = self._extract_video_data(data)
                            break
                        except json.JSONDecodeError:
                            continue

            # Cache'e kaydet
            self._cache_search_result(query_hash, query, videos)
            return videos[:max_results]

        except Exception as e:
            logger.error(f"YouTube arama hatası: {e}")
            return []

    def _extract_video_data(self, youtube_data: Dict) -> List[Dict]:
        """YouTube JSON verisinden video bilgilerini çıkar"""
        videos = []

        try:
            contents = (
                youtube_data.get("contents", {})
                .get("twoColumnSearchResultsRenderer", {})
                .get("primaryContents", {})
                .get("sectionListRenderer", {})
                .get("contents", [])
            )

            for section in contents:
                items = section.get("itemSectionRenderer", {}).get("contents", [])

                for item in items:
                    video_renderer = item.get("videoRenderer", {})
                    if not video_renderer:
                        continue

                    video_id = video_renderer.get("videoId")
                    if not video_id:
                        continue

                    title = (
                        video_renderer.get("title", {})
                        .get("runs", [{}])[0]
                        .get("text", "")
                    )

                    channel_name = ""
                    channel_id = ""
                    if "ownerText" in video_renderer:
                        channel_name = (
                            video_renderer["ownerText"]
                            .get("runs", [{}])[0]
                            .get("text", "")
                        )
                        channel_id = (
                            video_renderer["ownerText"]
                            .get("runs", [{}])[0]
                            .get("navigationEndpoint", {})
                            .get("commandMetadata", {})
                            .get("webCommandMetadata", {})
                            .get("url", "")
                            .split("/")[-1]
                        )

                    # View count
                    view_text = video_renderer.get("viewCountText", {}).get(
                        "simpleText", "0"
                    )
                    view_count = self._parse_view_count(view_text)

                    # Duration
                    duration = video_renderer.get("lengthText", {}).get(
                        "simpleText", "0:00"
                    )

                    # Thumbnail
                    thumbnail = ""
                    thumbnails = video_renderer.get("thumbnail", {}).get(
                        "thumbnails", []
                    )
                    if thumbnails:
                        thumbnail = thumbnails[-1].get("url", "")

                    # Upload date
                    upload_date = video_renderer.get("publishedTimeText", {}).get(
                        "simpleText", ""
                    )

                    video_data = {
                        "video_id": video_id,
                        "title": title,
                        "channel": channel_name,
                        "channel_id": channel_id,
                        "duration": duration,
                        "view_count": view_count,
                        "upload_date": upload_date,
                        "thumbnail": thumbnail,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                    }

                    videos.append(video_data)

        except Exception as e:
            logger.error(f"Video data extraction error: {e}")

        return videos

    def _parse_view_count(self, view_text: str) -> int:
        """View count metni sayıya çevir"""
        if not view_text:
            return 0

        # Türkçe view count formatları
        view_text = (
            view_text.lower()
            .replace(" görüntüleme", "")
            .replace(",", "")
            .replace(".", "")
        )

        multipliers = {
            "b": 1000000000,  # milyar
            "mn": 1000000,  # milyon
            "m": 1000000,  # milyon
            "k": 1000,  # bin
            "bin": 1000,  # bin
        }

        for suffix, multiplier in multipliers.items():
            if suffix in view_text:
                number = view_text.replace(suffix, "").strip()
                try:
                    return int(float(number) * multiplier)
                except ValueError:
                    continue

        try:
            return int(view_text)
        except ValueError:
            return 0

    async def _analyze_video_with_llm(
        self,
        video_data: Dict,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
    ) -> Dict:
        """LLM ile video içeriği analizi"""
        try:
            # Hugging Face endpoint URL
            hf_endpoint = (
                "https://cf781mfqobm2ynkk.us-east-1.aws.endpoints.huggingface.cloud"
            )

            # Video başlığı ve açıklaması
            title = video_data.get("title", "")
            description = video_data.get("description", "")
            channel = video_data.get("channel", "")

            # LLM prompt
            prompt = f"""Aşağıdaki YouTube videosunu analiz et:

Başlık: {title}
Kanal: {channel}
Açıklama: {description[:300]}

Hedef: {exam_type.value} {subject.value} {difficulty.value} seviye

Bu videoyu şu kriterlere göre değerlendir:
1. İçerik uygunluğu (0-10): Hedef konu ve seviyeye uygunluk
2. Türkçe içerik: İçerik Türkçe mi?
3. Eğitim kalitesi (0-10): Öğretici değer
4. Seviye uygunluğu (0-10): Hedef zorluk seviyesine uygunluk

Sadece aşağıdaki JSON formatında cevap ver:
{{"relevance_score": 8.5, "turkish_content": true, "educational_quality": 9.0, "level_appropriateness": 8.0}}"""

            # Hugging Face API çağrısı
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 200,
                    "temperature": 0.1,
                    "do_sample": False,
                },
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    hf_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        # Response'u parse et
                        if isinstance(result, list) and len(result) > 0:
                            generated_text = result[0].get("generated_text", "")
                        else:
                            generated_text = result.get("generated_text", "")

                        # JSON kısmını çıkar
                        json_start = generated_text.find("{")
                        json_end = generated_text.rfind("}") + 1

                        if json_start != -1 and json_end > json_start:
                            json_str = generated_text[json_start:json_end]
                            try:
                                parsed_result = json.loads(json_str)
                                logger.info(
                                    f"LLM analizi: {title[:30]}... -> Score: {parsed_result.get('relevance_score', 0)}"
                                )
                                return parsed_result
                            except json.JSONDecodeError:
                                logger.warning(f"LLM JSON parse hatası: {json_str}")
                    else:
                        logger.warning(f"HF API hatası: {response.status}")

            # Fallback değerler
            return {
                "relevance_score": 7.0,
                "turkish_content": True,
                "educational_quality": 8.0,
                "level_appropriateness": 8.0,
            }

        except Exception as e:
            logger.error(f"LLM analizi hatası: {e}")
            return {
                "relevance_score": 7.0,
                "turkish_content": True,
                "educational_quality": 8.0,
            }

    def _calculate_quality_score_fast(
        self, video_data: Dict, subject: SubjectType, exam_type: ExamType
    ) -> float:
        """Hızlı kalite puanı hesaplama (performance optimized)"""
        score = 5.0  # Base score

        title_lower = video_data["title"].lower()

        # Hızlı başlık kontrolü
        if subject.value in title_lower:
            score += 2.0
        if exam_type.value.lower() in title_lower:
            score += 2.0
        if any(
            keyword in title_lower
            for keyword in ["konu anlatım", "ders", "2025", "2024"]
        ):
            score += 1.0

        # Hızlı kanal kontrolü
        channel_lower = video_data["channel"].lower()
        if any(
            keyword in channel_lower for keyword in ["öğretmen", "akademi", "eğitim"]
        ):
            score += 1.0

        return min(score, 10.0)

    def _is_turkish_content(self, text: str) -> bool:
        """Türkçe içerik tespiti - gelişmiş NLP"""
        if not text:
            return False

        # Türkçe karakterler
        turkish_chars = set("çğıöşüÇĞIİÖŞÜ")

        # Türkçe kelimeler (eğitim terminolojisi)
        turkish_education_words = {
            "matematik",
            "fizik",
            "kimya",
            "biyoloji",
            "türkçe",
            "edebiyat",
            "tarih",
            "coğrafya",
            "felsefe",
            "sosyal",
            "üniversite",
            "sınav",
            "tyt",
            "ayt",
            "yks",
            "konu",
            "anlatım",
            "ders",
            "öğretmen",
            "akademi",
            "eğitim",
            "çözüm",
            "soru",
            "test",
            "deneme",
            "hazırlık",
            "kursu",
            "öğrenci",
            "öğrenme",
            "açıklama",
        }

        # Metni normalize et
        text_lower = text.lower()
        text_normalized = unicodedata.normalize("NFD", text_lower)

        # Türkçe karakter oranı
        char_count = len([c for c in text if c.isalpha()])
        turkish_char_count = len([c for c in text if c in turkish_chars])
        turkish_char_ratio = turkish_char_count / max(char_count, 1)

        # Türkçe kelime tespiti
        words = re.findall(r"\b\w+\b", text_lower)
        turkish_word_count = len([w for w in words if w in turkish_education_words])

        # İngilizce kelime tespiti (red flag)
        english_words = {
            "the",
            "and",
            "for",
            "with",
            "this",
            "that",
            "from",
            "they",
            "have",
            "will",
            "you",
            "can",
            "all",
            "were",
            "been",
            "said",
            "what",
            "use",
            "your",
            "how",
            "our",
            "out",
            "many",
            "time",
            "very",
            "when",
            "much",
            "new",
            "would",
            "there",
            "each",
            "which",
            "their",
            "make",
            "like",
            "into",
            "him",
            "has",
            "two",
            "more",
            "go",
            "no",
            "way",
            "could",
            "my",
            "than",
            "first",
            "water",
            "long",
            "little",
            "most",
            "after",
            "school",
            "learn",
            "tutorial",
            "course",
            "lesson",
            "study",
            "guide",
        }
        english_word_count = len([w for w in words if w in english_words])

        # Skor hesaplama
        score = 0

        # Türkçe karakter bonusu
        if turkish_char_ratio > 0.1:
            score += 3

        # Türkçe eğitim kelimesi bonusu
        if turkish_word_count > 0:
            score += 4

        # İngilizce kelime cezası
        if english_word_count > 2:
            score -= 3

        # Kanal ismi kontrolü
        if any(
            word in text_lower for word in ["akademi", "eğitim", "öğretmen", "kurs"]
        ):
            score += 2

        return score >= 3

    def _filter_turkish_content(self, videos: List[Dict]) -> List[Dict]:
        """Türkçe içerik filtreleme"""
        filtered_videos = []

        for video in videos:
            title = video.get("title", "")
            channel = video.get("channel", "")
            description = video.get("description", "")

            # Türkçe içerik kontrolü
            text_to_check = f"{title} {channel} {description}"
            is_turkish = self._is_turkish_content(text_to_check)

            if is_turkish:
                video["turkish_content_score"] = 10.0
                filtered_videos.append(video)
            else:
                # Türkçe olmayan içeriği düşük skorla işaretle
                video["turkish_content_score"] = 2.0
                logger.debug(f"Non-Turkish content filtered: {title[:50]}")

        return filtered_videos

    def _advanced_content_filtering(
        self, videos: List[Dict], subject: SubjectType, difficulty: DifficultyLevel
    ) -> List[Dict]:
        """Gelişmiş içerik filtreleme"""

        # Önce Türkçe filtresi uygula
        turkish_videos = self._filter_turkish_content(videos)

        # Konu uygunluk filtreleme
        subject_keywords = {
            SubjectType.MATEMATIK: [
                "matematik",
                "geometri",
                "analiz",
                "trigonometri",
                "fonksiyon",
                "türev",
                "integral",
            ],
            SubjectType.FIZIK: [
                "fizik",
                "mekanik",
                "elektrik",
                "manyetizma",
                "optik",
                "termodinamik",
                "hareket",
            ],
            SubjectType.KIMYA: [
                "kimya",
                "atom",
                "molekül",
                "reaksiyon",
                "element",
                "periyodik",
                "organik",
            ],
            SubjectType.BIYOLOJI: [
                "biyoloji",
                "hücre",
                "dna",
                "protein",
                "metabolizma",
                "ekosistem",
                "evrim",
            ],
            SubjectType.TURKCE: [
                "türkçe",
                "dil",
                "gramer",
                "yazım",
                "sözcük",
                "cümle",
                "paragraf",
            ],
            SubjectType.EDEBIYAT: [
                "edebiyat",
                "şiir",
                "roman",
                "hikaye",
                "yazar",
                "eser",
                "dönem",
            ],
            SubjectType.TARIH: [
                "tarih",
                "osmanlı",
                "cumhuriyet",
                "savaş",
                "devrim",
                "medeniyet",
                "kültür",
            ],
            SubjectType.COGRAFYA: [
                "coğrafya",
                "harita",
                "iklim",
                "nüfus",
                "ekonomi",
                "bölge",
                "şehir",
            ],
            SubjectType.SOSYAL: [
                "sosyal",
                "toplum",
                "ekonomi",
                "siyaset",
                "hukuk",
                "sosyoloji",
                "felsefe",
            ],
            SubjectType.INGILIZCE: [
                "ingilizce",
                "english",
                "grammar",
                "vocabulary",
                "tense",
                "kelime",
            ],
        }

        filtered_videos = []
        subject_words = subject_keywords.get(subject, [])

        for video in turkish_videos:
            title = video.get("title", "").lower()
            channel = video.get("channel", "").lower()

            # Konu uygunluk skoru
            subject_score = 0
            for keyword in subject_words:
                if keyword in title or keyword in channel:
                    subject_score += 1

            # TYT/AYT uygunluk
            exam_keywords = ["tyt", "ayt", "yks", "üniversite", "sınav"]
            exam_score = sum(
                1 for keyword in exam_keywords if keyword in title or keyword in channel
            )

            # Toplam uygunluk skoru
            relevance_score = subject_score * 2 + exam_score

            if relevance_score > 0:  # En az bir konu kelimesi olmalı
                video["content_relevance_score"] = min(10.0, relevance_score * 2)
                filtered_videos.append(video)
            else:
                logger.debug(
                    f"Low relevance content filtered: {video.get('title', '')[:50]}"
                )

        return filtered_videos

    async def _calculate_dynamic_quality_score(
        self,
        video_data: Dict,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        student_level: int = 5,
    ) -> float:
        """Öğrenci seviyesine göre dinamik kalite puanı hesaplama"""

        # Temel kalite puanı
        base_score = self._calculate_quality_score(video_data, subject, exam_type)

        # LLM analizi ile gelişmiş scoring
        llm_analysis = await self._analyze_video_with_llm(
            video_data, subject, difficulty, exam_type
        )

        # Öğrenci seviyesine göre adaptasyon
        level_factor = 1.0
        if student_level <= 3:  # Başlangıç seviye
            if difficulty == DifficultyLevel.BASLANGIC:
                level_factor = 1.3  # Başlangıç videoları tercih et
            elif difficulty == DifficultyLevel.ILERI:
                level_factor = 0.7  # İleri videoları cezalandır
        elif student_level >= 8:  # İleri seviye
            if difficulty == DifficultyLevel.ILERI:
                level_factor = 1.2  # İleri videoları tercih et
            elif difficulty == DifficultyLevel.BASLANGIC:
                level_factor = 0.8  # Başlangıç videoları azalt

        # LLM skorlarını entegre et
        relevance_score = llm_analysis.get("relevance_score", 7.0)
        educational_quality = llm_analysis.get("educational_quality", 8.0)
        level_appropriateness = llm_analysis.get("level_appropriateness", 8.0)
        turkish_content = llm_analysis.get("turkish_content", True)

        # Final score calculation
        final_score = (
            base_score * 0.3
            + relevance_score * 0.25  # %30 temel score
            + educational_quality * 0.25  # %25 LLM relevance
            + level_appropriateness * 0.2  # %25 eğitim kalitesi  # %20 seviye uygunluğu
        ) * level_factor

        # Türkçe içerik bonusu
        if turkish_content:
            final_score *= 1.1

        return min(final_score, 10.0)

    def _calculate_quality_score(
        self, video_data: Dict, subject: SubjectType, exam_type: ExamType
    ) -> float:
        """Video kalite puanı hesapla"""
        score = 0.0

        # Kanal güvenilirliği (40% ağırlık)
        channel_score = self._get_channel_quality(video_data["channel"], subject)
        score += channel_score * 0.4

        # Başlık relevansı (25% ağırlık)
        title_score = self._calculate_title_relevance(
            video_data["title"], subject, exam_type
        )
        score += title_score * 0.25

        # View count normalized (15% ağırlık)
        view_score = (
            min(video_data["view_count"] / 100000, 10) / 10
        )  # 100k+ view = max score
        score += view_score * 0.15

        # Video süresi (10% ağırlık)
        duration_score = self._calculate_duration_score(video_data["duration"])
        score += duration_score * 0.10

        # Upload date (10% ağırlık)
        date_score = self._calculate_date_score(video_data["upload_date"])
        score += date_score * 0.10

        return min(score, 10.0)  # Maksimum 10 puan

    def _get_channel_quality(self, channel_name: str, subject: SubjectType) -> float:
        """Kanal kalite puanı al"""
        subject_channels = self.trusted_channels.get(subject.value, [])

        for channel in subject_channels:
            if channel["name"].lower() in channel_name.lower():
                return channel["quality"]

        # Genel eğitim kanalı kontrolü
        educational_keywords = ["öğretmen", "akademi", "eğitim", "ders", "kurs", "okul"]
        for keyword in educational_keywords:
            if keyword in channel_name.lower():
                return 7.0

        return 5.0  # Varsayılan puan

    def _calculate_title_relevance(
        self, title: str, subject: SubjectType, exam_type: ExamType
    ) -> float:
        """Başlık relevans puanı"""
        title_lower = title.lower()
        score = 0.0

        # Konu adı varlığı
        if subject.value in title_lower:
            score += 3.0

        # Sınav türü varlığı
        if exam_type.value.lower() in title_lower:
            score += 3.0

        # Eğitim anahtar kelimeleri
        edu_keywords = [
            "konu anlatımı",
            "ders",
            "öğretim",
            "anlatım",
            "hazırlık",
            "çözüm",
        ]
        for keyword in edu_keywords:
            if keyword in title_lower:
                score += 1.0
                break

        # Yıl varlığı (güncellik)
        if "2025" in title_lower or "2024" in title_lower:
            score += 1.0

        # Türkçe olduğunu gösteren işaretler
        turkish_indicators = ["türkçe", "tr", "turkish"]
        for indicator in turkish_indicators:
            if indicator in title_lower:
                score += 1.0
                break

        return min(score, 10.0)

    def _calculate_duration_score(self, duration: str) -> float:
        """Video süre puanı"""
        try:
            parts = duration.split(":")
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                total_seconds = minutes * 60 + seconds
            elif len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                total_seconds = hours * 3600 + minutes * 60 + seconds
            else:
                return 5.0

            # İdeal süre 10-45 dakika arası
            if 600 <= total_seconds <= 2700:  # 10-45 dakika
                return 10.0
            elif 300 <= total_seconds <= 3600:  # 5-60 dakika
                return 8.0
            elif total_seconds <= 300:  # Çok kısa
                return 6.0
            else:  # Çok uzun
                return 7.0

        except ValueError:
            return 5.0

    def _calculate_date_score(self, upload_date: str) -> float:
        """Upload tarihi puanı"""
        if not upload_date:
            return 5.0

        # Güncellik puanı
        current_year = datetime.now().year

        if "2025" in upload_date or "2024" in upload_date:
            return 10.0
        elif "2023" in upload_date:
            return 8.0
        elif "2022" in upload_date:
            return 6.0
        else:
            return 4.0

    async def discover_videos(
        self,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        max_results: int = 50,
    ) -> List[VideoMetadata]:
        """Ana video keşif fonksiyonu"""

        # Önce cache'den kontrol et - agresif cache kullanımı
        cached_videos = self._get_cached_videos(
            subject, difficulty, exam_type, max_age_hours=72
        )
        if (
            cached_videos and len(cached_videos) >= 1
        ):  # Minimum 1 video varsa cache kullan
            logger.info(f"Cache'den {len(cached_videos)} video döndürülüyor")
            return cached_videos[:max_results]

        # Hızlı öneriler varsa kullan (immediate response) - RANDOMIZED
        quick_key = (subject.value, difficulty.value, exam_type.value)
        if quick_key in self.quick_recommendations:
            logger.info(f"Quick recommendations kullanılıyor (randomized): {quick_key}")

            # Video listesini karıştır - her seferinde farklı sıralama
            available_videos = list(self.quick_recommendations[quick_key])
            random.shuffle(available_videos)

            quick_videos = []
            for video_data in available_videos:
                video_metadata = VideoMetadata(
                    video_id=video_data["video_id"],
                    title=video_data["title"],
                    channel=video_data["channel"],
                    channel_id="",
                    duration="20:00",
                    view_count=100000,
                    upload_date="2024",
                    thumbnail=f"https://img.youtube.com/vi/{video_data['video_id']}/maxresdefault.jpg",
                    description="",
                    quality_score=video_data["quality_score"]
                    + random.uniform(-0.3, 0.3),  # Slight randomization
                    subject=subject,
                    difficulty=difficulty,
                    exam_type=exam_type,
                )
                quick_videos.append(video_metadata)

            # Quality score'a göre tekrar sırala (ama randomized)
            quick_videos.sort(key=lambda x: x.quality_score, reverse=True)

            # Quick videolarını cache'e kaydet
            for video in quick_videos:
                self._cache_video(video)

            if quick_videos:
                logger.info(
                    f"Randomized video selection returned: {len(quick_videos[:max_results])} videos"
                )
                return quick_videos[:max_results]

        all_videos = []

        # Arama sorgularını oluştur
        queries = self._generate_search_queries(subject, difficulty, exam_type)

        # Concurrent search ile hızlandır - sadece en iyi 2 query
        best_queries = queries[:2]  # Sadece ilk 2 sorgu
        search_tasks = []

        for query in best_queries:
            task = self._search_youtube_concurrent(
                query, subject, difficulty, exam_type, max_results=10
            )
            search_tasks.append(task)

        # Paralel arama yap
        if search_tasks:
            results_list = await asyncio.gather(*search_tasks, return_exceptions=True)

            for results in results_list:
                if isinstance(results, Exception):
                    logger.error(f"Paralel arama hatası: {results}")
                    continue

                if isinstance(results, list):
                    all_videos.extend(results)

        # Türkçe NLP filtreleme uygula
        video_dicts = [asdict(video) for video in all_videos]
        filtered_videos_dict = self._advanced_content_filtering(
            video_dicts, subject, difficulty
        )

        # VideoMetadata'ya geri çevir
        filtered_videos = []
        for video_dict in filtered_videos_dict:
            video_metadata = VideoMetadata(
                video_id=video_dict["video_id"],
                title=video_dict["title"],
                channel=video_dict["channel"],
                channel_id=video_dict.get("channel_id", ""),
                duration=video_dict.get("duration", "20:00"),
                view_count=video_dict.get("view_count", 0),
                upload_date=video_dict.get("upload_date", "2024"),
                thumbnail=video_dict.get("thumbnail", ""),
                description=video_dict.get("description", ""),
                quality_score=video_dict.get("quality_score", 5.0),
                subject=subject,
                difficulty=difficulty,
                exam_type=exam_type,
                relevance_keywords=video_dict.get("relevance_keywords", []),
            )
            # Türkçe NLP skorlarını ekle
            video_metadata.quality_score = max(
                video_metadata.quality_score,
                video_dict.get("turkish_content_score", 5.0),
                video_dict.get("content_relevance_score", 5.0),
            )
            filtered_videos.append(video_metadata)

        # Duplikatları kaldır ve kalite puanına göre sırala
        unique_videos = {}
        for video in filtered_videos:
            if video.video_id not in unique_videos:
                unique_videos[video.video_id] = video
            elif video.quality_score > unique_videos[video.video_id].quality_score:
                unique_videos[video.video_id] = video

        sorted_videos = sorted(
            unique_videos.values(), key=lambda x: x.quality_score, reverse=True
        )

        logger.info(
            f"Türkçe NLP filtreleme: {len(all_videos)} -> {len(sorted_videos)} video"
        )

        # Cache'e kaydet
        for video in sorted_videos[:max_results]:
            self._cache_video(video)

        return sorted_videos[:max_results]

    def _get_cached_videos(
        self,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        max_age_hours: int = 24,
    ) -> List[VideoMetadata]:
        """Cache'den video listesi al"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM video_cache 
                WHERE subject = ? AND difficulty = ? AND exam_type = ?
                AND last_updated > ?
                ORDER BY quality_score DESC
            """,
                (subject.value, difficulty.value, exam_type.value, cutoff_time),
            )

            videos = []
            for row in cursor.fetchall():
                video = VideoMetadata(
                    video_id=row[0],
                    title=row[1],
                    channel=row[2],
                    channel_id=row[3],
                    duration=row[4],
                    view_count=row[5],
                    upload_date=row[6],
                    thumbnail=row[7],
                    description=row[8],
                    quality_score=row[9],
                    subject=SubjectType(row[10]),
                    difficulty=DifficultyLevel(row[11]),
                    exam_type=ExamType(row[12]),
                )
                videos.append(video)

            return videos

    def _cache_video(self, video: VideoMetadata):
        """Video'yu cache'e kaydet"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO video_cache 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
                (
                    video.video_id,
                    video.title,
                    video.channel,
                    video.channel_id,
                    video.duration,
                    video.view_count,
                    video.upload_date,
                    video.thumbnail,
                    video.description,
                    video.quality_score,
                    video.subject.value,
                    video.difficulty.value,
                    video.exam_type.value,
                    video.language,
                ),
            )

    def _get_cached_search(
        self, query_hash: str, max_age_hours: int = 6
    ) -> Optional[List[Dict]]:
        """Arama sonucunu cache'den al"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT results FROM search_cache 
                WHERE query_hash = ? AND cached_at > ?
            """,
                (query_hash, cutoff_time),
            )

            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    def _cache_search_result(self, query_hash: str, query: str, results: List[Dict]):
        """Arama sonucunu cache'e kaydet"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO search_cache 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (query_hash, query, json.dumps(results)),
            )

    async def monitor_rss_feeds(self):
        """RSS feed'leri izle ve yeni videoları yakala"""
        # Bu fonksiyon periyodik olarak çalışacak

    async def get_video_recommendations(
        self, student_profile: Dict, max_per_subject: int = 10
    ) -> Dict[str, List[VideoMetadata]]:
        """Öğrenci profiline göre video önerileri - FAST VERSION"""
        recommendations = {}

        goals = student_profile.get("goals", [])
        current_level = student_profile.get("currentLevel", {})

        # HIZLI ÇÖZMe: Sadece pre-computed recommendations kullan
        for goal in goals:
            for subject_key, level in current_level.items():
                try:
                    # Seviyeye göre zorluk belirle
                    if level <= 3:
                        difficulty_str = "başlangıç"
                    elif level <= 7:
                        difficulty_str = "orta"
                    else:
                        difficulty_str = "ileri"

                    # Pre-computed recommendations'dan bul
                    quick_key = (subject_key, difficulty_str, goal)

                    if quick_key in self.quick_recommendations:
                        logger.info(f"Pre-computed recommendation bulundu: {quick_key}")

                        videos = []
                        for video_data in self.quick_recommendations[quick_key][
                            :max_per_subject
                        ]:
                            # Dynamic quality score calculation based on student level
                            dynamic_score = await self._calculate_dynamic_quality_score(
                                video_data,
                                SubjectType(subject_key),
                                DifficultyLevel(difficulty_str),
                                ExamType(goal),
                                student_level=level,
                            )

                            video_metadata = VideoMetadata(
                                video_id=video_data["video_id"],
                                title=video_data["title"],
                                channel=video_data["channel"],
                                channel_id="",
                                duration="20:00",
                                view_count=100000,
                                upload_date="2024",
                                thumbnail=f"https://img.youtube.com/vi/{video_data['video_id']}/maxresdefault.jpg",
                                description="",
                                quality_score=dynamic_score,  # Use dynamic score
                                subject=SubjectType(subject_key),
                                difficulty=DifficultyLevel(difficulty_str),
                                exam_type=ExamType(goal),
                            )
                            videos.append(video_metadata)

                        # Student level based sorting - higher quality scores first
                        videos.sort(key=lambda x: x.quality_score, reverse=True)

                        key = f"{goal}_{subject_key}"
                        recommendations[key] = videos

                        logger.info(
                            f"Dynamic scoring applied for student level {level}: {len(videos)} videos"
                        )
                    else:
                        logger.warning(
                            f"Pre-computed recommendation bulunamadı: {quick_key}"
                        )
                        # Fallback: boş liste değil, default videolar
                        default_videos = []
                        if subject_key == "matematik":
                            default_videos = [
                                VideoMetadata(
                                    video_id="default_math",
                                    title=f"{goal} {subject_key.title()} - Temel Konular",
                                    channel="Eğitim Kanalı",
                                    channel_id="",
                                    duration="15:00",
                                    view_count=50000,
                                    upload_date="2024",
                                    thumbnail="https://img.youtube.com/vi/default_math/maxresdefault.jpg",
                                    description="",
                                    quality_score=7.5,
                                    subject=SubjectType(subject_key),
                                    difficulty=DifficultyLevel(difficulty_str),
                                    exam_type=ExamType(goal),
                                )
                            ]

                        key = f"{goal}_{subject_key}"
                        recommendations[key] = default_videos

                except (ValueError, KeyError) as e:
                    logger.error(f"Recommendation error for {subject_key}: {e}")
                    continue

        return recommendations


# Singleton instance
_youtube_discovery = None


def get_youtube_discovery() -> YouTubeDiscovery:
    """YouTube discovery singleton"""
    global _youtube_discovery
    if _youtube_discovery is None:
        _youtube_discovery = YouTubeDiscovery()
    return _youtube_discovery
