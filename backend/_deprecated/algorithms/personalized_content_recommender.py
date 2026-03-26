"""
Hibrit Öğrenme Stiline Göre Kişiselleştirilmiş İçerik Önerisi Algoritması
64 farklı profil için optimize edilmiş öneri sistemi
"""
import logging
from dataclasses import dataclass
from datetime import datetime

import numpy as np
from typing import Dict, List, Tuple

from models.learning_style import (
    ContentRecommendation,
    HybridLearningProfile,
    VARKDimension,
)

logger = logging.getLogger(__name__)


@dataclass
class ContentType:
    """İçerik türü tanımları"""

    VIDEO_LECTURE = "video_lecture"
    INTERACTIVE_SIMULATION = "interactive_simulation"
    TEXT_ARTICLE = "text_article"
    AUDIO_PODCAST = "audio_podcast"
    HANDS_ON_EXERCISE = "hands_on_exercise"
    VISUAL_INFOGRAPHIC = "visual_infographic"
    QUIZ_PRACTICE = "quiz_practice"
    GROUP_DISCUSSION = "group_discussion"
    STEP_BY_STEP_GUIDE = "step_by_step_guide"
    CONCEPT_MAP = "concept_map"


@dataclass
class LearningStrategy:
    """Öğrenme stratejisi tanımları"""

    SPACED_REPETITION = "spaced_repetition"
    ACTIVE_RECALL = "active_recall"
    ELABORATIVE_INTERROGATION = "elaborative_interrogation"
    SELF_EXPLANATION = "self_explanation"
    INTERLEAVED_PRACTICE = "interleaved_practice"
    DUAL_CODING = "dual_coding"
    CHUNKING = "chunking"
    MNEMONICS = "mnemonics"


