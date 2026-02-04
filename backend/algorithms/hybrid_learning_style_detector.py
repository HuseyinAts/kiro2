"""
VARK + Felder-Silverman Hibrit Öğrenme Stili Tespit Sistemi
64 farklı öğrenme profili kombinasyonu - DÜNYA ÇAPINDA YENİLİKÇİ
"""
import logging
from dataclasses import dataclass
from datetime import datetime

# import numpy as np  # Lazy import
from typing import Any, Dict, List, Optional, Tuple

from models.learning_style import (
    BehavioralData,
    FelderProfile,
    HybridLearningProfile,
    LearningStyleConfidence,
    QuestionnaireResponse,
    VARKDimension,
    VARKProfile,
)

logger = logging.getLogger(__name__)


@dataclass
class VARKWeights:
    """VARK analizi için ağırlık konfigürasyonu"""

    video_engagement: float = 0.3
    text_preference: float = 0.25
    interactive_usage: float = 0.2
    performance_correlation: float = 0.25


@dataclass
class FelderWeights:
    """Felder-Silverman analizi için ağırlık konfigürasyonu"""

    behavioral_patterns: float = 0.4
    questionnaire_responses: float = 0.35
    performance_indicators: float = 0.25


class HybridLearningStyleDetector:
    """
    VARK + Felder-Silverman = 64 öğrenme profili
    Dünya çapında ilk hibrit öğrenme stili tespit sistemi
    """

    def __init__(self):
        self.vark_weights = VARKWeights()
        self.felder_weights = FelderWeights()

        # 64 hibrit kod kombinasyonları (4x4x4x4 = 64)
        self.hybrid_codes = self._generate_hybrid_codes()

        # Minimum veri gereksinimleri
        self.min_data_points = 10
        self.min_observation_days = 7

        logger.info(
            "Hibrit Öğrenme Stili Tespit Sistemi başlatıldı - 64 profil kombinasyonu hazır"
        )

    def _generate_hybrid_codes(self) -> Dict[str, Dict[str, Any]]:
        """64 farklı hibrit kod kombinasyonu oluştur"""
        codes = {}

        # VARK boyutları (4 seçenek)
        vark_options = ["V", "A", "R", "K"]  # Visual, Auditory, Reading, Kinesthetic

        # Felder boyutları (her biri 2 seçenek = 2^4 = 16 kombinasyon)
        felder_combinations = [
            "ASVS",
            "ASVG",
            "ASBS",
            "ASBG",  # Active-Sensing
            "AIVS",
            "AIVG",
            "AIBS",
            "AIBG",  # Active-Intuitive
            "RSVS",
            "RSVG",
            "RSBS",
            "RSBG",  # Reflective-Sensing
            "RIVS",
            "RIVG",
            "RIBS",
            "RIBG",  # Reflective-Intuitive
        ]

        # 64 kombinasyon oluştur (4 VARK x 16 Felder = 64)
        for vark in vark_options:
            for felder in felder_combinations:
                code = f"{vark}-{felder}"
                codes[code] = {
                    "vark_dominant": vark,
                    "felder_pattern": felder,
                    "description": self._get_profile_description(vark, felder),
                }

        return codes

    def _get_profile_description(self, vark: str, felder: str) -> str:
        """Profil açıklaması oluştur"""
        vark_desc = {
            "V": "Görsel öğrenme tercihi",
            "A": "İşitsel öğrenme tercihi",
            "R": "Okuma/yazma tercihi",
            "K": "Kinestetik öğrenme tercihi",
        }

        # Felder pattern decode
        processing = "Aktif" if felder[0] == "A" else "Yansıtıcı"
        perception = "Algısal" if felder[1] == "S" else "Sezgisel"
        input_pref = "Görsel" if felder[2] == "V" else "Sözel"
        understanding = "Sıralı" if felder[3] == "S" else "Bütünsel"

        return f"{vark_desc[vark]} + {processing}-{perception}-{input_pref}-{understanding}"

    async def detect_hybrid_profile(
        self,
        student_id: str,
        behavioral_data: List[BehavioralData],
        questionnaire_responses: List[QuestionnaireResponse],
    ) -> HybridLearningProfile:
        """
        64 farklı profil kombinasyonundan birini tespit et
        DEVRIMSEL: VARK + Felder-Silverman hibrit analizi
        """
        logger.info(f"Hibrit profil tespiti başlatıldı - Öğrenci: {student_id}")

        # Veri yeterliliği kontrolü
        if len(behavioral_data) < self.min_data_points:
            raise ValueError(f"Minimum {self.min_data_points} veri noktası gerekli")

        # VARK analizi
        vark_profile = await self._analyze_vark_preferences(
            behavioral_data, questionnaire_responses
        )

        # Felder-Silverman analizi
        felder_profile = await self._analyze_felder_dimensions(
            behavioral_data, questionnaire_responses
        )

        # Hibrit kod oluştur
        hybrid_code = self._generate_hybrid_code(vark_profile, felder_profile)

        # Güven seviyesi hesapla
        confidence_score, confidence_level = self._calculate_confidence(
            vark_profile, felder_profile, len(behavioral_data)
        )

        profile = HybridLearningProfile(
            student_id=student_id,
            vark_profile=vark_profile,
            felder_profile=felder_profile,
            hybrid_code=hybrid_code,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            data_points_used=len(behavioral_data),
        )

        logger.info(
            f"Hibrit profil tespit edildi: {hybrid_code} (Güven: {confidence_score:.2f})"
        )
        return profile

    async def _analyze_vark_preferences(
        self,
        behavioral_data: List[BehavioralData],
        questionnaire_responses: List[QuestionnaireResponse],
    ) -> VARKProfile:
        """VARK duyusal tercih analizi"""

        # Davranışsal veri analizi
        behavioral_scores = await self._calculate_vark_behavioral_scores(
            behavioral_data
        )

        # Anket yanıtları analizi
        questionnaire_scores = await self._calculate_vark_questionnaire_scores(
            questionnaire_responses
        )

        # Ağırlıklı kombinasyon
        final_scores = {}
        for dimension in VARKDimension:
            behavioral_weight = 0.7  # Davranışsal veri daha güvenilir
            questionnaire_weight = 0.3

            final_scores[dimension.value] = (
                behavioral_scores.get(dimension.value, 0.25) * behavioral_weight
                + questionnaire_scores.get(dimension.value, 0.25) * questionnaire_weight
            )

        # Normalize et (toplam = 1.0)
        total = sum(final_scores.values())
        if total > 0:
            final_scores = {k: v / total for k, v in final_scores.items()}

        return VARKProfile(
            visual=final_scores.get("visual", 0.25),
            auditory=final_scores.get("auditory", 0.25),
            reading=final_scores.get("reading", 0.25),
            kinesthetic=final_scores.get("kinesthetic", 0.25),
        )

    async def _calculate_vark_behavioral_scores(
        self, behavioral_data: List[BehavioralData]
    ) -> Dict[str, float]:
        """Davranışsal veriden VARK skorları hesapla"""

        scores = {"visual": 0.0, "auditory": 0.0, "reading": 0.0, "kinesthetic": 0.0}

        for data in behavioral_data:
            # Görsel tercih göstergeleri
            visual_indicators = [
                data.video_watch_time / 60.0,  # Video izleme süresi (saat)
                data.visual_content_performance,
                data.interactive_engagement / 30.0,  # Etkileşimli içerik kullanımı
            ]
            scores["visual"] += (
                sum(visual_indicators) / len(visual_indicators)
                if visual_indicators
                else 0
            )

            # İşitsel tercih göstergeleri
            auditory_indicators = [
                data.auditory_content_performance,
                data.question_asking_frequency / 10.0,  # Soru sorma sıklığı
                data.peer_interaction_count / 5.0,  # Akran etkileşimi
            ]
            scores["auditory"] += (
                sum(auditory_indicators) / len(auditory_indicators)
                if auditory_indicators
                else 0
            )

            # Okuma/yazma tercih göstergeleri
            reading_indicators = [
                data.text_reading_time / 60.0,  # Metin okuma süresi
                data.text_content_performance,
                data.note_taking_frequency / 10.0,  # Not alma sıklığı
            ]
            scores["reading"] += (
                sum(reading_indicators) / len(reading_indicators)
                if reading_indicators
                else 0
            )

            # Kinestetik tercih göstergeleri
            kinesthetic_indicators = [
                data.hands_on_performance,
                data.interactive_engagement / 30.0,
                data.quiz_completion_rate,
            ]
            scores["kinesthetic"] += (
                sum(kinesthetic_indicators) / len(kinesthetic_indicators)
                if kinesthetic_indicators
                else 0
            )

        # Ortalama al
        data_count = len(behavioral_data)
        if data_count > 0:
            scores = {k: v / data_count for k, v in scores.items()}

        return scores

    async def _calculate_vark_questionnaire_scores(
        self, questionnaire_responses: List[QuestionnaireResponse]
    ) -> Dict[str, float]:
        """Anket yanıtlarından VARK skorları hesapla"""

        scores = {"visual": 0.0, "auditory": 0.0, "reading": 0.0, "kinesthetic": 0.0}

        vark_responses = [
            r for r in questionnaire_responses if r.questionnaire_type == "VARK"
        ]

        if not vark_responses:
            return scores

        for response in vark_responses:
            responses = response.responses

            # VARK anket soruları analizi
            for question_id, answer in responses.items():
                if isinstance(answer, str):
                    # Cevap türüne göre skor ver
                    if "görsel" in answer.lower() or "resim" in answer.lower():
                        scores["visual"] += 1
                    elif "dinle" in answer.lower() or "ses" in answer.lower():
                        scores["auditory"] += 1
                    elif "oku" in answer.lower() or "yaz" in answer.lower():
                        scores["reading"] += 1
                    elif "yap" in answer.lower() or "uygula" in answer.lower():
                        scores["kinesthetic"] += 1

        # Normalize et
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}

        return scores

    async def _analyze_felder_dimensions(
        self,
        behavioral_data: List[BehavioralData],
        questionnaire_responses: List[QuestionnaireResponse],
    ) -> FelderProfile:
        """Felder-Silverman 4 boyut analizi"""

        # Davranışsal analiz
        behavioral_scores = await self._calculate_felder_behavioral_scores(
            behavioral_data
        )

        # Anket analizi
        questionnaire_scores = await self._calculate_felder_questionnaire_scores(
            questionnaire_responses
        )

        # Ağırlıklı kombinasyon
        final_scores = {}
        for dimension in [
            "active_reflective",
            "sensing_intuitive",
            "visual_verbal",
            "sequential_global",
        ]:
            behavioral_weight = 0.6
            questionnaire_weight = 0.4

            final_scores[dimension] = (
                behavioral_scores.get(dimension, 0.0) * behavioral_weight
                + questionnaire_scores.get(dimension, 0.0) * questionnaire_weight
            )

        return FelderProfile(
            active_reflective=final_scores.get("active_reflective", 0.0),
            sensing_intuitive=final_scores.get("sensing_intuitive", 0.0),
            visual_verbal=final_scores.get("visual_verbal", 0.0),
            sequential_global=final_scores.get("sequential_global", 0.0),
        )

    async def _calculate_felder_behavioral_scores(
        self, behavioral_data: List[BehavioralData]
    ) -> Dict[str, float]:
        """Davranışsal veriden Felder skorları hesapla"""

        scores = {
            "active_reflective": 0.0,
            "sensing_intuitive": 0.0,
            "visual_verbal": 0.0,
            "sequential_global": 0.0,
        }

        for data in behavioral_data:
            # Aktif ↔ Yansıtıcı
            active_indicators = [
                data.peer_interaction_count / 10.0,
                data.question_asking_frequency / 10.0,
                data.interactive_engagement / 30.0,
            ]
            reflective_indicators = [
                data.text_reading_time / 120.0,  # Uzun okuma süreleri
                data.note_taking_frequency / 10.0,
            ]
            scores["active_reflective"] += (
                sum(reflective_indicators) / len(reflective_indicators)
                if reflective_indicators
                else 0
            ) - (
                sum(active_indicators) / len(active_indicators)
                if active_indicators
                else 0
            )

            # Algısal ↔ Sezgisel
            sensing_indicators = [data.hands_on_performance, data.quiz_completion_rate]
            intuitive_indicators = [
                data.visual_content_performance,
                data.help_seeking_behavior / 5.0,
            ]
            scores["sensing_intuitive"] += (
                sum(intuitive_indicators) / len(intuitive_indicators)
                if intuitive_indicators
                else 0
            ) - (
                sum(sensing_indicators) / len(sensing_indicators)
                if sensing_indicators
                else 0
            )

            # Görsel ↔ Sözel
            visual_indicators = [
                data.video_watch_time / 60.0,
                data.visual_content_performance,
            ]
            verbal_indicators = [
                data.text_reading_time / 60.0,
                data.auditory_content_performance,
            ]
            scores["visual_verbal"] += (
                sum(verbal_indicators) / len(verbal_indicators)
                if verbal_indicators
                else 0
            ) - (
                sum(visual_indicators) / len(visual_indicators)
                if visual_indicators
                else 0
            )

            # Sıralı ↔ Bütünsel
            sequential_indicators = [
                data.quiz_completion_rate,
                data.text_content_performance,
            ]
            global_indicators = [
                data.interactive_engagement / 30.0,
                data.peer_interaction_count / 10.0,
            ]
            scores["sequential_global"] += (
                sum(global_indicators) / len(global_indicators)
                if global_indicators
                else 0
            ) - (
                sum(sequential_indicators) / len(sequential_indicators)
                if sequential_indicators
                else 0
            )

        # Ortalama al ve [-1, 1] aralığına normalize et
        data_count = len(behavioral_data)
        if data_count > 0:
            for key in scores:
                scores[key] = max(-1.0, min(1.0, scores[key] / data_count))

        return scores

    async def _calculate_felder_questionnaire_scores(
        self, questionnaire_responses: List[QuestionnaireResponse]
    ) -> Dict[str, float]:
        """Anket yanıtlarından Felder skorları hesapla"""

        scores = {
            "active_reflective": 0.0,
            "sensing_intuitive": 0.0,
            "visual_verbal": 0.0,
            "sequential_global": 0.0,
        }

        felder_responses = [
            r for r in questionnaire_responses if r.questionnaire_type == "Felder"
        ]

        if not felder_responses:
            return scores

        for response in felder_responses:
            responses = response.responses

            # Felder-Silverman anket analizi (basitleştirilmiş)
            for question_id, answer in responses.items():
                if isinstance(answer, str):
                    answer_lower = answer.lower()

                    # Aktif vs Yansıtıcı
                    if "grup" in answer_lower or "tartış" in answer_lower:
                        scores["active_reflective"] -= 0.1  # Aktif yönde
                    elif "tek başına" in answer_lower or "düşün" in answer_lower:
                        scores["active_reflective"] += 0.1  # Yansıtıcı yönde

                    # Algısal vs Sezgisel
                    if "detay" in answer_lower or "adım" in answer_lower:
                        scores["sensing_intuitive"] -= 0.1  # Algısal yönde
                    elif "genel" in answer_lower or "kavram" in answer_lower:
                        scores["sensing_intuitive"] += 0.1  # Sezgisel yönde

                    # Görsel vs Sözel
                    if "şema" in answer_lower or "grafik" in answer_lower:
                        scores["visual_verbal"] -= 0.1  # Görsel yönde
                    elif "açıkla" in answer_lower or "anlat" in answer_lower:
                        scores["visual_verbal"] += 0.1  # Sözel yönde

                    # Sıralı vs Bütünsel
                    if "sıra" in answer_lower or "adım adım" in answer_lower:
                        scores["sequential_global"] -= 0.1  # Sıralı yönde
                    elif "bütün" in answer_lower or "genel" in answer_lower:
                        scores["sequential_global"] += 0.1  # Bütünsel yönde

        # [-1, 1] aralığına sınırla
        for key in scores:
            scores[key] = max(-1.0, min(1.0, scores[key]))

        return scores

    def _generate_hybrid_code(
        self, vark_profile: VARKProfile, felder_profile: FelderProfile
    ) -> str:
        """VARK + Felder kombinasyonundan hibrit kod oluştur"""

        # VARK baskın boyut
        vark_code = vark_profile.dominant_vark.value[0].upper()  # V, A, R, K

        # Felder boyutları
        active_reflective = "A" if felder_profile.active_reflective < 0 else "R"
        sensing_intuitive = "S" if felder_profile.sensing_intuitive < 0 else "I"
        visual_verbal = "V" if felder_profile.visual_verbal < 0 else "B"  # B = Verbal
        sequential_global = "S" if felder_profile.sequential_global < 0 else "G"

        felder_code = (
            f"{active_reflective}{sensing_intuitive}{visual_verbal}{sequential_global}"
        )

        return f"{vark_code}-{felder_code}"

    def _calculate_confidence(
        self, vark_profile: VARKProfile, felder_profile: FelderProfile, data_points: int
    ) -> Tuple[float, LearningStyleConfidence]:
        """Tespit güven seviyesi hesapla"""

        # VARK güven hesaplama
        vark_scores = [
            vark_profile.visual,
            vark_profile.auditory,
            vark_profile.reading,
            vark_profile.kinesthetic,
        ]
        vark_max = max(vark_scores)
        vark_confidence = vark_max - (1.0 - vark_max) / 3  # Baskınlık derecesi

        # Felder güven hesaplama
        felder_scores = [
            abs(felder_profile.active_reflective),
            abs(felder_profile.sensing_intuitive),
            abs(felder_profile.visual_verbal),
            abs(felder_profile.sequential_global),
        ]
        felder_confidence = (
            sum(felder_scores) / len(felder_scores) if felder_scores else 0
        )  # Ortalama kesinlik

        # Veri miktarı faktörü
        data_factor = min(1.0, data_points / 50.0)  # 50 veri noktasında maksimum güven

        # Genel güven skoru
        overall_confidence = (
            vark_confidence * 0.4 + felder_confidence * 0.4 + data_factor * 0.2
        )

        # Güven seviyesi belirleme
        if overall_confidence >= 0.8:
            confidence_level = LearningStyleConfidence.HIGH
        elif overall_confidence >= 0.6:
            confidence_level = LearningStyleConfidence.MEDIUM
        else:
            confidence_level = LearningStyleConfidence.LOW

        return overall_confidence, confidence_level

    async def update_learning_style(
        self,
        student_id: str,
        new_behavioral_data: BehavioralData,
        current_profile: HybridLearningProfile,
    ) -> Optional[HybridLearningProfile]:
        """Davranışsal veri ile öğrenme stilini güncelle"""

        logger.info(f"Öğrenme stili güncelleme kontrolü - Öğrenci: {student_id}")

        # Yeni veri ile mevcut profili karşılaştır
        significance = await self._calculate_update_significance(
            new_behavioral_data, current_profile
        )

        # Önemli değişiklik varsa güncelle
        if significance > 0.3:  # %30 eşik değeri
            logger.info(f"Önemli değişiklik tespit edildi (Önem: {significance:.2f})")

            # Yeni profil hesapla (basitleştirilmiş)
            # Gerçek implementasyonda tüm geçmiş veri ile yeniden hesaplanmalı
            updated_profile = await self._recalculate_profile_with_new_data(
                student_id, new_behavioral_data, current_profile
            )

            return updated_profile

        return None

    async def _calculate_update_significance(
        self, new_data: BehavioralData, current_profile: HybridLearningProfile
    ) -> float:
        """Güncelleme önem derecesi hesapla"""

        # Yeni veri ile mevcut profil arasındaki uyumsuzluk
        vark = current_profile.vark_profile

        # Performans uyumsuzluğu
        performance_mismatch = 0.0

        if vark.dominant_vark.value == "visual":
            performance_mismatch = abs(new_data.visual_content_performance - 0.8)
        elif vark.dominant_vark.value == "auditory":
            performance_mismatch = abs(new_data.auditory_content_performance - 0.8)
        elif vark.dominant_vark.value == "reading":
            performance_mismatch = abs(new_data.text_content_performance - 0.8)
        elif vark.dominant_vark.value == "kinesthetic":
            performance_mismatch = abs(new_data.hands_on_performance - 0.8)

        return performance_mismatch

    async def _recalculate_profile_with_new_data(
        self,
        student_id: str,
        new_data: BehavioralData,
        current_profile: HybridLearningProfile,
    ) -> HybridLearningProfile:
        """Yeni veri ile profili yeniden hesapla"""

        # Basitleştirilmiş güncelleme
        # Gerçek implementasyonda tüm geçmiş veri kullanılmalı

        updated_profile = current_profile.copy()
        updated_profile.last_updated = datetime.now()
        updated_profile.data_points_used += 1

        # Güven seviyesini yeniden hesapla
        confidence_score, confidence_level = self._calculate_confidence(
            current_profile.vark_profile,
            current_profile.felder_profile,
            updated_profile.data_points_used,
        )

        updated_profile.confidence_score = confidence_score
        updated_profile.confidence_level = confidence_level

        return updated_profile
