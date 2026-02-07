"""
Kültürel Adaptasyon Motoru - Türk Kültürü Faktörleri Dinamik Ayarlama

Bu modül, Türk öğrenci davranışlarını ve kültürel faktörleri dikkate alarak
öğrenme deneyimini dinamik olarak ayarlayan devrimsel sistemi içerir.

Özellikler:
- Ramazan, Kurban Bayramı, sınav dönemleri için otomatik adaptasyon
- Aile baskısı ve sosyal çevre faktörlerini hesaplama
- Bölgesel eğitim kültürü farklılıklarını dikkate alma
- Öğrenci yaş grubuna göre kültürel faktör ağırlıklandırma
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Tuple

from hijri_converter import Gregorian

logger = logging.getLogger(__name__)


class CulturalPeriod(Enum):
    """Türk kültürüne özel dönemler"""

    NORMAL = "normal"
    RAMADAN = "ramazan"
    KURBAN_BAYRAMI = "kurban_bayrami"
    RAMAZAN_BAYRAMI = "ramazan_bayrami"
    EXAM_SEASON = "sinav_donemi"
    SUMMER_BREAK = "yaz_tatili"
    WINTER_BREAK = "kis_tatili"
    NATIONAL_HOLIDAYS = "milli_bayramlar"


class RegionalCulture(Enum):
    """Türkiye'deki bölgesel kültür farklılıkları"""

    MARMARA = "marmara"
    EGE = "ege"
    AKDENIZ = "akdeniz"
    IC_ANADOLU = "ic_anadolu"
    KARADENIZ = "karadeniz"
    DOGU_ANADOLU = "dogu_anadolu"
    GUNEYDOGU_ANADOLU = "guneydogu_anadolu"


class AgeGroup(Enum):
    """Öğrenci yaş grupları"""

    ELEMENTARY = "ilkokul"  # 6-10 yaş
    MIDDLE_SCHOOL = "ortaokul"  # 11-14 yaş
    HIGH_SCHOOL = "lise"  # 15-18 yaş
    UNIVERSITY = "universite"  # 18+ yaş


@dataclass
class CulturalFactors:
    """Kültürel faktörler veri yapısı"""

    family_pressure_level: float  # 0.0-1.0
    social_environment_influence: float  # 0.0-1.0
    religious_observance_level: float  # 0.0-1.0
    regional_education_culture: float  # 0.0-1.0
    peer_competition_intensity: float  # 0.0-1.0
    authority_respect_level: float  # 0.0-1.0
    group_study_preference: float  # 0.0-1.0
    individual_achievement_focus: float  # 0.0-1.0


@dataclass
class CulturalAdaptationResult:
    """Kültürel adaptasyon sonucu"""

    current_period: CulturalPeriod
    adaptation_multiplier: float
    recommended_study_hours: int
    optimal_study_times: List[str]
    content_difficulty_adjustment: float
    social_learning_emphasis: float
    individual_focus_emphasis: float
    motivational_message_type: str
    cultural_context_explanation: str


