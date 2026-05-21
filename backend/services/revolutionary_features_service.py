"""
Devrimsel Özellikler Servisi
VARK + Felder-Silverman, ZPD + Maarif, IRT + Morfoloji entegrasyonu
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from algorithms.turkish_zpd_maarif_system import TurkishZPDMaarifSystem
from services.irt_calibration_service import IRTCalibrationService

logger = logging.getLogger(__name__)


@dataclass
class VARKProfile:
    """VARK öğrenme stili profili"""

    visual: float
    auditory: float
    reading: float
    kinesthetic: float
    dominant: str


@dataclass
class FelderProfile:
    """Felder-Silverman öğrenme stili profili"""

    active_reflective: float
    sensing_intuitive: float
    visual_verbal: float
    sequential_global: float
    preferences: list[str]


@dataclass
class HybridLearningProfile:
    """Hibrit öğrenme stili profili"""

    student_id: str
    hybrid_code: str
    vark_profile: VARKProfile
    felder_profile: FelderProfile
    confidence: dict[str, Any]
    data_points_used: int
    detection_date: str
    last_updated: str


@dataclass
class CulturalContext:
    """Kültürel bağlam"""

    group_learning_preference: float
    teacher_respect_level: float
    family_involvement: float
    peer_competition: float
    authority_acceptance: float
    collective_success: float
    elder_wisdom_value: float
    social_harmony: float


@dataclass
class MaarifAlignment:
    """MEB Maarif değerleri uyumu"""

    overall_alignment: float
    national_values_alignment: float
    universal_values_alignment: float
    root_values_alignment: float
    aligned_values: list[str]


@dataclass
class TurkishZPDRange:
    """Türk ZPD aralığı"""

    student_id: str
    subject: str
    current_level: float
    lower_bound: float
    upper_bound: float
    optimal_challenge: float
    group_individual_balance: float
    cultural_context: CulturalContext
    maarif_alignment: MaarifAlignment
    calculated_at: str


@dataclass
class ZPDRecommendation:
    """ZPD önerisi"""

    student_id: str
    subject: str
    recommended_difficulty: float
    learning_mode: str
    content_type: str
    teacher_guidance_level: float
    peer_support_level: float
    maarif_integration: list[str]
    reasoning: str
    confidence_score: float


class RevolutionaryFeaturesService:
    """Devrimsel özellikler servisi"""

    def __init__(self):
        self.zpd_system = TurkishZPDMaarifSystem()
        self.irt_service = IRTCalibrationService()

        # VARK ağırlıkları
        self.vark_weights = {
            "video_watch_time": {
                "visual": 0.8,
                "auditory": 0.6,
                "reading": 0.2,
                "kinesthetic": 0.3,
            },
            "text_reading_time": {
                "visual": 0.3,
                "auditory": 0.2,
                "reading": 0.9,
                "kinesthetic": 0.1,
            },
            "interactive_engagement": {
                "visual": 0.5,
                "auditory": 0.4,
                "reading": 0.3,
                "kinesthetic": 0.9,
            },
            "note_taking_frequency": {
                "visual": 0.6,
                "auditory": 0.3,
                "reading": 0.8,
                "kinesthetic": 0.4,
            },
        }

        # Felder-Silverman ağırlıkları
        self.felder_weights = {
            "group_study_sessions": {
                "active_reflective": 0.8,
                "sensing_intuitive": 0.3,
                "visual_verbal": 0.2,
                "sequential_global": 0.4,
            },
            "individual_study_sessions": {
                "active_reflective": -0.8,
                "sensing_intuitive": 0.2,
                "visual_verbal": 0.1,
                "sequential_global": 0.3,
            },
            "hands_on_performance": {
                "active_reflective": 0.7,
                "sensing_intuitive": 0.8,
                "visual_verbal": 0.1,
                "sequential_global": 0.2,
            },
            "quiz_completion_rate": {
                "active_reflective": 0.2,
                "sensing_intuitive": 0.6,
                "visual_verbal": 0.3,
                "sequential_global": 0.7,
            },
        }

    async def detect_hybrid_learning_style(
        self,
        student_id: str,
        behavioral_data: dict[str, Any],
        questionnaire_responses: list[str] | None = None,
        force_recalculation: bool = False,
    ) -> HybridLearningProfile:
        """Hibrit öğrenme stili tespiti"""

        try:
            logger.info(
                f"Hibrit öğrenme stili tespiti başlatıldı - Öğrenci: {student_id}"
            )

            # VARK profili hesapla
            vark_profile = await self._calculate_vark_profile(
                behavioral_data, questionnaire_responses
            )

            # Felder-Silverman profili hesapla
            felder_profile = await self._calculate_felder_profile(
                behavioral_data, questionnaire_responses
            )

            # Hibrit kod oluştur (4x4x4x4 = 64 kombinasyon)
            hybrid_code = self._generate_hybrid_code(vark_profile, felder_profile)

            # Güven skoru hesapla
            confidence = self._calculate_confidence(
                behavioral_data, questionnaire_responses
            )

            profile = HybridLearningProfile(
                student_id=student_id,
                hybrid_code=hybrid_code,
                vark_profile=vark_profile,
                felder_profile=felder_profile,
                confidence=confidence,
                data_points_used=len(behavioral_data),
                detection_date=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
            )

            logger.info(
                f"Hibrit profil oluşturuldu - Kod: {hybrid_code}, Güven: {confidence['score']:.2f}"
            )
            return profile

        except Exception as e:
            logger.error(f"Hibrit öğrenme stili tespit hatası: {e}", exc_info=True)
            raise

    async def _calculate_vark_profile(
        self,
        behavioral_data: dict[str, Any],
        questionnaire_responses: list[str] | None = None,
    ) -> VARKProfile:
        """VARK profili hesaplama"""

        vark_scores = {
            "visual": 0.0,
            "auditory": 0.0,
            "reading": 0.0,
            "kinesthetic": 0.0,
        }

        # Davranışsal verilerden VARK skorları
        for behavior, value in behavioral_data.items():
            if behavior in self.vark_weights:
                weights = self.vark_weights[behavior]
                normalized_value = (
                    min(1.0, value / 100.0) if isinstance(value, (int, float)) else 0.5
                )

                for vark_type, weight in weights.items():
                    vark_scores[vark_type] += normalized_value * weight

        # Anket yanıtlarından ek skorlar
        if questionnaire_responses:
            questionnaire_bonus = self._analyze_questionnaire_for_vark(
                questionnaire_responses
            )
            for vark_type, bonus in questionnaire_bonus.items():
                vark_scores[vark_type] += bonus

        # Normalize et
        total_score = sum(vark_scores.values())
        if total_score > 0:
            for vark_type in vark_scores:
                vark_scores[vark_type] /= total_score

        # Dominant stili belirle
        dominant = max(vark_scores.keys(), key=lambda k: vark_scores[k])

        return VARKProfile(
            visual=vark_scores["visual"],
            auditory=vark_scores["auditory"],
            reading=vark_scores["reading"],
            kinesthetic=vark_scores["kinesthetic"],
            dominant=dominant,
        )

    async def _calculate_felder_profile(
        self,
        behavioral_data: dict[str, Any],
        questionnaire_responses: list[str] | None = None,
    ) -> FelderProfile:
        """Felder-Silverman profili hesaplama"""

        felder_scores = {
            "active_reflective": 0.0,
            "sensing_intuitive": 0.0,
            "visual_verbal": 0.0,
            "sequential_global": 0.0,
        }

        # Davranışsal verilerden Felder skorları
        for behavior, value in behavioral_data.items():
            if behavior in self.felder_weights:
                weights = self.felder_weights[behavior]
                normalized_value = (
                    min(1.0, value / 100.0) if isinstance(value, (int, float)) else 0.5
                )

                for dimension, weight in weights.items():
                    felder_scores[dimension] += normalized_value * weight

        # Anket yanıtlarından ek skorlar
        if questionnaire_responses:
            questionnaire_bonus = self._analyze_questionnaire_for_felder(
                questionnaire_responses
            )
            for dimension, bonus in questionnaire_bonus.items():
                felder_scores[dimension] += bonus

        # -1 ile +1 arası normalize et
        for dimension in felder_scores:
            felder_scores[dimension] = max(-1.0, min(1.0, felder_scores[dimension]))

        # Tercihleri belirle
        preferences = []
        if felder_scores["active_reflective"] > 0.3:
            preferences.append("active")
        elif felder_scores["active_reflective"] < -0.3:
            preferences.append("reflective")

        if felder_scores["sensing_intuitive"] > 0.3:
            preferences.append("sensing")
        elif felder_scores["sensing_intuitive"] < -0.3:
            preferences.append("intuitive")

        if felder_scores["visual_verbal"] > 0.3:
            preferences.append("visual")
        elif felder_scores["visual_verbal"] < -0.3:
            preferences.append("verbal")

        if felder_scores["sequential_global"] > 0.3:
            preferences.append("sequential")
        elif felder_scores["sequential_global"] < -0.3:
            preferences.append("global")

        return FelderProfile(
            active_reflective=felder_scores["active_reflective"],
            sensing_intuitive=felder_scores["sensing_intuitive"],
            visual_verbal=felder_scores["visual_verbal"],
            sequential_global=felder_scores["sequential_global"],
            preferences=preferences,
        )

    def _generate_hybrid_code(
        self, vark_profile: VARKProfile, felder_profile: FelderProfile
    ) -> str:
        """64 farklı hibrit kod oluştur"""

        # VARK kodu (4 seçenek)
        vark_code = vark_profile.dominant[0].upper()  # V, A, R, K

        # Felder kodları (her boyut için 2 seçenek = 2^4 = 16 kombinasyon)
        felder_codes = []

        # Active/Reflective
        felder_codes.append("A" if felder_profile.active_reflective > 0 else "R")

        # Sensing/Intuitive
        felder_codes.append("S" if felder_profile.sensing_intuitive > 0 else "I")

        # Visual/Verbal
        felder_codes.append(
            "V" if felder_profile.visual_verbal > 0 else "B"
        )  # B for Verbal

        # Sequential/Global
        felder_codes.append(
            "Q" if felder_profile.sequential_global > 0 else "G"
        )  # Q for Sequential

        felder_code = "".join(felder_codes)

        # Final hibrit kod: VARK + Felder = 4 x 16 = 64 kombinasyon
        hybrid_code = f"{vark_code}-{felder_code}"

        return hybrid_code

    def _calculate_confidence(
        self,
        behavioral_data: dict[str, Any],
        questionnaire_responses: list[str] | None = None,
    ) -> dict[str, Any]:
        """Güven skoru hesaplama"""

        confidence_factors = []

        # Veri noktası sayısı
        data_points = len(behavioral_data)
        data_confidence = min(1.0, data_points / 10.0)  # 10+ veri noktası ideal
        confidence_factors.append(data_confidence * 0.4)

        # Anket yanıtları
        if questionnaire_responses:
            questionnaire_confidence = min(
                1.0, len(questionnaire_responses) / 20.0
            )  # 20+ yanıt ideal
            confidence_factors.append(questionnaire_confidence * 0.3)
        else:
            confidence_factors.append(0.0)

        # Davranışsal tutarlılık
        consistency = self._calculate_behavioral_consistency(behavioral_data)
        confidence_factors.append(consistency * 0.3)

        total_confidence = sum(confidence_factors)

        # Güven seviyesi
        if total_confidence >= 0.8:
            level = "Yüksek"
        elif total_confidence >= 0.6:
            level = "Orta"
        elif total_confidence >= 0.4:
            level = "Düşük"
        else:
            level = "Çok Düşük"

        return {
            "score": total_confidence,
            "level": level,
            "factors": {
                "data_points": data_confidence,
                "questionnaire": confidence_factors[1] / 0.3
                if len(confidence_factors) > 1
                else 0.0,
                "consistency": consistency,
            },
        }

    def _calculate_behavioral_consistency(
        self, behavioral_data: dict[str, Any]
    ) -> float:
        """Davranışsal tutarlılık hesaplama"""

        # Basit tutarlılık kontrolü
        # Örnek: Video izleme süresi yüksekse, görsel performans da yüksek olmalı

        consistency_checks = []

        # Video-Görsel tutarlılık
        if (
            "video_watch_time" in behavioral_data
            and "visual_content_performance" in behavioral_data
        ):
            video_norm = min(1.0, behavioral_data["video_watch_time"] / 120.0)
            visual_perf = behavioral_data["visual_content_performance"]
            consistency_checks.append(1.0 - abs(video_norm - visual_perf))

        # Grup-Bireysel denge
        if (
            "group_study_sessions" in behavioral_data
            and "individual_study_sessions" in behavioral_data
        ):
            group_sessions = behavioral_data["group_study_sessions"]
            individual_sessions = behavioral_data["individual_study_sessions"]
            total_sessions = group_sessions + individual_sessions
            if total_sessions > 0:
                balance = min(group_sessions, individual_sessions) / total_sessions
                consistency_checks.append(balance * 2)  # 0.5 ideal denge

        # Ortalama tutarlılık
        if consistency_checks:
            return sum(consistency_checks) / len(consistency_checks)
        return 0.5  # Varsayılan

    def _analyze_questionnaire_for_vark(self, responses: list[str]) -> dict[str, float]:
        """Anket yanıtlarından VARK bonusu"""

        # Basit anahtar kelime analizi
        vark_keywords = {
            "visual": ["görsel", "resim", "grafik", "şema", "diyagram", "renk"],
            "auditory": ["dinleme", "müzik", "ses", "konuşma", "tartışma", "açıklama"],
            "reading": ["okuma", "yazma", "metin", "kitap", "makale", "not"],
            "kinesthetic": [
                "yaparak",
                "deneyim",
                "hareket",
                "dokunma",
                "uygulama",
                "pratik",
            ],
        }

        bonuses = {"visual": 0.0, "auditory": 0.0, "reading": 0.0, "kinesthetic": 0.0}

        for response in responses:
            response_lower = response.lower()
            for vark_type, keywords in vark_keywords.items():
                for keyword in keywords:
                    if keyword in response_lower:
                        bonuses[vark_type] += 0.1

        return bonuses

    def _analyze_questionnaire_for_felder(
        self, responses: list[str]
    ) -> dict[str, float]:
        """Anket yanıtlarından Felder bonusu"""

        # Basit anahtar kelime analizi
        felder_keywords = {
            "active_reflective": {
                "active": ["grup", "tartışma", "uygulama", "deneme", "hemen"],
                "reflective": ["düşünme", "analiz", "tek başına", "planlama", "önce"],
            },
            "sensing_intuitive": {
                "sensing": ["gerçek", "somut", "detay", "adım", "örnek"],
                "intuitive": ["kavram", "teori", "genel", "anlam", "yaratıcı"],
            },
            "visual_verbal": {
                "visual": ["görsel", "şema", "grafik", "resim", "diyagram"],
                "verbal": ["açıklama", "konuşma", "yazılı", "kelime", "anlatım"],
            },
            "sequential_global": {
                "sequential": ["adım", "sıra", "düzen", "sistematik", "aşama"],
                "global": ["genel", "bütün", "kavram", "anlam", "ilişki"],
            },
        }

        bonuses = {
            "active_reflective": 0.0,
            "sensing_intuitive": 0.0,
            "visual_verbal": 0.0,
            "sequential_global": 0.0,
        }

        for response in responses:
            response_lower = response.lower()
            for dimension, keywords_dict in felder_keywords.items():
                for pole, keywords in keywords_dict.items():
                    for keyword in keywords:
                        if keyword in response_lower:
                            if pole in ["active", "sensing", "visual", "sequential"]:
                                bonuses[dimension] += 0.1
                            else:
                                bonuses[dimension] -= 0.1

        return bonuses

    async def calculate_revolutionary_zpd(
        self,
        student_id: str,
        subject: str,
        current_level: float,
        behavioral_data: dict[str, Any],
        content_description: str = "",
        family_survey: dict[str, Any] | None = None,
    ) -> TurkishZPDRange:
        """Devrimsel ZPD hesaplama"""

        try:
            logger.info(
                f"Devrimsel ZPD hesaplama başlatıldı - Öğrenci: {student_id}, Konu: {subject}"
            )

            # Kültürel bağlamı tespit et
            cultural_context = await self.detect_cultural_context(
                student_id, behavioral_data
            )

            # MEB Maarif uyumunu hesapla
            maarif_alignment = await self.calculate_maarif_alignment(
                subject, content_description
            )

            # ZPD aralığını hesapla
            zpd_result = await self.zpd_system.calculate_turkish_zpd(
                student_current_level=current_level,
                subject=subject,
                cultural_context=asdict(cultural_context),
            )

            # Grup-birey dengesini hesapla
            group_individual_balance = self._calculate_group_individual_balance(
                behavioral_data
            )

            zpd_range = TurkishZPDRange(
                student_id=student_id,
                subject=subject,
                current_level=current_level,
                lower_bound=zpd_result.lower_bound,
                upper_bound=zpd_result.upper_bound,
                optimal_challenge=zpd_result.optimal_challenge,
                group_individual_balance=group_individual_balance,
                cultural_context=cultural_context,
                maarif_alignment=maarif_alignment,
                calculated_at=datetime.now().isoformat(),
            )

            logger.info(
                f"ZPD hesaplandı - Aralık: {zpd_result.lower_bound:.2f}-{zpd_result.upper_bound:.2f}"
            )
            return zpd_range

        except Exception as e:
            logger.error(f"ZPD hesaplama hatası: {e}", exc_info=True)
            raise

    async def detect_cultural_context(
        self, student_id: str, behavioral_data: dict[str, Any]
    ) -> CulturalContext:
        """Kültürel bağlam tespiti"""

        # Davranışsal verilerden kültürel faktörleri çıkar
        group_learning = min(1.0, behavioral_data.get("group_study_sessions", 0) / 20.0)
        teacher_questions = min(
            1.0, behavioral_data.get("teacher_question_count", 0) / 15.0
        )
        peer_interaction = min(
            1.0, behavioral_data.get("peer_interaction_count", 0) / 30.0
        )
        help_seeking = min(1.0, behavioral_data.get("help_seeking_frequency", 0) / 15.0)

        return CulturalContext(
            group_learning_preference=group_learning,
            teacher_respect_level=teacher_questions,
            family_involvement=0.7,  # Varsayılan yüksek
            peer_competition=peer_interaction * 0.8,
            authority_acceptance=teacher_questions * 0.9,
            collective_success=group_learning * 0.8,
            elder_wisdom_value=0.8,  # Türk kültürü için yüksek
            social_harmony=peer_interaction * 0.7,
        )

    async def calculate_maarif_alignment(
        self, subject: str, content_description: str
    ) -> MaarifAlignment:
        """MEB Maarif değerleri uyumu"""

        # Basit anahtar kelime analizi
        national_keywords = [
            "vatan",
            "millet",
            "bayrak",
            "türk",
            "atatürk",
            "cumhuriyet",
        ]
        universal_keywords = [
            "adalet",
            "dostluk",
            "dürüstlük",
            "barış",
            "hoşgörü",
            "saygı",
        ]
        root_keywords = ["sabır", "sevgi", "merhamet", "yardımlaşma", "dayanışma"]

        content_lower = content_description.lower()

        national_score = sum(
            1 for keyword in national_keywords if keyword in content_lower
        ) / len(national_keywords)
        universal_score = sum(
            1 for keyword in universal_keywords if keyword in content_lower
        ) / len(universal_keywords)
        root_score = sum(
            1 for keyword in root_keywords if keyword in content_lower
        ) / len(root_keywords)

        # Konu bazlı ayarlama
        subject_multipliers = {
            "tarih": {"national": 1.5, "universal": 1.0, "root": 1.2},
            "türkçe": {"national": 1.3, "universal": 1.1, "root": 1.4},
            "matematik": {"national": 0.8, "universal": 1.2, "root": 1.0},
            "fen": {"national": 0.9, "universal": 1.3, "root": 1.1},
        }

        multiplier = subject_multipliers.get(
            subject.lower(), {"national": 1.0, "universal": 1.0, "root": 1.0}
        )

        national_score *= multiplier["national"]
        universal_score *= multiplier["universal"]
        root_score *= multiplier["root"]

        # Normalize et
        national_score = min(1.0, national_score)
        universal_score = min(1.0, universal_score)
        root_score = min(1.0, root_score)

        overall_alignment = (national_score + universal_score + root_score) / 3

        # Uyumlu değerleri belirle
        aligned_values = []
        if national_score > 0.3:
            aligned_values.extend(["vatan sevgisi", "milli bilinç"])
        if universal_score > 0.3:
            aligned_values.extend(["adalet", "hoşgörü"])
        if root_score > 0.3:
            aligned_values.extend(["sabır", "sevgi"])

        return MaarifAlignment(
            overall_alignment=overall_alignment,
            national_values_alignment=national_score,
            universal_values_alignment=universal_score,
            root_values_alignment=root_score,
            aligned_values=aligned_values,
        )

    def _calculate_group_individual_balance(
        self, behavioral_data: dict[str, Any]
    ) -> float:
        """Grup-birey öğrenme dengesi"""

        group_sessions = behavioral_data.get("group_study_sessions", 0)
        individual_sessions = behavioral_data.get("individual_study_sessions", 0)

        total_sessions = group_sessions + individual_sessions
        if total_sessions == 0:
            return 0.5  # Varsayılan denge

        group_ratio = group_sessions / total_sessions
        return group_ratio

    async def generate_revolutionary_recommendation(
        self,
        student_id: str,
        subject: str,
        current_level: float,
        behavioral_data: dict[str, Any],
        learning_objective: str,
        content_description: str = "",
        family_survey: dict[str, Any] | None = None,
    ) -> ZPDRecommendation:
        """Devrimsel öneri oluşturma"""

        try:
            # ZPD aralığını hesapla
            zpd_range = await self.calculate_revolutionary_zpd(
                student_id,
                subject,
                current_level,
                behavioral_data,
                content_description,
                family_survey,
            )

            # Öğrenme stilini tespit et
            learning_profile = await self.detect_hybrid_learning_style(
                student_id, behavioral_data
            )

            # Öneri parametrelerini hesapla
            recommended_difficulty = zpd_range.optimal_challenge

            # Öğrenme modunu belirle
            if zpd_range.group_individual_balance > 0.6:
                learning_mode = "group"
            elif zpd_range.group_individual_balance < 0.4:
                learning_mode = "individual"
            else:
                learning_mode = "mixed"

            # İçerik tipini belirle
            dominant_vark = learning_profile.vark_profile.dominant
            content_type_map = {
                "visual": "infographic",
                "auditory": "podcast",
                "reading": "text",
                "kinesthetic": "interactive",
            }
            content_type = content_type_map.get(dominant_vark, "mixed")

            # Öğretmen rehberliği seviyesi
            teacher_guidance = zpd_range.cultural_context.teacher_respect_level

            # Akran desteği seviyesi
            peer_support = zpd_range.cultural_context.peer_competition

            # Maarif entegrasyonu
            maarif_integration = zpd_range.maarif_alignment.aligned_values[
                :3
            ]  # İlk 3 değer

            # Gerekçe oluştur
            reasoning = self._generate_reasoning(
                zpd_range, learning_profile, learning_objective
            )

            # Güven skoru
            confidence_score = (
                learning_profile.confidence["score"] * 0.4
                + zpd_range.maarif_alignment.overall_alignment * 0.3
                + min(1.0, len(behavioral_data) / 10.0) * 0.3
            )

            recommendation = ZPDRecommendation(
                student_id=student_id,
                subject=subject,
                recommended_difficulty=recommended_difficulty,
                learning_mode=learning_mode,
                content_type=content_type,
                teacher_guidance_level=teacher_guidance,
                peer_support_level=peer_support,
                maarif_integration=maarif_integration,
                reasoning=reasoning,
                confidence_score=confidence_score,
            )

            logger.info(
                f"Devrimsel öneri oluşturuldu - Zorluk: {recommended_difficulty:.2f}, Mod: {learning_mode}"
            )
            return recommendation

        except Exception as e:
            logger.error(f"Öneri oluşturma hatası: {e}", exc_info=True)
            raise

    def _generate_reasoning(
        self,
        zpd_range: TurkishZPDRange,
        learning_profile: HybridLearningProfile,
        learning_objective: str,
    ) -> str:
        """Öneri gerekçesi oluştur"""

        reasoning_parts = []

        # ZPD gerekçesi
        if zpd_range.optimal_challenge > zpd_range.current_level + 0.5:
            reasoning_parts.append(
                "Mevcut seviyenizin üzerinde zorlayıcı içerik önerilmektedir"
            )
        else:
            reasoning_parts.append(
                "Mevcut seviyenize uygun pekiştirici içerik önerilmektedir"
            )

        # Öğrenme stili gerekçesi
        dominant_style = learning_profile.vark_profile.dominant
        style_descriptions = {
            "visual": "görsel öğrenme tercihinize uygun",
            "auditory": "işitsel öğrenme tercihinize uygun",
            "reading": "okuma-yazma tercihinize uygun",
            "kinesthetic": "uygulamalı öğrenme tercihinize uygun",
        }
        reasoning_parts.append(
            style_descriptions.get(dominant_style, "öğrenme stilinize uygun")
        )

        # Kültürel bağlam gerekçesi
        if zpd_range.group_individual_balance > 0.6:
            reasoning_parts.append("grup çalışması tercihleriniz dikkate alınmıştır")
        elif zpd_range.group_individual_balance < 0.4:
            reasoning_parts.append("bireysel çalışma tercihleriniz dikkate alınmıştır")

        # Maarif entegrasyonu
        if zpd_range.maarif_alignment.overall_alignment > 0.5:
            reasoning_parts.append("MEB değerleriyle uyumlu içerik seçilmiştir")

        return ". ".join(reasoning_parts).capitalize() + "."


# Global instance
revolutionary_features_service = RevolutionaryFeaturesService()
