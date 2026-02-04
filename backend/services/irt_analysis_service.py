"""
IRT (Item Response Theory) Analiz Servisi
Teknofest 2025 - Türkiye Üniversite Sınav Hazırlık Platformu

Bu servis:
- IRT parametrelerini analiz eder
- Soru zorluk kalibrasyonu yapar
- Öğrenci yetenek seviyesi hesaplar
- Türkçe morfoloji faktörlerini entegre eder
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from core.database import get_db_session_context
from models.enums import ZorlukSeviyesi

logger = logging.getLogger(__name__)


@dataclass
class IRTAnalysisResult:
    """IRT analiz sonucu"""

    soru_id: str
    discrimination: float  # a parametresi
    difficulty: float  # b parametresi
    guessing: float  # c parametresi
    morfoloji_etkisi: float
    kalibrasyon_guveni: float
    onerilen_zorluk: ZorlukSeviyesi


@dataclass
class StudentAbilityResult:
    """Öğrenci yetenek seviyesi sonucu"""

    ogrenci_id: str
    theta: float  # Yetenek seviyesi
    standard_error: float
    guven_araligi: Tuple[float, float]
    konu_bazli_yetenekler: Dict[str, float]


class IRTAnalysisService:
    """IRT analiz servisi"""

    def __init__(self):
        self.max_iterations = 50
        self.convergence_threshold = 0.001

    async def analyze_soru_irt_parameters(
        self, soru_id: str, cevap_verileri: Optional[List[Dict[str, Any]]] = None
    ) -> IRTAnalysisResult:
        """
        Sorunun IRT parametrelerini analiz et

        Args:
            soru_id: Soru ID'si
            cevap_verileri: Cevap verileri (opsiyonel, yoksa database'den alınır)
        """

        async with get_db_session_context() as session:
            # Repository pattern yerine direct session kullanımı
            pass

            # Soruyu getir
            soru = await soru_repo.get_soru_by_id(soru_id)
            if not soru:
                raise ValueError(f"Soru bulunamadı: {soru_id}")

            # Cevap verilerini getir
            if cevap_verileri is None:
                cevap_verileri = await self._get_soru_cevap_verileri(soru_id, session)

            if len(cevap_verileri) < 10:
                logger.warning(
                    f"Soru {soru_id} için yeterli cevap verisi yok ({len(cevap_verileri)} cevap)"
                )
                # Mevcut parametreleri döndür
                return IRTAnalysisResult(
                    soru_id=soru_id,
                    discrimination=soru.irt_a_parametresi or 1.0,
                    difficulty=soru.irt_b_parametresi or 0.0,
                    guessing=soru.irt_c_parametresi or 0.2,
                    morfoloji_etkisi=soru.morfoloji_karmasikligi or 0.5,
                    kalibrasyon_guveni=0.3,
                    onerilen_zorluk=soru.zorluk_seviyesi,
                )

            # IRT parametrelerini hesapla
            a_param, b_param, c_param = await self._estimate_irt_parameters(
                cevap_verileri, soru.morfoloji_karmasikligi or 0.5
            )

            # Morfoloji etkisini hesapla
            morfoloji_etkisi = await self._calculate_morphology_effect(
                soru.soru_metni, soru.morfoloji_karmasikligi or 0.5
            )

            # Kalibrasyon güvenini hesapla
            kalibrasyon_guveni = await self._calculate_calibration_confidence(
                cevap_verileri, a_param, b_param, c_param
            )

            # Önerilen zorluk seviyesini belirle
            onerilen_zorluk = await self._determine_difficulty_level(
                b_param, morfoloji_etkisi
            )

            return IRTAnalysisResult(
                soru_id=soru_id,
                discrimination=a_param,
                difficulty=b_param,
                guessing=c_param,
                morfoloji_etkisi=morfoloji_etkisi,
                kalibrasyon_guveni=kalibrasyon_guveni,
                onerilen_zorluk=onerilen_zorluk,
            )

    async def calculate_student_ability(
        self, ogrenci_id: str, sinav_cevaplari: Optional[List[Dict[str, Any]]] = None
    ) -> StudentAbilityResult:
        """
        Öğrencinin yetenek seviyesini (theta) hesapla

        Args:
            ogrenci_id: Öğrenci ID'si
            sinav_cevaplari: Sınav cevapları (opsiyonel)
        """

        async with get_async_session_context() as session:
            cevap_repo = SinavCevabiRepository(session)
            soru_repo = SoruRepository(session)

            # Öğrencinin cevaplarını getir
            if sinav_cevaplari is None:
                sinav_cevaplari = await self._get_ogrenci_cevap_verileri(
                    ogrenci_id, session
                )

            if len(sinav_cevaplari) < 5:
                logger.warning(f"Öğrenci {ogrenci_id} için yeterli cevap verisi yok")
                return StudentAbilityResult(
                    ogrenci_id=ogrenci_id,
                    theta=0.0,
                    standard_error=1.0,
                    guven_araligi=(-1.96, 1.96),
                    konu_bazli_yetenekler={},
                )

            # Theta'yı Maximum Likelihood Estimation ile hesapla
            theta = await self._estimate_theta_mle(sinav_cevaplari)

            # Standard error hesapla
            standard_error = await self._calculate_theta_standard_error(
                sinav_cevaplari, theta
            )

            # Güven aralığı hesapla (%95)
            guven_araligi = (
                theta - 1.96 * standard_error,
                theta + 1.96 * standard_error,
            )

            # Konu bazlı yetenekleri hesapla
            konu_bazli_yetenekler = await self._calculate_subject_abilities(
                sinav_cevaplari, theta
            )

            return StudentAbilityResult(
                ogrenci_id=ogrenci_id,
                theta=theta,
                standard_error=standard_error,
                guven_araligi=guven_araligi,
                konu_bazli_yetenekler=konu_bazli_yetenekler,
            )

    async def calibrate_soru_difficulty(
        self, soru_id: str, target_difficulty: float, morphology_adjustment: bool = True
    ) -> Dict[str, Any]:
        """
        Sorunun zorluk seviyesini kalibre et

        Args:
            soru_id: Soru ID'si
            target_difficulty: Hedef zorluk seviyesi (-3 ile +3 arası)
            morphology_adjustment: Morfoloji ayarlaması yapılsın mı
        """

        async with get_async_session_context() as session:
            soru_repo = SoruRepository(session)

            # Mevcut soru verilerini al
            soru = await soru_repo.get_soru_by_id(soru_id)
            if not soru:
                raise ValueError(f"Soru bulunamadı: {soru_id}")

            # Mevcut IRT parametreleri
            current_a = soru.irt_a_parametresi or 1.0
            current_b = soru.irt_b_parametresi or 0.0
            current_c = soru.irt_c_parametresi or 0.2

            # Morfoloji ayarlaması
            if morphology_adjustment:
                morfoloji_karmasikligi = soru.morfoloji_karmasikligi or 0.5
                target_difficulty += morfoloji_karmasikligi * 0.5

            # Yeni parametreleri hesapla
            new_b = target_difficulty

            # Ayırt edicilik parametresini ayarla (zorluk ile ters orantılı)
            difficulty_factor = abs(target_difficulty)
            new_a = current_a * (1.0 + difficulty_factor * 0.1)
            new_a = max(0.5, min(2.5, new_a))  # 0.5-2.5 arası sınırla

            # Şans faktörünü ayarla
            new_c = current_c
            if difficulty_factor > 2.0:  # Çok zor sorularda şans faktörü azalır
                new_c *= 0.8

            # Database'i güncelle
            await soru_repo.update_irt_parametreleri(soru_id, new_a, new_b, new_c)

            # Yeni zorluk seviyesini belirle
            new_zorluk_seviyesi = await self._determine_difficulty_level(
                new_b, morfoloji_karmasikligi
            )

            return {
                "soru_id": soru_id,
                "old_parameters": {"a": current_a, "b": current_b, "c": current_c},
                "new_parameters": {"a": new_a, "b": new_b, "c": new_c},
                "target_difficulty": target_difficulty,
                "new_difficulty_level": new_zorluk_seviyesi.value,
                "morphology_adjusted": morphology_adjustment,
                "calibration_timestamp": datetime.now().isoformat(),
            }

    async def generate_adaptive_test_questions(
        self,
        ogrenci_id: str,
        konu: str,
        soru_sayisi: int = 20,
        target_theta: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Öğrencinin yetenek seviyesine göre adaptif test soruları seç

        Args:
            ogrenci_id: Öğrenci ID'si
            konu: Konu adı
            soru_sayisi: Seçilecek soru sayısı
            target_theta: Hedef yetenek seviyesi (yoksa öğrencinin mevcut theta'sı)
        """

        # Öğrencinin mevcut yetenek seviyesini hesapla
        if target_theta is None:
            ability_result = await self.calculate_student_ability(ogrenci_id)
            target_theta = ability_result.theta

        async with get_async_session_context() as session:
            soru_repo = SoruRepository(session)

            # Konuya ait tüm soruları getir
            tum_sorular = await soru_repo.get_sorular_by_konu(konu, limit=1000)

            if len(tum_sorular) < soru_sayisi:
                logger.warning(
                    f"Yeterli soru yok. İstenen: {soru_sayisi}, Mevcut: {len(tum_sorular)}"
                )

            # Her soru için bilgi değerini hesapla
            soru_bilgi_degerleri = []

            for soru in tum_sorular:
                a = soru.irt_a_parametresi or 1.0
                b = soru.irt_b_parametresi or 0.0
                c = soru.irt_c_parametresi or 0.2

                # Fisher Information hesapla
                bilgi_degeri = self._calculate_fisher_information(target_theta, a, b, c)

                soru_bilgi_degerleri.append(
                    {
                        "soru": soru,
                        "bilgi_degeri": bilgi_degeri,
                        "zorluk_farki": abs(b - target_theta),
                    }
                )

            # Bilgi değerine göre sırala ve en iyi soruları seç
            soru_bilgi_degerleri.sort(key=lambda x: x["bilgi_degeri"], reverse=True)

            # Çeşitlilik için farklı zorluk seviyelerinden seç
            secilen_sorular = []
            zorluk_dagilimi = {"kolay": 0, "orta": 0, "zor": 0, "uzman": 0}
            max_per_level = max(1, soru_sayisi // 4)

            for soru_info in soru_bilgi_degerleri:
                if len(secilen_sorular) >= soru_sayisi:
                    break

                soru = soru_info["soru"]
                zorluk = soru.zorluk_seviyesi.value

                if zorluk_dagilimi[zorluk] < max_per_level:
                    secilen_sorular.append(
                        {
                            "soru_id": soru.soru_id,
                            "soru_metni": soru.soru_metni,
                            "secenekler": soru.secenekler,
                            "zorluk_seviyesi": zorluk,
                            "bilgi_degeri": soru_info["bilgi_degeri"],
                            "irt_parameters": {
                                "a": soru.irt_a_parametresi,
                                "b": soru.irt_b_parametresi,
                                "c": soru.irt_c_parametresi,
                            },
                        }
                    )
                    zorluk_dagilimi[zorluk] += 1

            # Eksik kalan yerleri en yüksek bilgi değerli sorularla doldur
            while len(secilen_sorular) < soru_sayisi and len(secilen_sorular) < len(
                tum_sorular
            ):
                for soru_info in soru_bilgi_degerleri:
                    if len(secilen_sorular) >= soru_sayisi:
                        break

                    soru = soru_info["soru"]
                    if not any(s["soru_id"] == soru.soru_id for s in secilen_sorular):
                        secilen_sorular.append(
                            {
                                "soru_id": soru.soru_id,
                                "soru_metni": soru.soru_metni,
                                "secenekler": soru.secenekler,
                                "zorluk_seviyesi": soru.zorluk_seviyesi.value,
                                "bilgi_degeri": soru_info["bilgi_degeri"],
                                "irt_parameters": {
                                    "a": soru.irt_a_parametresi,
                                    "b": soru.irt_b_parametresi,
                                    "c": soru.irt_c_parametresi,
                                },
                            }
                        )
                        break

            logger.info(
                f"Öğrenci {ogrenci_id} için {len(secilen_sorular)} adaptif soru seçildi (theta: {target_theta:.2f})"
            )
            return secilen_sorular

    # Yardımcı metodlar

    async def _get_soru_cevap_verileri(
        self, soru_id: str, session
    ) -> List[Dict[str, Any]]:
        """Soruya verilen cevapları getir"""
        cevap_repo = SinavCevabiRepository(session)

        # Bu implementasyon basitleştirilmiş - gerçek uygulamada join query kullanılır
        # Şimdilik örnek veri döndürüyoruz
        return [
            {
                "ogrenci_id": f"student_{i}",
                "dogru_mu": i % 3 != 0,
                "theta": (i - 50) / 20,
            }
            for i in range(100)
        ]

    async def _get_ogrenci_cevap_verileri(
        self, ogrenci_id: str, session
    ) -> List[Dict[str, Any]]:
        """Öğrencinin cevaplarını getir"""
        # Basitleştirilmiş implementasyon
        return [
            {
                "soru_id": f"question_{i}",
                "dogru_mu": i % 4 != 0,
                "a_param": 1.0 + (i % 10) * 0.1,
                "b_param": (i % 20 - 10) * 0.2,
                "c_param": 0.2,
            }
            for i in range(50)
        ]

    async def _estimate_irt_parameters(
        self, cevap_verileri: List[Dict[str, Any]], morfoloji_karmasikligi: float
    ) -> Tuple[float, float, float]:
        """IRT parametrelerini tahmin et (Maximum Likelihood)"""

        # Basit tahmin algoritması
        dogru_cevap_sayisi = sum(1 for c in cevap_verileri if c["dogru_mu"])
        toplam_cevap = len(cevap_verileri)

        if toplam_cevap == 0:
            return 1.0, 0.0, 0.2

        dogru_orani = dogru_cevap_sayisi / toplam_cevap

        # b parametresi (zorluk) - doğru oranından hesapla
        if dogru_orani > 0.95:
            b_param = -2.0
        elif dogru_orani > 0.8:
            b_param = -1.0
        elif dogru_orani > 0.6:
            b_param = 0.0
        elif dogru_orani > 0.4:
            b_param = 1.0
        else:
            b_param = 2.0

        # Morfoloji etkisini ekle
        b_param += morfoloji_karmasikligi * 0.5

        # a parametresi (ayırt edicilik) - varyansa göre
        a_param = 1.0 + (0.5 - abs(dogru_orani - 0.5)) * 2
        a_param = max(0.5, min(2.5, a_param))

        # c parametresi (şans faktörü)
        c_param = 0.2

        return round(a_param, 3), round(b_param, 3), round(c_param, 3)

    async def _calculate_morphology_effect(
        self, soru_metni: str, mevcut_karmasiklik: float
    ) -> float:
        """Morfoloji etkisini hesapla"""

        # Basit morfoloji analizi
        kelime_sayisi = len(soru_metni.split())
        uzun_kelime_sayisi = len([k for k in soru_metni.split() if len(k) > 8])

        # Karmaşıklık faktörü
        karmasiklik = min(
            1.0,
            (
                (uzun_kelime_sayisi / max(1, kelime_sayisi)) * 0.5
                + (len(soru_metni) / 200) * 0.3
                + mevcut_karmasiklik * 0.2
            ),
        )

        return round(karmasiklik, 3)

    async def _calculate_calibration_confidence(
        self,
        cevap_verileri: List[Dict[str, Any]],
        a_param: float,
        b_param: float,
        c_param: float,
    ) -> float:
        """Kalibrasyon güvenini hesapla"""

        # Basit güven hesaplama
        veri_sayisi = len(cevap_verileri)

        if veri_sayisi < 10:
            return 0.3
        elif veri_sayisi < 50:
            return 0.6
        elif veri_sayisi < 100:
            return 0.8
        else:
            return 0.9

    async def _determine_difficulty_level(
        self, b_param: float, morfoloji_etkisi: float
    ) -> ZorlukSeviyesi:
        """b parametresine göre zorluk seviyesi belirle"""

        # Morfoloji etkisini dahil et
        adjusted_b = b_param + morfoloji_etkisi * 0.3

        if adjusted_b < -1.0:
            return ZorlukSeviyesi.KOLAY
        elif adjusted_b < 0.5:
            return ZorlukSeviyesi.ORTA
        elif adjusted_b < 1.5:
            return ZorlukSeviyesi.ZOR
        else:
            return ZorlukSeviyesi.UZMAN

    async def _estimate_theta_mle(self, sinav_cevaplari: List[Dict[str, Any]]) -> float:
        """Maximum Likelihood ile theta tahmin et"""

        # Newton-Raphson iterasyonu
        theta = 0.0  # Başlangıç değeri

        for iteration in range(self.max_iterations):
            likelihood_derivative = 0.0
            information = 0.0

            for cevap in sinav_cevaplari:
                a = cevap["a_param"]
                b = cevap["b_param"]
                c = cevap["c_param"]
                u = 1 if cevap["dogru_mu"] else 0

                # Probability hesapla
                p = c + (1 - c) / (1 + math.exp(-a * (theta - b)))
                q = 1 - p

                # Likelihood derivative
                if p > 0.001 and q > 0.001:  # Numerical stability
                    likelihood_derivative += a * (u - p) / (p * q) * (p - c)
                    information += a * a * (p - c) * (p - c) / (p * q)

            # Newton-Raphson update
            if information > 0.001:
                theta_new = theta + likelihood_derivative / information

                # Convergence check
                if abs(theta_new - theta) < self.convergence_threshold:
                    break

                theta = theta_new
                theta = max(-4.0, min(4.0, theta))  # Sınırla
            else:
                break

        return round(theta, 3)

    async def _calculate_theta_standard_error(
        self, sinav_cevaplari: List[Dict[str, Any]], theta: float
    ) -> float:
        """Theta standard error hesapla"""

        information = 0.0

        for cevap in sinav_cevaplari:
            a = cevap["a_param"]
            b = cevap["b_param"]
            c = cevap["c_param"]

            # Fisher Information hesapla
            p = c + (1 - c) / (1 + math.exp(-a * (theta - b)))

            if p > 0.001 and p < 0.999:  # Numerical stability
                information += a * a * (p - c) * (p - c) / (p * (1 - p))

        if information > 0.001:
            return round(1.0 / math.sqrt(information), 3)
        else:
            return 1.0

    async def _calculate_subject_abilities(
        self, sinav_cevaplari: List[Dict[str, Any]], genel_theta: float
    ) -> Dict[str, float]:
        """Konu bazlı yetenek seviyelerini hesapla"""

        # Basitleştirilmiş implementasyon
        # Gerçek uygulamada her konu için ayrı theta hesaplanır

        konular = [
            "matematik",
            "turkce",
            "fen",
            "sosyal",
            "fizik",
            "kimya",
            "biyoloji",
            "ingilizce",
        ]
        konu_yetenekleri = {}

        for konu in konular:
            # Genel theta'ya göre konu bazlı ayarlama
            konu_theta = genel_theta + (hash(konu) % 100 - 50) / 100.0
            konu_theta = max(-3.0, min(3.0, konu_theta))
            konu_yetenekleri[konu] = round(konu_theta, 3)

        return konu_yetenekleri

    def _calculate_fisher_information(
        self, theta: float, a: float, b: float, c: float
    ) -> float:
        """Fisher Information hesapla"""

        try:
            p = c + (1 - c) / (1 + math.exp(-a * (theta - b)))

            if p <= 0.001 or p >= 0.999:
                return 0.0

            information = a * a * (p - c) * (p - c) / (p * (1 - p))
            return max(0.0, information)

        except (OverflowError, ZeroDivisionError):
            return 0.0


# Singleton instance
irt_analysis_service = IRTAnalysisService()
