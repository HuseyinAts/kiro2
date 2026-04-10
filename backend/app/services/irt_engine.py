"""
KIRO2 — IRT Engine
==================
3-Parameter Logistic (3PL) Item Response Theory hesaplamaları.

Neden 3PL?
  YKS çoktan seçmeli (4 şık) → şans faktörü c≈0.25 görmezden gelinemez.
  2PL'de şanslı doğrular θ'yı yanlış yukarı çeker.

Temel formüller:
  P(θ) = c + (1-c) / (1 + exp(-a(θ-b)))
    a = discrimination (ayrım gücü, 0.5–2.5)
    b = difficulty     (güçlük, -4..+4)
    c = guessing       (şans, ≈0.25 for 4-choice MCQ)

  Fisher Information:
    I(θ) = a² * [P(θ)-c]² * [1-P(θ)] / [P(θ) * (1-c)²]

  EAP (Expected A Posteriori):
    θ_hat = ∫ θ * L(θ) * π(θ) dθ  /  ∫ L(θ) * π(θ) dθ
    SE    = sqrt( ∫ (θ-θ_hat)² * posterior dθ )

Termination criterion: SE < 0.35  (yeterli kesinlik)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import numpy as np
from scipy import stats

# ------------------------------------------------------------------
# Sabitler
# ------------------------------------------------------------------

THETA_GRID = np.linspace(-4.0, 4.0, 201)  # θ arama uzayı
PRIOR_MEAN = 0.0  # N(0,1) — YKS öğrenci dağılımı
PRIOR_SD = 1.0
SE_STOP = 0.35  # Oturumu bitir eşiği
MAX_ITEMS = 20  # Maks soru sayısı


# ------------------------------------------------------------------
# Veri yapıları
# ------------------------------------------------------------------


@dataclass
class ItemParams:
    """Bir sorunun IRT parametreleri."""

    question_id: str
    a: float = 1.0  # discrimination — varsayılan kalibrasyon öncesi
    b: float = 0.0  # difficulty
    c: float = 0.25  # guessing (4-şık MCQ)

    def __post_init__(self) -> None:
        """DM-02: Parametre sınırlarını zorla — a∈[0.1,3], b∈[-4,4], c∈[0,0.5]."""
        self.a = max(0.1, min(3.0, self.a))
        self.b = max(-4.0, min(4.0, self.b))
        self.c = max(0.0, min(0.5, self.c))

    def is_calibrated(self) -> bool:
        """Gerçek kalibrasyon yapıldı mı? Yoksa varsayılan mı?"""
        return not (self.a == 1.0 and self.b == 0.0 and self.c == 0.25)


@dataclass
class IRTResult:
    """EAP sonucu."""

    theta: float  # yetenek tahmini
    se: float  # standart hata
    converged: bool  # SE eşiğine ulaşıldı mı


# ------------------------------------------------------------------
# Temel IRT fonksiyonları
# ------------------------------------------------------------------


def p_correct(
    theta: float | np.ndarray, a: float, b: float, c: float
) -> float | np.ndarray:
    """
    3PL P(doğru | θ, a, b, c).

    Örnek:
      p_correct(0.0, 1.0, 0.0, 0.25) ≈ 0.625
      p_correct(2.0, 1.2, 0.5, 0.20) ≈ 0.86
    """
    return c + (1.0 - c) / (1.0 + np.exp(-a * (theta - b)))


def fisher_information(
    theta: float | np.ndarray, a: float, b: float, c: float
) -> float | np.ndarray:
    """
    Madde Fisher Bilgi Fonksiyonu I(θ).

    Yüksek I(θ) → bu θ bölgesinde soru çok bilgi veriyor.
    MFI (Maximum Fisher Information) → CAT'te en yüksek I(θ) olan soruyu seç.

    Not: c → 0 olursa 2PL Fisher formülüne indirger: I = a² P(1-P)
    """
    p = p_correct(theta, a, b, c)
    # Numerik kararlılık: sıfıra yakın paydaları koru
    p_safe = np.clip(p, 1e-9, 1.0 - 1e-9)
    numerator = (a**2) * ((p_safe - c) ** 2) * (1.0 - p_safe)
    denominator = p_safe * ((1.0 - c) ** 2)
    return numerator / denominator


# ------------------------------------------------------------------
# EAP Theta Güncelleme
# ------------------------------------------------------------------


def eap_update(
    responses: list[int],
    item_params: list[ItemParams],
    prior_mean: float = PRIOR_MEAN,
    prior_sd: float = PRIOR_SD,
) -> IRTResult:
    """
    EAP (Expected A Posteriori) ile θ ve SE güncelle.

    Argümanlar:
      responses   : [0, 1, 1, 0, ...]   (0=yanlış, 1=doğru)
      item_params : her yanıta karşılık gelen ItemParams listesi

    Döndürür:
      IRTResult(theta, se, converged)

    Algoritma:
      1. θ grid üzerinde prior N(μ,σ) dağılımı hesapla
      2. Her yanıt için likelihood çarp: L *= P(resp|θ,a,b,c)
      3. Posterior = L × prior, normalize et
      4. E[θ] = ∫ θ · posterior dθ  (trapz ile)
      5. SE  = sqrt(∫ (θ-E[θ])² · posterior dθ)

    Neden EAP, MAP değil?
      MAP tek nokta tahmin verir, belirsizliği göremez.
      EAP standart hata üretir → SE ile oturum sonlandırma yapılabilir.
    """
    if len(responses) == 0:
        # İlk soru öncesi: prior'dan başla
        return IRTResult(theta=prior_mean, se=prior_sd, converged=False)

    if len(responses) != len(item_params):
        raise ValueError(
            f"responses ({len(responses)}) ve item_params ({len(item_params)}) "
            f"eşit uzunlukta olmalı"
        )

    # Prior
    prior = stats.norm.pdf(THETA_GRID, prior_mean, prior_sd)

    # Likelihood: tüm yanıtların çarpımı
    likelihood = np.ones_like(THETA_GRID)
    for resp, item in zip(responses, item_params):
        p = p_correct(THETA_GRID, item.a, item.b, item.c)
        p = np.clip(p, 1e-9, 1.0 - 1e-9)
        likelihood *= np.where(resp == 1, p, 1.0 - p)

    # Posterior = normalize(likelihood × prior)
    raw_posterior = likelihood * prior
    norm_factor = np.trapezoid(raw_posterior, THETA_GRID)

    if norm_factor < 1e-300:
        # Numerik underflow — prior'a dön (kötü veri sinyali)
        return IRTResult(theta=prior_mean, se=prior_sd, converged=False)

    posterior = raw_posterior / norm_factor

    # E[θ] ve SE
    theta_hat = float(np.trapezoid(THETA_GRID * posterior, THETA_GRID))
    variance = float(
        np.trapezoid((THETA_GRID - theta_hat) ** 2 * posterior, THETA_GRID)
    )
    se = float(math.sqrt(max(variance, 1e-10)))

    return IRTResult(
        theta=round(theta_hat, 4), se=round(se, 4), converged=(se < SE_STOP)
    )


# ------------------------------------------------------------------
# Soru Seçimi: Epsilon-Greedy MFI
# ------------------------------------------------------------------


def select_next_question(
    theta: float,
    candidates: list[ItemParams],
    answered_ids: set[str],
    epsilon: float = 0.20,
    max_exposure_rate: float = 0.30,
    exposure_counts: dict[str, int] | None = None,
    total_sessions: int = 1,
) -> ItemParams | None:
    """
    Bir sonraki soruyu seç: Epsilon-greedy Maximum Fisher Information.

    Mantık:
      1. Zaten yanıtlananları çıkar (answered_ids)
      2. Exposure rate > max_exposure_rate olanları çıkar
         (aynı soru çok fazla kişiye gitmesin)
      3. ZPD filtresi: P(doğru | θ) ∈ [0.20, 0.85]
         (çok kolay veya çok zor soruyu atla)
      4. epsilon=0.20 ihtimalle rastgele seç (exploration)
         1-epsilon ihtimalle en yüksek I(θ) olan soruyu seç (exploitation)

    Neden epsilon-greedy?
      Saf MFI aynı 10-20 soruyu herkese verir → item exposure patlaması.
      %20 rastgele seçim bu soruyu çözer, θ yakınsama kalitesi az düşer.

    Argümanlar:
      theta              : mevcut θ tahmini
      candidates         : havuzdaki sorular
      answered_ids       : bu oturumda yanıtlanan soru ID'leri
      epsilon            : keşif olasılığı (0.20 önerilen)
      max_exposure_rate  : bir sorunun max gösterilme oranı
      exposure_counts    : {question_id: gösterim sayısı}
      total_sessions     : toplam oturum sayısı (exposure hesabı için)
    """
    # Adım 1: yanıtlananları çıkar
    pool = [q for q in candidates if q.question_id not in answered_ids]
    if not pool:
        return None

    # Adım 2: exposure filtresi
    if exposure_counts and total_sessions > 10:
        pool = [
            q
            for q in pool
            if (exposure_counts.get(q.question_id, 0) / total_sessions)
            <= max_exposure_rate
        ]
    if not pool:
        # Exposure filtresi hepsini elediyse orijinal pool'a dön
        pool = [q for q in candidates if q.question_id not in answered_ids]

    # Adım 3: ZPD filtresi — optimal challenge zone
    # DM-03: Alt sınır 0.40→0.20 (düşük yetenek öğrenciye uygun soru seçimi)
    zpd_pool = [
        q for q in pool if 0.20 <= float(p_correct(theta, q.a, q.b, q.c)) <= 0.85
    ]
    # DM-08: ZPD boşsa önce gevşek band [0.10, 0.95] dene, sonra full pool
    if not zpd_pool:
        zpd_pool = [
            q for q in pool if 0.10 <= float(p_correct(theta, q.a, q.b, q.c)) <= 0.95
        ]
    if not zpd_pool:
        zpd_pool = pool

    # Adım 4: epsilon-greedy
    if random.random() < epsilon or len(zpd_pool) == 1:
        return random.choice(zpd_pool[:50])  # rastgele, ama ilk 50'den

    # Exploitation: Maximum Fisher Information
    return max(zpd_pool, key=lambda q: float(fisher_information(theta, q.a, q.b, q.c)))


# ------------------------------------------------------------------
# Bitiş koşulu
# ------------------------------------------------------------------


def should_terminate(
    se: float, n_items: int, se_threshold: float = SE_STOP, max_items: int = MAX_ITEMS
) -> tuple[bool, str]:
    """
    CAT oturumu bitmeli mi?

    Döndürür: (bitirmeli_mi, sebep)
    """
    if se <= se_threshold:
        return True, "se_threshold"
    if n_items >= max_items:
        return True, "max_questions"
    return False, ""
