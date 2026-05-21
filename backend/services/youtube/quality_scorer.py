"""
YouTube Video Kalite Puanlama Mixin

DEPRECATED: Use quality.py QualityScorer for standalone usage.
This mixin is kept for backward compatibility with YouTubeDiscovery.
"""

import json
import logging
from typing import TYPE_CHECKING

import aiohttp

from core.turkish_nlp_utils import normalize_tr

from .models import DifficultyLevel, ExamType, SubjectType

if TYPE_CHECKING:
    from .discovery import YouTubeDiscovery

logger = logging.getLogger(__name__)


class QualityScorerMixin:
    """Video kalite puanlama mixin'i"""

    # Type hints for mixin attributes
    trusted_channels: dict[str, list]

    def _calculate_quality_score_fast(
        self: "YouTubeDiscovery",
        video_data: dict,
        subject: SubjectType,
        exam_type: ExamType,
    ) -> float:
        """Hizli kalite puani hesaplama (performance optimized)"""
        score = 5.0  # Base score

        title_lower = normalize_tr(video_data["title"])

        # Hizli baslik kontrolu
        if subject.value in title_lower:
            score += 2.0
        if normalize_tr(exam_type.value) in title_lower:
            score += 2.0
        if any(
            keyword in title_lower
            for keyword in ["konu anlatim", "ders", "2025", "2024"]
        ):
            score += 1.0

        # Hizli kanal kontrolu
        channel_lower = normalize_tr(video_data["channel"])
        if any(
            keyword in channel_lower for keyword in ["ogretmen", "akademi", "egitim"]
        ):
            score += 1.0

        return min(score, 10.0)

    def _calculate_quality_score(
        self: "YouTubeDiscovery",
        video_data: dict,
        subject: SubjectType,
        exam_type: ExamType,
    ) -> float:
        """Video kalite puani hesapla"""
        score = 0.0

        # Kanal guvenilirligi (40% agirlik)
        channel_score = self._get_channel_quality(video_data["channel"], subject)
        score += channel_score * 0.4

        # Baslik relevansi (25% agirlik)
        title_score = self._calculate_title_relevance(
            video_data["title"], subject, exam_type
        )
        score += title_score * 0.25

        # View count normalized (15% agirlik)
        view_score = (
            min(video_data["view_count"] / 100000, 10) / 10
        )  # 100k+ view = max score
        score += view_score * 0.15

        # Video suresi (10% agirlik)
        duration_score = self._calculate_duration_score(video_data["duration"])
        score += duration_score * 0.10

        # Upload date (10% agirlik)
        date_score = self._calculate_date_score(video_data["upload_date"])
        score += date_score * 0.10

        return min(score, 10.0)  # Maksimum 10 puan

    def _get_channel_quality(
        self: "YouTubeDiscovery", channel_name: str, subject: SubjectType
    ) -> float:
        """Kanal kalite puani al"""
        subject_channels = self.trusted_channels.get(subject.value, [])

        channel_name_lower = normalize_tr(channel_name)
        for channel in subject_channels:
            if normalize_tr(channel["name"]) in channel_name_lower:
                return channel["quality"]

        # Genel egitim kanali kontrolu (ASCII-only keywords, normalize_tr handles any Turkish in channel_name)
        educational_keywords = ["ogretmen", "akademi", "egitim", "ders", "kurs", "okul"]
        for keyword in educational_keywords:
            if keyword in channel_name_lower:
                return 7.0

        return 5.0  # Varsayilan puan

    def _calculate_title_relevance(
        self: "YouTubeDiscovery",
        title: str,
        subject: SubjectType,
        exam_type: ExamType,
    ) -> float:
        """Baslik relevans puani"""
        title_lower = normalize_tr(title)
        score = 0.0

        # Konu adi varligi
        if subject.value in title_lower:
            score += 3.0

        # Sinav turu varligi
        if normalize_tr(exam_type.value) in title_lower:
            score += 3.0

        # Egitim anahtar kelimeleri
        edu_keywords = [
            "konu anlatimi",
            "ders",
            "ogretim",
            "anlatim",
            "hazirlik",
            "cozum",
        ]
        for keyword in edu_keywords:
            if keyword in title_lower:
                score += 1.0
                break

        # Yil varligi (guncellik)
        if "2025" in title_lower or "2024" in title_lower:
            score += 1.0

        # Turkce oldugunu gosteren isaretler
        turkish_indicators = ["turkce", "tr", "turkish"]
        for indicator in turkish_indicators:
            if indicator in title_lower:
                score += 1.0
                break

        return min(score, 10.0)

    def _calculate_duration_score(self: "YouTubeDiscovery", duration: str) -> float:
        """Video sure puani"""
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

            # Ideal sure 10-45 dakika arasi
            if 600 <= total_seconds <= 2700:  # 10-45 dakika
                return 10.0
            if 300 <= total_seconds <= 3600:  # 5-60 dakika
                return 8.0
            if total_seconds <= 300:  # Cok kisa
                return 6.0
            # Cok uzun
            return 7.0

        except ValueError:
            return 5.0

    def _calculate_date_score(self: "YouTubeDiscovery", upload_date: str) -> float:
        """Upload tarihi puani"""
        if not upload_date:
            return 5.0

        # Guncellik puani - yil bazli degerlendirme
        if "2025" in upload_date or "2024" in upload_date:
            return 10.0
        if "2023" in upload_date:
            return 8.0
        if "2022" in upload_date:
            return 6.0
        return 4.0

    async def _calculate_dynamic_quality_score(
        self: "YouTubeDiscovery",
        video_data: dict,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        student_level: int = 5,
    ) -> float:
        """Ogrenci seviyesine gore dinamik kalite puani hesaplama"""

        # Temel kalite puani
        base_score = self._calculate_quality_score(video_data, subject, exam_type)

        # LLM analizi ile gelismis scoring
        llm_analysis = await self._analyze_video_with_llm(
            video_data, subject, difficulty, exam_type
        )

        # Ogrenci seviyesine gore adaptasyon
        level_factor = 1.0
        if student_level <= 3:  # Baslangic seviye
            if difficulty == DifficultyLevel.BASLANGIC:
                level_factor = 1.3  # Baslangic videolari tercih et
            elif difficulty == DifficultyLevel.ILERI:
                level_factor = 0.7  # Ileri videolari cezalandir
        elif student_level >= 8:  # Ileri seviye
            if difficulty == DifficultyLevel.ILERI:
                level_factor = 1.2  # Ileri videolari tercih et
            elif difficulty == DifficultyLevel.BASLANGIC:
                level_factor = 0.8  # Baslangic videolari azalt

        # LLM skorlarini entegre et
        relevance_score = llm_analysis.get("relevance_score", 7.0)
        educational_quality = llm_analysis.get("educational_quality", 8.0)
        level_appropriateness = llm_analysis.get("level_appropriateness", 8.0)
        turkish_content = llm_analysis.get("turkish_content", True)

        # Final score calculation
        final_score = (
            base_score * 0.3
            + relevance_score * 0.25  # %30 temel score
            + educational_quality * 0.25  # %25 LLM relevance
            + level_appropriateness * 0.2  # %25 egitim kalitesi  # %20 seviye uygunlugu
        ) * level_factor

        # Turkce icerik bonusu
        if turkish_content:
            final_score *= 1.1

        return min(final_score, 10.0)

    async def _analyze_video_with_llm(
        self: "YouTubeDiscovery",
        video_data: dict,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
    ) -> dict:
        """LLM ile video icerigi analizi"""
        try:
            import os

            # Hugging Face endpoint URL
            hf_endpoint = os.environ.get(
                "HF_INFERENCE_ENDPOINT",
                "https://cf781mfqobm2ynkk.us-east-1.aws.endpoints.huggingface.cloud",
            )

            # Video basligi ve aciklamasi
            title = video_data.get("title", "")
            description = video_data.get("description", "")
            channel = video_data.get("channel", "")

            # LLM prompt
            prompt = f"""Asagidaki YouTube videosunu analiz et:

Baslik: {title}
Kanal: {channel}
Aciklama: {description[:300]}

Hedef: {exam_type.value} {subject.value} {difficulty.value} seviye

Bu videoyu su kriterlere gore degerlendir:
1. Icerik uygunlugu (0-10): Hedef konu ve seviyeye uygunluk
2. Turkce icerik: Icerik Turkce mi?
3. Egitim kalitesi (0-10): Ogretici deger
4. Seviye uygunlugu (0-10): Hedef zorluk seviyesine uygunluk

Sadece asagidaki JSON formatinda cevap ver:
{{"relevance_score": 8.5, "turkish_content": true, "educational_quality": 9.0, "level_appropriateness": 8.0}}"""

            # Hugging Face API cagrisi
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

                        # JSON kismini cikar
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
                                logger.warning(f"LLM JSON parse hatasi: {json_str}")
                    else:
                        logger.warning(f"HF API hatasi: {response.status}")

            # Fallback degerler
            return {
                "relevance_score": 7.0,
                "turkish_content": True,
                "educational_quality": 8.0,
                "level_appropriateness": 8.0,
            }

        except Exception as e:
            logger.error(f"LLM analizi hatasi: {e}", exc_info=True)
            return {
                "relevance_score": 7.0,
                "turkish_content": True,
                "educational_quality": 8.0,
            }
