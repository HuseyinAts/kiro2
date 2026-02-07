"""
MEB (Milli Eğitim Bakanlığı) Resource Client

Bu modül, MEB resmi kaynaklarından bilgi doğrulaması yapar.

Features:
- MEB müfredat kazanımları doğrulama
- Resmi eğitim içeriği kontrolü
- Source priority: MEB en yüksek öncelik (%60)

Requirements: REQ-4.4
"""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MEBVerificationResult(BaseModel):
    """MEB doğrulama sonucu"""
    found: bool = Field(description="Bilgi bulundu mu")
    confidence: float = Field(ge=0.0, le=1.0, description="Güven skoru")
    status: str = Field(description="true/false/partially_true/unverified")
    evidence: Optional[str] = Field(default=None, description="Kanıt metni")
    kazanim_code: Optional[str] = Field(default=None, description="İlgili kazanım kodu")
    grade_level: Optional[int] = Field(default=None, description="Sınıf seviyesi")


class MEBResourceClient:
    """
    MEB resmi kaynak client'ı.

    Müfredat kazanımları ve eğitim içeriği doğrulaması yapar.
    MEB kaynakları en yüksek güvenilirliğe sahiptir.
    """

    # MEB güvenilirlik çarpanı (diğer kaynaklara göre ağırlık)
    TRUST_MULTIPLIER = 0.6

    def __init__(
        self,
        api_url: Optional[str] = None,
        use_local_data: bool = True,
    ):
        """
        Args:
            api_url: MEB API URL'i (varsa)
            use_local_data: Lokal müfredat verisini kullan
        """
        self.api_url = api_url
        self.use_local_data = use_local_data

        # Lokal müfredat verisi (offline kullanım için)
        self._curriculum_data = self._load_curriculum_data()

    def _load_curriculum_data(self) -> Dict[str, Any]:
        """
        Müfredat verisini yükle.

        Returns:
            Dict: Müfredat verisi
        """
        # YKS/TYT/AYT müfredat konuları
        return {
            "matematik": {
                "temel": [
                    "sayılar ve işlemler",
                    "cebir",
                    "denklem ve eşitsizlikler",
                    "üstel ve logaritmik fonksiyonlar",
                    "diziler",
                    "polinomlar",
                    "permütasyon ve kombinasyon",
                    "olasılık",
                    "istatistik",
                ],
                "geometri": [
                    "üçgenler",
                    "dörtgenler",
                    "çember ve daire",
                    "katı cisimler",
                    "analitik geometri",
                    "trigonometri",
                ],
                "facts": {
                    "pi sayısı": "3.14159...",
                    "euler sayısı": "2.71828...",
                    "altın oran": "1.618...",
                },
            },
            "fizik": {
                "konular": [
                    "hareket ve kuvvet",
                    "enerji",
                    "ısı ve sıcaklık",
                    "elektrik",
                    "manyetizma",
                    "optik",
                    "dalgalar",
                    "modern fizik",
                ],
                "facts": {
                    "ışık hızı": "299,792,458 m/s",
                    "yerçekimi ivmesi": "9.8 m/s²",
                    "planck sabiti": "6.626×10⁻³⁴ J·s",
                },
            },
            "kimya": {
                "konular": [
                    "atom ve periyodik sistem",
                    "kimyasal bağlar",
                    "madde ve özellikleri",
                    "kimyasal tepkimeler",
                    "asitler ve bazlar",
                    "organik kimya",
                ],
                "facts": {
                    "avogadro sayısı": "6.022×10²³",
                    "su kaynama noktası": "100°C (1 atm)",
                    "su donma noktası": "0°C (1 atm)",
                },
            },
            "biyoloji": {
                "konular": [
                    "hücre",
                    "canlıların sınıflandırılması",
                    "kalıtım",
                    "ekosistem",
                    "insan fizyolojisi",
                ],
                "facts": {
                    "dna yapısı": "çift sarmal",
                    "hücre teorisi": "tüm canlılar hücrelerden oluşur",
                    "fotosentez": "6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂",
                },
            },
            "tarih": {
                "konular": [
                    "türk inkılap tarihi",
                    "osmanlı tarihi",
                    "türk-islam tarihi",
                    "dünya tarihi",
                ],
                "facts": {
                    "cumhuriyet": "29 Ekim 1923",
                    "istanbul fethi": "29 Mayıs 1453",
                    "osmanlı kuruluşu": "1299",
                    "kurtuluş savaşı": "1919-1923",
                    "atatürk doğum": "1881",
                    "lozan antlaşması": "24 Temmuz 1923",
                },
            },
            "coğrafya": {
                "konular": [
                    "türkiye coğrafyası",
                    "dünya coğrafyası",
                    "beşeri coğrafya",
                    "fiziki coğrafya",
                ],
                "facts": {
                    "türkiye yüzölçümü": "783,562 km²",
                    "türkiye nüfusu": "~85 milyon",
                    "başkent": "Ankara",
                },
            },
        }

    async def verify_claim(self, claim: str) -> MEBVerificationResult:
        """
        Bir iddiayı MEB kaynaklarında doğrula.

        Args:
            claim: Doğrulanacak iddia

        Returns:
            MEBVerificationResult: Doğrulama sonucu
        """
        # API kullanılabilirse önce onu dene
        if self.api_url:
            try:
                api_result = await self._verify_via_api(claim)
                if api_result.found:
                    return api_result
            except Exception as e:
                logger.warning(f"MEB API error: {e}")

        # Lokal veri ile doğrula
        return self._verify_with_local_data(claim)

    async def _verify_via_api(self, claim: str) -> MEBVerificationResult:
        """
        MEB API ile doğrula.

        Args:
            claim: Doğrulanacak iddia

        Returns:
            MEBVerificationResult: Doğrulama sonucu
        """
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/verify",
                    json={"claim": claim},
                    timeout=aiohttp.ClientTimeout(total=10.0),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return MEBVerificationResult(
                            found=data.get("found", False),
                            confidence=data.get("confidence", 0.0),
                            status=data.get("status", "unverified"),
                            evidence=data.get("evidence"),
                            kazanim_code=data.get("kazanim_code"),
                            grade_level=data.get("grade_level"),
                        )
        except Exception as e:
            logger.error(f"MEB API verification error: {e}")

        return MEBVerificationResult(
            found=False,
            confidence=0.0,
            status="unverified",
            evidence=None,
        )

    def _verify_with_local_data(self, claim: str) -> MEBVerificationResult:
        """
        Lokal müfredat verisi ile doğrula.

        Args:
            claim: Doğrulanacak iddia

        Returns:
            MEBVerificationResult: Doğrulama sonucu
        """
        claim_lower = claim.lower()

        # Her ders için kontrol et
        for subject, data in self._curriculum_data.items():
            # Facts kontrolü
            facts = data.get("facts", {})
            for fact_name, fact_value in facts.items():
                if fact_name.lower() in claim_lower:
                    # Değer eşleşmesi kontrolü
                    fact_value_lower = str(fact_value).lower()

                    if fact_value_lower in claim_lower:
                        return MEBVerificationResult(
                            found=True,
                            confidence=0.95,
                            status="true",
                            evidence=f"MEB Müfredatı: {fact_name} = {fact_value}",
                        )
                    else:
                        # Fact adı geçiyor ama değer farklı olabilir
                        return MEBVerificationResult(
                            found=True,
                            confidence=0.7,
                            status="partially_true",
                            evidence=f"MEB Müfredatı'na göre {fact_name}: {fact_value}",
                        )

            # Konu kontrolü
            topics = data.get("konular", data.get("temel", []))
            topics.extend(data.get("geometri", []))

            for topic in topics:
                if topic.lower() in claim_lower:
                    return MEBVerificationResult(
                        found=True,
                        confidence=0.8,
                        status="true",
                        evidence=f"MEB {subject.title()} müfredatında yer alan konu: {topic}",
                    )

        # Bulunamadı
        return MEBVerificationResult(
            found=False,
            confidence=0.0,
            status="unverified",
            evidence=None,
        )

    async def validate_topic(
        self,
        topic: str,
        grade_level: int,
        subject: Optional[str] = None,
    ) -> bool:
        """
        Bir konunun müfredatta olup olmadığını kontrol et.

        Args:
            topic: Konu adı
            grade_level: Sınıf seviyesi
            subject: Ders adı (opsiyonel)

        Returns:
            bool: Müfredatta var mı
        """
        topic_lower = topic.lower()

        subjects_to_check = (
            [subject] if subject
            else self._curriculum_data.keys()
        )

        for subj in subjects_to_check:
            if subj not in self._curriculum_data:
                continue

            data = self._curriculum_data[subj]
            all_topics = []

            # Tüm konu listelerini birleştir
            for key, value in data.items():
                if isinstance(value, list):
                    all_topics.extend(value)

            # Eşleşme kontrolü
            for curriculum_topic in all_topics:
                if (
                    topic_lower in curriculum_topic.lower() or
                    curriculum_topic.lower() in topic_lower
                ):
                    return True

        return False

    def get_curriculum_topics(
        self,
        subject: str,
        category: Optional[str] = None,
    ) -> List[str]:
        """
        Bir dersin müfredat konularını al.

        Args:
            subject: Ders adı
            category: Kategori (temel, geometri, vb.)

        Returns:
            List[str]: Konu listesi
        """
        if subject not in self._curriculum_data:
            return []

        data = self._curriculum_data[subject]

        if category and category in data:
            return data[category]

        # Tüm konuları birleştir
        all_topics = []
        for key, value in data.items():
            if isinstance(value, list):
                all_topics.extend(value)

        return all_topics

    def get_fact(
        self,
        subject: str,
        fact_name: str,
    ) -> Optional[str]:
        """
        Belirli bir bilimsel gerçeği al.

        Args:
            subject: Ders adı
            fact_name: Gerçek adı

        Returns:
            str: Gerçek değeri
        """
        if subject not in self._curriculum_data:
            return None

        facts = self._curriculum_data[subject].get("facts", {})
        return facts.get(fact_name.lower())
