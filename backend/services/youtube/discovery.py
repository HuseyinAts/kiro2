"""
YouTube Video Kesif Sistemi - Ana Sinif

Mixin'leri birlestiren ana YouTubeDiscovery sinifi.
"""

import asyncio
import logging
import random
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp

from .cache_manager import CacheManagerMixin
from .models import DifficultyLevel, ExamType, SubjectType, VideoMetadata
from .quality_scorer import QualityScorerMixin
from .search_engine import SearchEngineMixin
from .turkish_filter import TurkishFilterMixin

logger = logging.getLogger(__name__)


class YouTubeDiscovery(
    SearchEngineMixin,
    QualityScorerMixin,
    TurkishFilterMixin,
    CacheManagerMixin,
):
    """Gelismis YouTube video kesif sistemi"""

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.db_path = self.cache_dir / "youtube_cache.db"
        self.session: Optional[aiohttp.ClientSession] = None

        # Genisletilmis video veritabani
        self.quick_recommendations = self._build_quick_recommendations()

        # Guvenilir Turk egitim kanallari
        self.trusted_channels = self._build_trusted_channels()

        # Arama query sablonlari
        self.search_templates = {
            ExamType.TYT: [
                "{subject} TYT {difficulty} konu anlatimi 2025",
                "TYT {subject} {difficulty} ders {year}",
                "{subject} temel yeterlilik {difficulty} video",
                "YKS {subject} TYT {difficulty} hazirlik",
            ],
            ExamType.AYT: [
                "{subject} AYT {difficulty} konu anlatimi 2025",
                "AYT {subject} {difficulty} ders {year}",
                "{subject} alan yeterlilik {difficulty} video",
                "YKS {subject} AYT {difficulty} hazirlik",
            ],
        }

        self._init_database()

    def _build_quick_recommendations(self) -> Dict:
        """Hizli oneri veritabanini olustur"""
        return {
            ("matematik", "orta", "TYT"): [
                {
                    "video_id": "qsf8ERnJHho",
                    "title": "Fonksiyonlar - TYT Matematik",
                    "channel": "Matematik Ogretmeni",
                    "quality_score": 8.5,
                },
                {
                    "video_id": "abc123def",
                    "title": "Turev - TYT Matematik",
                    "channel": "TongucAkademi",
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
                    "title": "Integral - TYT Matematik",
                    "channel": "Matematik Ogretmeni",
                    "quality_score": 8.9,
                },
                {
                    "video_id": "math_new1",
                    "title": "Logaritma - TYT Matematik",
                    "channel": "Matematikciler",
                    "quality_score": 8.8,
                },
                {
                    "video_id": "math_new2",
                    "title": "Ucgenler - TYT Matematik",
                    "channel": "TongucAkademi",
                    "quality_score": 8.6,
                },
            ],
            ("matematik", "baslangic", "TYT"): [
                {
                    "video_id": "basic_math1",
                    "title": "Temel Matematik - TYT",
                    "channel": "TongucAkademi",
                    "quality_score": 8.3,
                },
                {
                    "video_id": "basic_math2",
                    "title": "Sayilar - TYT Matematik",
                    "channel": "Matematik Ogretmeni",
                    "quality_score": 8.1,
                },
            ],
            ("matematik", "ileri", "TYT"): [
                {
                    "video_id": "adv_math1",
                    "title": "Karmasik Fonksiyonlar - TYT",
                    "channel": "Ileri Matematik",
                    "quality_score": 9.1,
                },
            ],
            ("fizik", "baslangic", "TYT"): [
                {
                    "video_id": "2m4xyR1QlIU",
                    "title": "Hareket - TYT Fizik",
                    "channel": "Fizik Muallimi",
                    "quality_score": 8.8,
                },
                {
                    "video_id": "def456ghi",
                    "title": "Kuvvet - TYT Fizik",
                    "channel": "TongucAkademi",
                    "quality_score": 8.9,
                },
            ],
            ("fizik", "orta", "TYT"): [
                {
                    "video_id": "fizik_orta1",
                    "title": "Elektrik - TYT Fizik",
                    "channel": "TongucAkademi",
                    "quality_score": 8.6,
                },
            ],
            ("turkce", "orta", "TYT"): [
                {
                    "video_id": "LKZKJt3u7oA",
                    "title": "Sozcuk Turleri - TYT Turkce",
                    "channel": "Turkce Ogretmeni",
                    "quality_score": 8.6,
                },
            ],
            ("kimya", "orta", "TYT"): [
                {
                    "video_id": "kimya123abc",
                    "title": "Atom - TYT Kimya",
                    "channel": "Kimya Ogretmeni",
                    "quality_score": 8.5,
                },
            ],
            ("biyoloji", "orta", "TYT"): [
                {
                    "video_id": "bio123abc",
                    "title": "Hucre - TYT Biyoloji",
                    "channel": "Biyoloji Ogretmeni",
                    "quality_score": 8.3,
                },
            ],
        }

    def _build_trusted_channels(self) -> Dict:
        """Guvenilir kanal listesini olustur"""
        return {
            "matematik": [
                {"name": "Matematik Ogretmeni", "id": "UCxxxxxx", "quality": 9.2},
                {
                    "name": "TongucAkademi",
                    "id": "UC5Bu5lNaUYBYG-ZW-bMeXWA",
                    "quality": 8.8,
                },
                {"name": "KAMP Online", "id": "UCyyyyyy", "quality": 8.5},
            ],
            "fizik": [
                {"name": "Fizik Ogretmeni", "id": "UCaaaaaa", "quality": 9.0},
                {
                    "name": "TongucAkademi",
                    "id": "UC5Bu5lNaUYBYG-ZW-bMeXWA",
                    "quality": 8.8,
                },
            ],
            "turkce": [
                {"name": "Turkce Ogretmeni", "id": "UCbbbbbbb", "quality": 9.1},
            ],
            "sosyal": [
                {"name": "TRT EBA TV", "id": "UCddddddd", "quality": 8.9},
            ],
        }

    async def start_session(self) -> None:
        """HTTP session baslat"""
        if not self.session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            self.session = aiohttp.ClientSession(
                headers=headers, timeout=aiohttp.ClientTimeout(total=30)
            )

    async def close_session(self) -> None:
        """HTTP session kapat"""
        if self.session:
            await self.session.close()
            self.session = None

    async def discover_videos(
        self,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        max_results: int = 50,
    ) -> List[VideoMetadata]:
        """Ana video kesif fonksiyonu"""

        # Once cache'den kontrol et
        cached_videos = self._get_cached_videos(
            subject, difficulty, exam_type, max_age_hours=72
        )
        if cached_videos and len(cached_videos) >= 1:
            logger.info(f"Cache'den {len(cached_videos)} video donduruluyor")
            return cached_videos[:max_results]

        # Hizli oneriler varsa kullan (randomized)
        quick_key = (subject.value, difficulty.value, exam_type.value)
        if quick_key in self.quick_recommendations:
            logger.info(f"Quick recommendations kullaniliyor: {quick_key}")

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
                    + random.uniform(-0.3, 0.3),
                    subject=subject,
                    difficulty=difficulty,
                    exam_type=exam_type,
                )
                quick_videos.append(video_metadata)

            quick_videos.sort(key=lambda x: x.quality_score, reverse=True)

            for video in quick_videos:
                self._cache_video(video)

            return quick_videos[:max_results]

        all_videos = []

        # Arama sorgularini olustur
        queries = self._generate_search_queries(subject, difficulty, exam_type)

        # Concurrent search
        best_queries = queries[:2]
        search_tasks = []

        for query in best_queries:
            task = self._search_youtube_concurrent(
                query, subject, difficulty, exam_type, max_results=10
            )
            search_tasks.append(task)

        if search_tasks:
            results_list = await asyncio.gather(*search_tasks, return_exceptions=True)

            for results in results_list:
                if isinstance(results, Exception):
                    logger.error(f"Paralel arama hatasi: {results}")
                    continue

                if isinstance(results, list):
                    all_videos.extend(results)

        # Turkce NLP filtreleme
        video_dicts = [asdict(video) for video in all_videos]
        filtered_videos_dict = self._advanced_content_filtering(
            video_dicts, subject, difficulty
        )

        # VideoMetadata'ya geri cevir
        filtered_videos = []
        for video_dict in filtered_videos_dict:
            video_metadata = VideoMetadata.from_dict(
                video_dict, subject, difficulty, exam_type
            )
            video_metadata.quality_score = max(
                video_metadata.quality_score,
                video_dict.get("turkish_content_score", 5.0),
                video_dict.get("content_relevance_score", 5.0),
            )
            filtered_videos.append(video_metadata)

        # Duplikatlari kaldir
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
            f"Turkce NLP filtreleme: {len(all_videos)} -> {len(sorted_videos)} video"
        )

        for video in sorted_videos[:max_results]:
            self._cache_video(video)

        return sorted_videos[:max_results]

    async def get_video_recommendations(
        self, student_profile: Dict, max_per_subject: int = 10
    ) -> Dict[str, List[VideoMetadata]]:
        """Ogrenci profiline gore video onerileri"""
        recommendations = {}

        goals = student_profile.get("goals", [])
        current_level = student_profile.get("currentLevel", {})

        for goal in goals:
            for subject_key, level in current_level.items():
                try:
                    if level <= 3:
                        difficulty_str = "baslangic"
                    elif level <= 7:
                        difficulty_str = "orta"
                    else:
                        difficulty_str = "ileri"

                    quick_key = (subject_key, difficulty_str, goal)

                    if quick_key in self.quick_recommendations:
                        logger.info(f"Pre-computed recommendation bulundu: {quick_key}")

                        videos = []
                        for video_data in self.quick_recommendations[quick_key][
                            :max_per_subject
                        ]:
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
                                quality_score=dynamic_score,
                                subject=SubjectType(subject_key),
                                difficulty=DifficultyLevel(difficulty_str),
                                exam_type=ExamType(goal),
                            )
                            videos.append(video_metadata)

                        videos.sort(key=lambda x: x.quality_score, reverse=True)

                        key = f"{goal}_{subject_key}"
                        recommendations[key] = videos
                    else:
                        logger.warning(
                            f"Pre-computed recommendation bulunamadi: {quick_key}"
                        )
                        key = f"{goal}_{subject_key}"
                        recommendations[key] = []

                except (ValueError, KeyError) as e:
                    logger.error(f"Recommendation error for {subject_key}: {e}")
                    continue

        return recommendations

    async def monitor_rss_feeds(self) -> None:
        """RSS feed'leri izle ve yeni videolari yakala"""
        # Bu fonksiyon periyodik olarak calisacak
        pass


# Singleton instance
_youtube_discovery: Optional[YouTubeDiscovery] = None


def get_youtube_discovery() -> YouTubeDiscovery:
    """YouTube discovery singleton"""
    global _youtube_discovery
    if _youtube_discovery is None:
        _youtube_discovery = YouTubeDiscovery()
    return _youtube_discovery
