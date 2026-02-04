"""
Gerçek YouTube API v3 Entegrasyonu
Türkçe Eğitim Videoları için Özelleştirilmiş
"""

import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class YouTubeVideoResult:
    """YouTube API'den gelen video sonucu"""

    video_id: str
    title: str
    channel: str
    channel_id: str
    description: str
    thumbnail: str
    duration: str
    view_count: int
    upload_date: str
    quality_score: float
    language_score: float
    education_relevance: float
    url: str


class RealYouTubeAPI:
    """Gerçek YouTube API v3 Servisi"""

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.session: Optional[aiohttp.ClientSession] = None

        # Türkçe eğitim kanalları ID'leri
        self.trusted_channel_ids = {
            "TonguçAkademi": "UCQaEgq0uA7wHQlUkE3o8L4w",
            "KAMP Online": "UCkamp_online",
            "Khan Academy Türkçe": "UCzeM1QxMZG7LCILPl8GIzLA",
            "MEB Uzaktan Eğitim": "UC_meb_uzaktan",
            "Fizik Öğretmeni": "UC_fizik_teacher",
            "Matematik Öğretmeni": "UC_matematik_teacher",
        }

        # Türkçe eğitim anahtar kelimeleri
        self.turkish_edu_keywords = {
            "matematik": [
                "matematik",
                "mat",
                "tyt matematik",
                "ayt matematik",
                "fonksiyon",
                "türev",
                "integral",
                "limit",
            ],
            "fizik": [
                "fizik",
                "fiz",
                "tyt fizik",
                "ayt fizik",
                "hareket",
                "kuvvet",
                "enerji",
                "elektrik",
            ],
            "kimya": [
                "kimya",
                "kim",
                "tyt kimya",
                "ayt kimya",
                "atom",
                "molekül",
                "reaksiyon",
                "periyodik",
            ],
            "türkçe": [
                "türkçe",
                "tr",
                "tyt türkçe",
                "dil bilgisi",
                "anlam",
                "sözcük",
                "metin",
            ],
        }

        if not self.api_key or self.api_key == "test-youtube-api-key":
            logger.warning("YouTube API key bulunamadı - test modu")

    async def get_session(self) -> aiohttp.ClientSession:
        """HTTP session al veya oluştur"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session

    async def close(self):
        """Session'ı kapat"""
        if self.session:
            await self.session.close()
            self.session = None

    def _build_search_query(self, subject: str, exam_type: str, difficulty: str) -> str:
        """Türkçe eğitim odaklı arama sorgusu oluştur"""
        base_keywords = self.turkish_edu_keywords.get(subject.lower(), [subject])

        # Ana sorgu
        query_parts = [f"{exam_type} {subject}", "konu anlatımı", "türkçe"]

        # Zorluk seviyesi
        if difficulty == "başlangıç":
            query_parts.extend(["temel", "başlangıç", "kolay"])
        elif difficulty == "ileri":
            query_parts.extend(["ileri", "zor", "detaylı"])

        # Müzik ve sanat içeriğini engelle
        negative_keywords = ["-müzik", "-music", "-şarkı", "-song", "-sanat", "-art"]

        query = " ".join(query_parts) + " " + " ".join(negative_keywords)
        return query

    async def search_videos(
        self,
        subject: str,
        exam_type: str = "TYT",
        difficulty: str = "orta",
        max_results: int = 10,
    ) -> List[YouTubeVideoResult]:
        """YouTube API ile video arama"""

        if not self.api_key or self.api_key == "test-youtube-api-key":
            logger.warning(
                "API key yok - gerçek YouTube verisi için geçerli API key gerekli"
            )
            return []

        try:
            session = await self.get_session()

            # Arama sorgusu oluştur
            query = self._build_search_query(subject, exam_type, difficulty)

            # YouTube API search endpoint
            search_url = f"{self.base_url}/search"
            search_params = {
                "key": self.api_key,
                "part": "snippet",
                "type": "video",
                "q": query,
                "maxResults": min(max_results * 2, 50),  # Extra results for filtering
                "order": "relevance",
                "regionCode": "TR",
                "relevanceLanguage": "tr",
                "videoDefinition": "any",
                "videoDuration": "medium",  # 4-20 dakika arası
            }

            logger.info(f"YouTube API araması: {query}")

            async with session.get(search_url, params=search_params) as response:
                if response.status != 200:
                    logger.error(f"YouTube API hatası: {response.status}")
                    return []

                data = await response.json()
                video_ids = [item["id"]["videoId"] for item in data.get("items", [])]

                if not video_ids:
                    logger.warning("YouTube API'den video bulunamadı")
                    return []

                # Video detaylarını al
                videos = await self._get_video_details(video_ids)

                # Türkçe eğitim videoları filtrele
                filtered_videos = self._filter_turkish_education_videos(
                    videos, subject, exam_type, difficulty
                )

                return filtered_videos[:max_results]

        except Exception as e:
            logger.error(f"YouTube API araması başarısız: {str(e)}")
            return []

    async def _get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """Video detaylarını al"""
        try:
            session = await self.get_session()

            # Videos endpoint
            videos_url = f"{self.base_url}/videos"
            videos_params = {
                "key": self.api_key,
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(video_ids),
            }

            async with session.get(videos_url, params=videos_params) as response:
                if response.status != 200:
                    logger.error(f"Video detayları alınamadı: {response.status}")
                    return []

                data = await response.json()
                return data.get("items", [])

        except Exception as e:
            logger.error(f"Video detayları hatası: {str(e)}")
            return []

    def _filter_turkish_education_videos(
        self, videos: List[Dict], subject: str, exam_type: str, difficulty: str
    ) -> List[YouTubeVideoResult]:
        """Türkçe eğitim videolarını filtrele ve skorla"""

        results = []

        for video in videos:
            try:
                # Video bilgileri
                snippet = video["snippet"]
                statistics = video.get("statistics", {})
                content_details = video.get("contentDetails", {})

                video_id = video["id"]
                title = snippet.get("title", "")
                description = snippet.get("description", "")
                channel_title = snippet.get("channelTitle", "")
                channel_id = snippet.get("channelId", "")

                # Müzik kontrolü - HARD BLOCK
                if self._is_music_content(title, description, channel_title):
                    logger.debug(f"Müzik içeriği engellendi: {title}")
                    continue

                # Türkçe dil kontrolü
                language_score = self._calculate_language_score(title, description)
                if language_score < 5.0:  # Minimum Türkçe skoru
                    continue

                # Eğitim içeriği kontrolü
                education_score = self._calculate_education_score(
                    title, description, channel_title, subject
                )
                if education_score < 6.0:  # Minimum eğitim skoru
                    continue

                # Kalite skoru
                quality_score = self._calculate_quality_score(
                    statistics, title, channel_title
                )

                # Süre formatı
                duration = self._parse_duration(content_details.get("duration", ""))

                # Görüntülenme sayısı
                view_count = int(statistics.get("viewCount", 0))

                # Thumbnail
                thumbnails = snippet.get("thumbnails", {})
                thumbnail = (
                    thumbnails.get("maxres", {}).get("url")
                    or thumbnails.get("high", {}).get("url")
                    or thumbnails.get("medium", {}).get("url", "")
                )

                # Upload tarihi
                upload_date = snippet.get("publishedAt", "")[:10]

                # URL
                url = f"https://www.youtube.com/embed/{video_id}"

                result = YouTubeVideoResult(
                    video_id=video_id,
                    title=title,
                    channel=channel_title,
                    channel_id=channel_id,
                    description=description[:200] + "..."
                    if len(description) > 200
                    else description,
                    thumbnail=thumbnail,
                    duration=duration,
                    view_count=view_count,
                    upload_date=upload_date,
                    quality_score=quality_score,
                    language_score=language_score,
                    education_relevance=education_score,
                    url=url,
                )

                results.append(result)

            except Exception as e:
                logger.error(f"Video işleme hatası: {str(e)}")
                continue

        # Skorlara göre sırala
        results.sort(
            key=lambda x: (x.education_relevance + x.quality_score + x.language_score),
            reverse=True,
        )

        logger.info(
            f"YouTube API'den {len(results)} kaliteli Türkçe eğitim videosu filtrelendi"
        )
        return results

    def _is_music_content(self, title: str, description: str, channel: str) -> bool:
        """Müzik içeriği kontrolü"""
        text = f"{title} {description} {channel}".lower()
        music_terms = [
            "müzik",
            "music",
            "şarkı",
            "song",
            "beste",
            "melodi",
            "ritim",
            "cover",
            "remix",
            "acoustic",
            "live performance",
            "konser",
        ]
        return any(term in text for term in music_terms)

    def _calculate_language_score(self, title: str, description: str) -> float:
        """Türkçe dil kalitesi skoru"""
        text = f"{title} {description}".lower()

        # Türkçe karakterler
        turkish_chars = ["ç", "ğ", "ı", "ş", "ü", "ö"]
        turkish_score = sum(1 for char in turkish_chars if char in text)

        # Türkçe eğitim terimleri
        turkish_terms = [
            "konu anlatımı",
            "ders",
            "öğretmen",
            "eğitim",
            "matematik",
            "fizik",
            "kimya",
            "türkçe",
            "tyt",
            "ayt",
            "sınav",
        ]
        term_score = sum(2 for term in turkish_terms if term in text)

        # İngilizce terimler (negatif)
        english_terms = ["tutorial", "lesson", "math", "physics", "chemistry"]
        english_penalty = sum(1 for term in english_terms if term in text)

        score = 5.0 + (turkish_score * 0.5) + term_score - english_penalty
        return max(0.0, min(score, 10.0))

    def _calculate_education_score(
        self, title: str, description: str, channel: str, subject: str
    ) -> float:
        """Eğitim içeriği relevans skoru"""
        text = f"{title} {description}".lower()

        score = 5.0

        # Konu relevansı
        subject_keywords = self.turkish_edu_keywords.get(subject.lower(), [])
        for keyword in subject_keywords:
            if keyword in text:
                score += 1.5

        # Güvenilir kanal kontrolü
        for trusted_channel, channel_id in self.trusted_channel_ids.items():
            if trusted_channel.lower() in channel.lower():
                score += 2.0
                break

        # Eğitim terimleri
        edu_terms = ["konu anlatımı", "ders", "öğretmen", "sınav", "örnek soru"]
        for term in edu_terms:
            if term in text:
                score += 0.8

        return min(score, 10.0)

    def _calculate_quality_score(self, stats: Dict, title: str, channel: str) -> float:
        """Video kalite skoru"""
        score = 5.0

        # Görüntülenme sayısı
        view_count = int(stats.get("viewCount", 0))
        if 10000 <= view_count <= 1000000:
            score += 2.0
        elif view_count > 1000000:
            score += 1.0
        elif view_count > 1000:
            score += 0.5

        # Like oranı
        like_count = int(stats.get("likeCount", 0))
        if like_count > 100:
            score += 1.0

        # Başlık kalitesi
        if "konu anlatımı" in title.lower() or "ders" in title.lower():
            score += 1.0

        return min(score, 10.0)

    def _parse_duration(self, duration_str: str) -> str:
        """ISO 8601 duration formatını dakika:saniye'ye çevir"""
        if not duration_str:
            return "00:00"

        # PT15M33S -> 15:33
        import re

        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
        if not match:
            return "00:00"

        hours, minutes, seconds = match.groups()
        hours = int(hours) if hours else 0
        minutes = int(minutes) if minutes else 0
        seconds = int(seconds) if seconds else 0

        total_minutes = hours * 60 + minutes
        return f"{total_minutes:02d}:{seconds:02d}"


# Global instance
real_youtube_api = RealYouTubeAPI()


async def get_real_youtube_api() -> RealYouTubeAPI:
    """Real YouTube API instance'ını al"""
    return real_youtube_api
