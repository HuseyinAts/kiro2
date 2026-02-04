"""
IRT + Türkçe Morfoloji Modelleri
Parametreli IRT + Türkçe Morfoloji Sistemi veri modelleri

Bu modül ÖSYM ve ETS standartlarını aşan soru analizi ve zorluk belirleme
sistemi için gerekli veri modellerini içerir.
"""

import math
from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field, field_validator


class MorfolojiKarmasiklikSeviyesi(Enum):
    """Morfoloji karmaşıklık seviyeleri"""

    BASIT = 1
    ORTA = 2
    KARMASIK = 3
    COK_KARMASIK = 4


class IRTParametreTipi(Enum):
    """IRT parametre tipleri"""

    BIR_PARAMETRE = "1PL"  # Rasch Model
    IKI_PARAMETRE = "2PL"  # 2-Parameter Logistic
    UC_PARAMETRE = "3PL"  # 3-Parameter Logistic
    DORT_PARAMETRE = "4PL"  # 4-Parameter Logistic


class TurkceEkTipi(Enum):
    """Türkçe ek tipleri"""

    ISIM_CEKIM = "isim_cekim"
    FIIL_CEKIM = "fiil_cekim"
    ISIM_YAPIM = "isim_yapim"
    FIIL_YAPIM = "fiil_yapim"
    SIFAT_YAPIM = "sifat_yapim"
    ZARF_YAPIM = "zarf_yapim"


class MorfolojiAnalizi(BaseModel):
    """Kelime morfoloji analizi"""

    kelime: str = Field(..., description="Analiz edilen kelime")
    kok: str = Field(..., description="Kelimenin kök hali")
    ekler: List[str] = Field(default_factory=list, description="Eklerin listesi")
    ek_tipleri: List[TurkceEkTipi] = Field(
        default_factory=list, description="Ek tiplerinin listesi"
    )
    ek_sayisi: int = Field(0, ge=0, description="Toplam ek sayısı")
    kok_frekansi: float = Field(0.0, ge=0.0, description="Kök kelimenin frekansı")
    ek_frekansi: float = Field(0.0, ge=0.0, description="Eklerin ortalama frekansı")
    yaygınlık_skoru: float = Field(
        0.0, ge=0.0, le=1.0, description="Kelimenin yaygınlık skoru"
    )

    @field_validator("ek_sayisi")
    @classmethod
    def validate_ek_sayisi(cls, v, values):
        """Ek sayısı doğrulama"""
        if "ekler" in values and len(values["ekler"]) != v:
            raise ValueError("Ek sayısı ekler listesi uzunluğu ile uyuşmuyor")
        return v


class IRTParametreleri(BaseModel):
    """IRT model parametreleri"""

    a_parametresi: float = Field(
        ..., description="Ayırt edicilik parametresi (discrimination)"
    )
    b_parametresi: float = Field(..., description="Zorluk parametresi (difficulty)")
    c_parametresi: float = Field(
        0.0, ge=0.0, le=1.0, description="Şans parametresi (guessing)"
    )
    d_parametresi: float = Field(
        1.0, ge=0.0, le=1.0, description="Üst asimptot parametresi"
    )
    parametre_tipi: IRTParametreTipi = Field(..., description="IRT model tipi")
    guven_araligi: float = Field(0.95, ge=0.0, le=1.0, description="Güven aralığı")
    standart_hata: float = Field(0.0, ge=0.0, description="Standart hata")

    def olasilik_hesapla(self, theta: float) -> float:
        """
        Verilen yetenek seviyesi (theta) için doğru cevap olasılığını hesapla

        Args:
            theta: Öğrenci yetenek seviyesi

        Returns:
            Doğru cevap olasılığı (0-1 arası)
        """
        if self.parametre_tipi == IRTParametreTipi.BIR_PARAMETRE:
            # Rasch Model: P(θ) = exp(θ - b) / (1 + exp(θ - b))
            exp_val = math.exp(theta - self.b_parametresi)
            return exp_val / (1 + exp_val)

        elif self.parametre_tipi == IRTParametreTipi.IKI_PARAMETRE:
            # 2PL Model: P(θ) = exp(a(θ - b)) / (1 + exp(a(θ - b)))
            exp_val = math.exp(self.a_parametresi * (theta - self.b_parametresi))
            return exp_val / (1 + exp_val)

        elif self.parametre_tipi == IRTParametreTipi.UC_PARAMETRE:
            # 3PL Model: P(θ) = c + (1 - c) * exp(a(θ - b)) / (1 + exp(a(θ - b)))
            exp_val = math.exp(self.a_parametresi * (theta - self.b_parametresi))
            logistic = exp_val / (1 + exp_val)
            return self.c_parametresi + (1 - self.c_parametresi) * logistic

        elif self.parametre_tipi == IRTParametreTipi.DORT_PARAMETRE:
            # 4PL Model: P(θ) = c + (d - c) * exp(a(θ - b)) / (1 + exp(a(θ - b)))
            exp_val = math.exp(self.a_parametresi * (theta - self.b_parametresi))
            logistic = exp_val / (1 + exp_val)
            return (
                self.c_parametresi
                + (self.d_parametresi - self.c_parametresi) * logistic
            )

        else:
            raise ValueError(f"Desteklenmeyen parametre tipi: {self.parametre_tipi}")


