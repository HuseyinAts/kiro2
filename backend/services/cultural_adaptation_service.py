"""
Kültürel Adaptasyon Servisi

Bu servis, Türk kültürü faktörlerini dikkate alarak öğrenci deneyimini
dinamik olarak ayarlayan sistemin servis katmanını sağlar.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from algorithms.cultural_adaptation_engine import (
    AgeGroup,
    CulturalAdaptationEngine,
    CulturalAdaptationResult,
    CulturalContextAnalyzer,
    CulturalFactors,
    CulturalPeriod,
    RegionalCulture,
)
from core.database import get_db_session

logger = logging.getLogger(__name__)


class CulturalAdaptationService:
    """
    Kültürel Adaptasyon Servisi

    Türk öğrenci kültürüne uyarlanmış dinamik öğrenme deneyimi sağlar.
    """

    def __init__(self) -> None:
        """Servisi başlat."""
        self.adaptation_engine = CulturalAdaptationEngine()
        self.context_analyzer = CulturalContextAnalyzer()

        # Cache için basit in-memory storage
        self._adaptation_cache: dict[str, dict[str, Any]] = {}
        self._cache_ttl = 3600  # 1 saat

    async def get_student_cultural_adaptation(
        self, student_id: str, force_refresh: bool = False
    ) -> dict[str, Any]:
        """
        Öğrenci için kültürel adaptasyon bilgilerini getir

        Args:
            student_id: Öğrenci ID'si
            force_refresh: Cache'i yoksay ve yeniden hesapla

        Returns:
            Dict: Kültürel adaptasyon bilgileri
        """
        try:
            # Cache kontrolü
            if not force_refresh and student_id in self._adaptation_cache:
                cached_data = self._adaptation_cache[student_id]
                cache_time = cached_data.get("timestamp", 0)

                if (datetime.now().timestamp() - cache_time) < self._cache_ttl:
                    logger.info(
                        f"Cache'den kültürel adaptasyon döndürülüyor: {student_id}"
                    )
                    return cached_data["data"]

            # Öğrenci bilgilerini getir
            async with get_db_session() as session:
                student_info = await self._get_student_info(session, student_id)

                if not student_info:
                    raise ValueError(f"Öğrenci bulunamadı: {student_id}")

                # Davranış verilerini topla
                behavioral_data = await self._collect_behavioral_data(
                    session, student_id
                )
                interaction_history = await self._get_interaction_history(
                    session, student_id
                )

                # Kültürel faktörleri belirle
                cultural_factors = await self._determine_cultural_factors(
                    student_info, behavioral_data, interaction_history
                )

                # Adaptasyon hesapla
                adaptation_result = (
                    self.adaptation_engine.calculate_cultural_adaptation(
                        student_id=student_id,
                        age_group=self._determine_age_group(student_info["birth_date"]),
                        regional_culture=self._determine_regional_culture(
                            student_info["location"]
                        ),
                        cultural_factors=cultural_factors,
                        current_date=datetime.now(),
                    )
                )

                # Gerçek zamanlı kültürel bağlam analizi
                context_analysis = (
                    await self.context_analyzer.analyze_student_cultural_context(
                        student_id=student_id,
                        behavioral_data=behavioral_data,
                        interaction_history=interaction_history,
                    )
                )

                # Sonucu formatla
                result = {
                    "student_id": student_id,
                    "cultural_adaptation": {
                        "current_period": adaptation_result.current_period.value,
                        "adaptation_multiplier": adaptation_result.adaptation_multiplier,
                        "recommended_study_hours": adaptation_result.recommended_study_hours,
                        "optimal_study_times": adaptation_result.optimal_study_times,
                        "content_difficulty_adjustment": adaptation_result.content_difficulty_adjustment,
                        "social_learning_emphasis": adaptation_result.social_learning_emphasis,
                        "individual_focus_emphasis": adaptation_result.individual_focus_emphasis,
                        "motivational_message_type": adaptation_result.motivational_message_type,
                        "cultural_context_explanation": adaptation_result.cultural_context_explanation,
                    },
                    "context_analysis": context_analysis,
                    "cultural_factors": {
                        "family_pressure_level": cultural_factors.family_pressure_level,
                        "social_environment_influence": cultural_factors.social_environment_influence,
                        "religious_observance_level": cultural_factors.religious_observance_level,
                        "regional_education_culture": cultural_factors.regional_education_culture,
                        "peer_competition_intensity": cultural_factors.peer_competition_intensity,
                        "authority_respect_level": cultural_factors.authority_respect_level,
                        "group_study_preference": cultural_factors.group_study_preference,
                        "individual_achievement_focus": cultural_factors.individual_achievement_focus,
                    },
                    "recommendations": await self._generate_personalized_recommendations(
                        adaptation_result, context_analysis
                    ),
                    "last_updated": datetime.now().isoformat(),
                }

                # Cache'e kaydet
                self._adaptation_cache[student_id] = {
                    "data": result,
                    "timestamp": datetime.now().timestamp(),
                }

                logger.info(f"Kültürel adaptasyon hesaplandı: {student_id}")
                return result

        except Exception as e:
            logger.error(f"Kültürel adaptasyon hesaplama hatası: {e}")
            raise

    async def update_cultural_context(
        self, student_id: str, behavioral_update: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Öğrenci davranış verilerini güncelle ve adaptasyonu yenile

        Args:
            student_id: Öğrenci ID'si
            behavioral_update: Yeni davranış verileri

        Returns:
            Dict: Güncellenmiş adaptasyon bilgileri
        """
        try:
            # Davranış verilerini kaydet
            async with get_db_session() as session:
                await self._save_behavioral_update(
                    session, student_id, behavioral_update
                )

            # Cache'i temizle ve yeniden hesapla
            if student_id in self._adaptation_cache:
                del self._adaptation_cache[student_id]

            return await self.get_student_cultural_adaptation(
                student_id, force_refresh=True
            )

        except Exception as e:
            logger.error(f"Kültürel bağlam güncelleme hatası: {e}")
            raise

    async def get_cultural_period_info(self, date: datetime = None) -> dict[str, Any]:
        """
        Mevcut kültürel dönem bilgilerini getir

        Args:
            date: Kontrol edilecek tarih (None ise bugün)

        Returns:
            Dict: Kültürel dönem bilgileri
        """
        if date is None:
            date = datetime.now()

        current_period = self.adaptation_engine.detect_current_cultural_period(date)

        period_info = {
            "current_period": current_period.value,
            "period_name": self._get_period_display_name(current_period),
            "period_description": self._get_period_description(current_period),
            "general_recommendations": self._get_general_period_recommendations(
                current_period
            ),
            "date_checked": date.isoformat(),
        }

        return period_info

    async def get_regional_culture_info(self, region: str) -> dict[str, Any]:
        """
        Bölgesel kültür bilgilerini getir

        Args:
            region: Bölge adı

        Returns:
            Dict: Bölgesel kültür bilgileri
        """
        try:
            regional_culture = RegionalCulture(region.lower())
            regional_factors = self.adaptation_engine.regional_factors[regional_culture]

            return {
                "region": region,
                "cultural_factors": regional_factors,
                "characteristics": self._get_regional_characteristics(regional_culture),
                "education_approach": self._get_regional_education_approach(
                    regional_culture
                ),
            }

        except ValueError:
            # Bilinmeyen bölge için varsayılan değerler
            return {
                "region": region,
                "cultural_factors": {
                    "modernization_level": 0.7,
                    "traditional_values": 0.7,
                    "education_priority": 0.8,
                    "family_pressure": 0.75,
                },
                "characteristics": "Genel Türk kültürü özellikleri",
                "education_approach": "Dengeli yaklaşım",
            }

    async def _get_student_info(
        self, session: AsyncSession, student_id: str
    ) -> dict[str, Any] | None:
        """Öğrenci bilgilerini getir"""
        # Bu kısım gerçek veritabanı implementasyonunda User modelinden gelecek
        # Şimdilik mock data döndürüyoruz
        return {
            "id": student_id,
            "birth_date": datetime(2008, 5, 15),  # 15 yaşında örnek öğrenci
            "location": "istanbul",
            "grade_level": 9,
        }

    async def _collect_behavioral_data(
        self, session: AsyncSession, student_id: str
    ) -> dict[str, Any]:
        """Davranış verilerini topla"""
        # Mock behavioral data - gerçek implementasyonda veritabanından gelecek
        return {
            "study_time_preference": "evening",
            "group_study_sessions": 3,
            "individual_study_time": 120,  # dakika
            "parent_account_activity": 0.8,
            "recommendation_compliance": 0.75,
            "leaderboard_engagement": 0.6,
            "help_requests_sent": 5,
            "help_provided_to_peers": 3,
            "attention_span": 45,  # dakika
            "study_schedule_regularity": 0.8,
        }

    async def _get_interaction_history(
        self, session: AsyncSession, student_id: str
    ) -> list[dict[str, Any]]:
        """Etkileşim geçmişini getir"""
        # Mock interaction history - gerçek implementasyonda veritabanından gelecek
        return [
            {
                "content": "Ailem matematik çalışmamı istiyor ama zorlanıyorum",
                "timestamp": "2024-01-15T10:00:00",
                "type": "chat_message",
            },
            {
                "content": "Arkadaşlarımla beraber çalışmak daha eğlenceli",
                "timestamp": "2024-01-14T15:30:00",
                "type": "chat_message",
            },
            {
                "content": "Lütfen daha kolay sorular verebilir misiniz?",
                "timestamp": "2024-01-13T09:15:00",
                "type": "help_request",
            },
        ]

    async def _determine_cultural_factors(
        self,
        student_info: dict[str, Any],
        behavioral_data: dict[str, Any],
        interaction_history: list[dict[str, Any]],
    ) -> CulturalFactors:
        """Kültürel faktörleri belirle"""

        # Davranış verilerinden kültürel faktörleri çıkar
        family_pressure = behavioral_data.get("parent_account_activity", 0.5)
        social_influence = min(
            1.0,
            (
                behavioral_data.get("group_study_sessions", 0) * 0.1
                + behavioral_data.get("help_requests_sent", 0) * 0.05
            ),
        )

        # Etkileşim geçmişinden dini gözlem seviyesini tahmin et
        religious_keywords = ["ramazan", "bayram", "namaz", "dua", "allah"]
        religious_mentions = sum(
            1
            for interaction in interaction_history
            if any(
                keyword in interaction.get("content", "").lower()
                for keyword in religious_keywords
            )
        )
        religious_observance = min(1.0, religious_mentions * 0.2)

        return CulturalFactors(
            family_pressure_level=family_pressure,
            social_environment_influence=social_influence,
            religious_observance_level=religious_observance,
            regional_education_culture=0.75,  # Varsayılan değer
            peer_competition_intensity=behavioral_data.get(
                "leaderboard_engagement", 0.5
            ),
            authority_respect_level=behavioral_data.get(
                "recommendation_compliance", 0.7
            ),
            group_study_preference=min(
                1.0, behavioral_data.get("group_study_sessions", 0) * 0.2
            ),
            individual_achievement_focus=0.6,  # Varsayılan değer
        )

    def _determine_age_group(self, birth_date: datetime) -> AgeGroup:
        """Yaş grubunu belirle"""
        age = (datetime.now() - birth_date).days // 365

        if age <= 10:
            return AgeGroup.ELEMENTARY
        if age <= 14:
            return AgeGroup.MIDDLE_SCHOOL
        if age <= 18:
            return AgeGroup.HIGH_SCHOOL
        return AgeGroup.UNIVERSITY

    def _determine_regional_culture(self, location: str) -> RegionalCulture:
        """Bölgesel kültürü belirle"""
        location_lower = location.lower()

        # Şehir-bölge eşleştirmesi
        region_mapping = {
            "istanbul": RegionalCulture.MARMARA,
            "ankara": RegionalCulture.IC_ANADOLU,
            "izmir": RegionalCulture.EGE,
            "antalya": RegionalCulture.AKDENIZ,
            "trabzon": RegionalCulture.KARADENIZ,
            "erzurum": RegionalCulture.DOGU_ANADOLU,
            "diyarbakir": RegionalCulture.GUNEYDOGU_ANADOLU,
            "bursa": RegionalCulture.MARMARA,
            "adana": RegionalCulture.AKDENIZ,
            "konya": RegionalCulture.IC_ANADOLU,
        }

        return region_mapping.get(location_lower, RegionalCulture.IC_ANADOLU)

    async def _generate_personalized_recommendations(
        self,
        adaptation_result: CulturalAdaptationResult,
        context_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Kişiselleştirilmiş öneriler oluştur"""

        recommendations = {
            "study_schedule": {
                "daily_hours": adaptation_result.recommended_study_hours,
                "optimal_times": adaptation_result.optimal_study_times,
                "break_intervals": "25 dakika çalış, 5 dakika mola"
                if adaptation_result.recommended_study_hours <= 3
                else "45 dakika çalış, 10 dakika mola",
            },
            "content_approach": {
                "difficulty_level": "kolay"
                if adaptation_result.content_difficulty_adjustment < 0.8
                else "orta"
                if adaptation_result.content_difficulty_adjustment < 1.2
                else "zor",
                "social_learning_ratio": f"{int(adaptation_result.social_learning_emphasis * 100)}% grup, {int(adaptation_result.individual_focus_emphasis * 100)}% bireysel",
                "motivational_style": adaptation_result.motivational_message_type,
            },
            "cultural_considerations": {
                "period_awareness": adaptation_result.cultural_context_explanation,
                "family_involvement": "yüksek"
                if context_analysis["cultural_analysis"]["family_involvement_level"]
                > 0.7
                else "orta",
                "peer_interaction": context_analysis["cultural_analysis"][
                    "peer_interaction_style"
                ],
            },
            "adaptive_features": context_analysis.get("adaptation_recommendations", {}),
        }

        return recommendations

    async def _save_behavioral_update(
        self, session: AsyncSession, student_id: str, behavioral_update: dict[str, Any]
    ):
        """Davranış güncellemesini kaydet"""
        # Gerçek implementasyonda veritabanına kaydedilecek
        logger.info(f"Davranış verisi güncellendi: {student_id} - {behavioral_update}")

    def _get_period_display_name(self, period: CulturalPeriod) -> str:
        """Dönem görüntü adını getir"""
        names = {
            CulturalPeriod.NORMAL: "Normal Dönem",
            CulturalPeriod.RAMADAN: "Ramazan Ayı",
            CulturalPeriod.KURBAN_BAYRAMI: "Kurban Bayramı",
            CulturalPeriod.RAMAZAN_BAYRAMI: "Ramazan Bayramı",
            CulturalPeriod.EXAM_SEASON: "Sınav Dönemi",
            CulturalPeriod.SUMMER_BREAK: "Yaz Tatili",
            CulturalPeriod.WINTER_BREAK: "Kış Tatili",
            CulturalPeriod.NATIONAL_HOLIDAYS: "Milli Bayramlar",
        }
        return names.get(period, "Bilinmeyen Dönem")

    def _get_period_description(self, period: CulturalPeriod) -> str:
        """Dönem açıklamasını getir"""
        descriptions = {
            CulturalPeriod.RAMADAN: "Ramazan ayında çalışma programınız daha esnek ve manevi değerlerle uyumlu olacak.",
            CulturalPeriod.EXAM_SEASON: "Sınav döneminde yoğun ve hedefe odaklı çalışma programı uygulanacak.",
            CulturalPeriod.SUMMER_BREAK: "Yaz tatilinde rahat ve eğlenceli öğrenme deneyimi sunulacak.",
            CulturalPeriod.KURBAN_BAYRAMI: "Bayram döneminde aile zamanına öncelik verilecek.",
        }
        return descriptions.get(period, "Normal çalışma programı uygulanacak.")

    def _get_general_period_recommendations(self, period: CulturalPeriod) -> list[str]:
        """Genel dönem önerilerini getir"""
        recommendations = {
            CulturalPeriod.RAMADAN: [
                "Sahur sonrası ve iftar sonrası saatleri değerlendirin",
                "Manevi değerlerle öğrenmeyi birleştirin",
                "Daha kısa ama etkili çalışma seansları planlayın",
            ],
            CulturalPeriod.EXAM_SEASON: [
                "Günlük çalışma saatlerinizi artırın",
                "Zayıf konularınıza odaklanın",
                "Düzenli tekrar programı uygulayın",
            ],
            CulturalPeriod.SUMMER_BREAK: [
                "Eğlenceli öğrenme aktivitelerini tercih edin",
                "Sosyal öğrenme fırsatlarını değerlendirin",
                "Dinlenme ve öğrenme dengesini koruyun",
            ],
        }
        return recommendations.get(period, ["Düzenli çalışma programınızı sürdürün"])

    def _get_regional_characteristics(self, regional_culture: RegionalCulture) -> str:
        """Bölgesel özellikler açıklaması"""
        characteristics = {
            RegionalCulture.MARMARA: "Modern yaşam tarzı, yüksek eğitim beklentisi, rekabetçi ortam",
            RegionalCulture.EGE: "Özgür düşünce, yaratıcılık, dengeli yaklaşım",
            RegionalCulture.AKDENIZ: "Sosyal yaşam odaklı, esnek yaklaşım, aile değerleri",
            RegionalCulture.IC_ANADOLU: "Geleneksel değerler, disiplinli çalışma, otorite saygısı",
            RegionalCulture.KARADENIZ: "Çalışkanlık, azim, toplumsal dayanışma",
            RegionalCulture.DOGU_ANADOLU: "Güçlü aile bağları, geleneksel eğitim yaklaşımı",
            RegionalCulture.GUNEYDOGU_ANADOLU: "Aile odaklı kararlar, toplumsal değerler",
        }
        return characteristics.get(regional_culture, "Genel Türk kültürü özellikleri")

    def _get_regional_education_approach(
        self, regional_culture: RegionalCulture
    ) -> str:
        """Bölgesel eğitim yaklaşımı"""
        approaches = {
            RegionalCulture.MARMARA: "Teknoloji destekli, bireysel başarı odaklı",
            RegionalCulture.EGE: "Yaratıcılık ve eleştirel düşünce vurgulu",
            RegionalCulture.AKDENIZ: "Sosyal öğrenme ve işbirliği odaklı",
            RegionalCulture.IC_ANADOLU: "Geleneksel değerlerle modern eğitim sentezi",
            RegionalCulture.KARADENIZ: "Çalışkanlık ve sebat vurgulu",
            RegionalCulture.DOGU_ANADOLU: "Aile desteği ve rehberlik odaklı",
            RegionalCulture.GUNEYDOGU_ANADOLU: "Toplumsal değerler ve aile onuru odaklı",
        }
        return approaches.get(regional_culture, "Dengeli eğitim yaklaşımı")
