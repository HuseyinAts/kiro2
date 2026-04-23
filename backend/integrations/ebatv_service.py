"""
EBA TV İçerik Entegrasyonu Servisi

TRT EBA TV video linklerini manuel toplama ve yönetim sistemi.
MEB müfredatına uygun içerik kategorilendirme ve metadata çıkarma.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import aiohttp

from core.config import get_settings
from models.enums import DifficultyLevel

logger = logging.getLogger(__name__)
settings = get_settings()


class EBAContentCategory(Enum):
    """EBA TV içerik kategorileri"""

    MATEMATIK = "matematik"
    TURKCE = "turkce"
    FEN_BILIMLERI = "fen_bilimleri"
    SOSYAL_BILGILER = "sosyal_bilgiler"
    INGILIZCE = "ingilizce"
    FIZIK = "fizik"
    KIMYA = "kimya"
    BIYOLOJI = "biyoloji"
    TARIH = "tarih"
    COGRAFYA = "cografya"
    FELSEFE = "felsefe"
    EDEBIYAT = "edebiyat"


class EBAGradeLevel(Enum):
    """EBA TV sınıf seviyeleri"""

    SINIF_5 = "5"
    SINIF_6 = "6"
    SINIF_7 = "7"
    SINIF_8 = "8"  # LGS
    SINIF_9 = "9"
    SINIF_10 = "10"
    SINIF_11 = "11"
    SINIF_12 = "12"  # YKS


@dataclass
class EBAVideoMetadata:
    """EBA TV video metadata yapısı"""

    title: str
    description: str
    duration_minutes: int
    category: EBAContentCategory
    grade_level: EBAGradeLevel
    subject_topics: list[str]
    difficulty_level: DifficultyLevel
    video_url: str
    thumbnail_url: str | None
    transcript: str | None
    quality_score: float
    curriculum_alignment: dict[str, Any]
    accessibility_features: list[str]
    created_date: datetime
    last_updated: datetime


@dataclass
class EBAContentCollection:
    """EBA TV içerik koleksiyonu"""

    videos: list[EBAVideoMetadata]
    total_count: int
    categories: dict[EBAContentCategory, int]
    grade_levels: dict[EBAGradeLevel, int]
    quality_distribution: dict[str, int]
    last_updated: datetime


class EBAContentQualityAnalyzer:
    """EBA TV içerik kalite değerlendirme sistemi"""

    def __init__(self):
        self.quality_criteria = {
            "video_duration": {"min": 5, "max": 45, "optimal": 15},  # dakika
            "title_clarity": {"min_words": 3, "max_words": 12},
            "description_length": {"min_chars": 50, "max_chars": 500},
            "curriculum_keywords": [
                "kazanım",
                "hedef",
                "beceri",
                "öğrenme",
                "anlama",
                "çözüm",
                "problem",
                "örnek",
                "uygulama",
                "değerlendirme",
            ],
        }

    async def analyze_video_quality(self, metadata: EBAVideoMetadata) -> float:
        """Video kalitesini 0-10 arası puanla"""

        quality_score = 0.0
        max_score = 10.0

        # Süre uygunluğu (2 puan)
        duration_score = self._evaluate_duration(metadata.duration_minutes)
        quality_score += duration_score * 2

        # Başlık netliği (2 puan)
        title_score = self._evaluate_title_clarity(metadata.title)
        quality_score += title_score * 2

        # Açıklama kalitesi (2 puan)
        description_score = self._evaluate_description(metadata.description)
        quality_score += description_score * 2

        # Müfredat uyumu (2 puan)
        curriculum_score = self._evaluate_curriculum_alignment(metadata)
        quality_score += curriculum_score * 2

        # Erişilebilirlik özellikleri (2 puan)
        accessibility_score = self._evaluate_accessibility(
            metadata.accessibility_features
        )
        quality_score += accessibility_score * 2

        return min(max_score, quality_score)

    def _evaluate_duration(self, duration: int) -> float:
        """Video süresini değerlendir"""
        criteria = self.quality_criteria["video_duration"]

        if duration < criteria["min"]:
            return 0.3  # Çok kısa
        if duration > criteria["max"]:
            return 0.5  # Çok uzun
        if abs(duration - criteria["optimal"]) <= 5:
            return 1.0  # Optimal
        return 0.7  # Kabul edilebilir

    def _evaluate_title_clarity(self, title: str) -> float:
        """Başlık netliğini değerlendir"""
        words = title.split()
        criteria = self.quality_criteria["title_clarity"]

        if len(words) < criteria["min_words"]:
            return 0.4  # Çok kısa
        if len(words) > criteria["max_words"]:
            return 0.6  # Çok uzun
        return 1.0  # Uygun

    def _evaluate_description(self, description: str) -> float:
        """Açıklama kalitesini değerlendir"""
        if not description:
            return 0.0

        criteria = self.quality_criteria["description_length"]
        length = len(description)

        if length < criteria["min_chars"]:
            return 0.3
        if length > criteria["max_chars"]:
            return 0.7
        return 1.0

    def _evaluate_curriculum_alignment(self, metadata: EBAVideoMetadata) -> float:
        """Müfredat uyumunu değerlendir"""
        keywords = self.quality_criteria["curriculum_keywords"]
        text = f"{metadata.title} {metadata.description}".lower()

        found_keywords = sum(1 for keyword in keywords if keyword in text)
        return min(1.0, found_keywords / len(keywords) * 2)

    def _evaluate_accessibility(self, features: list[str]) -> float:
        """Erişilebilirlik özelliklerini değerlendir"""
        if not features:
            return 0.2

        # Temel erişilebilirlik özellikleri
        expected_features = ["altyazi", "transkript", "sesli_betimleme", "buyuk_yazi"]
        found_features = sum(1 for feature in expected_features if feature in features)

        return min(1.0, found_features / len(expected_features))


class EBACurriculumMatcher:
    """EBA TV içeriklerini MEB müfredatı ile eşleştirme sistemi"""

    def __init__(self):
        # MEB müfredat konuları (örnek)
        self.curriculum_topics = {
            EBAGradeLevel.SINIF_8: {
                EBAContentCategory.MATEMATIK: [
                    "Çarpanlar ve Katlar",
                    "Üslü İfadeler",
                    "Kareköklü İfadeler",
                    "Veri Analizi",
                    "Olasılık",
                    "Cebirsel İfadeler",
                    "Eşitsizlikler",
                    "Üçgenler",
                    "Dönüşüm Geometrisi",
                ],
                EBAContentCategory.TURKCE: [
                    "Okuma",
                    "Yazma",
                    "Dinleme",
                    "Konuşma",
                    "Dil Bilgisi",
                    "Edebiyat",
                    "Metin Türleri",
                ],
                EBAContentCategory.FEN_BILIMLERI: [
                    "Madde ve Değişim",
                    "Kuvvet ve Hareket",
                    "Enerji",
                    "Işık ve Ses",
                    "Canlılar ve Yaşam",
                    "Fen ve Mühendislik",
                ],
            },
            EBAGradeLevel.SINIF_12: {
                EBAContentCategory.MATEMATIK: [
                    "Trigonometri",
                    "Logaritma",
                    "Diziler",
                    "Limit ve Süreklilik",
                    "Türev",
                    "İntegral",
                    "Olasılık",
                    "İstatistik",
                ],
                EBAContentCategory.FIZIK: [
                    "Elektrik ve Manyetizma",
                    "Dalgalar",
                    "Modern Fizik",
                    "Optik",
                    "Atom Fiziği",
                ],
                EBAContentCategory.KIMYA: [
                    "Kimyasal Türler Arası Etkileşimler",
                    "Karışımlar",
                    "Kimyasal Tepkimeler",
                    "Enerji Değişimleri",
                ],
            },
        }

    async def match_content_to_curriculum(
        self, metadata: EBAVideoMetadata
    ) -> dict[str, Any]:
        """İçeriği müfredat ile eşleştir"""

        grade_topics = self.curriculum_topics.get(metadata.grade_level, {})
        category_topics = grade_topics.get(metadata.category, [])

        if not category_topics:
            return {"alignment_score": 0.0, "matched_topics": [], "suggestions": []}

        # Başlık ve açıklamada konu anahtar kelimelerini ara
        content_text = f"{metadata.title} {metadata.description}".lower()
        matched_topics = []

        for topic in category_topics:
            topic_keywords = topic.lower().split()
            if any(keyword in content_text for keyword in topic_keywords):
                matched_topics.append(topic)

        alignment_score = len(matched_topics) / len(category_topics)

        # Eksik konular için öneriler
        missing_topics = [
            topic for topic in category_topics if topic not in matched_topics
        ]
        suggestions = missing_topics[:3]  # İlk 3 eksik konu

        return {
            "alignment_score": alignment_score,
            "matched_topics": matched_topics,
            "missing_topics": missing_topics,
            "suggestions": suggestions,
            "curriculum_coverage": f"{len(matched_topics)}/{len(category_topics)}",
        }


class EBAContentCollector:
    """EBA TV içerik toplama sistemi"""

    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.quality_analyzer = EBAContentQualityAnalyzer()
        self.curriculum_matcher = EBACurriculumMatcher()

        # Manuel EBA TV video linkleri (örnek)
        self.manual_video_links = {
            EBAGradeLevel.SINIF_8: {
                EBAContentCategory.MATEMATIK: [
                    {
                        "title": "8. Sınıf Matematik - Çarpanlar ve Katlar (EBOB-EKOK)",
                        "url": "https://www.youtube.com/watch?v=B5zOYfz0-Fw",
                        "description": "8. sınıf matematik dersi - Çarpanlar, Katlar, EBOB ve EKOK konusu detaylı anlatım",
                        "duration": 25,
                        "topics": ["Çarpanlar ve Katlar", "EBOB", "EKOK"],
                    },
                    {
                        "title": "8. Sınıf Matematik - Üslü Sayılar",
                        "url": "https://www.youtube.com/watch?v=hP8ZVjGx0zQ",
                        "description": "Üslü sayılar konusu - Üs kuralları ve işlemler detaylı anlatım",
                        "duration": 30,
                        "topics": ["Üslü İfadeler", "Üs Kuralları"],
                    },
                ],
                EBAContentCategory.TURKCE: [
                    {
                        "title": "TYT Türkçe - Paragraf Anlama ve Çıkarım",
                        "url": "https://www.youtube.com/watch?v=8LwvvFw6Qvg",
                        "description": "TYT Türkçe - Paragraf sorularında anlama ve çıkarım yapma teknikleri",
                        "duration": 20,
                        "topics": ["Okuma", "Anlama", "Çıkarım", "Paragraf"],
                    }
                ],
                EBAContentCategory.SOSYAL_BILGILER: [
                    {
                        "title": "TYT Tarih - Atatürk İlkeleri ve İnkılap Tarihi",
                        "url": "https://www.youtube.com/watch?v=c3T7gGK5qLg",
                        "description": "Atatürk İlkeleri (Altı Ok) ve Türk İnkılap Tarihi - TYT için özel ders",
                        "duration": 35,
                        "topics": [
                            "Atatürk İlkeleri",
                            "İnkılap Tarihi",
                            "TYT",
                            "Altı Ok",
                            "Cumhuriyet",
                        ],
                    }
                ],
            },
            EBAGradeLevel.SINIF_12: {
                EBAContentCategory.MATEMATIK: [
                    {
                        "title": "AYT Matematik - Limit Konu Anlatımı",
                        "url": "https://www.youtube.com/watch?v=iFzJUO5t-MA",
                        "description": "AYT Matematik - Limit konusu detaylı anlatım ve soru çözümü",
                        "duration": 35,
                        "topics": ["Limit", "Süreklilik", "YKS", "AYT"],
                    }
                ],
                EBAContentCategory.FIZIK: [
                    {
                        "title": "AYT Fizik - Elektrik ve Manyetizma Konu Anlatımı",
                        "url": "https://www.youtube.com/watch?v=RjrA4b9lZxo",
                        "description": "AYT Fizik - Elektrik ve Manyetizma konusu detaylı ders anlatımı",
                        "duration": 40,
                        "topics": ["Elektrik", "Manyetizma", "YKS Fizik", "AYT"],
                    }
                ],
                EBAContentCategory.TARIH: [
                    {
                        "title": "TYT Tarih - Atatürk İlkeleri Konu Anlatımı",
                        "url": "https://www.youtube.com/watch?v=c3T7gGK5qLg",
                        "description": "TYT Tarih - Atatürk İlkeleri (6 Ok) ve İnkılap Tarihi detaylı anlatım",
                        "duration": 45,
                        "topics": [
                            "Atatürk İlkeleri",
                            "İnkılap Tarihi",
                            "TYT",
                            "Türk Devrimi",
                            "Altı Ok",
                        ],
                    }
                ],
            },
        }

    async def __aenter__(self):
        """Async context manager giriş"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "EBA-Content-Collector/1.0"},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager çıkış"""
        if self.session:
            await self.session.close()

    async def collect_all_content(self) -> EBAContentCollection:
        """Tüm EBA TV içeriklerini topla"""

        all_videos = []
        categories_count = {}
        grade_levels_count = {}

        for grade_level in EBAGradeLevel:
            for category in EBAContentCategory:
                videos = await self.collect_content_by_category(grade_level, category)
                all_videos.extend(videos)

                # İstatistikleri güncelle
                categories_count[category] = categories_count.get(category, 0) + len(
                    videos
                )
                grade_levels_count[grade_level] = grade_levels_count.get(
                    grade_level, 0
                ) + len(videos)

        # Kalite dağılımı
        quality_distribution = {"high": 0, "medium": 0, "low": 0}
        for video in all_videos:
            if video.quality_score >= 8.0:
                quality_distribution["high"] += 1
            elif video.quality_score >= 6.0:
                quality_distribution["medium"] += 1
            else:
                quality_distribution["low"] += 1

        return EBAContentCollection(
            videos=all_videos,
            total_count=len(all_videos),
            categories=categories_count,
            grade_levels=grade_levels_count,
            quality_distribution=quality_distribution,
            last_updated=datetime.now(),
        )

    async def collect_content_by_category(
        self, grade_level: EBAGradeLevel, category: EBAContentCategory
    ) -> list[EBAVideoMetadata]:
        """Belirli kategori için içerik topla"""

        videos = []

        # Manuel linklerden veri al
        grade_data = self.manual_video_links.get(grade_level, {})
        category_data = grade_data.get(category, [])

        for video_data in category_data:
            try:
                # Video metadata oluştur
                metadata = await self._create_video_metadata(
                    video_data, grade_level, category
                )

                # Kalite analizi yap
                quality_score = await self.quality_analyzer.analyze_video_quality(
                    metadata
                )
                metadata.quality_score = quality_score

                # Müfredat eşleştirmesi yap
                curriculum_alignment = (
                    await self.curriculum_matcher.match_content_to_curriculum(metadata)
                )
                metadata.curriculum_alignment = curriculum_alignment

                videos.append(metadata)

                logger.info(
                    f"EBA video toplandı: {metadata.title} (Kalite: {quality_score:.1f})"
                )

            except Exception as e:
                logger.error(
                    f"EBA video işlenirken hata: {video_data.get('title', 'Unknown')} - {e}"
                )
                continue

        return videos

    async def _create_video_metadata(
        self,
        video_data: dict[str, Any],
        grade_level: EBAGradeLevel,
        category: EBAContentCategory,
    ) -> EBAVideoMetadata:
        """Video metadata oluştur"""

        # Zorluk seviyesini tahmin et
        difficulty = self._estimate_difficulty(
            grade_level, video_data.get("duration", 20)
        )

        # Erişilebilirlik özelliklerini belirle
        accessibility_features = ["altyazi"]  # Temel özellik
        if video_data.get("duration", 0) > 30:
            accessibility_features.append("transkript")

        return EBAVideoMetadata(
            title=video_data["title"],
            description=video_data["description"],
            duration_minutes=video_data["duration"],
            category=category,
            grade_level=grade_level,
            subject_topics=video_data.get("topics", []),
            difficulty_level=difficulty,
            video_url=video_data["url"],
            thumbnail_url=None,  # EBA'dan çekilecek
            transcript=None,  # EBA'dan çekilecek
            quality_score=0.0,  # Analiz sonrası doldurulacak
            curriculum_alignment={},  # Eşleştirme sonrası doldurulacak
            accessibility_features=accessibility_features,
            created_date=datetime.now(),
            last_updated=datetime.now(),
        )

    def _estimate_difficulty(
        self, grade_level: EBAGradeLevel, duration: int
    ) -> DifficultyLevel:
        """Zorluk seviyesini tahmin et"""

        # Sınıf seviyesi bazlı zorluk
        if grade_level in [EBAGradeLevel.SINIF_5, EBAGradeLevel.SINIF_6]:
            base_difficulty = DifficultyLevel.EASY
        elif grade_level in [EBAGradeLevel.SINIF_7, EBAGradeLevel.SINIF_8]:
            base_difficulty = DifficultyLevel.MEDIUM
        else:  # 9-12. sınıflar
            base_difficulty = DifficultyLevel.HARD

        # Video süresi bazlı ayarlama
        if duration > 35:
            # Uzun videolar genelde daha karmaşık
            if base_difficulty == DifficultyLevel.EASY:
                return DifficultyLevel.MEDIUM
            if base_difficulty == DifficultyLevel.MEDIUM:
                return DifficultyLevel.HARD

        return base_difficulty