class SoruMorfolojiAnalizi(BaseModel):
    """Soru metni morfoloji analizi"""

    soru_id: str = Field(..., description="Soru benzersiz kimliği")
    soru_metni: str = Field(..., description="Soru metni")
    morfoloji_analizleri: List[MorfolojiAnalizi] = Field(
        default_factory=list, description="Kelime analizleri"
    )
    toplam_kelime_sayisi: int = Field(0, ge=0, description="Toplam kelime sayısı")
    karmasik_kelime_sayisi: int = Field(0, ge=0, description="Karmaşık kelime sayısı")
    ortalama_ek_sayisi: float = Field(0.0, ge=0.0, description="Ortalama ek sayısı")
    morfoloji_karmasiklik_skoru: float = Field(
        0.0, ge=0.0, le=1.0, description="Morfoloji karmaşıklık skoru"
    )
    karmasiklik_seviyesi: MorfolojiKarmasiklikSeviyesi = Field(
        ..., description="Karmaşıklık seviyesi"
    )


class OgrenciMorfolojiProfili(BaseModel):
    """Öğrenci morfoloji yetenek profili"""

    ogrenci_id: str = Field(..., description="Öğrenci benzersiz kimliği")
    morfoloji_yetenek_seviyesi: float = Field(
        0.0, ge=-3.0, le=3.0, description="Morfoloji yetenek seviyesi (theta)"
    )
    ek_tanima_yetisi: float = Field(0.0, ge=0.0, le=1.0, description="Ek tanıma yetisi")
    kok_kelime_bilgisi: float = Field(
        0.0, ge=0.0, le=1.0, description="Kök kelime bilgisi"
    )
    karmasik_yapi_anlama: float = Field(
        0.0, ge=0.0, le=1.0, description="Karmaşık yapı anlama yetisi"
    )
    morfoloji_farkindaliği: float = Field(
        0.0, ge=0.0, le=1.0, description="Morfoloji farkındalığı"
    )
    guncelleme_tarihi: datetime = Field(
        default_factory=datetime.now, description="Son güncelleme tarihi"
    )


class IRTKalibrasyonSonucu(BaseModel):
    """IRT kalibrasyon sonucu"""

    soru_id: str = Field(..., description="Soru benzersiz kimliği")
    irt_parametreleri: IRTParametreleri = Field(
        ..., description="Kalibre edilmiş IRT parametreleri"
    )
    model_uyumu: float = Field(0.0, ge=0.0, le=1.0, description="Model uyum indeksi")
    kalibrasyon_tarihi: datetime = Field(
        default_factory=datetime.now, description="Kalibrasyon tarihi"
    )
    orneklem_buyuklugu: int = Field(
        0, ge=0, description="Kalibrasyon örneklem büyüklüğü"
    )
    iterasyon_sayisi: int = Field(0, ge=0, description="Kalibrasyon iterasyon sayısı")
    yakinsama_durumu: bool = Field(False, description="Yakınsama durumu")


