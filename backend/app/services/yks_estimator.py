# -*- coding: utf-8 -*-
"""
KIRO2 — YKS Net & Puan Tahmincisi
====================================
IRT θ tahmininden gerçek sınav performansı tahmini.

Temel akış:
  θ (IRT yetenek) → tahmini net sayısı → ÖSYM ham puan → tahmini sıralama

Neden bu modül önemli?
  Öğrenci "θ=0.8 ne demek?" diye soramaz, anlayamaz.
  "Şu an çalışırsan AYT-SAY'dan ~350-360 puan alabilirsin" anlaşılır.
  Bu motivasyon ve hedef belirlemede kritiktir.

ÖSYM puan formülleri (2024 kılavuzu baz alındı):
  TYT Puanı:
    Ham = Σ(ders_ağırlığı × net_sayısı)
    Standart = 100 + (Ham - Ham_ort) / Ham_ss * 10
    Puan = 100 + standart_katsayı * standart

  AYT puan türleri:
    SAY  = f(AYT-Mat, AYT-Fizik, AYT-Kimya, AYT-Biyoloji, TYT)
    EA   = f(AYT-Mat, AYT-Edebiyat, AYT-Tarih, AYT-Coğrafya, TYT)
    SÖZ  = f(AYT-Edebiyat, AYT-Tarih, AYT-Coğrafya, AYT-Felsefe, TYT)
    DİL  = f(YDT)

IRT θ → net tahmini:
  Bir ders için n_soru sorusu varsa, IRT 3PL ile:
  E[net] = Σ P(θ, a_i, b_i, c_i) - 0.25 * Σ (1 - P(...))   # doğru - yanlış×0.25
  Pratik: ortalama madde parametreleri varsayılır.

Sıralama tahmini:
  ÖSYM geçmiş yıl puan-sıralama verisinden regresyon.
  Basit log-normal model: sıralama = A * exp(-B * puan)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ─── ÖSYM Soru/Ağırlık Yapısı (2024) ─────────────────────────────────────────

@dataclass(frozen=True)
class DersYapisi:
    """Bir sınav dersinin yapısı."""
    ad:           str
    n_soru:       int
    yanlis_kesi:  float = 0.25   # 4 yanlış = 1 doğru silinir
    # Ortalama IRT parametreleri (kalibre edilmeden önce kullanılır)
    ort_a:        float = 1.0
    ort_b:        float = 0.0
    ort_c:        float = 0.25


# TYT ders yapısı
TYT_DERSLER: Dict[str, DersYapisi] = {
    "turkce":   DersYapisi("Türkçe",          40, 0.25, ort_a=1.1, ort_b=-0.2),
    "sosyal":   DersYapisi("Sosyal Bilimler",  20, 0.25, ort_a=0.9, ort_b=0.1),
    "mat":      DersYapisi("Temel Matematik",  40, 0.25, ort_a=1.2, ort_b=0.3),
    "fen":      DersYapisi("Fen Bilimleri",    20, 0.25, ort_a=1.0, ort_b=0.2),
}

# AYT ders yapısı
AYT_DERSLER: Dict[str, DersYapisi] = {
    "mat":      DersYapisi("Matematik",        40, 0.25, ort_a=1.3, ort_b=0.5),
    "fizik":    DersYapisi("Fizik",            14, 0.25, ort_a=1.1, ort_b=0.4),
    "kimya":    DersYapisi("Kimya",            13, 0.25, ort_a=1.0, ort_b=0.3),
    "biyoloji": DersYapisi("Biyoloji",         13, 0.25, ort_a=1.0, ort_b=0.2),
    "edebiyat": DersYapisi("Türk Dili Edb.",   24, 0.25, ort_a=1.0, ort_b=0.0),
    "tarih1":   DersYapisi("Tarih-1",          10, 0.25, ort_a=0.9, ort_b=0.1),
    "cografya1":DersYapisi("Coğrafya-1",        6, 0.25, ort_a=0.9, ort_b=0.0),
    "tarih2":   DersYapisi("Tarih-2",          11, 0.25, ort_a=0.9, ort_b=0.1),
    "cografya2":DersYapisi("Coğrafya-2",        6, 0.25, ort_a=0.9, ort_b=0.0),
    "felsefe":  DersYapisi("Felsefe",          12, 0.25, ort_a=0.9, ort_b=0.0),
    "din":      DersYapisi("Din Kültürü",       6, 0.25, ort_a=0.9, ort_b=-0.2),
}

# AYT puan türü ders ağırlıkları (ÖSYM kılavuzu 2024)
# Katsayılar: {puan_turu: {ders_kodu: ağırlık}}
AYT_KATSAYILAR: Dict[str, Dict[str, float]] = {
    "SAY": {
        "tyt":      0.4,
        "mat":      0.3,
        "fizik":    0.15,
        "kimya":    0.1,
        "biyoloji": 0.05,
    },
    "EA": {
        "tyt":      0.4,
        "mat":      0.3,
        "edebiyat": 0.18,
        "tarih1":   0.07,
        "cografya1":0.05,
    },
    "SÖZ": {
        "tyt":      0.4,
        "edebiyat": 0.24,
        "tarih1":   0.12,
        "tarih2":   0.10,
        "cografya1":0.06,
        "cografya2":0.04,
        "felsefe":  0.04,
    },
    "DİL": {
        "tyt":      0.4,
        "ydt":      0.6,  # Yabancı Dil Testi
    },
}


# ─── Puan-Sıralama Modeli (tarihsel ÖSYM verisinden fit edilmiş) ──────────────
# Model: sıralama(puan) = N_toplam * P(X > puan)
# Basit log-normal approximation: fit edilmiş ortalama/std değerler
#
# Kaynak: 2019-2024 ÖSYM kılavuzlarından elde edilen genel bilgiler,
# yaklaşık kalibrasyon değerleri kullanılmaktadır.
# UYARI: Gerçek ÖSYM dağılımı yıla göre değişir; bu değerler kaba tahmindir.

PUAN_DAGILIM: Dict[str, Dict[str, float]] = {
    "TYT":  {"mu": 265.0, "sigma": 35.0, "n_aday": 2_500_000},
    "SAY":  {"mu": 310.0, "sigma": 50.0, "n_aday":   700_000},
    "EA":   {"mu": 305.0, "sigma": 45.0, "n_aday":   400_000},
    "SÖZ":  {"mu": 295.0, "sigma": 40.0, "n_aday":   350_000},
    "DİL":  {"mu": 320.0, "sigma": 55.0, "n_aday":    80_000},
}


# ─── Veri yapıları ────────────────────────────────────────────────────────────

@dataclass
class DersTheta:
    """Bir ders için θ tahmini."""
    ders_kodu:  str
    theta:      float
    se:         float = 0.5


@dataclass
class TahminiNetler:
    """Ders başına tahmini net sayıları."""
    dersler:     Dict[str, float]   # ders_kodu → tahmini net
    toplam_tyt:  Optional[float]    = None
    toplam_ayt:  Optional[float]    = None


@dataclass
class PuanTahmini:
    """Bir puan türü için tahmin."""
    puan_turu:       str             # TYT | SAY | EA | SÖZ | DİL
    puan:            float
    alt_sinir:       float           # ±1 SE bandı
    ust_sinir:       float
    tahmini_siralama: int
    siralama_alt:    int
    siralama_ust:    int
    yuzdelik:        float           # kaçıncı yüzdelik
    guvenilik:       str             # yüksek | orta | düşük


@dataclass
class YKSTahminRaporu:
    """Tüm puan türleri için tam rapor."""
    tyt:       Optional[PuanTahmini]
    say:       Optional[PuanTahmini]
    ea:        Optional[PuanTahmini]
    soz:       Optional[PuanTahmini]
    dil:       Optional[PuanTahmini]
    oneriler:  List[str] = field(default_factory=list)


# ─── IRT θ → tahmini net ─────────────────────────────────────────────────────

def theta_to_net(
    theta: float,
    ders:  DersYapisi,
    irt_a: Optional[float] = None,
    irt_b: Optional[float] = None,
    irt_c: Optional[float] = None,
) -> float:
    """
    IRT θ tahmininden bir ders için tahmini net sayısını hesapla.

    Formül (n_soru soruluk test için):
      E[doğru]  = n × P(θ, a, b, c)
      E[yanlış] = n × (1 - P(θ, a, b, c))
      E[net]    = E[doğru] - kesinti × E[yanlış]
                = n × [P - kesinti × (1-P)]
                = n × [P(1 + kesinti) - kesinti]

    Argümanlar:
      theta: IRT yetenek tahmini
      ders:  DersYapisi (soru sayısı, ortalama parametreler)
      irt_a/b/c: gerçek kalibre edilmiş parametreler (opsiyonel, yoksa ders ortalaması)
    """
    a = irt_a if irt_a is not None else ders.ort_a
    b = irt_b if irt_b is not None else ders.ort_b
    c = irt_c if irt_c is not None else ders.ort_c

    # 3PL ICC
    p = c + (1.0 - c) / (1.0 + math.exp(-a * (theta - b)))
    k = ders.yanlis_kesi

    # Tahmini net = n × [P(1+k) - k]
    net = ders.n_soru * (p * (1.0 + k) - k)

    # Net 0'dan küçük olamaz, n_soru'dan büyük olamaz
    return max(0.0, min(net, float(ders.n_soru)))


def net_guvensizlik(
    theta: float,
    se:    float,
    ders:  DersYapisi,
    irt_a: Optional[float] = None,
    irt_b: Optional[float] = None,
    irt_c: Optional[float] = None,
) -> Tuple[float, float]:
    """
    SE'yi kullanarak net sayısı için ±1 güven bandı.
    Döndürür: (alt_net, ust_net)
    """
    net_merkez = theta_to_net(theta,       ders, irt_a, irt_b, irt_c)
    net_alt    = theta_to_net(theta - se,  ders, irt_a, irt_b, irt_c)
    net_ust    = theta_to_net(theta + se,  ders, irt_a, irt_b, irt_c)
    return (min(net_alt, net_ust), max(net_alt, net_ust))


# ─── Net → Ham puan ──────────────────────────────────────────────────────────

def tyt_puan_hesapla(netleri: Dict[str, float]) -> float:
    """
    TYT ham puanını hesapla (100-500 aralığı).

    Ağırlıklı net toplamını max olası net toplamına normalize eder:
      puan = 100 + 400 × ham / max_ham
      max_ham = 6×40 + 4.5×20 + 6×40 + 4.5×20 = 660
    """
    w = {"turkce": 6.0, "sosyal": 4.5, "mat": 6.0, "fen": 4.5}
    MAX_HAM = 660.0  # tam doğru için: 6×40 + 4.5×20 + 6×40 + 4.5×20

    ham = sum(w.get(k, 0.0) * v for k, v in netleri.items())
    puan = 100.0 + 400.0 * (ham / MAX_HAM)
    return round(min(max(puan, 100.0), 500.0), 2)


def ayt_puan_hesapla(
    puan_turu:   str,
    ayt_netleri: Dict[str, float],
    tyt_puan:    float,
) -> float:
    """
    AYT puan türü için birleşik puan hesapla.

    Formül:
      OBP (Ortaöğretim Başarı Puanı) ihmal edilmiştir (not yok).
      AYT_puan = Σ(katsayı_i × standart_puan_i)

    Basitleştirilmiş model (ÖSYM'nin tam formülü yayımlanmaz):
      puan = 0.4 × TYT + 0.6 × AYT_ham
      AYT_ham = Σ(ders_ağırlığı × net_i / max_net_i × 100)
    """
    katsayilar = AYT_KATSAYILAR.get(puan_turu, {})

    # TYT katkısı
    tyt_katkisi = katsayilar.get("tyt", 0.4) * tyt_puan

    # AYT ders katkıları
    ayt_katkisi = 0.0
    ayt_toplam_agirlik = sum(v for k, v in katsayilar.items() if k != "tyt")

    for ders_kodu, agirlik in katsayilar.items():
        if ders_kodu == "tyt":
            continue
        if ders_kodu not in ayt_netleri:
            continue
        ders = AYT_DERSLER.get(ders_kodu)
        if ders is None:
            continue
        # Normalize net (0-100 arası)
        norm_net = (ayt_netleri[ders_kodu] / ders.n_soru) * 100.0
        # Puana dönüştür: 100 + norm_net * 4 → yaklaşık 100-500 aralığı
        ders_puan = 100.0 + norm_net * 3.5
        ayt_katkisi += agirlik * ders_puan

    if ayt_toplam_agirlik > 0:
        ayt_katkisi /= ayt_toplam_agirlik

    toplam = tyt_katkisi + ayt_katkisi
    return round(min(max(toplam, 100.0), 550.0), 2)


# ─── Puan → Sıralama ─────────────────────────────────────────────────────────

def puan_to_siralama(puan: float, puan_turu: str) -> Tuple[int, float]:
    """
    Puandan tahmini sıralamayı hesapla.

    Model: Log-normal dağılım varsayımı.
      P(X > puan) = 1 - Φ((ln(puan) - mu_ln) / sigma_ln)
      Sıralama = N_aday × P(X > puan)

    Döndürür: (tahmini_siralama, yuzdelik)
    """
    dist = PUAN_DAGILIM.get(puan_turu, PUAN_DAGILIM["TYT"])
    mu    = dist["mu"]
    sigma = dist["sigma"]
    n     = dist["n_aday"]

    # Normal CDF yaklaşımı (scipy olmadan)
    z = (puan - mu) / sigma
    p_kucuk = _normal_cdf(z)
    p_buyuk = 1.0 - p_kucuk

    siralama = max(1, int(n * p_buyuk))
    yuzdelik = round(p_kucuk * 100.0, 1)
    return siralama, yuzdelik


def _normal_cdf(z: float) -> float:
    """Standart normal CDF — erfc ile numerik kararlı."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# ─── Ana Estimator ───────────────────────────────────────────────────────────

class YKSEstimator:
    """
    IRT θ tahminlerinden YKS performans raporu oluşturur.

    Kullanım:
      est = YKSEstimator()

      # TYT tahmini
      tyt_thetas = {
          "turkce": DersTheta("turkce", theta=0.5, se=0.3),
          "mat":    DersTheta("mat",    theta=0.8, se=0.4),
          ...
      }
      rapor = est.tyt_raporu(tyt_thetas)

      # AYT SAY tahmini
      ayt_thetas = {...}
      rapor = est.ayt_raporu("SAY", tyt_thetas, ayt_thetas)
    """

    def tyt_raporu(
        self,
        ders_thetalar: Dict[str, DersTheta],
    ) -> PuanTahmini:
        """TYT için puan ve sıralama tahmini."""
        netleri      = {}
        netleri_alt  = {}
        netleri_ust  = {}

        for kod, yapisi in TYT_DERSLER.items():
            dt = ders_thetalar.get(kod)
            theta = dt.theta if dt else 0.0
            se    = dt.se    if dt else 1.0

            netleri[kod]     = theta_to_net(theta, yapisi)
            alt, ust         = net_guvensizlik(theta, se, yapisi)
            netleri_alt[kod] = alt
            netleri_ust[kod] = ust

        puan     = tyt_puan_hesapla(netleri)
        puan_alt = tyt_puan_hesapla(netleri_alt)
        puan_ust = tyt_puan_hesapla(netleri_ust)

        siralama,      yuzdelik = puan_to_siralama(puan,     "TYT")
        siralama_alt,  _        = puan_to_siralama(puan_ust, "TYT")  # yüksek puan → düşük sıralama
        siralama_ust,  _        = puan_to_siralama(puan_alt, "TYT")

        ort_se = sum(dt.se for dt in ders_thetalar.values()) / max(len(ders_thetalar), 1)

        return PuanTahmini(
            puan_turu       ="TYT",
            puan            = puan,
            alt_sinir       = puan_alt,
            ust_sinir       = puan_ust,
            tahmini_siralama= siralama,
            siralama_alt    = siralama_alt,
            siralama_ust    = siralama_ust,
            yuzdelik        = yuzdelik,
            guvenilik       = _guvenilik(ort_se),
        )

    def ayt_raporu(
        self,
        puan_turu:        str,
        tyt_ders_thetalar: Dict[str, DersTheta],
        ayt_ders_thetalar: Dict[str, DersTheta],
    ) -> PuanTahmini:
        """Bir AYT puan türü için tahmin."""
        # TYT puanını hesapla
        tyt_netleri = {
            kod: theta_to_net(dt.theta, TYT_DERSLER[kod])
            for kod, dt in tyt_ders_thetalar.items()
            if kod in TYT_DERSLER
        }
        tyt_puan = tyt_puan_hesapla(tyt_netleri)

        # AYT netlerini hesapla
        ayt_netleri     = {}
        ayt_netleri_alt = {}
        ayt_netleri_ust = {}

        for kod, yapisi in AYT_DERSLER.items():
            dt = ayt_ders_thetalar.get(kod)
            theta = dt.theta if dt else 0.0
            se    = dt.se    if dt else 1.0

            ayt_netleri[kod]     = theta_to_net(theta, yapisi)
            alt, ust             = net_guvensizlik(theta, se, yapisi)
            ayt_netleri_alt[kod] = alt
            ayt_netleri_ust[kod] = ust

        puan     = ayt_puan_hesapla(puan_turu, ayt_netleri,     tyt_puan)
        puan_alt = ayt_puan_hesapla(puan_turu, ayt_netleri_alt, tyt_puan)
        puan_ust = ayt_puan_hesapla(puan_turu, ayt_netleri_ust, tyt_puan)

        siralama,     yuzdelik = puan_to_siralama(puan,     puan_turu)
        siralama_alt, _        = puan_to_siralama(puan_ust, puan_turu)
        siralama_ust, _        = puan_to_siralama(puan_alt, puan_turu)

        tum_thetalar = {**tyt_ders_thetalar, **ayt_ders_thetalar}
        ort_se = sum(dt.se for dt in tum_thetalar.values()) / max(len(tum_thetalar), 1)

        return PuanTahmini(
            puan_turu       = puan_turu,
            puan            = puan,
            alt_sinir       = puan_alt,
            ust_sinir       = puan_ust,
            tahmini_siralama= siralama,
            siralama_alt    = siralama_alt,
            siralama_ust    = siralama_ust,
            yuzdelik        = yuzdelik,
            guvenilik       = _guvenilik(ort_se),
        )

    def tam_rapor(
        self,
        tyt_thetalar: Dict[str, DersTheta],
        ayt_thetalar: Optional[Dict[str, DersTheta]] = None,
        hedef_puan_turu: Optional[str] = None,
    ) -> YKSTahminRaporu:
        """Tüm uygulanabilir puan türleri için rapor oluştur."""
        tyt   = self.tyt_raporu(tyt_thetalar)
        say = ea = soz = dil = None

        if ayt_thetalar:
            if hedef_puan_turu in (None, "SAY"):
                say = self.ayt_raporu("SAY", tyt_thetalar, ayt_thetalar)
            if hedef_puan_turu in (None, "EA"):
                ea  = self.ayt_raporu("EA",  tyt_thetalar, ayt_thetalar)
            if hedef_puan_turu in (None, "SÖZ"):
                soz = self.ayt_raporu("SÖZ", tyt_thetalar, ayt_thetalar)

        oneriler = _oneriler_uret(tyt, say, ea, soz)

        return YKSTahminRaporu(
            tyt=tyt, say=say, ea=ea, soz=soz, dil=dil,
            oneriler=oneriler,
        )

    def tek_ders_katkisi(
        self,
        puan_turu:     str,
        ders_kodu:     str,
        mevcut_theta:  float,
        hedef_theta:   float,
        diger_thetalar: Dict[str, DersTheta],
    ) -> Dict[str, float]:
        """
        Bir derste θ artışının puana katkısını hesapla.
        "Matematiği 0.5 → 1.5'e çıkarırsam SAY puanım ne kadar artar?"

        Döndürür: {
          "puan_artisi": float,
          "siralama_degisimi": int,  # negatif = iyileşme
        }
        """
        # Mevcut durum
        tyt_thetalar = {k: v for k, v in diger_thetalar.items()
                        if k in TYT_DERSLER}
        ayt_thetalar = {k: v for k, v in diger_thetalar.items()
                        if k in AYT_DERSLER}

        if ders_kodu in TYT_DERSLER:
            tyt_thetalar[ders_kodu] = DersTheta(ders_kodu, mevcut_theta)
        elif ders_kodu in AYT_DERSLER:
            ayt_thetalar[ders_kodu] = DersTheta(ders_kodu, mevcut_theta)

        rapor_oncesi = self.tam_rapor(tyt_thetalar, ayt_thetalar or None,
                                      hedef_puan_turu=puan_turu)

        # Hedef durum
        if ders_kodu in TYT_DERSLER:
            tyt_thetalar[ders_kodu] = DersTheta(ders_kodu, hedef_theta)
        elif ders_kodu in AYT_DERSLER:
            ayt_thetalar[ders_kodu] = DersTheta(ders_kodu, hedef_theta)

        rapor_sonrasi = self.tam_rapor(tyt_thetalar, ayt_thetalar or None,
                                       hedef_puan_turu=puan_turu)

        puan_once  = getattr(rapor_oncesi,  puan_turu.lower().replace("ö","o"), rapor_oncesi.tyt)
        puan_sonra = getattr(rapor_sonrasi, puan_turu.lower().replace("ö","o"), rapor_sonrasi.tyt)

        if puan_once is None or puan_sonra is None:
            return {"puan_artisi": 0.0, "siralama_degisimi": 0}

        return {
            "puan_artisi":       round(puan_sonra.puan - puan_once.puan, 2),
            "siralama_degisimi": puan_sonra.tahmini_siralama - puan_once.tahmini_siralama,
        }


# ─── Yardımcı fonksiyonlar ────────────────────────────────────────────────────

def _guvenilik(ort_se: float) -> str:
    if ort_se <= 0.35:  return "yüksek"
    if ort_se <= 0.55:  return "orta"
    return "düşük"


def _oneriler_uret(
    tyt: Optional[PuanTahmini],
    say: Optional[PuanTahmini],
    ea:  Optional[PuanTahmini],
    soz: Optional[PuanTahmini],
) -> List[str]:
    """Puan tahminine göre motivasyonel öneriler üret."""
    oneriler: List[str] = []

    if tyt and tyt.puan < 250:
        oneriler.append(
            "TYT puanın henüz düşük. Tüm AYT puan türleri için TYT tabanını "
            "güçlendirmek ilk önceliklerin olmalı."
        )
    elif tyt and tyt.puan >= 320:
        oneriler.append("TYT tabanın güçlü! AYT çalışmalarına odaklanabilirsin.")

    if say and say.puan >= 450:
        oneriler.append(
            f"SAY puanın ({say.puan:.0f}) ile üst 100 üniversiteye "
            "yerleşme şansın var. Mevcut tempoyu koru."
        )

    if ea and ea.puan >= 420:
        oneriler.append(
            f"EA puanın ({ea.puan:.0f}) iyi bir seviyede. "
            "Matematik ve Edebiyat'ı dengeli tutmaya devam et."
        )

    if soz and soz.puan >= 400:
        oneriler.append(
            f"SÖZ puanın ({soz.puan:.0f}) yeterli. "
            "Edebiyat ve Tarih konularına ağırlık ver."
        )

    if not oneriler:
        oneriler.append(
            "Düzenli çalışmaya devam et. "
            "Her gün 2-3 CAT oturumu ile hızlı ilerleme kaydedebilirsin."
        )

    return oneriler
