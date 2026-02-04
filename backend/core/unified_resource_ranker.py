"""
Unified Resource Ranking and Filtering System
Teknofest 2025 - Eğitim Eylemci Projesi

Bu modül:
- Multi-platform resource quality assessment
- Student profile-based relevance scoring
- Unified ranking algorithm
- Metadata extraction and enrichment
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceQualityMetric(Enum):
    """Kaynak kalite metrikleri"""

    EDUCATIONAL_VALUE = "educational_value"
    CONTENT_ACCURACY = "content_accuracy"
    PRESENTATION_QUALITY = "presentation_quality"
    ACCESSIBILITY = "accessibility"
    ENGAGEMENT_LEVEL = "engagement_level"
    CURRENCY = "currency"  # Güncellik


@dataclass
class QualityScore:
    """Kalite skoru"""

    overall_score: float  # 0-1 arası genel skor
    metric_scores: dict[ResourceQualityMetric, float]  # Her metrik için skor
    confidence_level: float  # Skorun güvenilirlik seviyesi
    reasoning: list[str]  # Skor gerekçeleri


@dataclass
class RelevanceScore:
    """İlgililik skoru"""

    topic_relevance: float  # Konu ile ilgililik
    level_appropriateness: float  # Seviye uygunluğu
    style_match: float  # Öğrenme stili uyumu
    goal_alignment: float  # Hedef uyumu
    overall_relevance: float  # Genel ilgililik
    reasoning: list[str]


@dataclass
class UnifiedResourceScore:
    """Birleşik kaynak skoru"""

    resource_id: str
    quality_score: QualityScore
    relevance_score: RelevanceScore
    final_score: float  # 0-1 arası final skor
    ranking_position: int
    recommendation_strength: str  # "excellent", "good", "moderate", "low"
    metadata_enriched: dict[str, Any]


class UnifiedResourceRanker:
    """Birleşik Kaynak Sıralama Sistemi"""

    def __init__(self):
        self.platform_weights = self._load_platform_weights()
        self.quality_weights = self._load_quality_weights()
        self.content_type_scores = self._load_content_type_scores()
        self.accessibility_features = self._load_accessibility_features()

    def _load_platform_weights(self) -> dict[str, float]:
        """Platform güvenilirlik ağırlıkları"""
        return {
            "Khan Academy": 1.0,
            "MIT OpenCourseWare": 1.0,
            "TED-Ed": 0.95,
            "YouTube": 0.7,  # Kanal kalitesine bağlı
            "OER Commons": 0.85,
            "Wikipedia": 0.8,
            "internal": 0.9,  # RAG içeriği
            "Coursera": 0.9,
            "edX": 0.9,
            "BTK Akademi": 0.95,
            "EBA": 0.9,
        }

    def _load_quality_weights(self) -> dict[ResourceQualityMetric, float]:
        """Kalite metrik ağırlıkları"""
        return {
            ResourceQualityMetric.EDUCATIONAL_VALUE: 0.3,
            ResourceQualityMetric.CONTENT_ACCURACY: 0.25,
            ResourceQualityMetric.PRESENTATION_QUALITY: 0.15,
            ResourceQualityMetric.ACCESSIBILITY: 0.15,
            ResourceQualityMetric.ENGAGEMENT_LEVEL: 0.1,
            ResourceQualityMetric.CURRENCY: 0.05,
        }

    def _load_content_type_scores(self) -> dict[str, float]:
        """İçerik türü temel skorları"""
        return {
            "course": 0.95,  # Yapılandırılmış kurslar
            "lesson": 0.9,  # Dersler
            "video": 0.85,  # Videolar
            "article": 0.8,  # Makaleler
            "interactive": 0.9,  # Etkileşimli içerik
            "quiz": 0.75,  # Quizler
            "exercise": 0.8,  # Alıştırmalar
            "simulation": 0.85,  # Simülasyonlar
            "book": 0.8,  # Kitaplar
            "pdf": 0.7,  # PDF'ler
            "audio": 0.75,  # Ses dosyaları
            "podcast": 0.8,  # Podcastler
        }

    def _load_accessibility_features(self) -> list[str]:
        """Erişilebilirlik özellikleri"""
        return [
            "captions_available",
            "transcript_available",
            "screen_reader_compatible",
            "keyboard_navigable",
            "high_contrast_available",
            "adjustable_font_size",
            "audio_description",
            "sign_language_interpretation",
        ]

    async def rank_resources(
        self,
        resources: list[dict[str, Any]],
        student_profile: dict[str, Any] | None = None,
        topic: str | None = None,
        learning_goals: list[str] | None = None,
    ) -> list[UnifiedResourceScore]:
        """
        Kaynakları birleşik algoritma ile sırala

        Args:
            resources: Kaynak listesi
            student_profile: Öğrenci profili
            topic: Hedef konu
            learning_goals: Öğrenme hedefleri

        Returns:
            Sıralanmış kaynak skorları
        """
        try:
            scored_resources = []

            for resource in resources:
                # Kalite skorunu hesapla
                quality_score = await self._calculate_quality_score(resource)

                # İlgililik skorunu hesapla
                relevance_score = await self._calculate_relevance_score(
                    resource, student_profile, topic, learning_goals
                )

                # Final skoru hesapla
                final_score = self._calculate_final_score(
                    quality_score, relevance_score
                )

                # Metadata'yı zenginleştir
                enriched_metadata = await self._enrich_metadata(resource)

                # Öneri gücünü belirle
                recommendation_strength = self._determine_recommendation_strength(
                    final_score
                )

                scored_resource = UnifiedResourceScore(
                    resource_id=resource.get("resource_id", "unknown"),
                    quality_score=quality_score,
                    relevance_score=relevance_score,
                    final_score=final_score,
                    ranking_position=0,  # Sonra güncellenecek
                    recommendation_strength=recommendation_strength,
                    metadata_enriched=enriched_metadata,
                )

                scored_resources.append(scored_resource)

            # Final skora göre sırala
            scored_resources.sort(key=lambda x: x.final_score, reverse=True)

            # Sıralama pozisyonlarını güncelle
            for i, scored_resource in enumerate(scored_resources):
                scored_resource.ranking_position = i + 1

            logger.info(
                f"Ranked {len(scored_resources)} resources using unified algorithm"
            )
            return scored_resources

        except Exception as e:
            logger.error(f"Rank resources error: {e!s}")
            return []

    async def _calculate_quality_score(self, resource: dict[str, Any]) -> QualityScore:
        """Kaynak kalite skorunu hesapla"""
        try:
            metric_scores = {}
            reasoning = []

            # Platform güvenilirliği
            platform = resource.get("source", "unknown")
            platform_weight = self.platform_weights.get(platform, 0.5)

            # Eğitim değeri
            educational_value = self._assess_educational_value(resource)
            metric_scores[ResourceQualityMetric.EDUCATIONAL_VALUE] = educational_value
            if educational_value > 0.8:
                reasoning.append(f"Yüksek eğitim değeri ({educational_value:.2f})")

            # İçerik doğruluğu (platform ve metadata'ya dayalı)
            content_accuracy = self._assess_content_accuracy(resource, platform_weight)
            metric_scores[ResourceQualityMetric.CONTENT_ACCURACY] = content_accuracy
            if content_accuracy > 0.9:
                reasoning.append(f"Güvenilir platform ({platform})")

            # Sunum kalitesi
            presentation_quality = self._assess_presentation_quality(resource)
            metric_scores[
                ResourceQualityMetric.PRESENTATION_QUALITY
            ] = presentation_quality

            # Erişilebilirlik
            accessibility = self._assess_accessibility(resource)
            metric_scores[ResourceQualityMetric.ACCESSIBILITY] = accessibility
            if accessibility > 0.7:
                reasoning.append("İyi erişilebilirlik özellikleri")

            # Etkileşim seviyesi
            engagement_level = self._assess_engagement_level(resource)
            metric_scores[ResourceQualityMetric.ENGAGEMENT_LEVEL] = engagement_level

            # Güncellik
            currency = self._assess_currency(resource)
            metric_scores[ResourceQualityMetric.CURRENCY] = currency

            # Genel skoru hesapla
            overall_score = sum(
                score * self.quality_weights[metric]
                for metric, score in metric_scores.items()
            )

            # Güven seviyesi
            confidence_level = min(platform_weight + 0.2, 1.0)

            return QualityScore(
                overall_score=overall_score,
                metric_scores=metric_scores,
                confidence_level=confidence_level,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Calculate quality score error: {e!s}")
            return QualityScore(0.5, {}, 0.5, ["Hata nedeniyle varsayılan skor"])

    def _assess_educational_value(self, resource: dict[str, Any]) -> float:
        """Eğitim değerini değerlendir"""
        score = 0.5  # Başlangıç skoru

        # İçerik türü
        content_type = resource.get("content_type", "unknown")
        type_score = self.content_type_scores.get(content_type, 0.5)
        score = (score + type_score) / 2

        # Başlık ve açıklama analizi
        title = resource.get("title", "").lower()
        description = resource.get("description", "").lower()

        # Eğitim anahtar kelimeleri
        educational_keywords = [
            "ders",
            "öğren",
            "eğitim",
            "kurs",
            "tutorial",
            "guide",
            "lesson",
            "learn",
            "education",
            "course",
            "study",
            "practice",
            "exercise",
        ]

        keyword_count = sum(
            1
            for keyword in educational_keywords
            if keyword in title or keyword in description
        )

        if keyword_count > 0:
            score += min(keyword_count * 0.1, 0.3)

        # Rating varsa kullan
        rating = resource.get("rating")
        if rating and rating > 0:
            score = (score + (rating / 5.0)) / 2

        return min(score, 1.0)

    def _assess_content_accuracy(
        self, resource: dict[str, Any], platform_weight: float
    ) -> float:
        """İçerik doğruluğunu değerlendir"""
        # Platform güvenilirliği temel skor
        score = platform_weight

        # Yazar/kurum bilgisi varsa bonus
        author = resource.get("metadata", {}).get("author")
        institution = resource.get("metadata", {}).get("institution")

        if author or institution:
            score += 0.1

        # Güncellenme tarihi varsa bonus
        last_updated = resource.get("metadata", {}).get("last_updated")
        if last_updated:
            score += 0.05

        return min(score, 1.0)

    def _assess_presentation_quality(self, resource: dict[str, Any]) -> float:
        """Sunum kalitesini değerlendir"""
        score = 0.6  # Başlangıç skoru

        # Thumbnail varsa bonus
        if resource.get("metadata", {}).get("thumbnail_url"):
            score += 0.1

        # Video için view count
        view_count = resource.get("metadata", {}).get("view_count", 0)
        if view_count > 1000:
            score += 0.1
        if view_count > 10000:
            score += 0.1

        # Açıklama kalitesi
        description = resource.get("description", "")
        if len(description) > 100:  # Detaylı açıklama
            score += 0.1

        return min(score, 1.0)

    def _assess_accessibility(self, resource: dict[str, Any]) -> float:
        """Erişilebilirliği değerlendir"""
        score = 0.3  # Temel skor
        metadata = resource.get("metadata", {})

        # Erişilebilirlik özelliklerini kontrol et
        for feature in self.accessibility_features:
            if metadata.get(feature, False):
                score += 0.1

        # Dil desteği
        language = resource.get("language", "")
        if language == "tr":  # Türkçe içerik
            score += 0.1

        return min(score, 1.0)

    def _assess_engagement_level(self, resource: dict[str, Any]) -> float:
        """Etkileşim seviyesini değerlendir"""
        score = 0.5

        content_type = resource.get("content_type", "")

        # Etkileşimli içerik türleri
        if content_type in ["interactive", "simulation", "quiz", "exercise"]:
            score += 0.3
        elif content_type in ["video", "course"]:
            score += 0.2

        # Like/view oranı (YouTube için)
        like_count = resource.get("metadata", {}).get("like_count", 0)
        view_count = resource.get("metadata", {}).get("view_count", 0)

        if view_count > 0 and like_count > 0:
            like_ratio = like_count / view_count
            if like_ratio > 0.01:  # %1'den fazla like oranı
                score += 0.1

        return min(score, 1.0)

    def _assess_currency(self, resource: dict[str, Any]) -> float:
        """Güncelliği değerlendir"""
        score = 0.5

        # Yayın tarihi
        published_at = resource.get("metadata", {}).get("published_at")
        if published_at:
            try:
                pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                days_old = (datetime.now() - pub_date.replace(tzinfo=None)).days

                if days_old < 365:  # 1 yıldan yeni
                    score = 1.0
                elif days_old < 365 * 2:  # 2 yıldan yeni
                    score = 0.8
                elif days_old < 365 * 5:  # 5 yıldan yeni
                    score = 0.6
                else:
                    score = 0.4
            except:
                pass

        return score

    async def _calculate_relevance_score(
        self,
        resource: dict[str, Any],
        student_profile: dict[str, Any] | None,
        topic: str | None,
        learning_goals: list[str] | None,
    ) -> RelevanceScore:
        """İlgililik skorunu hesapla"""
        try:
            reasoning = []

            # Konu ile ilgililik
            topic_relevance = self._calculate_topic_relevance(resource, topic)
            if topic_relevance > 0.8:
                reasoning.append(f"Konu ile yüksek ilgililik ({topic_relevance:.2f})")

            # Seviye uygunluğu
            level_appropriateness = self._calculate_level_appropriateness(
                resource, student_profile
            )
            if level_appropriateness > 0.8:
                reasoning.append("Öğrenci seviyesine uygun")

            # Öğrenme stili uyumu
            style_match = self._calculate_style_match(resource, student_profile)
            if style_match > 0.7:
                reasoning.append("Öğrenme stili ile uyumlu")

            # Hedef uyumu
            goal_alignment = self._calculate_goal_alignment(resource, learning_goals)
            if goal_alignment > 0.7:
                reasoning.append("Öğrenme hedefleri ile uyumlu")

            # Genel ilgililik
            overall_relevance = (
                topic_relevance * 0.4
                + level_appropriateness * 0.3
                + style_match * 0.2
                + goal_alignment * 0.1
            )

            return RelevanceScore(
                topic_relevance=topic_relevance,
                level_appropriateness=level_appropriateness,
                style_match=style_match,
                goal_alignment=goal_alignment,
                overall_relevance=overall_relevance,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Calculate relevance score error: {e!s}")
            return RelevanceScore(
                0.5, 0.5, 0.5, 0.5, 0.5, ["Hata nedeniyle varsayılan skor"]
            )

    def _calculate_topic_relevance(
        self, resource: dict[str, Any], topic: str | None
    ) -> float:
        """Konu ile ilgililik hesapla"""
        if not topic:
            return 0.5

        topic_lower = topic.lower()
        title = resource.get("title", "").lower()
        description = resource.get("description", "").lower()
        tags = [tag.lower() for tag in resource.get("tags", [])]

        # Başlıkta geçiyor mu?
        if topic_lower in title:
            return 1.0

        # Açıklamada geçiyor mu?
        if topic_lower in description:
            return 0.8

        # Tag'lerde geçiyor mu?
        if any(topic_lower in tag for tag in tags):
            return 0.7

        # Kısmi eşleşme
        topic_words = topic_lower.split()
        title_words = title.split()

        matches = sum(1 for word in topic_words if word in title_words)
        if matches > 0:
            return 0.5 + (matches / len(topic_words)) * 0.3

        return 0.3

    def _calculate_level_appropriateness(
        self, resource: dict[str, Any], student_profile: dict[str, Any] | None
    ) -> float:
        """Seviye uygunluğu hesapla"""
        if not student_profile:
            return 0.7  # Varsayılan uygun

        student_level = student_profile.get("knowledge_level", "intermediate")
        resource_level = resource.get("difficulty_level", "medium")

        # Seviye eşleştirmesi
        level_mapping = {
            "beginner": 1,
            "very_easy": 1,
            "easy": 2,
            "elementary": 2,
            "medium": 3,
            "intermediate": 3,
            "advanced": 4,
            "hard": 4,
            "expert": 5,
            "very_hard": 5,
        }

        student_num = level_mapping.get(student_level, 3)
        resource_num = level_mapping.get(resource_level, 3)

        # Seviye farkı
        diff = abs(student_num - resource_num)

        if diff == 0:
            return 1.0  # Tam uyum
        if diff == 1:
            return 0.8  # Yakın seviye
        if diff == 2:
            return 0.5  # Orta uyum
        return 0.3  # Zayıf uyum

    def _calculate_style_match(
        self, resource: dict[str, Any], student_profile: dict[str, Any] | None
    ) -> float:
        """Öğrenme stili uyumu hesapla"""
        if not student_profile:
            return 0.6

        student_style = student_profile.get("learning_style", "mixed")
        content_type = resource.get("content_type", "unknown")

        # İçerik türü - öğrenme stili eşleştirmesi
        style_mapping = {
            "visual": ["video", "animation", "infographic", "image", "diagram"],
            "auditory": ["audio", "podcast", "lecture", "music"],
            "reading": ["article", "text", "book", "pdf", "blog", "course"],
            "kinesthetic": ["interactive", "simulation", "project", "quiz", "exercise"],
            "mixed": ["video", "article", "interactive", "quiz"],
        }

        preferred_types = style_mapping.get(student_style, [])

        if content_type in preferred_types:
            return 1.0
        if student_style == "mixed":
            return 0.8
        return 0.4

    def _calculate_goal_alignment(
        self, resource: dict[str, Any], learning_goals: list[str] | None
    ) -> float:
        """Hedef uyumu hesapla"""
        if not learning_goals:
            return 0.6

        title = resource.get("title", "").lower()
        description = resource.get("description", "").lower()
        tags = [tag.lower() for tag in resource.get("tags", [])]

        total_alignment = 0
        for goal in learning_goals:
            goal_lower = goal.lower()

            if goal_lower in title or goal_lower in description:
                total_alignment += 1.0
            elif any(goal_lower in tag for tag in tags):
                total_alignment += 0.7
            else:
                # Kısmi eşleşme kontrolü
                goal_words = goal_lower.split()
                if any(word in title or word in description for word in goal_words):
                    total_alignment += 0.3

        return min(total_alignment / len(learning_goals), 1.0)

    def _calculate_final_score(
        self, quality_score: QualityScore, relevance_score: RelevanceScore
    ) -> float:
        """Final skoru hesapla"""
        # Kalite ve ilgililik ağırlıkları
        quality_weight = 0.6
        relevance_weight = 0.4

        final_score = (
            quality_score.overall_score * quality_weight
            + relevance_score.overall_relevance * relevance_weight
        )

        # Güven seviyesi ile ağırlıklandır
        confidence_adjusted = final_score * quality_score.confidence_level

        return min(confidence_adjusted, 1.0)

    async def _enrich_metadata(self, resource: dict[str, Any]) -> dict[str, Any]:
        """Metadata'yı zenginleştir"""
        enriched = resource.get("metadata", {}).copy()

        # Süre tahmini
        if "estimated_time" not in enriched:
            enriched["estimated_time"] = self._estimate_duration(resource)

        # Zorluk seviyesi tahmini
        if "difficulty_level" not in enriched:
            enriched["difficulty_level"] = self._estimate_difficulty(resource)

        # Erişilebilirlik özellikleri
        enriched["accessibility_features"] = self._extract_accessibility_features(
            resource
        )

        # İçerik kategorisi
        enriched["content_category"] = self._categorize_content(resource)

        return enriched

    def _estimate_duration(self, resource: dict[str, Any]) -> int:
        """Süre tahmini (dakika)"""
        content_type = resource.get("content_type", "")

        # İçerik türüne göre varsayılan süreler
        default_durations = {
            "video": 15,
            "article": 10,
            "course": 60,
            "lesson": 30,
            "quiz": 5,
            "exercise": 20,
            "interactive": 25,
            "book": 120,
            "pdf": 15,
        }

        return default_durations.get(content_type, 15)

    def _estimate_difficulty(self, resource: dict[str, Any]) -> str:
        """Zorluk seviyesi tahmini"""
        title = resource.get("title", "").lower()
        description = resource.get("description", "").lower()

        # Zorluk belirten anahtar kelimeler
        if any(
            word in title or word in description
            for word in ["basic", "temel", "başlangıç", "giriş"]
        ):
            return "easy"
        if any(
            word in title or word in description
            for word in ["advanced", "ileri", "uzman", "expert"]
        ):
            return "hard"
        return "medium"

    def _extract_accessibility_features(self, resource: dict[str, Any]) -> list[str]:
        """Erişilebilirlik özelliklerini çıkar"""
        features = []
        metadata = resource.get("metadata", {})

        # Mevcut özellikleri kontrol et
        for feature in self.accessibility_features:
            if metadata.get(feature, False):
                features.append(feature)

        # İçerik türüne göre varsayılan özellikler
        content_type = resource.get("content_type", "")
        if content_type == "video":
            features.extend(["captions_available", "transcript_available"])
        elif content_type in ["article", "text", "pdf"]:
            features.extend(["screen_reader_compatible", "adjustable_font_size"])

        return list(set(features))  # Tekrarları kaldır

    def _categorize_content(self, resource: dict[str, Any]) -> str:
        """İçerik kategorisi belirle"""
        content_type = resource.get("content_type", "")

        categories = {
            "video": "multimedia",
            "audio": "multimedia",
            "article": "text_based",
            "book": "text_based",
            "pdf": "text_based",
            "interactive": "hands_on",
            "simulation": "hands_on",
            "quiz": "assessment",
            "exercise": "practice",
            "course": "structured_learning",
        }

        return categories.get(content_type, "general")

    def _determine_recommendation_strength(self, final_score: float) -> str:
        """Öneri gücünü belirle"""
        if final_score >= 0.8:
            return "excellent"
        if final_score >= 0.6:
            return "good"
        if final_score >= 0.4:
            return "moderate"
        return "low"


# Singleton instance
unified_resource_ranker = UnifiedResourceRanker()
