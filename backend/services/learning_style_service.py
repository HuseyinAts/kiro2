"""
Hibrit Öğrenme Stili Servisi - Database Integration
VARK + Felder-Silverman hibrit öğrenme stili tespiti
REFACTORED: Mock data removed, replaced with real behavioral analysis
Part of Mock Data Cleanup - Phase 4
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import cache_manager
from models import ExamSession, LearningAnalytics, StudentLearningProfile
from models.learning_style import ContentRecommendation

logger = logging.getLogger(__name__)


class LearningStyleService:
    """
    Hibrit öğrenme stili servisi
    VARK + Felder-Silverman = 64 farklı öğrenme profili

    REFACTORED (2025-11-17):
    - Removed self.student_profiles in-memory dictionary
    - All data now persisted in student_learning_profiles table
    - Real behavioral analysis replaces hardcoded scores
    - Dependency injection: db: AsyncSession parameter
    """

    def __init__(self):
        """Servisi başlat"""
        # VARK boyutları
        self.vark_dimensions = ["visual", "auditory", "reading", "kinesthetic"]

        # Felder-Silverman boyutları
        self.felder_dimensions = [
            "active_reflective",
            "sensing_intuitive",
            "visual_verbal",
            "sequential_global",
        ]

    async def detect_learning_style(
        self,
        student_id: str,
        db: AsyncSession,
        behavioral_data: dict[str, Any],
        questionnaire_responses: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Hibrit öğrenme stilini tespit et

        REFACTORED: Real behavioral analysis + database persistence
        - Calculates VARK scores from actual student behavior
        - Calculates Felder-Silverman scores from learning patterns
        - Saves to database instead of in-memory dict
        """
        try:
            # Cache kontrolü
            cache_key = f"learning_style:{student_id}"
            cached_profile = await cache_manager.get(cache_key)
            if cached_profile:
                logger.info(f"Cache hit: {student_id}")
                return cached_profile

            logger.info(f"Cache miss: {student_id} - analyzing behavioral data")

            # Check if profile exists in database
            result = await db.execute(
                select(StudentLearningProfile).where(
                    StudentLearningProfile.student_id == student_id
                )
            )
            existing_profile = result.scalar_one_or_none()

            # If profile exists and is recent (< 30 days), return it
            if existing_profile and not existing_profile.needs_update:
                profile_dict = self._profile_to_dict(existing_profile)
                await cache_manager.set(cache_key, profile_dict, ttl=3600)
                return profile_dict

            # Calculate VARK profile from behavioral data
            vark_profile = await self._calculate_vark_profile(
                student_id, db, behavioral_data
            )

            # Calculate Felder-Silverman profile from behavioral data
            felder_profile = await self._calculate_felder_profile(
                student_id, db, behavioral_data
            )

            # Calculate confidence score based on data availability
            confidence_score = self._calculate_confidence(
                behavioral_data, questionnaire_responses
            )

            # Generate hybrid code
            hibrit_kod = self._generate_hibrit_code(vark_profile, felder_profile)

            # Determine dominant styles
            dominant_vark = max(vark_profile, key=vark_profile.get)
            dominant_felder = max(felder_profile, key=lambda k: abs(felder_profile[k]))

            # Profile description
            profile_description = self._get_profile_description(hibrit_kod)

            # Save or update profile in database
            if existing_profile:
                # Update existing profile
                existing_profile.vark_visual = vark_profile["visual"]
                existing_profile.vark_auditory = vark_profile["auditory"]
                existing_profile.vark_reading = vark_profile["reading"]
                existing_profile.vark_kinesthetic = vark_profile["kinesthetic"]
                existing_profile.felder_active_reflective = felder_profile[
                    "active_reflective"
                ]
                existing_profile.felder_sensing_intuitive = felder_profile[
                    "sensing_intuitive"
                ]
                existing_profile.felder_visual_verbal = felder_profile["visual_verbal"]
                existing_profile.felder_sequential_global = felder_profile[
                    "sequential_global"
                ]
                existing_profile.hybrid_code = hibrit_kod
                existing_profile.dominant_vark_style = dominant_vark
                existing_profile.dominant_felder_dimension = dominant_felder
                existing_profile.confidence_score = confidence_score
                existing_profile.profile_description = profile_description
                existing_profile.behavioral_data_snapshot = str(behavioral_data)
                existing_profile.questionnaire_responses = (
                    str(questionnaire_responses) if questionnaire_responses else None
                )
                existing_profile.updated_at = datetime.now(UTC)

                await db.commit()
                await db.refresh(existing_profile)
                profile = existing_profile
            else:
                # Create new profile
                new_profile = StudentLearningProfile(
                    id=f"lp_{uuid.uuid4().hex[:12]}",
                    student_id=student_id,
                    vark_visual=vark_profile["visual"],
                    vark_auditory=vark_profile["auditory"],
                    vark_reading=vark_profile["reading"],
                    vark_kinesthetic=vark_profile["kinesthetic"],
                    felder_active_reflective=felder_profile["active_reflective"],
                    felder_sensing_intuitive=felder_profile["sensing_intuitive"],
                    felder_visual_verbal=felder_profile["visual_verbal"],
                    felder_sequential_global=felder_profile["sequential_global"],
                    hybrid_code=hibrit_kod,
                    dominant_vark_style=dominant_vark,
                    dominant_felder_dimension=dominant_felder,
                    confidence_score=confidence_score,
                    profile_description=profile_description,
                    behavioral_data_snapshot=str(behavioral_data),
                    questionnaire_responses=str(questionnaire_responses)
                    if questionnaire_responses
                    else None,
                )

                db.add(new_profile)
                await db.commit()
                await db.refresh(new_profile)
                profile = new_profile

            # Convert to dict for response
            hibrit_profil = self._profile_to_dict(profile)

            # Cache'e kaydet (1 saat TTL)
            await cache_manager.set(cache_key, hibrit_profil, ttl=3600)
            logger.info(
                f"Profile saved to database: {student_id} -> {hibrit_kod} (confidence: {confidence_score:.2f})"
            )

            return hibrit_profil

        except Exception as e:
            logger.error(
                f"Öğrenme stili tespit hatası - Öğrenci: {student_id}, Hata: {e!s}"
            )
            raise

    async def _calculate_vark_profile(
        self, student_id: str, db: AsyncSession, behavioral_data: dict[str, Any]
    ) -> dict[str, float]:
        """
        Calculate VARK profile from real behavioral data

        REFACTORED: Real calculations based on student behavior
        - Visual: Video watch time, image interactions
        - Auditory: Audio content consumption
        - Reading: Text reading time, note-taking
        - Kinesthetic: Interactive exercises, hands-on activities
        """
        # Get learning analytics data
        result = await db.execute(
            select(LearningAnalytics).where(LearningAnalytics.student_id == student_id)
        )
        analytics = result.scalars().all()

        # Initialize scores
        vark_scores = {
            "visual": 0.0,
            "auditory": 0.0,
            "reading": 0.0,
            "kinesthetic": 0.0,
        }

        if not analytics:
            # No data yet - use neutral profile
            return {
                "visual": 0.25,
                "auditory": 0.25,
                "reading": 0.25,
                "kinesthetic": 0.25,
            }

        # Calculate total study time
        total_study_minutes = sum(a.study_time_minutes for a in analytics)

        if total_study_minutes == 0:
            return {
                "visual": 0.25,
                "auditory": 0.25,
                "reading": 0.25,
                "kinesthetic": 0.25,
            }

        # Extract behavioral indicators from behavioral_data (if provided)
        video_time = behavioral_data.get("video_watch_time_minutes", 0)
        audio_time = behavioral_data.get("audio_content_time_minutes", 0)
        reading_time = behavioral_data.get("text_reading_time_minutes", 0)
        interactive_time = behavioral_data.get("interactive_exercise_time_minutes", 0)

        # Calculate proportions (normalized to 0-1 range)
        total_content_time = video_time + audio_time + reading_time + interactive_time

        if total_content_time > 0:
            vark_scores["visual"] = min(1.0, (video_time / total_content_time) * 1.5)
            vark_scores["auditory"] = min(1.0, (audio_time / total_content_time) * 1.5)
            vark_scores["reading"] = min(1.0, (reading_time / total_content_time) * 1.5)
            vark_scores["kinesthetic"] = min(
                1.0, (interactive_time / total_content_time) * 1.5
            )
        else:
            # No specific content data - use question performance patterns
            # Students who solve more problems tend to be kinesthetic
            total_questions = sum(a.questions_attempted for a in analytics)
            if total_questions > 100:
                vark_scores["kinesthetic"] = 0.6
                vark_scores["reading"] = 0.4
                vark_scores["visual"] = 0.3
                vark_scores["auditory"] = 0.2
            else:
                # Default balanced profile with slight visual preference
                vark_scores["visual"] = 0.4
                vark_scores["reading"] = 0.35
                vark_scores["kinesthetic"] = 0.3
                vark_scores["auditory"] = 0.25

        # Normalize scores to sum to 1.0 (proportional distribution)
        total_score = sum(vark_scores.values())
        if total_score > 0:
            vark_scores = {k: v / total_score for k, v in vark_scores.items()}

        return vark_scores

    async def _calculate_felder_profile(
        self, student_id: str, db: AsyncSession, behavioral_data: dict[str, Any]
    ) -> dict[str, float]:
        """
        Calculate Felder-Silverman profile from behavioral data

        REFACTORED: Real calculations based on learning patterns
        - Active/Reflective: Group vs solo study patterns
        - Sensing/Intuitive: Concrete vs abstract content preference
        - Visual/Verbal: Image/video vs text preference
        - Sequential/Global: Linear vs holistic learning path
        """
        # Get exam sessions for performance patterns
        result = await db.execute(
            select(ExamSession).where(ExamSession.student_id == student_id)
        )
        exam_sessions = result.scalars().all()

        # Initialize scores (-1 to +1 range)
        felder_scores = {
            "active_reflective": 0.0,
            "sensing_intuitive": 0.0,
            "visual_verbal": 0.0,
            "sequential_global": 0.0,
        }

        if not exam_sessions:
            # No data - return neutral profile
            return felder_scores

        # Extract behavioral indicators
        group_study_time = behavioral_data.get("group_study_minutes", 0)
        solo_study_time = behavioral_data.get("solo_study_minutes", 0)
        visual_content_time = behavioral_data.get("visual_content_minutes", 0)
        text_content_time = behavioral_data.get("text_content_minutes", 0)

        # Active/Reflective (-1=reflective, +1=active)
        if group_study_time + solo_study_time > 0:
            ratio = (group_study_time - solo_study_time) / (
                group_study_time + solo_study_time
            )
            felder_scores["active_reflective"] = max(-1.0, min(1.0, ratio))
        else:
            # Default: slightly reflective (students tend to study alone for exams)
            felder_scores["active_reflective"] = -0.2

        # Sensing/Intuitive (-1=intuitive, +1=sensing)
        # Sensing: prefer concrete, practical content
        # Intuitive: prefer abstract, theoretical content
        # Use exam performance variance as proxy
        if len(exam_sessions) > 3:
            scores = [e.scaled_score for e in exam_sessions if e.scaled_score]
            if scores:
                variance = sum(
                    (x - sum(scores) / len(scores)) ** 2 for x in scores
                ) / len(scores)
                # Low variance -> sensing (consistent, methodical)
                # High variance -> intuitive (creative, varied approach)
                felder_scores["sensing_intuitive"] = max(
                    -1.0, min(1.0, 0.5 - variance / 100)
                )
        else:
            felder_scores["sensing_intuitive"] = 0.0

        # Visual/Verbal (-1=verbal, +1=visual)
        if visual_content_time + text_content_time > 0:
            ratio = (visual_content_time - text_content_time) / (
                visual_content_time + text_content_time
            )
            felder_scores["visual_verbal"] = max(-1.0, min(1.0, ratio))
        else:
            # Default: slightly visual (modern students prefer visual content)
            felder_scores["visual_verbal"] = 0.3

        # Sequential/Global (-1=global, +1=sequential)
        # Sequential: linear, step-by-step learning
        # Global: holistic, big-picture learning
        # Use question completion patterns as proxy
        completion_rate = behavioral_data.get("question_completion_rate", 0.5)
        if completion_rate > 0.8:
            # High completion -> sequential (completes tasks linearly)
            felder_scores["sequential_global"] = 0.4
        elif completion_rate < 0.5:
            # Low completion -> global (jumps around, explores)
            felder_scores["sequential_global"] = -0.3
        else:
            felder_scores["sequential_global"] = 0.0

        return felder_scores

    def _calculate_confidence(
        self, behavioral_data: dict[str, Any], questionnaire_responses: list[str] | None
    ) -> float:
        """
        Calculate confidence score based on data availability

        REFACTORED: Real confidence based on data quality
        - More behavioral data = higher confidence
        - Questionnaire responses boost confidence
        - Returns 0.0-1.0 score
        """
        confidence = 0.0

        # Base confidence from behavioral data presence
        data_points = [
            "video_watch_time_minutes",
            "audio_content_time_minutes",
            "text_reading_time_minutes",
            "interactive_exercise_time_minutes",
            "group_study_minutes",
            "solo_study_minutes",
        ]

        available_data = sum(
            1 for key in data_points if behavioral_data.get(key, 0) > 0
        )
        confidence += (
            available_data / len(data_points)
        ) * 0.6  # Up to 0.6 from behavioral data

        # Boost from questionnaire responses
        if questionnaire_responses and len(questionnaire_responses) > 0:
            confidence += min(
                0.3, len(questionnaire_responses) * 0.05
            )  # Up to 0.3 from survey

        # Minimum baseline confidence
        confidence = max(0.3, confidence)  # At least 0.3 (low but valid)
        confidence = min(1.0, confidence)  # Cap at 1.0

        return round(confidence, 2)

    def _profile_to_dict(self, profile: StudentLearningProfile) -> dict[str, Any]:
        """Convert StudentLearningProfile ORM model to dictionary"""
        return {
            "student_id": profile.student_id,
            "vark_profili": profile.vark_profile_dict,
            "felder_silverman_profili": profile.felder_profile_dict,
            "hibrit_kod": profile.hybrid_code,
            "dominant_vark_stili": profile.dominant_vark_style,
            "dominant_felder_boyutu": profile.dominant_felder_dimension,
            "guven_seviyesi": profile.confidence_score,
            "tespit_tarihi": profile.detected_at.isoformat(),
            "profil_aciklamasi": profile.profile_description,
        }

    async def generate_content_recommendations(
        self,
        student_id: str,
        db: AsyncSession,
        subject_area: str = "matematik",
        difficulty_level: str = "orta",
        force_refresh: bool = False,
    ) -> ContentRecommendation:
        """
        Hibrit profile ve VARK baskinina gore icerik onerileri (API ile uyumlu).
        """
        result = await db.execute(
            select(StudentLearningProfile).where(
                StudentLearningProfile.student_id == student_id
            )
        )
        profile_model = result.scalar_one_or_none()

        if not profile_model or force_refresh:
            await self.detect_learning_style(student_id, db, behavioral_data={})
            result = await db.execute(
                select(StudentLearningProfile).where(
                    StudentLearningProfile.student_id == student_id
                )
            )
            profile_model = result.scalar_one_or_none()

        if not profile_model:
            w = 1.0 / 3.0
            return ContentRecommendation(
                student_id=student_id,
                hybrid_code="M-MM-MM",
                recommended_content_types=[
                    "video_lecture",
                    "quiz_practice",
                    "reading",
                ],
                content_weights={
                    "video_lecture": w,
                    "quiz_practice": w,
                    "reading": w,
                },
                learning_strategies=["active_learning", "spaced_repetition"],
                study_techniques=["pomodoro", "note_taking", "retrieval_practice"],
                difficulty_adjustment=0.0,
                pace_adjustment=0.0,
                confidence_score=0.35,
            )

        dom = (profile_model.dominant_vark_style or "visual").lower()
        if dom == "visual":
            content_types = ["video_lecture", "infographic", "visual_aid"]
            learning_strategies = ["visual_aids", "mind_mapping", "color_coding"]
            study_techniques = ["diagram_notes", "video_summaries", "sketching"]
        elif dom == "auditory":
            content_types = ["audio_content", "group_discussion", "podcast"]
            learning_strategies = ["verbal_repetition", "teach_back", "debate"]
            study_techniques = ["read_aloud", "audio_notes", "rhythm_phrasing"]
        elif dom == "reading":
            content_types = ["reading", "text_summary", "flashcards"]
            learning_strategies = ["annotated_reading", "outlines", "self_quizzing"]
            study_techniques = ["SQ3R", "keyword_lists", "margin_notes"]
        else:  # kinesthetic
            content_types = [
                "interactive_simulation",
                "practice_test",
                "hands_on_lab",
            ]
            learning_strategies = [
                "active_learning",
                "problem_sets",
                "spaced_repetition",
            ]
            study_techniques = [
                "pomodoro",
                "retrieval_practice",
                "interleaving",
            ]

        w = 1.0 / len(content_types)
        content_weights = dict.fromkeys(content_types, w)

        dl = (difficulty_level or "orta").lower()
        if dl in ("kolay", "easy", "dusuk"):
            diff_adj = -0.15
        elif dl in ("zor", "hard", "yuksek"):
            diff_adj = 0.15
        else:
            diff_adj = 0.0

        conf = float(profile_model.confidence_score or 0.5)
        conf = max(0.0, min(1.0, conf))

        return ContentRecommendation(
            student_id=student_id,
            hybrid_code=profile_model.hybrid_code or "M-MM-MM",
            recommended_content_types=content_types,
            content_weights=content_weights,
            learning_strategies=learning_strategies,
            study_techniques=study_techniques,
            difficulty_adjustment=diff_adj,
            pace_adjustment=0.0,
            confidence_score=conf,
        )

    async def get_learning_recommendations(
        self, student_id: str, db: AsyncSession, subject: str = "genel"
    ) -> list[dict[str, Any]]:
        """
        Öğrenme stiline göre öneriler oluştur

        REFACTORED: Uses database profile
        """
        try:
            # Get profile from database
            result = await db.execute(
                select(StudentLearningProfile).where(
                    StudentLearningProfile.student_id == student_id
                )
            )
            profile_model = result.scalar_one_or_none()

            if not profile_model:
                # No profile yet - detect it first
                await self.detect_learning_style(student_id, db, {})
                result = await db.execute(
                    select(StudentLearningProfile).where(
                        StudentLearningProfile.student_id == student_id
                    )
                )
                profile_model = result.scalar_one_or_none()

            if not profile_model:
                return []

            recommendations = []

            # VARK tabanlı öneriler
            dominant_vark = profile_model.dominant_vark_style

            if dominant_vark == "visual":
                recommendations.append(
                    {
                        "tip": "görsel_materyaller",
                        "açıklama": "Diyagramlar, grafikler ve görsel materyaller kullanın",
                        "öncelik": "yüksek",
                    }
                )
            elif dominant_vark == "auditory":
                recommendations.append(
                    {
                        "tip": "sesli_çalışma",
                        "açıklama": "Sesli okuma, müzik eşliğinde çalışma ve tartışma grupları",
                        "öncelik": "yüksek",
                    }
                )
            elif dominant_vark == "reading":
                recommendations.append(
                    {
                        "tip": "metin_tabanlı",
                        "açıklama": "Kitap okuma, not alma ve yazılı özetler",
                        "öncelik": "yüksek",
                    }
                )
            elif dominant_vark == "kinesthetic":
                recommendations.append(
                    {
                        "tip": "uygulamalı_öğrenme",
                        "açıklama": "Deneyler, uygulamalı çalışmalar ve hareket içeren aktiviteler",
                        "öncelik": "yüksek",
                    }
                )

            # Felder-Silverman tabanlı öneriler
            if profile_model.felder_active_reflective > 0:
                recommendations.append(
                    {
                        "tip": "aktif_öğrenme",
                        "açıklama": "Grup çalışması ve tartışma odaklı öğrenme",
                        "öncelik": "orta",
                    }
                )
            else:
                recommendations.append(
                    {
                        "tip": "yansıtıcı_öğrenme",
                        "açıklama": "Bireysel düşünme ve analiz zamanı ayırın",
                        "öncelik": "orta",
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(
                f"Öğrenme önerileri hatası - Öğrenci: {student_id}, Hata: {e!s}"
            )
            raise

    def _generate_hibrit_code(
        self, vark_profile: dict[str, float], felder_profile: dict[str, float]
    ) -> str:
        """
        Hibrit kod oluştur (64 kombinasyondan biri)
        """
        # VARK kodu
        vark_code = ""
        for dimension, score in vark_profile.items():
            if score > 0.3:  # Threshold for inclusion
                vark_code += dimension[0].upper()

        if not vark_code:
            vark_code = "M"  # Mixed

        # Felder-Silverman kodu
        felder_code = ""

        # Active/Reflective
        if felder_profile["active_reflective"] > 0.3:
            felder_code += "A"
        elif felder_profile["active_reflective"] < -0.3:
            felder_code += "R"
        else:
            felder_code += "M"

        # Sensing/Intuitive
        if felder_profile["sensing_intuitive"] > 0.3:
            felder_code += "S"
        elif felder_profile["sensing_intuitive"] < -0.3:
            felder_code += "I"
        else:
            felder_code += "M"

        # Visual/Verbal
        if felder_profile["visual_verbal"] > 0.3:
            felder_code += "V"
        elif felder_profile["visual_verbal"] < -0.3:
            felder_code += "B"
        else:
            felder_code += "M"

        # Sequential/Global
        if felder_profile["sequential_global"] > 0.3:
            felder_code += "S"
        elif felder_profile["sequential_global"] < -0.3:
            felder_code += "G"
        else:
            felder_code += "M"

        return f"{vark_code}-{felder_code}"

    def _get_profile_description(self, hibrit_kod: str) -> str:
        """
        Hibrit kod açıklaması
        """
        return f"Hibrit öğrenme profili {hibrit_kod}: Bu profil, VARK ve Felder-Silverman modellerinin birleşiminden oluşur."

    async def get_student_profile(
        self, student_id: str, db: AsyncSession
    ) -> dict[str, Any] | None:
        """
        Öğrenci profilini getir

        REFACTORED: Queries database instead of in-memory dict
        """
        result = await db.execute(
            select(StudentLearningProfile).where(
                StudentLearningProfile.student_id == student_id
            )
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return None

        return self._profile_to_dict(profile)

    async def get_service_stats(self, db: AsyncSession) -> dict[str, Any]:
        """
        Servis istatistikleri

        REFACTORED: Queries database for real stats
        """
        result = await db.execute(
            select(sa_func.count()).select_from(StudentLearningProfile)
        )
        total_profiles = result.scalar() or 0

        return {
            "toplam_profil_sayisi": total_profiles,
            "vark_boyutlari": self.vark_dimensions,
            "felder_boyutlari": self.felder_dimensions,
            "toplam_kombinasyon": 64,
        }

    async def get_all_hybrid_codes(self) -> list[dict[str, Any]]:
        """
        Tüm 64 hibrit kod ve açıklamalarını döndür (CACHED - 1 saat, static data)
        """
        # Cache kontrolü (static data - 1 saat)
        cache_key = "learning_style:all_hybrid_codes"
        cached = await cache_manager.get(cache_key)
        if cached:
            logger.info("Cache hit: all_hybrid_codes")
            return cached

        logger.info("Cache miss: all_hybrid_codes - generating...")

        hybrid_codes = []

        # VARK boyutları: V (Visual), A (Auditory), R (Reading), K (Kinesthetic), M (Mixed)
        vark_codes = [
            "V",
            "A",
            "R",
            "K",
            "VR",
            "VK",
            "AR",
            "AK",
            "RK",
            "VAR",
            "VAK",
            "VRK",
            "ARK",
            "VARK",
            "M",
        ]

        # Felder-Silverman: 4 boyut x 3 değer (ilk karakter, ters karakter, M orta)
        # A/R (Active/Reflective), S/I (Sensing/Intuitive), V/B (Visual/Verbal), S/G (Sequential/Global)
        felder_base = [
            ["A", "R", "M"],  # Active/Reflective
            ["S", "I", "M"],  # Sensing/Intuitive
            ["V", "B", "M"],  # Visual/Verbal
            ["S", "G", "M"],  # Sequential/Global
        ]

        # Tüm Felder kombinasyonları
        felder_codes = []
        for ar in felder_base[0]:
            for si in felder_base[1]:
                for vb in felder_base[2]:
                    for sg in felder_base[3]:
                        felder_codes.append(f"{ar}{si}{vb}{sg}")

        # İlk 64 kombinasyonu oluştur
        count = 0
        for vark in vark_codes:
            for felder in felder_codes[:5]:  # Her VARK için 4-5 Felder kombinasyonu
                if count >= 64:
                    break

                hybrid_code = f"{vark}-{felder}"
                hybrid_codes.append(
                    {
                        "kod": hybrid_code,
                        "vark_komponenti": vark,
                        "felder_komponenti": felder,
                        "açıklama": self._get_profile_description(hybrid_code),
                        "örnek_öğrenci_sayısı": 0,
                    }
                )
                count += 1

            if count >= 64:
                break

        # Cache'e kaydet (1 saat - static data)
        await cache_manager.set(cache_key, hybrid_codes, ttl=3600)
        logger.info(f"Toplam {len(hybrid_codes)} hibrit kod döndürüldü ve cache'lendi")
        return hybrid_codes

    async def get_learning_style_statistics(self, db: AsyncSession) -> dict[str, Any]:
        """
        Öğrenme stili istatistikleri (CACHED - 5 dakika)

        REFACTORED: Queries database for real statistics
        """
        # Cache kontrolü
        cache_key = "learning_style:statistics"
        cached = await cache_manager.get(cache_key)
        if cached:
            logger.info("Cache hit: statistics")
            return cached

        logger.info("Cache miss: statistics - calculating from database...")

        # Get all profiles from database
        result = await db.execute(select(StudentLearningProfile))
        all_profiles = result.scalars().all()

        # Calculate distributions
        vark_distribution = dict.fromkeys(self.vark_dimensions, 0)
        felder_distribution = dict.fromkeys(self.felder_dimensions, 0)
        hybrid_code_distribution = {}

        for profile in all_profiles:
            # VARK distribution
            dominant_vark = profile.dominant_vark_style
            if dominant_vark in vark_distribution:
                vark_distribution[dominant_vark] += 1

            # Felder distribution
            dominant_felder = profile.dominant_felder_dimension
            if dominant_felder in felder_distribution:
                felder_distribution[dominant_felder] += 1

            # Hybrid code distribution
            hybrid_code = profile.hybrid_code
            hybrid_code_distribution[hybrid_code] = (
                hybrid_code_distribution.get(hybrid_code, 0) + 1
            )

        # Top 10 profiles
        top_hybrid_codes = sorted(
            hybrid_code_distribution.items(), key=lambda x: x[1], reverse=True
        )[:10]

        statistics = {
            "toplam_öğrenci": len(all_profiles),
            "vark_dağılımı": vark_distribution,
            "felder_dağılımı": felder_distribution,
            "en_yaygın_10_profil": [
                {
                    "kod": kod,
                    "öğrenci_sayısı": sayı,
                    "yüzde": round((sayı / len(all_profiles) * 100), 2)
                    if all_profiles
                    else 0,
                }
                for kod, sayı in top_hybrid_codes
            ],
            "benzersiz_profil_sayısı": len(hybrid_code_distribution),
            "son_güncelleme": datetime.now().isoformat(),
        }

        # Cache'e kaydet (5 dakika)
        await cache_manager.set(cache_key, statistics, ttl=300)
        logger.info(
            f"Statistics calculated from database - Total students: {len(all_profiles)}"
        )
        return statistics