class CulturalAdaptationEngine:
    """
    Türk Kültürü Faktörleri Dinamik Ayarlama Motoru

    Bu sınıf, Türk öğrenci davranışlarını ve kültürel faktörleri analiz ederek
    öğrenme deneyimini dinamik olarak optimize eder.
    """

    def __init__(self):
        """Kültürel adaptasyon motorunu başlat"""

        # Türk kültürüne özel temel faktörler
        self.base_cultural_factors = {
            "family_involvement": 0.85,  # Aile katılımı çok yüksek
            "teacher_respect": 0.90,  # Öğretmene saygı çok yüksek
            "group_learning": 0.75,  # Grup çalışması tercihi yüksek
            "peer_competition": 0.70,  # Akran rekabeti orta-yüksek
            "authority_acceptance": 0.80,  # Otorite kabulü yüksek
            "religious_influence": 0.65,  # Dini değerlerin etkisi orta-yüksek
            "regional_variation": 0.40,  # Bölgesel farklılık orta
        }

        # Yaş grubuna göre kültürel faktör ağırlıkları
        self.age_group_weights = {
            AgeGroup.ELEMENTARY: {
                "family_influence": 0.95,
                "peer_influence": 0.30,
                "individual_autonomy": 0.20,
            },
            AgeGroup.MIDDLE_SCHOOL: {
                "family_influence": 0.85,
                "peer_influence": 0.60,
                "individual_autonomy": 0.40,
            },
            AgeGroup.HIGH_SCHOOL: {
                "family_influence": 0.75,
                "peer_influence": 0.80,
                "individual_autonomy": 0.65,
            },
            AgeGroup.UNIVERSITY: {
                "family_influence": 0.60,
                "peer_influence": 0.70,
                "individual_autonomy": 0.85,
            },
        }

        # Bölgesel kültür faktörleri
        self.regional_factors = {
            RegionalCulture.MARMARA: {
                "modernization_level": 0.90,
                "traditional_values": 0.60,
                "education_priority": 0.95,
                "family_pressure": 0.80,
            },
            RegionalCulture.EGE: {
                "modernization_level": 0.85,
                "traditional_values": 0.65,
                "education_priority": 0.90,
                "family_pressure": 0.75,
            },
            RegionalCulture.AKDENIZ: {
                "modernization_level": 0.75,
                "traditional_values": 0.70,
                "education_priority": 0.85,
                "family_pressure": 0.70,
            },
            RegionalCulture.IC_ANADOLU: {
                "modernization_level": 0.70,
                "traditional_values": 0.85,
                "education_priority": 0.80,
                "family_pressure": 0.85,
            },
            RegionalCulture.KARADENIZ: {
                "modernization_level": 0.65,
                "traditional_values": 0.80,
                "education_priority": 0.85,
                "family_pressure": 0.75,
            },
            RegionalCulture.DOGU_ANADOLU: {
                "modernization_level": 0.55,
                "traditional_values": 0.90,
                "education_priority": 0.75,
                "family_pressure": 0.90,
            },
            RegionalCulture.GUNEYDOGU_ANADOLU: {
                "modernization_level": 0.50,
                "traditional_values": 0.95,
                "education_priority": 0.70,
                "family_pressure": 0.95,
            },
        }

    def detect_current_cultural_period(
        self, current_date: datetime = None
    ) -> CulturalPeriod:
        """
        Mevcut kültürel dönemi tespit et

        Args:
            current_date: Kontrol edilecek tarih (None ise bugün)

        Returns:
            CulturalPeriod: Tespit edilen kültürel dönem
        """
        if current_date is None:
            current_date = datetime.now()

        try:
            # Ramazan ayı kontrolü (Hicri takvim)
            if self._is_ramadan_period(current_date):
                return CulturalPeriod.RAMADAN

            # Kurban Bayramı kontrolü
            if self._is_kurban_bayrami(current_date):
                return CulturalPeriod.KURBAN_BAYRAMI

            # Ramazan Bayramı kontrolü
            if self._is_ramazan_bayrami(current_date):
                return CulturalPeriod.RAMAZAN_BAYRAMI

            # Sınav dönemi kontrolü (YKS, LGS dönemleri)
            if self._is_exam_season(current_date):
                return CulturalPeriod.EXAM_SEASON

            # Yaz tatili kontrolü
            if self._is_summer_break(current_date):
                return CulturalPeriod.SUMMER_BREAK

            # Kış tatili kontrolü
            if self._is_winter_break(current_date):
                return CulturalPeriod.WINTER_BREAK

            # Milli bayramlar kontrolü
            if self._is_national_holiday(current_date):
                return CulturalPeriod.NATIONAL_HOLIDAYS

            return CulturalPeriod.NORMAL

        except Exception as e:
            logger.error(f"Kültürel dönem tespitinde hata: {e}")
            return CulturalPeriod.NORMAL

    def calculate_cultural_adaptation(
        self,
        student_id: str,
        age_group: AgeGroup,
        regional_culture: RegionalCulture,
        cultural_factors: CulturalFactors,
        current_date: datetime = None,
    ) -> CulturalAdaptationResult:
        """
        Öğrenci için kültürel adaptasyon hesapla

        Args:
            student_id: Öğrenci ID'si
            age_group: Öğrenci yaş grubu
            regional_culture: Bölgesel kültür
            cultural_factors: Kültürel faktörler
            current_date: Mevcut tarih

        Returns:
            CulturalAdaptationResult: Adaptasyon sonucu
        """
        if current_date is None:
            current_date = datetime.now()

        # Mevcut kültürel dönemi tespit et
        current_period = self.detect_current_cultural_period(current_date)

        # Temel adaptasyon çarpanını hesapla
        base_multiplier = 1.0

        # Dönemsel ayarlamalar
        period_adjustments = self._get_period_adjustments(current_period)
        base_multiplier *= period_adjustments["study_intensity"]

        # Yaş grubu ayarlamaları
        age_weights = self.age_group_weights[age_group]
        age_adjustment = (
            age_weights["family_influence"] * cultural_factors.family_pressure_level
            + age_weights["peer_influence"]
            * cultural_factors.peer_competition_intensity
            + age_weights["individual_autonomy"]
            * cultural_factors.individual_achievement_focus
        ) / 3

        # Bölgesel ayarlamalar
        regional_adjustment = self._calculate_regional_adjustment(
            regional_culture, cultural_factors
        )

        # Final adaptasyon çarpanı
        adaptation_multiplier = base_multiplier * age_adjustment * regional_adjustment

        # Önerilen çalışma saatleri
        recommended_hours = self._calculate_study_hours(
            current_period, age_group, adaptation_multiplier
        )

        # Optimal çalışma zamanları
        optimal_times = self._get_optimal_study_times(
            current_period, cultural_factors.religious_observance_level
        )

        # İçerik zorluk ayarlaması
        difficulty_adjustment = self._calculate_difficulty_adjustment(
            current_period, cultural_factors, age_group
        )

        # Sosyal vs bireysel öğrenme vurgusu
        social_emphasis, individual_emphasis = self._calculate_learning_emphasis(
            cultural_factors, regional_culture, age_group
        )

        # Motivasyonel mesaj tipi
        message_type = self._determine_motivational_message_type(
            current_period, cultural_factors, age_group
        )

        # Kültürel bağlam açıklaması
        context_explanation = self._generate_cultural_context_explanation(
            current_period, regional_culture, age_group
        )

        return CulturalAdaptationResult(
            current_period=current_period,
            adaptation_multiplier=adaptation_multiplier,
            recommended_study_hours=recommended_hours,
            optimal_study_times=optimal_times,
            content_difficulty_adjustment=difficulty_adjustment,
            social_learning_emphasis=social_emphasis,
            individual_focus_emphasis=individual_emphasis,
            motivational_message_type=message_type,
            cultural_context_explanation=context_explanation,
        )

    def _is_ramadan_period(self, current_date: datetime) -> bool:
        """Ramazan ayı kontrolü"""
        try:
            # Hicri takvime göre Ramazan ayı (9. ay)
            hijri_date = Gregorian(
                current_date.year, current_date.month, current_date.day
            ).to_hijri()

            return hijri_date.month == 9
        except (ValueError, AttributeError) as e:
            # Hata durumunda yaklaşık hesaplama
            logger.debug(f"Hicri takvim hesaplama hatası: {e}")
            return False

    def _is_kurban_bayrami(self, current_date: datetime) -> bool:
        """Kurban Bayramı kontrolü"""
        # Kurban Bayramı tarihleri (yaklaşık)
        kurban_dates_2024 = [(6, 16), (6, 17), (6, 18), (6, 19)]  # Haziran 2024
        kurban_dates_2025 = [(6, 6), (6, 7), (6, 8), (6, 9)]  # Haziran 2025

        current_tuple = (current_date.month, current_date.day)

        if current_date.year == 2024:
            return current_tuple in kurban_dates_2024
        elif current_date.year == 2025:
            return current_tuple in kurban_dates_2025

        return False

    def _is_ramazan_bayrami(self, current_date: datetime) -> bool:
        """Ramazan Bayramı kontrolü"""
        # Ramazan Bayramı tarihleri (yaklaşık)
        ramazan_dates_2024 = [(4, 10), (4, 11), (4, 12)]  # Nisan 2024
        ramazan_dates_2025 = [(3, 30), (3, 31), (4, 1)]  # Mart-Nisan 2025

        current_tuple = (current_date.month, current_date.day)

        if current_date.year == 2024:
            return current_tuple in ramazan_dates_2024
        elif current_date.year == 2025:
            return current_tuple in ramazan_dates_2025

        return False

    def _is_exam_season(self, current_date: datetime) -> bool:
        """Sınav dönemi kontrolü"""
        month = current_date.month

        # YKS dönemi (Haziran-Temmuz)
        if month in [6, 7]:
            return True

        # LGS dönemi (Haziran)
        if month == 6:
            return True

        # Dönem sonu sınavları (Ocak, Haziran)
        if month in [1, 6]:
            return True

        return False

    def _is_summer_break(self, current_date: datetime) -> bool:
        """Yaz tatili kontrolü"""
        month = current_date.month
        return month in [7, 8]  # Temmuz-Ağustos

    def _is_winter_break(self, current_date: datetime) -> bool:
        """Kış tatili kontrolü"""
        month = current_date.month
        day = current_date.day

        # Ocak ayının ilk iki haftası
        if month == 1 and day <= 14:
            return True

        # Aralık ayının son iki haftası
        if month == 12 and day >= 15:
            return True

        return False

    def _is_national_holiday(self, current_date: datetime) -> bool:
        """Milli bayram kontrolü"""
        month = current_date.month
        day = current_date.day

        national_holidays = [
            (4, 23),  # 23 Nisan
            (5, 19),  # 19 Mayıs
            (8, 30),  # 30 Ağustos
            (10, 29),  # 29 Ekim
        ]

        return (month, day) in national_holidays

    def _get_period_adjustments(self, period: CulturalPeriod) -> Dict[str, float]:
        """Dönemsel ayarlamaları getir"""
        adjustments = {
            CulturalPeriod.NORMAL: {
                "study_intensity": 1.0,
                "content_difficulty": 1.0,
                "social_emphasis": 1.0,
            },
            CulturalPeriod.RAMADAN: {
                "study_intensity": 0.7,  # Ramazan'da çalışma yoğunluğu azalır
                "content_difficulty": 0.8,  # İçerik biraz daha kolay
                "social_emphasis": 1.2,  # Sosyal değerler vurgulanır
            },
            CulturalPeriod.KURBAN_BAYRAMI: {
                "study_intensity": 0.3,  # Bayramda çok az çalışma
                "content_difficulty": 0.6,
                "social_emphasis": 1.5,  # Aile ve sosyal değerler ön planda
            },
            CulturalPeriod.RAMAZAN_BAYRAMI: {
                "study_intensity": 0.3,
                "content_difficulty": 0.6,
                "social_emphasis": 1.5,
            },
            CulturalPeriod.EXAM_SEASON: {
                "study_intensity": 1.5,  # Sınav döneminde yoğun çalışma
                "content_difficulty": 1.2,  # Daha zor içerik
                "social_emphasis": 0.8,  # Bireysel odaklanma artırılır
            },
            CulturalPeriod.SUMMER_BREAK: {
                "study_intensity": 0.6,  # Yaz tatilinde rahat çalışma
                "content_difficulty": 0.9,
                "social_emphasis": 1.1,
            },
            CulturalPeriod.WINTER_BREAK: {
                "study_intensity": 0.5,
                "content_difficulty": 0.8,
                "social_emphasis": 1.3,  # Aile zamanı vurgulanır
            },
            CulturalPeriod.NATIONAL_HOLIDAYS: {
                "study_intensity": 0.4,
                "content_difficulty": 0.7,
                "social_emphasis": 1.4,  # Milli değerler vurgulanır
            },
        }

        return adjustments.get(period, adjustments[CulturalPeriod.NORMAL])

    def _calculate_regional_adjustment(
        self, regional_culture: RegionalCulture, cultural_factors: CulturalFactors
    ) -> float:
        """Bölgesel ayarlama hesapla"""

        regional_data = self.regional_factors[regional_culture]

        # Bölgesel faktörleri kültürel faktörlerle birleştir
        adjustment = (
            regional_data["modernization_level"] * 0.2
            + regional_data["traditional_values"]
            * cultural_factors.authority_respect_level
            * 0.3
            + regional_data["education_priority"] * 0.3
            + regional_data["family_pressure"]
            * cultural_factors.family_pressure_level
            * 0.2
        )

        return max(0.5, min(1.5, adjustment))  # 0.5-1.5 arası sınırla

    def _calculate_study_hours(
        self, period: CulturalPeriod, age_group: AgeGroup, adaptation_multiplier: float
    ) -> int:
        """Önerilen günlük çalışma saatlerini hesapla"""

        # Yaş grubuna göre temel çalışma saatleri
        base_hours = {
            AgeGroup.ELEMENTARY: 2,
            AgeGroup.MIDDLE_SCHOOL: 3,
            AgeGroup.HIGH_SCHOOL: 4,
            AgeGroup.UNIVERSITY: 5,
        }

        base = base_hours[age_group]
        adjusted_hours = int(base * adaptation_multiplier)

        # Minimum ve maksimum sınırlar
        min_hours = 1
        max_hours = {
            AgeGroup.ELEMENTARY: 4,
            AgeGroup.MIDDLE_SCHOOL: 6,
            AgeGroup.HIGH_SCHOOL: 8,
            AgeGroup.UNIVERSITY: 10,
        }

        return max(min_hours, min(max_hours[age_group], adjusted_hours))

    def _get_optimal_study_times(
        self, period: CulturalPeriod, religious_observance: float
    ) -> List[str]:
        """Optimal çalışma zamanlarını belirle"""

        if period == CulturalPeriod.RAMADAN:
            if religious_observance > 0.7:
                # Dindar öğrenciler için sahur sonrası ve iftar sonrası
                return ["05:00-07:00", "20:00-22:00"]
            else:
                # Daha esnek program
                return ["06:00-08:00", "19:00-21:00"]

        elif period == CulturalPeriod.EXAM_SEASON:
            # Sınav döneminde yoğun çalışma saatleri
            return ["08:00-12:00", "14:00-18:00", "20:00-22:00"]

        elif period in [CulturalPeriod.KURBAN_BAYRAMI, CulturalPeriod.RAMAZAN_BAYRAMI]:
            # Bayramlarda minimal çalışma
            return ["10:00-11:00"]

        elif period == CulturalPeriod.SUMMER_BREAK:
            # Yaz tatilinde esnek saatler
            return ["09:00-11:00", "16:00-18:00"]

        else:
            # Normal dönem
            return ["08:00-10:00", "14:00-16:00", "19:00-21:00"]

    def _calculate_difficulty_adjustment(
        self,
        period: CulturalPeriod,
        cultural_factors: CulturalFactors,
        age_group: AgeGroup,
    ) -> float:
        """İçerik zorluk ayarlamasını hesapla"""

        period_adjustments = self._get_period_adjustments(period)
        base_difficulty = period_adjustments["content_difficulty"]

        # Aile baskısı yüksekse zorluk artırılabilir
        family_pressure_effect = cultural_factors.family_pressure_level * 0.2

        # Yaş grubuna göre ayarlama
        age_adjustment = {
            AgeGroup.ELEMENTARY: 0.8,
            AgeGroup.MIDDLE_SCHOOL: 0.9,
            AgeGroup.HIGH_SCHOOL: 1.0,
            AgeGroup.UNIVERSITY: 1.1,
        }[age_group]

        final_adjustment = base_difficulty + family_pressure_effect
        final_adjustment *= age_adjustment

        return max(0.5, min(1.5, final_adjustment))

    def _calculate_learning_emphasis(
        self,
        cultural_factors: CulturalFactors,
        regional_culture: RegionalCulture,
        age_group: AgeGroup,
    ) -> Tuple[float, float]:
        """Sosyal vs bireysel öğrenme vurgusunu hesapla"""

        # Temel sosyal öğrenme tercihi
        base_social = cultural_factors.group_study_preference

        # Bölgesel faktör etkisi
        regional_data = self.regional_factors[regional_culture]
        regional_effect = regional_data["traditional_values"] * 0.3

        # Yaş grubu etkisi (yaş arttıkça bireysel öğrenme artar)
        age_weights = self.age_group_weights[age_group]
        individual_tendency = age_weights["individual_autonomy"]

        # Final hesaplama
        social_emphasis = base_social + regional_effect
        individual_emphasis = individual_tendency + (1 - base_social) * 0.5

        # Normalize et (toplamları 1.0 olsun)
        total = social_emphasis + individual_emphasis
        if total > 0:
            social_emphasis /= total
            individual_emphasis /= total

        return social_emphasis, individual_emphasis

    def _determine_motivational_message_type(
        self,
        period: CulturalPeriod,
        cultural_factors: CulturalFactors,
        age_group: AgeGroup,
    ) -> str:
        """Motivasyonel mesaj tipini belirle"""

        if period == CulturalPeriod.RAMADAN:
            return "spiritual_motivation"  # Manevi motivasyon

        elif period == CulturalPeriod.EXAM_SEASON:
            if cultural_factors.family_pressure_level > 0.8:
                return "family_honor_motivation"  # Aile onuru motivasyonu
            else:
                return "personal_achievement_motivation"  # Kişisel başarı

        elif period in [CulturalPeriod.KURBAN_BAYRAMI, CulturalPeriod.RAMAZAN_BAYRAMI]:
            return "family_values_motivation"  # Aile değerleri

        elif period == CulturalPeriod.NATIONAL_HOLIDAYS:
            return "national_pride_motivation"  # Milli gurur

        elif cultural_factors.peer_competition_intensity > 0.7:
            return "peer_competition_motivation"  # Akran rekabeti

        else:
            return "balanced_motivation"  # Dengeli motivasyon

    def _generate_cultural_context_explanation(
        self,
        period: CulturalPeriod,
        regional_culture: RegionalCulture,
        age_group: AgeGroup,
    ) -> str:
        """Kültürel bağlam açıklaması oluştur"""

        explanations = {
            CulturalPeriod.RAMADAN: (
                "Ramazan ayında çalışma programınız daha esnek olacak. "
                "Sahur sonrası ve iftar sonrası saatler en verimli dönemlerdir. "
                "Manevi değerlerle öğrenmeyi birleştirerek daha anlamlı bir deneyim yaşayacaksınız."
            ),
            CulturalPeriod.EXAM_SEASON: (
                "Sınav döneminde yoğun çalışma programı uygulanacak. "
                "Aile desteği ve akran rekabeti motivasyonunuzu artıracak. "
                "Başarı odaklı içeriklerle hedefinize ulaşmanız desteklenecek."
            ),
            CulturalPeriod.KURBAN_BAYRAMI: (
                "Kurban Bayramı'nda aile zamanına öncelik verilecek. "
                "Minimal çalışma programı ile bayram keyfini çıkarabilirsiniz. "
                "Paylaşım ve dayanışma değerleri vurgulanacak."
            ),
            CulturalPeriod.SUMMER_BREAK: (
                "Yaz tatilinde rahat ve eğlenceli öğrenme deneyimi sunulacak. "
                "Sosyal aktivitelerle öğrenmeyi birleştiren içerikler öne çıkacak. "
                "Dinlenme ve öğrenme dengesine özen gösterilecek."
            ),
        }

        base_explanation = explanations.get(
            period, "Normal dönemde dengeli bir çalışma programı uygulanacak."
        )

        # Bölgesel ekleme
        regional_additions = {
            RegionalCulture.MARMARA: " Şehirli yaşam tarzına uygun modern yaklaşımlar kullanılacak.",
            RegionalCulture.DOGU_ANADOLU: " Geleneksel değerlere saygılı, aile odaklı yaklaşım benimsenecek.",
            RegionalCulture.EGE: " Özgür düşünce ve yaratıcılığı destekleyen yöntemler tercih edilecek.",
            RegionalCulture.KARADENIZ: " Çalışkanlık ve azim değerleri vurgulanacak.",
        }

        regional_addition = regional_additions.get(regional_culture, "")

        return base_explanation + regional_addition