class TurkceIRTSoruAnalizi(BaseModel):
    """Türkçe'ye özel IRT soru analizi"""

    soru_id: str = Field(..., description="Soru benzersiz kimliği")
    morfoloji_analizi: SoruMorfolojiAnalizi = Field(
        ..., description="Morfoloji analizi"
    )
    kalibrasyon_sonucu: IRTKalibrasyonSonucu = Field(
        ..., description="IRT kalibrasyon sonucu"
    )
    turkce_zorluk_faktoru: float = Field(
        0.0, ge=0.0, le=1.0, description="Türkçe'ye özel zorluk faktörü"
    )
    morfoloji_etkisi: float = Field(
        0.0, ge=0.0, le=1.0, description="Morfoloji etkisi katsayısı"
    )
    kulturel_baglam_skoru: float = Field(
        0.0, ge=0.0, le=1.0, description="Kültürel bağlam skoru"
    )
    onerilen_sinif_seviyesi: int = Field(
        1, ge=1, le=12, description="Önerilen sınıf seviyesi"
    )
    analiz_tarihi: datetime = Field(
        default_factory=datetime.now, description="Analiz tarihi"
    )

    def toplam_zorluk_hesapla(self) -> float:
        """
        Toplam zorluk skorunu hesapla (IRT + Morfoloji + Türkçe faktörleri)

        Returns:
            Toplam zorluk skoru (0-1 arası)
        """
        # IRT zorluk parametresini normalize et (-3, 3) -> (0, 1)
        irt_zorluk_norm = (
            self.kalibrasyon_sonucu.irt_parametreleri.b_parametresi + 3
        ) / 6
        irt_zorluk_norm = max(0, min(1, irt_zorluk_norm))

        # Morfoloji karmaşıklık skoru
        morfoloji_zorluk = self.morfoloji_analizi.morfoloji_karmasiklik_skoru

        # Ağırlıklı toplam hesapla
        toplam_zorluk = (
            0.4 * irt_zorluk_norm
            + 0.3 * morfoloji_zorluk
            + 0.2 * self.turkce_zorluk_faktoru
            + 0.1
            * (1 - self.kulturel_baglam_skoru)  # Düşük kültürel bağlam = yüksek zorluk
        )

        return max(0, min(1, toplam_zorluk))

    def sinif_seviyesi_onerisi(self) -> int:
        """
        Toplam zorluk skoruna göre sınıf seviyesi önerisi

        Returns:
            Önerilen sınıf seviyesi (1-12)
        """
        toplam_zorluk = self.toplam_zorluk_hesapla()

        if toplam_zorluk <= 0.2:
            return min(5, self.onerilen_sinif_seviyesi)
        elif toplam_zorluk <= 0.4:
            return min(8, max(5, self.onerilen_sinif_seviyesi))
        elif toplam_zorluk <= 0.6:
            return min(10, max(8, self.onerilen_sinif_seviyesi))
        elif toplam_zorluk <= 0.8:
            return min(12, max(10, self.onerilen_sinif_seviyesi))
        else:
            return 12


class MorfolojiIRTRaporu(BaseModel):
    """Morfoloji IRT analiz raporu"""

    rapor_id: str = Field(..., description="Rapor benzersiz kimliği")
    ogrenci_id: str = Field(..., description="Öğrenci kimliği")
    soru_analizleri: List[TurkceIRTSoruAnalizi] = Field(
        default_factory=list, description="Soru analizleri"
    )
    ogrenci_profili: OgrenciMorfolojiProfili = Field(..., description="Öğrenci profili")
    genel_performans_skoru: float = Field(
        0.0, ge=0.0, le=1.0, description="Genel performans skoru"
    )
    morfoloji_guc_alanlari: List[str] = Field(
        default_factory=list, description="Morfoloji güçlü alanları"
    )
    morfoloji_zayif_alanlari: List[str] = Field(
        default_factory=list, description="Morfoloji zayıf alanları"
    )
    oneriler: List[str] = Field(default_factory=list, description="Gelişim önerileri")
    rapor_tarihi: datetime = Field(
        default_factory=datetime.now, description="Rapor tarihi"
    )

    def ortalama_zorluk_hesapla(self) -> float:
        """Ortalama zorluk seviyesi hesapla"""
        if not self.soru_analizleri:
            return 0.0

        toplam_zorluk = sum(
            analiz.toplam_zorluk_hesapla() for analiz in self.soru_analizleri
        )
        return toplam_zorluk / len(self.soru_analizleri)

    def basari_orani_hesapla(self) -> float:
        """Başarı oranı hesapla"""
        if not self.soru_analizleri:
            return 0.0

        # Öğrenci yetenek seviyesine göre beklenen başarı oranını hesapla
        toplam_beklenen_basari = 0.0

        for analiz in self.soru_analizleri:
            theta = self.ogrenci_profili.morfoloji_yetenek_seviyesi
            beklenen_olasilik = (
                analiz.kalibrasyon_sonucu.irt_parametreleri.olasilik_hesapla(theta)
            )
            toplam_beklenen_basari += beklenen_olasilik

        return toplam_beklenen_basari / len(self.soru_analizleri)
