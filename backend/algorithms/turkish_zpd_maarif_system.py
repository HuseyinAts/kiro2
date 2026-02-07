"""
Zone of Proximal Development + MEB Maarif Modeli
Vygotsky ZPD teorisi + Türk eğitim kültürü entegrasyonu - DEVRİMSEL
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MaarifValue(Enum):
    """MEB Maarif modeli değerleri"""

    # Milli değerler
    VATAN = "vatan"
    MILLET = "millet"
    AILE = "aile"
    BAYRAK = "bayrak"

    # Evrensel değerler
    ADALET = "adalet"
    DOSTLUK = "dostluk"
    DÜRÜSTLÜK = "dürüstlük"
    ÖZGÜRLÜK = "özgürlük"
    SAYGI = "saygı"
    SEVGI = "sevgi"
    SORUMLULUK = "sorumluluk"
    VATANDAŞLIK = "vatandaşlık"

    # Kök değerler
    SABIR = "sabır"
    MERHAMET = "merhamet"
    HOŞGÖRÜ = "hoşgörü"
    MISAFIRPERVERLIK = "misafirperverlik"


class TurkishCulturalFactor(Enum):
    """Türk öğrenci kültürü faktörleri"""

    GROUP_LEARNING_PREFERENCE = "group_learning_preference"
    TEACHER_RESPECT_LEVEL = "teacher_respect_level"
    FAMILY_INVOLVEMENT = "family_involvement"
    PEER_COMPETITION = "peer_competition"
    AUTHORITY_ACCEPTANCE = "authority_acceptance"
    COLLECTIVE_SUCCESS = "collective_success"
    ELDER_WISDOM_VALUE = "elder_wisdom_value"
    SOCIAL_HARMONY = "social_harmony"


@dataclass
class TurkishCulturalContext:
    """Türk öğrenci kültürel bağlam profili"""

    student_id: str

    # Grup çalışması tercihi (0.0-1.0)
    group_learning_preference: float = 0.8

    # Öğretmene saygı seviyesi (0.0-1.0)
    teacher_respect_level: float = 0.9

    # Aile katılımı (0.0-1.0)
    family_involvement: float = 0.7

    # Akran rekabeti (0.0-1.0)
    peer_competition: float = 0.6

    # Otorite kabulü (0.0-1.0)
    authority_acceptance: float = 0.8

    # Kolektif başarı odağı (0.0-1.0)
    collective_success: float = 0.7

    # Yaşça büyük bilgelik değeri (0.0-1.0)
    elder_wisdom_value: float = 0.8

    # Sosyal uyum (0.0-1.0)
    social_harmony: float = 0.9

    # Tespit tarihi
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class MaarifAlignment:
    """MEB Maarif modeli uyum skoru"""

    subject: str

    # Milli değerler uyumu (0.0-1.0)
    national_values_alignment: float = 0.0

    # Evrensel değerler uyumu (0.0-1.0)
    universal_values_alignment: float = 0.0

    # Kök değerler uyumu (0.0-1.0)
    root_values_alignment: float = 0.0

    # Genel uyum skoru (0.0-1.0)
    overall_alignment: float = 0.0

    # Uyumlu değerler listesi
    aligned_values: List[MaarifValue] = field(default_factory=list)


@dataclass
class TurkishZPDRange:
    """Türk kültürüne uyarlanmış ZPD aralığı"""

    student_id: str
    subject: str

    # Mevcut seviye
    current_level: float

    # ZPD alt sınır
    lower_bound: float

    # ZPD üst sınır
    upper_bound: float

    # Optimal zorluk seviyesi
    optimal_challenge: float

    # Kültürel faktörler
    cultural_context: TurkishCulturalContext

    # Maarif uyumu
    maarif_alignment: MaarifAlignment

    # Grup vs bireysel öğrenme dengesi (0.0=tamamen bireysel, 1.0=tamamen grup)
    group_individual_balance: float = 0.6

    # Hesaplama tarihi
    calculated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ZPDRecommendation:
    """ZPD tabanlı öğrenme önerisi"""

    student_id: str
    subject: str

    # Önerilen zorluk seviyesi
    recommended_difficulty: float

    # Önerilen öğrenme modu
    learning_mode: str  # "individual", "group", "mixed"

    # Önerilen içerik türü
    content_type: str  # "visual", "textual", "interactive", "mixed"

    # Öğretmen rehberliği seviyesi (0.0-1.0)
    teacher_guidance_level: float

    # Akran desteği seviyesi (0.0-1.0)
    peer_support_level: float

    # Maarif değerleri entegrasyonu
    maarif_integration: List[MaarifValue]

    # Gerekçe
    reasoning: str

    # Güven skoru (0.0-1.0)
    confidence_score: float


class TurkishZPDMaarifSystem:
    """
    Vygotsky ZPD + MEB Maarif + Türk öğrenci kültürü
    DEVRİMSEL: Türkiye'ye özel adaptif öğrenme sistemi
    """

    def __init__(self) -> None:
        # Türk eğitim kültürü varsayılan değerleri
        self.default_cultural_factors = {
            TurkishCulturalFactor.GROUP_LEARNING_PREFERENCE: 0.8,
            TurkishCulturalFactor.TEACHER_RESPECT_LEVEL: 0.9,
            TurkishCulturalFactor.FAMILY_INVOLVEMENT: 0.7,
            TurkishCulturalFactor.PEER_COMPETITION: 0.6,
            TurkishCulturalFactor.AUTHORITY_ACCEPTANCE: 0.8,
            TurkishCulturalFactor.COLLECTIVE_SUCCESS: 0.7,
            TurkishCulturalFactor.ELDER_WISDOM_VALUE: 0.8,
            TurkishCulturalFactor.SOCIAL_HARMONY: 0.9,
        }

        # MEB Maarif değerleri konu eşleştirmesi
        self.subject_maarif_mapping = {
            "tarih": [MaarifValue.VATAN, MaarifValue.MILLET, MaarifValue.ADALET],
            "türkçe": [MaarifValue.MILLET, MaarifValue.SEVGI, MaarifValue.SAYGI],
            "matematik": [
                MaarifValue.DÜRÜSTLÜK,
                MaarifValue.SABIR,
                MaarifValue.SORUMLULUK,
            ],
            "fen": [MaarifValue.ÖZGÜRLÜK, MaarifValue.SORUMLULUK, MaarifValue.SABIR],
            "sosyal": [
                MaarifValue.VATANDAŞLIK,
                MaarifValue.DOSTLUK,
                MaarifValue.HOŞGÖRÜ,
            ],
            "din": [
                MaarifValue.MERHAMET,
                MaarifValue.HOŞGÖRÜ,
                MaarifValue.MISAFIRPERVERLIK,
            ],
        }

        # Test compatibility attributes
        self.cultural_factors = self.default_cultural_factors
        self.maarif_components = self.subject_maarif_mapping

        # ZPD genişletme faktörleri
        self.zpd_expansion_factors = {
            "high_teacher_respect": 1.15,  # Öğretmene saygı yüksekse ZPD genişler
            "group_learning": 1.20,  # Grup çalışması tercih ediyorsa
            "family_support": 1.10,  # Aile desteği varsa
            "peer_competition": 1.05,  # Akran rekabeti motivasyon artırır
            "maarif_alignment": 1.25,  # Değerler uyumuysa büyük artış
        }

        logger.info("Türk ZPD + Maarif Sistemi başlatıldı - Kültürel adaptasyon hazır")

    async def detect_cultural_context(
        self,
        student_id: str,
        behavioral_data: Dict[str, Any],
        family_survey: Optional[Dict[str, Any]] = None,
    ) -> TurkishCulturalContext:
        """Öğrencinin Türk kültürel bağlamını tespit et"""

        logger.info(f"Kültürel bağlam tespiti başlatıldı - Öğrenci: {student_id}")

        context = TurkishCulturalContext(student_id=student_id)

        # Davranışsal veriden kültürel faktörleri çıkar
        if behavioral_data:
            # Grup çalışması tercihi
            group_activities = behavioral_data.get("group_study_sessions", 0)
            individual_activities = behavioral_data.get("individual_study_sessions", 0)
            total_activities = group_activities + individual_activities

            if total_activities > 0:
                context.group_learning_preference = group_activities / total_activities

            # Öğretmene soru sorma sıklığı (saygı göstergesi)
            teacher_interactions = behavioral_data.get("teacher_question_count", 0)
            context.teacher_respect_level = min(1.0, teacher_interactions / 20.0)

            # Akran etkileşimi (rekabet göstergesi)
            peer_interactions = behavioral_data.get("peer_interaction_count", 0)
            context.peer_competition = min(1.0, peer_interactions / 30.0)

            # Yardım isteme davranışı (otorite kabulü)
            help_seeking = behavioral_data.get("help_seeking_frequency", 0)
            context.authority_acceptance = min(1.0, help_seeking / 15.0)

        # Aile anketi varsa entegre et
        if family_survey:
            context.family_involvement = family_survey.get("involvement_level", 0.7)
            context.collective_success = family_survey.get("collective_focus", 0.7)
            context.elder_wisdom_value = family_survey.get("elder_respect", 0.8)
            context.social_harmony = family_survey.get("harmony_importance", 0.9)

        logger.info(
            f"Kültürel bağlam tespit edildi - Grup tercihi: {context.group_learning_preference:.2f}"
        )
        return context

    async def calculate_maarif_alignment(
        self, subject: str, content_description: str
    ) -> MaarifAlignment:
        """İçeriğin MEB Maarif değerleri ile uyumunu hesapla"""

        alignment = MaarifAlignment(subject=subject)

        # Konu bazlı değer eşleştirmesi
        subject_values = self.subject_maarif_mapping.get(subject.lower(), [])

        # İçerik analizi (basitleştirilmiş)
        content_lower = content_description.lower()
        aligned_values = []

        for value in subject_values:
            if self._check_value_alignment(value, content_lower):
                aligned_values.append(value)

        alignment.aligned_values = aligned_values

        # Uyum skorları hesapla
        total_subject_values = len(subject_values)
        aligned_count = len(aligned_values)

        if total_subject_values > 0:
            # alignment_ratio used implicitly via aligned_count/total_subject_values
            _ = aligned_count / total_subject_values  # For documentation purposes

            # Değer kategorilerine göre uyum skorları
            national_count = sum(
                1
                for v in aligned_values
                if v
                in [
                    MaarifValue.VATAN,
                    MaarifValue.MILLET,
                    MaarifValue.AILE,
                    MaarifValue.BAYRAK,
                ]
            )
            universal_count = sum(
                1
                for v in aligned_values
                if v
                in [
                    MaarifValue.ADALET,
                    MaarifValue.DOSTLUK,
                    MaarifValue.DÜRÜSTLÜK,
                    MaarifValue.ÖZGÜRLÜK,
                    MaarifValue.SAYGI,
                    MaarifValue.SEVGI,
                    MaarifValue.SORUMLULUK,
                    MaarifValue.VATANDAŞLIK,
                ]
            )
            root_count = sum(
                1
                for v in aligned_values
                if v
                in [
                    MaarifValue.SABIR,
                    MaarifValue.MERHAMET,
                    MaarifValue.HOŞGÖRÜ,
                    MaarifValue.MISAFIRPERVERLIK,
                ]
            )

            alignment.national_values_alignment = min(
                1.0, national_count / 2.0
            )  # Max 2 milli değer
            alignment.universal_values_alignment = min(
                1.0, universal_count / 4.0
            )  # Max 4 evrensel değer
            alignment.root_values_alignment = min(
                1.0, root_count / 2.0
            )  # Max 2 kök değer

            alignment.overall_alignment = (
                alignment.national_values_alignment * 0.3
                + alignment.universal_values_alignment * 0.4
                + alignment.root_values_alignment * 0.3
            )

        return alignment

    def _check_value_alignment(self, value: MaarifValue, content: str) -> bool:
        """İçeriğin belirli bir değer ile uyumunu kontrol et"""

        value_keywords = {
            MaarifValue.VATAN: ["vatan", "ülke", "türkiye", "milli"],
            MaarifValue.MILLET: ["millet", "halk", "toplum", "birlik"],
            MaarifValue.AILE: ["aile", "anne", "baba", "kardeş"],
            MaarifValue.ADALET: ["adalet", "hak", "eşitlik", "doğru"],
            MaarifValue.DOSTLUK: ["dostluk", "arkadaş", "birlik", "dayanışma"],
            MaarifValue.DÜRÜSTLÜK: ["dürüst", "doğru", "güvenilir", "samimi"],
            MaarifValue.SAYGI: ["saygı", "hürmet", "değer", "takdir"],
            MaarifValue.SEVGI: ["sevgi", "aşk", "şefkat", "merhamet"],
            MaarifValue.SORUMLULUK: ["sorumluluk", "görev", "yükümlülük"],
            MaarifValue.SABIR: ["sabır", "dayanıklılık", "bekleme"],
            MaarifValue.HOŞGÖRÜ: ["hoşgörü", "tolerans", "anlayış"],
        }

        keywords = value_keywords.get(value, [])
        return any(keyword in content for keyword in keywords)

    async def calculate_turkish_zpd(
        self,
        student_id: str,
        subject: str,
        current_level: float,
        cultural_context: TurkishCulturalContext,
        content_description: str = "",
    ) -> TurkishZPDRange:
        """
        Türk öğrenci kültürüne uyarlanmış ZPD hesaplama
        DEVRİMSEL: Vygotsky + MEB Maarif + Türk kültürü
        """

        logger.info(
            f"Türk ZPD hesaplama başlatıldı - Öğrenci: {student_id}, Konu: {subject}"
        )

        # Standart ZPD hesaplama (Vygotsky temel formülü)
        base_zpd_range = current_level * 0.3  # %30 genişleme

        # Türk kültürü ayarlamaları
        cultural_multiplier = 1.0

        # Grup çalışması tercihi yüksekse ZPD genişler
        if cultural_context.group_learning_preference > 0.7:
            cultural_multiplier *= self.zpd_expansion_factors["group_learning"]
            logger.debug(
                f"Grup çalışması faktörü uygulandı: {self.zpd_expansion_factors['group_learning']}"
            )

        # Öğretmene saygı yüksekse, rehberli öğrenme daha etkili
        if cultural_context.teacher_respect_level > 0.8:
            cultural_multiplier *= self.zpd_expansion_factors["high_teacher_respect"]
            logger.debug(
                f"Öğretmen saygısı faktörü uygulandı: {self.zpd_expansion_factors['high_teacher_respect']}"
            )

        # Aile katılımı yüksekse destek artar
        if cultural_context.family_involvement > 0.6:
            cultural_multiplier *= self.zpd_expansion_factors["family_support"]
            logger.debug(
                f"Aile desteği faktörü uygulandı: {self.zpd_expansion_factors['family_support']}"
            )

        # Akran rekabeti motivasyon artırır
        if cultural_context.peer_competition > 0.5:
            cultural_multiplier *= self.zpd_expansion_factors["peer_competition"]
            logger.debug(
                f"Akran rekabeti faktörü uygulandı: {self.zpd_expansion_factors['peer_competition']}"
            )

        # MEB Maarif değerleri entegrasyonu
        maarif_alignment = await self.calculate_maarif_alignment(
            subject, content_description
        )

        if maarif_alignment.overall_alignment > 0.6:
            cultural_multiplier *= self.zpd_expansion_factors["maarif_alignment"]
            logger.debug(
                f"Maarif uyum faktörü uygulandı: {self.zpd_expansion_factors['maarif_alignment']}"
            )

        # Kültürel ayarlama uygula
        adjusted_zpd_range = base_zpd_range * cultural_multiplier

        # Grup vs bireysel öğrenme dengesi hesapla
        group_individual_balance = self._calculate_learning_balance(cultural_context)

        # Optimal zorluk seviyesi (ZPD'nin %70'i)
        optimal_challenge = current_level + (adjusted_zpd_range * 0.7)

        zpd_range = TurkishZPDRange(
            student_id=student_id,
            subject=subject,
            current_level=current_level,
            lower_bound=current_level,
            upper_bound=current_level + adjusted_zpd_range,
            optimal_challenge=optimal_challenge,
            cultural_context=cultural_context,
            maarif_alignment=maarif_alignment,
            group_individual_balance=group_individual_balance,
        )

        logger.info(
            f"Türk ZPD hesaplandı - Optimal zorluk: {optimal_challenge:.2f}, Kültürel çarpan: {cultural_multiplier:.2f}"
        )
        return zpd_range

    def _calculate_learning_balance(
        self, cultural_context: TurkishCulturalContext
    ) -> float:
        """Grup vs bireysel öğrenme dengesini hesapla"""

        # Grup öğrenme faktörleri
        group_factors = [
            cultural_context.group_learning_preference,
            cultural_context.collective_success,
            cultural_context.social_harmony,
            cultural_context.peer_competition
            * 0.5,  # Rekabet grup öğrenmeyi kısmen destekler
        ]

        # Bireysel öğrenme faktörleri
        individual_factors = [
            1.0 - cultural_context.group_learning_preference,
            cultural_context.authority_acceptance,  # Otorite kabulü bireysel rehberliği destekler
            1.0 - cultural_context.collective_success,
        ]

        group_score = sum(group_factors) / len(group_factors)
        individual_score = sum(individual_factors) / len(individual_factors)

        # 0.0 = tamamen bireysel, 1.0 = tamamen grup
        balance = group_score / (group_score + individual_score)

        return balance

    async def generate_zpd_recommendation(
        self, zpd_range: TurkishZPDRange, learning_objective: str
    ) -> ZPDRecommendation:
        """ZPD tabanlı kişiselleştirilmiş öğrenme önerisi oluştur"""

        cultural_context = zpd_range.cultural_context
        maarif_alignment = zpd_range.maarif_alignment

        # Önerilen zorluk seviyesi
        recommended_difficulty = zpd_range.optimal_challenge

        # Öğrenme modu belirleme
        if zpd_range.group_individual_balance > 0.7:
            learning_mode = "group"
        elif zpd_range.group_individual_balance < 0.3:
            learning_mode = "individual"
        else:
            learning_mode = "mixed"

        # İçerik türü belirleme
        content_type = await self._determine_content_type(
            cultural_context, zpd_range.subject
        )

        # Öğretmen rehberliği seviyesi
        teacher_guidance_level = min(1.0, cultural_context.teacher_respect_level * 1.2)

        # Akran desteği seviyesi
        peer_support_level = (
            cultural_context.group_learning_preference
            * cultural_context.peer_competition
        )

        # Gerekçe oluştur
        reasoning = self._generate_reasoning(zpd_range, learning_mode, content_type)

        # Güven skoru hesapla
        confidence_score = self._calculate_recommendation_confidence(zpd_range)

        recommendation = ZPDRecommendation(
            student_id=zpd_range.student_id,
            subject=zpd_range.subject,
            recommended_difficulty=recommended_difficulty,
            learning_mode=learning_mode,
            content_type=content_type,
            teacher_guidance_level=teacher_guidance_level,
            peer_support_level=peer_support_level,
            maarif_integration=maarif_alignment.aligned_values,
            reasoning=reasoning,
            confidence_score=confidence_score,
        )

        logger.info(
            f"ZPD önerisi oluşturuldu - Mod: {learning_mode}, Zorluk: {recommended_difficulty:.2f}"
        )
        return recommendation

    async def _determine_content_type(
        self, cultural_context: TurkishCulturalContext, subject: str
    ) -> str:
        """Kültürel bağlama göre içerik türü belirle"""

        # Türk öğrenci tercihleri
        if cultural_context.group_learning_preference > 0.7:
            return "interactive"  # Grup etkileşimli içerik
        elif cultural_context.teacher_respect_level > 0.8:
            return "textual"  # Öğretmen rehberli metin içerik
        elif subject.lower() in ["matematik", "fen"]:
            return "visual"  # Görsel destekli içerik
        else:
            return "mixed"  # Karma içerik

    def _generate_reasoning(
        self, zpd_range: TurkishZPDRange, learning_mode: str, content_type: str
    ) -> str:
        """Öneri gerekçesi oluştur"""

        cultural_context = zpd_range.cultural_context

        reasoning_parts = []

        # Kültürel faktörler
        if cultural_context.group_learning_preference > 0.7:
            reasoning_parts.append(
                "Grup çalışması tercihiniz yüksek olduğu için işbirlikli öğrenme önerilir"
            )

        if cultural_context.teacher_respect_level > 0.8:
            reasoning_parts.append(
                "Öğretmen rehberliğine açık olduğunuz için yapılandırılmış öğrenme uygun"
            )

        if zpd_range.maarif_alignment.overall_alignment > 0.6:
            reasoning_parts.append(
                "İçerik MEB değerleri ile uyumlu olduğu için motivasyonunuz artacak"
            )

        # ZPD faktörleri
        reasoning_parts.append(
            f"Mevcut seviyeniz ({zpd_range.current_level:.2f}) göz önüne alınarak optimal zorluk belirlendi"
        )

        return ". ".join(reasoning_parts) + "."

    def _calculate_recommendation_confidence(self, zpd_range: TurkishZPDRange) -> float:
        """Öneri güven skoru hesapla"""

        confidence_factors = []

        # Kültürel bağlam güveni
        cultural_context = zpd_range.cultural_context
        cultural_confidence = (
            cultural_context.group_learning_preference
            + cultural_context.teacher_respect_level
            + cultural_context.family_involvement
        ) / 3.0

        confidence_factors.append(cultural_confidence * 0.4)

        # Maarif uyum güveni
        maarif_confidence = zpd_range.maarif_alignment.overall_alignment
        confidence_factors.append(maarif_confidence * 0.3)

        # ZPD hesaplama güveni (sabit değer - gerçek implementasyonda veri kalitesine bağlı)
        zpd_confidence = 0.8
        confidence_factors.append(zpd_confidence * 0.3)

        return sum(confidence_factors)

    async def adapt_difficulty_culturally(
        self,
        current_difficulty: float,
        student_performance: Dict[str, float],
        cultural_context: TurkishCulturalContext,
    ) -> float:
        """Kültürel faktörlere göre zorluk seviyesini adapte et"""

        adaptation_factor = 1.0

        # Grup başarısı odaklıysa, bireysel başarısızlık daha az zorluk azaltması
        if cultural_context.collective_success > 0.7:
            individual_performance = student_performance.get("individual_score", 0.5)
            group_performance = student_performance.get("group_score", 0.5)

            if group_performance > individual_performance:
                adaptation_factor *= 1.1  # Grup başarısı varsa zorluk artırılabilir

        # Öğretmen saygısı yüksekse, rehberli zorluk artışı
        if cultural_context.teacher_respect_level > 0.8:
            teacher_feedback = student_performance.get("teacher_feedback_score", 0.5)
            if teacher_feedback > 0.6:
                adaptation_factor *= 1.05

        # Aile desteği varsa, ev ödevi zorluğu artırılabilir
        if cultural_context.family_involvement > 0.6:
            homework_performance = student_performance.get("homework_score", 0.5)
            if homework_performance > 0.7:
                adaptation_factor *= 1.08

        adapted_difficulty = current_difficulty * adaptation_factor

        # Sınırlar içinde tut
        adapted_difficulty = max(0.1, min(1.0, adapted_difficulty))

        logger.info(
            f"Zorluk kültürel adaptasyon: {current_difficulty:.2f} → {adapted_difficulty:.2f}"
        )
        return adapted_difficulty

    async def monitor_cultural_learning_patterns(
        self, student_id: str, learning_sessions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Kültürel öğrenme kalıplarını izle ve analiz et"""

        patterns = {
            "group_vs_individual_performance": {},
            "teacher_interaction_correlation": 0.0,
            "family_support_impact": 0.0,
            "maarif_content_engagement": 0.0,
            "cultural_adaptation_success": 0.0,
        }

        if not learning_sessions:
            return patterns

        # Grup vs bireysel performans analizi
        group_scores = [
            s["score"] for s in learning_sessions if s.get("mode") == "group"
        ]
        individual_scores = [
            s["score"] for s in learning_sessions if s.get("mode") == "individual"
        ]

        if group_scores and individual_scores:
            patterns["group_vs_individual_performance"] = {
                "group_average": sum(group_scores) / len(group_scores),
                "individual_average": sum(individual_scores) / len(individual_scores),
                "group_preference_confirmed": sum(group_scores) / len(group_scores)
                > sum(individual_scores) / len(individual_scores),
            }

        # Öğretmen etkileşimi korelasyonu
        teacher_interactions = [
            s.get("teacher_interaction_count", 0) for s in learning_sessions
        ]
        session_scores = [s["score"] for s in learning_sessions]

        if len(teacher_interactions) > 1:
            # Basit korelasyon hesaplama
            patterns[
                "teacher_interaction_correlation"
            ] = self._calculate_simple_correlation(teacher_interactions, session_scores)

        # Maarif içerik katılımı
        maarif_sessions = [
            s for s in learning_sessions if s.get("maarif_aligned", False)
        ]
        if maarif_sessions:
            maarif_scores = [s["score"] for s in maarif_sessions]
            regular_scores = [
                s["score"]
                for s in learning_sessions
                if not s.get("maarif_aligned", False)
            ]

            if maarif_scores and regular_scores:
                patterns["maarif_content_engagement"] = sum(maarif_scores) / len(
                    maarif_scores
                ) - sum(regular_scores) / len(regular_scores)

        logger.info(f"Kültürel öğrenme kalıpları analiz edildi - Öğrenci: {student_id}")
        return patterns

    def _calculate_simple_correlation(self, x: List[float], y: List[float]) -> float:
        """Basit korelasyon hesaplama"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = (
            (n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)
        ) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator
