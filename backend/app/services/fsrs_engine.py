"""
KIRO2 — FSRS v6 Engine
=======================
Free Spaced Repetition Scheduler v6 (Ye et al., 2024)
GitHub: open-spaced-repetition/fsrs4anki

Neden FSRS, SM-2 değil?
  SM-2 (SuperMemo-2, 1987) sabit aralık çarpanları kullanır.
  FSRS, Ebbinghaus unutma eğrisini nöral ağ ile öğrenir:
    - Stability (S): hatırlamanın yarılanma ömrü (gün)
    - Difficulty (D): madde zorluğu, 1-10 skalası
    - Retrievability (R): şu anki hatırlama olasılığı

Temel formüller (FSRS v6):
  R(t, S) = (1 + FACTOR * t / S) ^ DECAY      # Hatırlama olasılığı
  S_new   = f(S, D, R, puan)                   # Yeni stabilite
  D_new   = D - w_D * (puan - 3)               # Yeni güçlük

YKS entegrasyonu:
  - Her doğru/yanlış yanıt FSRS state'ini günceller
  - due_date: bir sonraki tekrar zamanı
  - CAT soru seçiminde FSRS urgency skoru kullanılır:
    urgency = max(0, days_overdue) / stability

Bu dosya saf matematik — DB veya Redis bağlantısı yok.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

# ─── FSRS v6 sabit parametreleri (open-spaced-repetition/fsrs4anki'den) ───────
# Bu ağırlıklar büyük ölçekli Anki verisiyle optimize edilmiştir.
# YKS verisi biriktikçe fine-tune yapılabilir.
W = [
    0.4072,
    1.1829,
    3.1262,
    15.4722,  # w0-w3:  S_0 (ilk stabilite)
    7.2102,
    0.5316,
    1.0651,
    0.0589,  # w4-w7:  D parametreleri
    1.5330,
    0.1544,
    1.0040,  # w8-w10: stabilite artış faktörleri
    1.9829,
    0.0953,
    0.2975,
    2.2042,  # w11-w14: stabilite hesabı
    0.2407,
    2.9466,
    0.5034,  # w15-w17
    0.6567,
    0.1673,
    0.1415,  # w18-w20
]

DECAY = -0.5  # Hafıza bozunma katsayısı
FACTOR = 0.9 ** (1 / DECAY) - 1  # ≈ 0.8122

MAX_INTERVAL_DAYS: int = 36_500  # 100 yıl — FSRS+ standardı
MIN_INTERVAL_DAYS: int = 1

# Puan tanımları (Anki tarzı)
PUAN_TEKRAR = 1  # Tekrar: hiç hatırlamadı
PUAN_ZOR = 2  # Zor: hatırladı ama zorlandı
PUAN_İYİ = 3  # İyi: hatırladı (default doğru yanıt)
PUAN_KOLAY = 4  # Kolay: kolayca hatırladı

# State tanımları
DURUM_YENİ = 0
DURUM_ÖĞRENME = 1
DURUM_TEKRAR = 2
DURUM_YENİDEN = 3  # lapse: unutuldu, yeniden öğreniliyor


# ─── Veri yapıları ────────────────────────────────────────────────────────────


@dataclass
class FSRSState:
    """
    Bir kullanıcı-soru çiftinin FSRS durumu.
    user_item_fsrs tablosunun Python temsili.
    """

    user_id: str
    question_id: str
    stability: float = 1.0  # S: hafıza ömrü (gün)
    difficulty: float = 5.0  # D: 1-10, 5=orta
    due_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_review: datetime | None = None
    state: int = DURUM_YENİ
    reps: int = 0  # toplam tekrar sayısı
    lapses: int = 0  # unutulma sayısı
    scheduled_days: int = 0
    elapsed_days: float = 0.0

    @property
    def retrievability(self) -> float:
        """
        Şu anki hatırlama olasılığı R(t, S).
        t = şu an ile son tekrar arasındaki gün sayısı
        """
        if self.last_review is None:
            return 1.0
        now = datetime.now(UTC)
        t = (now - self.last_review).total_seconds() / 86400.0
        return _retrievability(t, self.stability)

    @property
    def days_overdue(self) -> float:
        """Vadesi kaç gün geçmiş? Negatifse henüz vadesi gelmemiş."""
        now = datetime.now(UTC)
        delta = (now - self.due_date).total_seconds() / 86400.0
        return delta

    @property
    def urgency_score(self) -> float:
        """
        CAT ile entegrasyon için aciliyet skoru.
        0.0: henüz vade gelmemiş
        1.0: tam zamanında
        >1.0: gecikmiş (ne kadar gecikmiş o kadar acil)
        """
        overdue = self.days_overdue
        if overdue <= 0:
            return 0.0
        return min(overdue / max(self.stability, 0.1), 3.0)  # max 3x ağırlık

    def is_due(self, buffer_hours: float = 0.0) -> bool:
        """Tekrar zamanı geldi mi?"""
        return self.days_overdue >= -(buffer_hours / 24.0)


@dataclass
class FSRSResult:
    """Bir tekrarın sonucu — DB'ye yazılacak yeni state."""

    new_state: FSRSState
    interval_days: int  # bir sonraki tekrara kaç gün
    puan: int


# ─── Temel FSRS formülleri ────────────────────────────────────────────────────


def _retrievability(t: float, s: float) -> float:
    """
    R(t, S) = (1 + FACTOR * t / S) ^ DECAY
    t: geçen gün, s: stabilite (gün)
    """
    if s <= 0:
        return 0.0
    return (1.0 + FACTOR * t / s) ** DECAY


def _initial_stability(puan: int) -> float:
    """İlk görülen madde için başlangıç stabilitesi."""
    # w0..w3: puan 1,2,3,4 için S_0 değerleri
    idx = max(0, min(puan - 1, 3))
    return max(W[idx], 0.1)


def _initial_difficulty(puan: int) -> float:
    """İlk görülen madde için başlangıç güçlüğü."""
    # D_0 = w4 - exp(w5 * (puan - 1)) + 1
    d = W[4] - math.exp(W[5] * (puan - 1)) + 1
    return max(1.0, min(10.0, d))


def _next_difficulty(d: float, puan: int) -> float:
    """
    Tekrar sonrası güçlük güncelleme:
    D_new = D - w_D * (puan - 3)
    Mean reversion: D → 5 (orta) yönünde çekim
    """
    d_new = d - W[6] * (puan - 3)
    # Mean reversion: w7 * (5 - d_new) eklenir
    d_new = d_new + W[7] * (5.0 - d_new)
    return max(1.0, min(10.0, d_new))


def _short_term_stability(s: float, puan: int) -> float:
    """
    Kısa dönem (aynı gün) stabilite güncellemesi.
    Öğrenme aşamasında kullanılır.
    """
    return s * math.exp(W[17] * (puan - 3 + W[18]))


def _next_recall_stability(s: float, d: float, r: float, puan: int) -> float:
    """
    Başarılı tekrar sonrası stabilite artışı.
    S_r = S * (e^w8 * (11-D) * S^(-w9) * (e^(w10*(1-R)) - 1) * w15 [if easy] * w16 [if hard])
    """
    hard_penalty = W[15] if puan == PUAN_ZOR else 1.0
    easy_bonus = W[16] if puan == PUAN_KOLAY else 1.0
    return s * (
        math.exp(W[8])
        * (11.0 - d)
        * (s ** (-W[9]))
        * (math.exp(W[10] * (1.0 - r)) - 1.0)
        * hard_penalty
        * easy_bonus
        + 1.0
    )


def _next_forget_stability(s: float, d: float, r: float) -> float:
    """Unutma (lapse) sonrası stabilite sıfırlanması."""
    return (
        W[11]
        * (d ** (-W[12]))
        * ((s + 1.0) ** W[13] - 1.0)
        * math.exp(W[14] * (1.0 - r))
    )


def _interval_from_stability(s: float, desired_r: float = 0.90) -> int:
    """
    İstenen hatırlama olasılığı için gereken aralık (gün).
    t = S / FACTOR * (desired_R^(1/DECAY) - 1)
    """
    interval = s / FACTOR * (desired_r ** (1.0 / DECAY) - 1.0)
    return max(MIN_INTERVAL_DAYS, min(MAX_INTERVAL_DAYS, round(interval)))


# ─── Ana FSRS güncelleme fonksiyonu ──────────────────────────────────────────