class EBAtvService:
    """EBA TV İçerik Entegrasyonu Ana Servisi"""

    def __init__(self):
        self.content_collector = EBAContentCollector()
        self.quality_analyzer = EBAContentQualityAnalyzer()
        self.curriculum_matcher = EBACurriculumMatcher()

        # Cache için
        self._content_cache: EBAContentCollection | None = None
        self._cache_expiry: datetime | None = None
        self._cache_duration = timedelta(hours=6)  # 6 saatte bir güncelle

    async def get_all_content(
        self, force_refresh: bool = False
    ) -> EBAContentCollection:
        """Tüm EBA TV içeriklerini getir (cache'li)"""

        # Cache kontrolü
        if (
            not force_refresh
            and self._content_cache
            and self._cache_expiry
            and datetime.now() < self._cache_expiry
        ):
            return self._content_cache

        # İçerikleri topla
        async with self.content_collector as collector:
            content_collection = await collector.collect_all_content()

        # Cache'i güncelle
        self._content_cache = content_collection
        self._cache_expiry = datetime.now() + self._cache_duration

        logger.info(
            f"EBA TV içerikleri güncellendi: {content_collection.total_count} video"
        )

        return content_collection

    async def search_content(
        self,
        query: str,
        grade_level: EBAGradeLevel | None = None,
        category: EBAContentCategory | None = None,
        min_quality: float = 6.0,
    ) -> list[EBAVideoMetadata]:
        """EBA TV içeriklerinde arama yap"""

        content_collection = await self.get_all_content()
        results = []

        query_lower = query.lower()

        for video in content_collection.videos:
            # Kalite filtresi
            if video.quality_score < min_quality:
                continue

            # Sınıf seviyesi filtresi
            if grade_level and video.grade_level != grade_level:
                continue

            # Kategori filtresi
            if category and video.category != category:
                continue

            # Metin araması
            searchable_text = f"{video.title} {video.description} {' '.join(video.subject_topics)}".lower()
            if query_lower in searchable_text:
                results.append(video)

        # Kalite skoruna göre sırala
        results.sort(key=lambda x: x.quality_score, reverse=True)

        return results

    async def get_content_by_curriculum_topic(
        self, grade_level: EBAGradeLevel, category: EBAContentCategory, topic: str
    ) -> list[EBAVideoMetadata]:
        """Müfredat konusuna göre içerik getir"""

        content_collection = await self.get_all_content()
        results = []

        topic_lower = topic.lower()

        for video in content_collection.videos:
            if video.grade_level == grade_level and video.category == category:
                # Konu eşleşmesi kontrol et
                video_topics = [t.lower() for t in video.subject_topics]
                if any(topic_lower in video_topic for video_topic in video_topics):
                    results.append(video)

        # Müfredat uyumu skoruna göre sırala
        results.sort(
            key=lambda x: x.curriculum_alignment.get("alignment_score", 0), reverse=True
        )

        return results

    async def get_recommended_content(
        self,
        student_grade: EBAGradeLevel,
        weak_subjects: list[EBAContentCategory],
        learning_style: str = "visual",
    ) -> list[EBAVideoMetadata]:
        """Öğrenci profiline göre önerilen içerikler"""

        content_collection = await self.get_all_content()
        recommendations = []

        for video in content_collection.videos:
            # Sınıf seviyesi uyumu
            if video.grade_level != student_grade:
                continue

            # Zayıf konulara odaklan
            if video.category in weak_subjects:
                # Görsel öğrenme stili için video süresi tercihi
                if (learning_style == "visual" and video.duration_minutes <= 20) or (learning_style == "auditory" and video.duration_minutes >= 15):
                    recommendations.append(video)
                else:
                    recommendations.append(video)

        # Kalite ve müfredat uyumuna göre sırala
        recommendations.sort(
            key=lambda x: (
                x.quality_score + x.curriculum_alignment.get("alignment_score", 0)
            )
            / 2,
            reverse=True,
        )

        return recommendations[:10]  # En iyi 10 öneri

    async def get_content_statistics(self) -> dict[str, Any]:
        """EBA TV içerik istatistikleri"""

        content_collection = await self.get_all_content()

        # Kategori bazlı istatistikler
        category_stats = {}
        for category in EBAContentCategory:
            category_videos = [
                v for v in content_collection.videos if v.category == category
            ]
            if category_videos:
                avg_quality = sum(v.quality_score for v in category_videos) / len(
                    category_videos
                )
                avg_duration = sum(v.duration_minutes for v in category_videos) / len(
                    category_videos
                )

                category_stats[category.value] = {
                    "video_count": len(category_videos),
                    "avg_quality": round(avg_quality, 2),
                    "avg_duration": round(avg_duration, 1),
                    "grade_distribution": {},
                }

                # Sınıf dağılımı
                for grade in EBAGradeLevel:
                    grade_count = len(
                        [v for v in category_videos if v.grade_level == grade]
                    )
                    if grade_count > 0:
                        category_stats[category.value]["grade_distribution"][
                            grade.value
                        ] = grade_count

        return {
            "total_videos": content_collection.total_count,
            "categories": category_stats,
            "quality_distribution": content_collection.quality_distribution,
            "last_updated": content_collection.last_updated.isoformat(),
            "cache_status": "active" if self._content_cache else "empty",
        }


# Global service instance
ebatv_service = EBAtvService()


async def get_ebatv_service() -> EBAtvService:
    """EBA TV servisini getir"""
    return ebatv_service