class PersonalizedContentRecommender:
    """
    64 hibrit profil için kişiselleştirilmiş içerik önerisi
    VARK + Felder-Silverman kombinasyonlarına optimize edilmiş
    """

    def __init__(self):
        # İçerik türü ağırlık matrisleri
        self.vark_content_weights = self._initialize_vark_content_weights()
        self.felder_content_weights = self._initialize_felder_content_weights()

        # Öğrenme stratejisi matrisleri
        self.learning_strategy_matrix = self._initialize_learning_strategies()

        # Çalışma teknikleri
        self.study_techniques = self._initialize_study_techniques()

        logger.info("Kişiselleştirilmiş İçerik Önerisi Sistemi başlatıldı")

    def _initialize_vark_content_weights(self) -> Dict[str, Dict[str, float]]:
        """VARK boyutları için içerik ağırlıkları"""
        return {
            VARKDimension.VISUAL: {
                ContentType.VIDEO_LECTURE: 0.9,
                ContentType.VISUAL_INFOGRAPHIC: 0.95,
                ContentType.INTERACTIVE_SIMULATION: 0.8,
                ContentType.CONCEPT_MAP: 0.9,
                ContentType.TEXT_ARTICLE: 0.3,
                ContentType.AUDIO_PODCAST: 0.2,
                ContentType.HANDS_ON_EXERCISE: 0.6,
                ContentType.QUIZ_PRACTICE: 0.7,
                ContentType.GROUP_DISCUSSION: 0.4,
                ContentType.STEP_BY_STEP_GUIDE: 0.8,
            },
            VARKDimension.AUDITORY: {
                ContentType.VIDEO_LECTURE: 0.8,
                ContentType.AUDIO_PODCAST: 0.95,
                ContentType.GROUP_DISCUSSION: 0.9,
                ContentType.INTERACTIVE_SIMULATION: 0.6,
                ContentType.TEXT_ARTICLE: 0.4,
                ContentType.VISUAL_INFOGRAPHIC: 0.3,
                ContentType.HANDS_ON_EXERCISE: 0.5,
                ContentType.QUIZ_PRACTICE: 0.6,
                ContentType.CONCEPT_MAP: 0.4,
                ContentType.STEP_BY_STEP_GUIDE: 0.7,
            },
            VARKDimension.READING: {
                ContentType.TEXT_ARTICLE: 0.95,
                ContentType.STEP_BY_STEP_GUIDE: 0.9,
                ContentType.QUIZ_PRACTICE: 0.8,
                ContentType.CONCEPT_MAP: 0.7,
                ContentType.VIDEO_LECTURE: 0.5,
                ContentType.AUDIO_PODCAST: 0.3,
                ContentType.VISUAL_INFOGRAPHIC: 0.6,
                ContentType.INTERACTIVE_SIMULATION: 0.4,
                ContentType.HANDS_ON_EXERCISE: 0.3,
                ContentType.GROUP_DISCUSSION: 0.5,
            },
            VARKDimension.KINESTHETIC: {
                ContentType.HANDS_ON_EXERCISE: 0.95,
                ContentType.INTERACTIVE_SIMULATION: 0.9,
                ContentType.QUIZ_PRACTICE: 0.8,
                ContentType.GROUP_DISCUSSION: 0.7,
                ContentType.VIDEO_LECTURE: 0.6,
                ContentType.TEXT_ARTICLE: 0.3,
                ContentType.AUDIO_PODCAST: 0.4,
                ContentType.VISUAL_INFOGRAPHIC: 0.5,
                ContentType.CONCEPT_MAP: 0.4,
                ContentType.STEP_BY_STEP_GUIDE: 0.7,
            },
        }

    def _initialize_felder_content_weights(self) -> Dict[str, Dict[str, float]]:
        """Felder-Silverman boyutları için içerik ağırlıkları"""
        return {
            "active": {
                ContentType.GROUP_DISCUSSION: 0.9,
                ContentType.HANDS_ON_EXERCISE: 0.8,
                ContentType.INTERACTIVE_SIMULATION: 0.85,
                ContentType.QUIZ_PRACTICE: 0.7,
                ContentType.VIDEO_LECTURE: 0.6,
                ContentType.TEXT_ARTICLE: 0.3,
                ContentType.AUDIO_PODCAST: 0.5,
                ContentType.VISUAL_INFOGRAPHIC: 0.6,
                ContentType.CONCEPT_MAP: 0.5,
                ContentType.STEP_BY_STEP_GUIDE: 0.6,
            },
            "reflective": {
                ContentType.TEXT_ARTICLE: 0.9,
                ContentType.STEP_BY_STEP_GUIDE: 0.8,
                ContentType.CONCEPT_MAP: 0.85,
                ContentType.VIDEO_LECTURE: 0.7,
                ContentType.VISUAL_INFOGRAPHIC: 0.8,
                ContentType.AUDIO_PODCAST: 0.6,
                ContentType.GROUP_DISCUSSION: 0.3,
                ContentType.HANDS_ON_EXERCISE: 0.4,
                ContentType.INTERACTIVE_SIMULATION: 0.5,
                ContentType.QUIZ_PRACTICE: 0.6,
            },
            "sensing": {
                ContentType.HANDS_ON_EXERCISE: 0.9,
                ContentType.STEP_BY_STEP_GUIDE: 0.85,
                ContentType.QUIZ_PRACTICE: 0.8,
                ContentType.INTERACTIVE_SIMULATION: 0.7,
                ContentType.VIDEO_LECTURE: 0.6,
                ContentType.TEXT_ARTICLE: 0.7,
                ContentType.VISUAL_INFOGRAPHIC: 0.6,
                ContentType.AUDIO_PODCAST: 0.5,
                ContentType.GROUP_DISCUSSION: 0.5,
                ContentType.CONCEPT_MAP: 0.4,
            },
            "intuitive": {
                ContentType.CONCEPT_MAP: 0.9,
                ContentType.VISUAL_INFOGRAPHIC: 0.8,
                ContentType.VIDEO_LECTURE: 0.7,
                ContentType.GROUP_DISCUSSION: 0.75,
                ContentType.INTERACTIVE_SIMULATION: 0.8,
                ContentType.TEXT_ARTICLE: 0.6,
                ContentType.AUDIO_PODCAST: 0.6,
                ContentType.HANDS_ON_EXERCISE: 0.5,
                ContentType.QUIZ_PRACTICE: 0.6,
                ContentType.STEP_BY_STEP_GUIDE: 0.4,
            },
            "visual_felder": {
                ContentType.VISUAL_INFOGRAPHIC: 0.95,
                ContentType.CONCEPT_MAP: 0.9,
                ContentType.VIDEO_LECTURE: 0.8,
                ContentType.INTERACTIVE_SIMULATION: 0.85,
                ContentType.STEP_BY_STEP_GUIDE: 0.7,
                ContentType.TEXT_ARTICLE: 0.4,
                ContentType.AUDIO_PODCAST: 0.3,
                ContentType.HANDS_ON_EXERCISE: 0.6,
                ContentType.QUIZ_PRACTICE: 0.7,
                ContentType.GROUP_DISCUSSION: 0.5,
            },
            "verbal": {
                ContentType.TEXT_ARTICLE: 0.9,
                ContentType.AUDIO_PODCAST: 0.85,
                ContentType.GROUP_DISCUSSION: 0.8,
                ContentType.STEP_BY_STEP_GUIDE: 0.75,
                ContentType.VIDEO_LECTURE: 0.6,
                ContentType.QUIZ_PRACTICE: 0.7,
                ContentType.VISUAL_INFOGRAPHIC: 0.4,
                ContentType.CONCEPT_MAP: 0.5,
                ContentType.INTERACTIVE_SIMULATION: 0.5,
                ContentType.HANDS_ON_EXERCISE: 0.4,
            },
            "sequential": {
                ContentType.STEP_BY_STEP_GUIDE: 0.95,
                ContentType.TEXT_ARTICLE: 0.8,
                ContentType.QUIZ_PRACTICE: 0.85,
                ContentType.VIDEO_LECTURE: 0.7,
                ContentType.HANDS_ON_EXERCISE: 0.6,
                ContentType.AUDIO_PODCAST: 0.6,
                ContentType.VISUAL_INFOGRAPHIC: 0.7,
                ContentType.INTERACTIVE_SIMULATION: 0.5,
                ContentType.GROUP_DISCUSSION: 0.4,
                ContentType.CONCEPT_MAP: 0.3,
            },
            "global": {
                ContentType.CONCEPT_MAP: 0.95,
                ContentType.VISUAL_INFOGRAPHIC: 0.8,
                ContentType.GROUP_DISCUSSION: 0.8,
                ContentType.INTERACTIVE_SIMULATION: 0.85,
                ContentType.VIDEO_LECTURE: 0.7,
                ContentType.TEXT_ARTICLE: 0.5,
                ContentType.AUDIO_PODCAST: 0.6,
                ContentType.HANDS_ON_EXERCISE: 0.7,
                ContentType.QUIZ_PRACTICE: 0.6,
                ContentType.STEP_BY_STEP_GUIDE: 0.4,
            },
        }

    def _initialize_learning_strategies(self) -> Dict[str, List[str]]:
        """Hibrit profiller için öğrenme stratejileri"""
        return {
            # VARK tabanlı stratejiler
            VARKDimension.VISUAL: [
                LearningStrategy.DUAL_CODING,
                "concept_mapping",
                "görsel_organizatörler",
                "renk_kodlama",
            ],
            VARKDimension.AUDITORY: [
                LearningStrategy.SELF_EXPLANATION,
                LearningStrategy.ELABORATIVE_INTERROGATION,
                "sesli_tekrar",
                "grup_tartışması",
            ],
            VARKDimension.READING: [
                LearningStrategy.ACTIVE_RECALL,
                LearningStrategy.SPACED_REPETITION,
                "özet_çıkarma",
                "not_alma",
            ],
            VARKDimension.KINESTHETIC: [
                LearningStrategy.INTERLEAVED_PRACTICE,
                "uygulamalı_öğrenme",
                "hareket_tabanlı_hafıza",
                "simülasyon",
            ],
            # Felder tabanlı stratejiler
            "active": [
                "grup_çalışması",
                "tartışma_forumları",
                "peer_teaching",
                "brainstorming",
            ],
            "reflective": [
                "bireysel_çalışma",
                "derin_düşünme",
                "journal_tutma",
                "meditasyon",
            ],
            "sensing": [
                "somut_örnekler",
                "adım_adım_çözüm",
                "pratik_uygulamalar",
                "gerçek_hayat_bağlantıları",
            ],
            "intuitive": [
                "kavramsal_öğrenme",
                "pattern_recognition",
                "yaratıcı_düşünme",
                "soyut_bağlantılar",
            ],
            "sequential": [
                "doğrusal_ilerleme",
                "yapılandırılmış_plan",
                "adım_adım_rehber",
                "kronolojik_sıra",
            ],
            "global": [
                "büyük_resim",
                "bağlantısal_öğrenme",
                "multidisipliner_yaklaşım",
                "holistik_görüş",
            ],
        }

    def _initialize_study_techniques(self) -> Dict[str, List[str]]:
        """Çalışma teknikleri matrisi"""
        return {
            # VARK teknikleri
            VARKDimension.VISUAL: [
                "mind_mapping",
                "flowchart_oluşturma",
                "renk_kodlu_notlar",
                "görsel_kartlar",
                "diagram_çizme",
            ],
            VARKDimension.AUDITORY: [
                "sesli_okuma",
                "müzik_eşliğinde_çalışma",
                "tartışma_grupları",
                "sesli_kayıt_alma",
                "ritim_tekniği",
            ],
            VARKDimension.READING: [
                "detaylı_not_alma",
                "özet_yazma",
                "liste_oluşturma",
                "metin_analizi",
                "yazılı_tekrar",
            ],
            VARKDimension.KINESTHETIC: [
                "hareket_halinde_çalışma",
                "manipülatif_kullanma",
                "rol_yapma",
                "fiziksel_modeller",
                "uygulamalı_deneyim",
            ],
            # Hibrit teknikler
            "hybrid_visual_active": [
                "interaktif_görsel_sunumlar",
                "grup_mind_mapping",
                "görsel_tartışma_panoları",
            ],
            "hybrid_auditory_reflective": [
                "sessiz_dinleme_seansları",
                "kendi_kendine_açıklama",
                "sesli_düşünme",
            ],
            "hybrid_reading_sequential": [
                "yapılandırılmış_okuma_planı",
                "adım_adım_not_alma",
                "kronolojik_özet",
            ],
            "hybrid_kinesthetic_global": [
                "bütünsel_simülasyonlar",
                "çok_duyulu_deneyimler",
                "sistem_düşüncesi_oyunları",
            ],
        }

    async def generate_personalized_recommendations(
        self,
        hybrid_profile: HybridLearningProfile,
        subject_area: str = "matematik",
        difficulty_level: str = "orta",
    ) -> ContentRecommendation:
        """
        64 hibrit profil için kişiselleştirilmiş içerik önerisi
        """
        logger.info(
            f"İçerik önerisi oluşturuluyor - Profil: {hybrid_profile.hybrid_code}"
        )

        # İçerik türü ağırlıklarını hesapla
        content_weights = await self._calculate_content_weights(hybrid_profile)

        # Önerilen içerik türlerini belirle
        recommended_types = await self._select_recommended_content_types(
            content_weights, hybrid_profile.confidence_score
        )

        # Öğrenme stratejilerini belirle
        learning_strategies = await self._select_learning_strategies(hybrid_profile)

        # Çalışma tekniklerini belirle
        study_techniques = await self._select_study_techniques(hybrid_profile)

        # Zorluk ve hız ayarlamaları
        difficulty_adjustment, pace_adjustment = await self._calculate_adjustments(
            hybrid_profile, difficulty_level
        )

        recommendation = ContentRecommendation(
            student_id=hybrid_profile.student_id,
            hybrid_code=hybrid_profile.hybrid_code,
            recommended_content_types=recommended_types,
            content_weights=content_weights,
            learning_strategies=learning_strategies,
            study_techniques=study_techniques,
            difficulty_adjustment=difficulty_adjustment,
            pace_adjustment=pace_adjustment,
            confidence_score=hybrid_profile.confidence_score,
        )

        logger.info(
            f"İçerik önerisi tamamlandı - {len(recommended_types)} tür önerildi"
        )
        return recommendation

    async def _calculate_content_weights(
        self, hybrid_profile: HybridLearningProfile
    ) -> Dict[str, float]:
        """Hibrit profil için içerik ağırlıklarını hesapla"""

        vark_profile = hybrid_profile.vark_profile
        felder_profile = hybrid_profile.felder_profile

        # VARK ağırlıkları
        vark_weights = self.vark_content_weights[vark_profile.dominant_vark]

        # Felder ağırlıkları
        felder_prefs = felder_profile.learning_preferences
        felder_weights = {}

        for content_type in ContentType.__dict__.values():
            if isinstance(content_type, str):
                felder_weight = 0.0

                # Her Felder boyutu için ağırlık topla
                for dimension, preference in felder_prefs.items():
                    if preference in self.felder_content_weights:
                        felder_weight += self.felder_content_weights[preference].get(
                            content_type, 0.0
                        )

                felder_weights[content_type] = felder_weight / len(felder_prefs)

        # VARK ve Felder ağırlıklarını birleştir
        combined_weights = {}
        for content_type in ContentType.__dict__.values():
            if isinstance(content_type, str):
                vark_w = vark_weights.get(content_type, 0.5)
                felder_w = felder_weights.get(content_type, 0.5)

                # Güven seviyesine göre ağırlık
                confidence_factor = hybrid_profile.confidence_score
                combined_weights[content_type] = (
                    vark_w * 0.6 * confidence_factor
                    + felder_w * 0.4 * confidence_factor
                    + 0.5 * (1 - confidence_factor)  # Düşük güvende ortalama ağırlık
                )

        return combined_weights

    async def _select_recommended_content_types(
        self, content_weights: Dict[str, float], confidence_score: float
    ) -> List[str]:
        """En uygun içerik türlerini seç"""

        # Ağırlıklara göre sırala
        sorted_types = sorted(content_weights.items(), key=lambda x: x[1], reverse=True)

        # Güven seviyesine göre öneri sayısını belirle
        if confidence_score >= 0.8:
            top_n = 3  # Yüksek güven: Az ama kesin öneriler
        elif confidence_score >= 0.6:
            top_n = 5  # Orta güven: Orta sayıda öneri
        else:
            top_n = 7  # Düşük güven: Daha fazla seçenek sun

        # En iyi N türü seç
        recommended = [
            content_type
            for content_type, weight in sorted_types[:top_n]
            if weight > 0.6
        ]

        # Minimum 3 öneri garantisi
        if len(recommended) < 3:
            recommended = [content_type for content_type, weight in sorted_types[:3]]

        return recommended

    async def _select_learning_strategies(
        self, hybrid_profile: HybridLearningProfile
    ) -> List[str]:
        """Hibrit profile göre öğrenme stratejileri seç"""

        strategies = []

        # VARK tabanlı stratejiler
        vark_strategies = self.learning_strategy_matrix.get(
            hybrid_profile.vark_profile.dominant_vark, []
        )
        strategies.extend(vark_strategies[:2])  # En iyi 2 strateji

        # Felder tabanlı stratejiler
        felder_prefs = hybrid_profile.felder_profile.learning_preferences
        for preference in felder_prefs.values():
            felder_strategies = self.learning_strategy_matrix.get(preference, [])
            strategies.extend(felder_strategies[:1])  # Her boyuttan 1 strateji

        # Tekrarları kaldır ve sınırla
        unique_strategies = list(dict.fromkeys(strategies))[:6]

        return unique_strategies

    async def _select_study_techniques(
        self, hybrid_profile: HybridLearningProfile
    ) -> List[str]:
        """Hibrit profile göre çalışma teknikleri seç"""

        techniques = []

        # VARK tabanlı teknikler
        vark_techniques = self.study_techniques.get(
            hybrid_profile.vark_profile.dominant_vark, []
        )
        techniques.extend(vark_techniques[:3])

        # Hibrit teknikler (VARK + Felder kombinasyonu)
        vark_code = hybrid_profile.vark_profile.dominant_vark.value
        felder_prefs = hybrid_profile.felder_profile.learning_preferences

        for felder_pref in felder_prefs.values():
            hybrid_key = f"hybrid_{vark_code}_{felder_pref}"
            hybrid_techniques = self.study_techniques.get(hybrid_key, [])
            techniques.extend(hybrid_techniques[:1])

        # Tekrarları kaldır ve sınırla
        unique_techniques = list(dict.fromkeys(techniques))[:8]

        return unique_techniques

    async def _calculate_adjustments(
        self, hybrid_profile: HybridLearningProfile, difficulty_level: str
    ) -> Tuple[float, float]:
        """Zorluk ve hız ayarlamaları hesapla"""

        felder_prefs = hybrid_profile.felder_profile.learning_preferences

        # Zorluk ayarlaması
        difficulty_adjustment = 0.0

        if felder_prefs.get("perception") == "sensing":
            difficulty_adjustment -= 0.1  # Algısal öğrenciler için biraz daha kolay
        elif felder_prefs.get("perception") == "intuitive":
            difficulty_adjustment += 0.1  # Sezgisel öğrenciler için biraz daha zor

        if felder_prefs.get("understanding") == "sequential":
            difficulty_adjustment -= 0.05  # Sıralı öğrenciler için yapılandırılmış
        elif felder_prefs.get("understanding") == "global":
            difficulty_adjustment += 0.05  # Bütünsel öğrenciler için daha karmaşık

        # Hız ayarlaması
        pace_adjustment = 0.0

        if felder_prefs.get("processing") == "active":
            pace_adjustment += 0.15  # Aktif öğrenciler daha hızlı
        elif felder_prefs.get("processing") == "reflective":
            pace_adjustment -= 0.15  # Yansıtıcı öğrenciler daha yavaş

        # Güven seviyesi faktörü
        confidence_factor = hybrid_profile.confidence_score
        difficulty_adjustment *= confidence_factor
        pace_adjustment *= confidence_factor

        # Sınırları kontrol et
        difficulty_adjustment = max(-0.5, min(0.5, difficulty_adjustment))
        pace_adjustment = max(-0.5, min(0.5, pace_adjustment))

        return difficulty_adjustment, pace_adjustment

    async def get_content_explanation(self, hybrid_code: str, content_type: str) -> str:
        """İçerik önerisi açıklaması"""

        explanations = {
            ContentType.VIDEO_LECTURE: "Görsel ve işitsel öğrenme stilinize uygun video dersler",
            ContentType.INTERACTIVE_SIMULATION: "Kinestetik öğrenme tercihiniz için etkileşimli simülasyonlar",
            ContentType.TEXT_ARTICLE: "Okuma/yazma stilinize uygun detaylı metin içerikleri",
            ContentType.AUDIO_PODCAST: "İşitsel öğrenme tercihiniz için podcast içerikleri",
            ContentType.HANDS_ON_EXERCISE: "Uygulamalı öğrenme stiliniz için pratik egzersizler",
            ContentType.VISUAL_INFOGRAPHIC: "Görsel öğrenme tercihiniz için infografikler",
            ContentType.QUIZ_PRACTICE: "Aktif öğrenme stiliniz için interaktif quizler",
            ContentType.GROUP_DISCUSSION: "Sosyal öğrenme tercihiniz için grup tartışmaları",
            ContentType.STEP_BY_STEP_GUIDE: "Sıralı öğrenme stiliniz için adım adım rehberler",
            ContentType.CONCEPT_MAP: "Bütünsel öğrenme stiliniz için kavram haritaları",
        }

        return explanations.get(content_type, "Öğrenme stilinize uygun içerik")

    async def update_recommendations_based_on_performance(
        self,
        student_id: str,
        current_recommendation: ContentRecommendation,
        performance_data: Dict[str, float],
    ) -> ContentRecommendation:
        """Performans verilerine göre önerileri güncelle"""

        logger.info(f"Performans tabanlı öneri güncelleme - Öğrenci: {student_id}")

        # Performans analizi
        avg_performance = np.mean(list(performance_data.values()))

        updated_recommendation = current_recommendation.copy()

        # Düşük performans durumunda
        if avg_performance < 0.6:
            # Zorluk seviyesini düşür
            updated_recommendation.difficulty_adjustment -= 0.1

            # Daha basit içerik türlerini öne çıkar
            simple_content_types = [
                ContentType.STEP_BY_STEP_GUIDE,
                ContentType.VIDEO_LECTURE,
                ContentType.VISUAL_INFOGRAPHIC,
            ]

            # Mevcut önerileri güncelle
            updated_types = []
            for content_type in simple_content_types:
                if content_type not in updated_recommendation.recommended_content_types:
                    updated_types.append(content_type)

            updated_recommendation.recommended_content_types = (
                simple_content_types
                + updated_recommendation.recommended_content_types[:2]
            )

        # Yüksek performans durumunda
        elif avg_performance > 0.8:
            # Zorluk seviyesini artır
            updated_recommendation.difficulty_adjustment += 0.1

            # Daha karmaşık içerik türlerini ekle
            advanced_content_types = [
                ContentType.INTERACTIVE_SIMULATION,
                ContentType.CONCEPT_MAP,
                ContentType.GROUP_DISCUSSION,
            ]

            for content_type in advanced_content_types:
                if content_type not in updated_recommendation.recommended_content_types:
                    updated_recommendation.recommended_content_types.append(
                        content_type
                    )

        updated_recommendation.generated_at = datetime.now()

        return updated_recommendation
