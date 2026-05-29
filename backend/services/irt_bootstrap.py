"""IRT cold-start bootstrap priors.

KIRO2 beta öncesi öğrenci yanıt verisi yok (irt_n_responses=0), bu yüzden
yanıttan IRT kalibrasyonu matematiksel olarak imkânsız. Ancak her aktif sorunun
``difficulty_level`` etiketi (%100 dolu) + ``bloom_level`` var. Bu fonksiyon o
proxy'lerden 3PL prior (a, b, c) türetir; CAT motoru ``irt_difficulty`` kolonunu
doğrudan okuduğu için bu prior'lar adaptif seçimi anında çalışır hale getirir.

Bu DEĞERLER KALİBRASYON DEĞİL prior'dır: beta sonrası gerçek yanıt geldikçe
(irt_n_responses >= 30) IRT EM kalibrasyonu bunların üzerine yazmalıdır. Bu yüzden
bootstrap kayıtları ``irt_method='bootstrap_difficulty_prior'`` ile işaretlenir.
"""

from __future__ import annotations

# difficulty_level enum (question_bank) -> IRT b (zorluk) taban değeri.
# Simetrik, tipik YKS aralığı [-2, +2] içinde.
_DIFFICULTY_B: dict[str, float] = {
    "VERY_EASY": -1.8,
    "EASY": -0.9,
    "MEDIUM": 0.0,
    "HARD": 0.9,
    "VERY_HARD": 1.8,
}

# 5 şıklı çoktan seçmeli (YKS) -> tahmin (guessing) tabanı 1/5 = 0.20.
_DEFAULT_C = 0.20
# Bootstrap prior ayrımcılık (discrimination). Prior'lar sahte kesinlik
# iddia etmemeli; orta-düzey sabit değer.
_DEFAULT_A = 0.9
# Bloom ekseni katsayısı: yüksek bilişsel seviye soruyu zorlaştırır. Bu, en kalabalık
# kova olan MEDIUM (~%64) içindeki b=0.0 yığılmasını kırmak için kritik.
_BLOOM_STEP = 0.15
_B_CLAMP = 3.5


def difficulty_to_irt(
    difficulty_level: str | None,
    bloom_level: int | None = None,
    *,
    a: float = _DEFAULT_A,
    c: float = _DEFAULT_C,
) -> dict[str, float]:
    """difficulty_level (+ opsiyonel bloom_level) -> 3PL prior (a, b, c).

    Args:
        difficulty_level: VERY_EASY|EASY|MEDIUM|HARD|VERY_HARD (case-insensitive).
            Bilinmeyen/None -> MEDIUM (b=0.0) tabanı.
        bloom_level: 1..6 (Bloom taksonomisi). Verilirse b'yi (bloom-3)*0.15 kaydırır,
            kova-içi yığılmayı kırar. None -> kayma yok.
        a: Ayrımcılık prior'u (varsayılan 0.9).
        c: Tahmin prior'u (varsayılan 0.20, 5 şıklı).

    Returns:
        {"a": float, "b": float, "c": float} — b [-3.5, 3.5] aralığına clamp'lenir.
    """
    base = _DIFFICULTY_B.get((difficulty_level or "MEDIUM").upper(), 0.0)
    b = base
    if bloom_level is not None:
        b += (int(bloom_level) - 3) * _BLOOM_STEP
    b = max(-_B_CLAMP, min(_B_CLAMP, b))
    return {"a": a, "b": round(b, 3), "c": c}