def fsrs_update(state: FSRSState, puan: int, desired_r: float = 0.90) -> FSRSResult:
    """
    Bir tekrarı işle → yeni FSRS state döndür.

    Argümanlar:
      state    : mevcut FSRSState
      puan     : 1=tekrar, 2=zor, 3=iyi, 4=kolay
      desired_r: hedef hatırlama olasılığı (varsayılan 0.90)

    Döndürür: FSRSResult(new_state, interval_days, puan)

    Durum makinesi:
      YENİ       → puan ile ÖĞRENME'ye gir
      ÖĞRENME    → puan≥3 ise TEKRAR'a geç, <3 ise ÖĞRENME'de kal
      TEKRAR     → puan≥2 ise TEKRAR'da kal, 1 ise YENİDEN'e gir
      YENİDEN    → puan≥3 ise TEKRAR'a dön
    """
    if puan not in (1, 2, 3, 4):
        raise ValueError(f"Puan 1-4 arasında olmalı, verilen: {puan}")

    now = datetime.now(UTC)

    # Geçen süreyi hesapla (gün)
    if state.last_review is not None:
        elapsed = (now - state.last_review).total_seconds() / 86400.0
    else:
        elapsed = 0.0

    new = FSRSState(
        user_id=state.user_id,
        question_id=state.question_id,
        stability=state.stability,
        difficulty=state.difficulty,
        last_review=now,
        reps=state.reps + 1,
        lapses=state.lapses,
    )

    # ── YENİ madde (ilk görüntülenme) ────────────────────────────
    if state.state == DURUM_YENİ:
        new.stability = _initial_stability(puan)
        new.difficulty = _initial_difficulty(puan)

        if puan >= PUAN_İYİ:
            new.state = DURUM_TEKRAR
            interval = _interval_from_stability(new.stability, desired_r)
        else:
            # Tekrar veya Zor → bugün tekrar göster
            new.state = DURUM_ÖĞRENME
            interval = 1

    # ── ÖĞRENME aşaması ──────────────────────────────────────────
    elif state.state == DURUM_ÖĞRENME:
        new.difficulty = _next_difficulty(state.difficulty, puan)

        if puan >= PUAN_İYİ:
            new.stability = _short_term_stability(state.stability, puan)
            new.state = DURUM_TEKRAR
            interval = _interval_from_stability(new.stability, desired_r)
        else:
            # Hâlâ öğrenme aşamasında
            new.stability = _short_term_stability(state.stability, puan)
            new.state = DURUM_ÖĞRENME
            interval = 1

    # ── TEKRAR aşaması ───────────────────────────────────────────
    elif state.state == DURUM_TEKRAR:
        r = _retrievability(elapsed, state.stability)
        new.difficulty = _next_difficulty(state.difficulty, puan)

        if puan == PUAN_TEKRAR:
            # Unuttu → lapse
            new.stability = _next_forget_stability(state.stability, new.difficulty, r)
            new.state = DURUM_YENİDEN
            new.lapses = state.lapses + 1
            interval = 1
        else:
            new.stability = _next_recall_stability(
                state.stability, new.difficulty, r, puan
            )
            new.state = DURUM_TEKRAR
            interval = _interval_from_stability(new.stability, desired_r)

    # ── YENİDEN ÖĞRENME ──────────────────────────────────────────
    elif state.state == DURUM_YENİDEN:
        new.difficulty = _next_difficulty(state.difficulty, puan)

        if puan >= PUAN_İYİ:
            new.stability = _short_term_stability(state.stability, puan)
            new.state = DURUM_TEKRAR
            interval = _interval_from_stability(new.stability, desired_r)
        else:
            # DM-07: YENİDEN state repeated lapse — forget stability (FSRS v6 spec)
            r = _retrievability(elapsed, state.stability)
            new.stability = _next_forget_stability(state.stability, new.difficulty, r)
            new.state = DURUM_YENİDEN
            interval = 1
    else:
        raise ValueError(f"Bilinmeyen durum: {state.state}")

    new.scheduled_days = interval
    new.elapsed_days = elapsed
    new.due_date = now + timedelta(days=interval)

    return FSRSResult(new_state=new, interval_days=interval, puan=puan)


# ─── YKS puan → FSRS puan dönüşümü ──────────────────────────────────────────


def answer_to_fsrs_rating(
    is_correct: bool,
    response_ms: int | None = None,
    theta: float | None = None,
    item_b: float | None = None,
) -> int:
    """
    CAT yanıtını FSRS puanına çevir.

    Mantık:
      Yanlış yanıt   → PUAN_TEKRAR (1) — her zaman
      Doğru + yavaş  → PUAN_ZOR    (2) — response_ms > 30sn
      Doğru + normal → PUAN_İYİ    (3) — default
      Doğru + hızlı  → PUAN_KOLAY  (4) — response_ms < 5sn VE kolay soru

    Neden yanıt süresi önemli?
      Çabuk doğru yanıt → uzun aralık planla (kolay bilgi)
      Yavaş doğru yanıt → kısa aralık planla (zorlanıyor, erken tekrar)
    """
    if not is_correct:
        return PUAN_TEKRAR

    # Yanıt süresi bazlı kalibrasyon
    if response_ms is not None:
        sn = response_ms / 1000.0
        if sn > 30.0:
            return PUAN_ZOR
        if sn < 5.0 and (item_b is None or item_b < -0.5):
            return PUAN_KOLAY

    return PUAN_İYİ


# ─── Birleşik skor: FSRS urgency + IRT information ───────────────────────────


def combined_priority_score(
    fsrs_state: FSRSState,
    irt_info: float,
    w_fsrs: float = 0.60,
    w_irt: float = 0.40,
) -> float:
    """
    CAT + FSRS birleşik öncelik skoru.

    Soru seçiminde hem hatırlatma aciliyeti hem bilgi kazancı önemlidir:
      score = w_fsrs × urgency + w_irt × normalized_info

    Kullanım (CATSessionService.select_next içinde):
      Vadesi geçmiş kartlar: urgency > 0 → öncelikli seçilir
      Vadesi gelmemiş kartlar: urgency = 0 → sadece IRT info'ya göre

    Ağırlıklar (5K kullanıcı için):
      w_fsrs=0.60: hafıza tazeleme öncelik kazanıyor
      w_irt=0.40:  bilgi kazancı ikincil
    """
    urgency = fsrs_state.urgency_score
    norm_info = min(irt_info / 2.0, 1.0)  # normalize: tipik I(θ) 0-2
    return w_fsrs * urgency + w_irt * norm_info