class CulturalContextAnalyzer:
    """
    Gerçek Zamanlı Kültürel Bağlam Analizi

    Bu sınıf öğrenci davranış verilerinden kültürel kalıpları tespit eder
    ve gerçek zamanlı adaptasyon sağlar.
    """

    def __init__(self):
        """Kültürel bağlam analizörünü başlat"""

        # Davranış kalıpları için eşik değerleri
        self.behavior_thresholds = {
            "family_involvement_high": 0.8,
            "group_study_preference": 0.7,
            "authority_respect_high": 0.85,
            "peer_competition_active": 0.6,
            "religious_observance_high": 0.75,
        }

        # Kültürel kalıp tanımlayıcıları
        self.cultural_patterns = {
            "traditional_family_oriented": {
                "family_involvement": 0.9,
                "authority_respect": 0.9,
                "group_preference": 0.8,
                "individual_autonomy": 0.3,
            },
            "modern_individualistic": {
                "family_involvement": 0.6,
                "authority_respect": 0.6,
                "group_preference": 0.4,
                "individual_autonomy": 0.8,
            },
            "balanced_cultural": {
                "family_involvement": 0.75,
                "authority_respect": 0.75,
                "group_preference": 0.6,
                "individual_autonomy": 0.6,
            },
            "peer_competitive": {
                "family_involvement": 0.7,
                "authority_respect": 0.7,
                "group_preference": 0.8,
                "individual_autonomy": 0.5,
                "competition_focus": 0.9,
            },
        }

    async def analyze_student_cultural_context(
        self,
        student_id: str,
        behavioral_data: Dict[str, Any],
        interaction_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Öğrenci davranış verilerinden kültürel bağlamı analiz et

        Args:
            student_id: Öğrenci ID'si
            behavioral_data: Davranış verileri
            interaction_history: Etkileşim geçmişi

        Returns:
            Dict: Kültürel bağlam analizi sonucu
        """

        # Aile katılım seviyesini değerlendir
        family_involvement = await self._assess_family_involvement(
            behavioral_data, interaction_history
        )

        # Grup çalışması vs bireysel çalışma tercihini analiz et
        study_preference = await self._analyze_study_preferences(
            behavioral_data, interaction_history
        )

        # Öğretmene saygı ve otorite kabulü seviyesini ölç
        authority_respect = await self._measure_authority_respect(
            behavioral_data, interaction_history
        )

        # Akran rekabeti ve sosyal etkileşim seviyesini tespit et
        peer_interaction = await self._analyze_peer_interaction(
            behavioral_data, interaction_history
        )

        # Kültürel kalıp tespiti
        cultural_pattern = await self._identify_cultural_pattern(
            family_involvement, study_preference, authority_respect, peer_interaction
        )

        # Dinamik ayarlama önerileri
        adaptation_recommendations = await self._generate_adaptation_recommendations(
            cultural_pattern, behavioral_data
        )

        return {
            "student_id": student_id,
            "cultural_analysis": {
                "family_involvement_level": family_involvement,
                "study_preference_type": study_preference,
                "authority_respect_level": authority_respect,
                "peer_interaction_style": peer_interaction,
                "identified_pattern": cultural_pattern,
            },
            "adaptation_recommendations": adaptation_recommendations,
            "confidence_score": self._calculate_analysis_confidence(
                behavioral_data, interaction_history
            ),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    async def _assess_family_involvement(
        self, behavioral_data: Dict[str, Any], interaction_history: List[Dict[str, Any]]
    ) -> float:
        """Aile katılım seviyesini değerlendir"""

        involvement_indicators = 0.0
        total_indicators = 0.0

        # Veli hesabı aktivitesi
        if "parent_account_activity" in behavioral_data:
            involvement_indicators += behavioral_data["parent_account_activity"] * 0.3
            total_indicators += 0.3

        # Aile ile ilgili sorular/yorumlar
        family_mentions = 0
        for interaction in interaction_history[-50:]:  # Son 50 etkileşim
            if any(
                word in interaction.get("content", "").lower()
                for word in ["ailem", "annem", "babam", "velim", "aile"]
            ):
                family_mentions += 1

        if len(interaction_history) > 0:
            family_mention_ratio = family_mentions / min(50, len(interaction_history))
            involvement_indicators += family_mention_ratio * 0.4
            total_indicators += 0.4

        # Çalışma saatleri (aile rutinlerine uyum)
        if "study_schedule_regularity" in behavioral_data:
            regularity = behavioral_data["study_schedule_regularity"]
            involvement_indicators += regularity * 0.3
            total_indicators += 0.3

        return (
            involvement_indicators / total_indicators if total_indicators > 0 else 0.5
        )

    async def _analyze_study_preferences(
        self, behavioral_data: Dict[str, Any], interaction_history: List[Dict[str, Any]]
    ) -> str:
        """Çalışma tercihlerini analiz et"""

        group_indicators = 0
        individual_indicators = 0

        # Grup çalışması ile ilgili aktiviteler
        if "group_study_sessions" in behavioral_data:
            group_indicators += behavioral_data["group_study_sessions"]

        # Bireysel çalışma süreleri
        if "individual_study_time" in behavioral_data:
            individual_indicators += behavioral_data["individual_study_time"]

        # Sohbet içeriği analizi
        for interaction in interaction_history[-30:]:
            content = interaction.get("content", "").lower()
            if any(
                word in content
                for word in ["arkadaşlarımla", "beraber", "grup", "birlikte"]
            ):
                group_indicators += 1
            elif any(word in content for word in ["tek başıma", "kendi", "bireysel"]):
                individual_indicators += 1

        if group_indicators > individual_indicators * 1.2:
            return "group_oriented"
        elif individual_indicators > group_indicators * 1.2:
            return "individual_oriented"
        else:
            return "balanced"

    async def _measure_authority_respect(
        self, behavioral_data: Dict[str, Any], interaction_history: List[Dict[str, Any]]
    ) -> float:
        """Otorite saygısı seviyesini ölç"""

        respect_score = 0.0
        total_interactions = 0

        # Öğretmen/sistem önerilerine uyum
        if "recommendation_compliance" in behavioral_data:
            respect_score += behavioral_data["recommendation_compliance"] * 0.4

        # Nezaket seviyesi ve saygılı dil kullanımı
        polite_interactions = 0
        for interaction in interaction_history[-20:]:
            content = interaction.get("content", "").lower()
            if any(
                word in content for word in ["lütfen", "teşekkür", "saygılar", "özür"]
            ):
                polite_interactions += 1
            total_interactions += 1

        if total_interactions > 0:
            politeness_ratio = polite_interactions / total_interactions
            respect_score += politeness_ratio * 0.6

        return min(1.0, respect_score)

    async def _analyze_peer_interaction(
        self, behavioral_data: Dict[str, Any], interaction_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Akran etkileşimini analiz et"""

        competition_level = 0.0
        collaboration_level = 0.0

        # Rekabet göstergeleri
        if "leaderboard_engagement" in behavioral_data:
            competition_level += behavioral_data["leaderboard_engagement"] * 0.5

        if "score_comparison_frequency" in behavioral_data:
            competition_level += behavioral_data["score_comparison_frequency"] * 0.3

        # İşbirliği göstergeleri
        if "help_requests_sent" in behavioral_data:
            collaboration_level += behavioral_data["help_requests_sent"] * 0.3

        if "help_provided_to_peers" in behavioral_data:
            collaboration_level += behavioral_data["help_provided_to_peers"] * 0.4

        # Sohbet analizi
        competitive_mentions = 0
        collaborative_mentions = 0

        for interaction in interaction_history[-25:]:
            content = interaction.get("content", "").lower()
            if any(
                word in content for word in ["yarış", "rekabet", "geçmek", "kazanmak"]
            ):
                competitive_mentions += 1
            elif any(
                word in content for word in ["yardım", "beraber", "paylaş", "destek"]
            ):
                collaborative_mentions += 1

        return {
            "competition_level": min(
                1.0, competition_level + competitive_mentions * 0.1
            ),
            "collaboration_level": min(
                1.0, collaboration_level + collaborative_mentions * 0.1
            ),
        }

    async def _identify_cultural_pattern(
        self,
        family_involvement: float,
        study_preference: str,
        authority_respect: float,
        peer_interaction: Dict[str, float],
    ) -> str:
        """Kültürel kalıbı tespit et"""

        # Skorları normalize et
        scores = {
            "family_involvement": family_involvement,
            "authority_respect": authority_respect,
            "group_preference": 1.0
            if study_preference == "group_oriented"
            else 0.5
            if study_preference == "balanced"
            else 0.0,
            "individual_autonomy": 1.0
            if study_preference == "individual_oriented"
            else 0.5
            if study_preference == "balanced"
            else 0.0,
            "competition_focus": peer_interaction.get("competition_level", 0.0),
        }

        # Her kalıpla benzerlik hesapla
        best_match = "balanced_cultural"
        best_score = 0.0

        for pattern_name, pattern_values in self.cultural_patterns.items():
            similarity = 0.0
            count = 0

            for key, expected_value in pattern_values.items():
                if key in scores:
                    # Euclidean distance benzeri hesaplama
                    similarity += 1 - abs(scores[key] - expected_value)
                    count += 1

            if count > 0:
                avg_similarity = similarity / count
                if avg_similarity > best_score:
                    best_score = avg_similarity
                    best_match = pattern_name

        return best_match

    async def _generate_adaptation_recommendations(
        self, cultural_pattern: str, behavioral_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adaptasyon önerilerini oluştur"""

        recommendations = {
            "traditional_family_oriented": {
                "content_style": "family_values_integrated",
                "motivation_type": "family_honor_based",
                "study_schedule": "family_routine_aligned",
                "social_features": "group_study_emphasized",
                "authority_guidance": "teacher_led_approach",
            },
            "modern_individualistic": {
                "content_style": "self_directed_learning",
                "motivation_type": "personal_achievement",
                "study_schedule": "flexible_self_paced",
                "social_features": "optional_collaboration",
                "authority_guidance": "advisory_approach",
            },
            "balanced_cultural": {
                "content_style": "mixed_approach",
                "motivation_type": "balanced_motivation",
                "study_schedule": "structured_flexibility",
                "social_features": "both_individual_group",
                "authority_guidance": "supportive_guidance",
            },
            "peer_competitive": {
                "content_style": "gamified_learning",
                "motivation_type": "competition_based",
                "study_schedule": "challenge_oriented",
                "social_features": "leaderboards_rankings",
                "authority_guidance": "coach_mentor_style",
            },
        }

        base_recommendations = recommendations.get(
            cultural_pattern, recommendations["balanced_cultural"]
        )

        # Davranış verilerine göre özelleştir
        customizations: Dict[str, Any] = {}

        if behavioral_data.get("study_time_preference") == "evening":
            customizations["optimal_study_times"] = ["19:00-21:00", "21:00-23:00"]
        elif behavioral_data.get("study_time_preference") == "morning":
            customizations["optimal_study_times"] = ["06:00-08:00", "08:00-10:00"]

        if behavioral_data.get("attention_span", 0) < 30:  # dakika
            customizations["content_chunking"] = "short_segments"
        elif behavioral_data.get("attention_span", 0) > 60:
            customizations["content_chunking"] = "long_form_content"

        return {**base_recommendations, **customizations}

    def _calculate_analysis_confidence(
        self, behavioral_data: Dict[str, Any], interaction_history: List[Dict[str, Any]]
    ) -> float:
        """Analiz güven skorunu hesapla"""

        confidence = 0.0

        # Veri miktarı faktörü
        data_points = len(behavioral_data)
        interaction_count = len(interaction_history)

        data_confidence = min(1.0, (data_points + interaction_count) / 100)
        confidence += data_confidence * 0.4

        # Veri çeşitliliği faktörü
        data_types = len(set(behavioral_data.keys()))
        diversity_confidence = min(1.0, data_types / 20)
        confidence += diversity_confidence * 0.3

        # Zaman aralığı faktörü (daha uzun gözlem daha güvenilir)
        if interaction_history:
            time_span_days = (
                datetime.now()
                - datetime.fromisoformat(
                    interaction_history[0].get("timestamp", datetime.now().isoformat())
                )
            ).days
            time_confidence = min(1.0, time_span_days / 30)  # 30 gün maksimum
            confidence += time_confidence * 0.3

        return confidence
