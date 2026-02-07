"""Cognitive Load Theory (CLT) Metrics Calculator.

Sweller's Cognitive Load Theory: Intrinsic, Extraneous, Germane load.
Calculates cognitive load estimate for YKS questions.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LoadCategory(str, Enum):
    """Bilissel yuk kategorisi."""

    DUSUK = "dusuk"  # Dusuk yuk
    ORTA = "orta"  # Orta yuk
    YUKSEK = "yuksek"  # Yuksek yuk
    ASIRI = "asiri"  # Asiri yuk (soru sadelestirilmeli)


@dataclass
class CLTResult:
    """Cognitive Load Theory analiz sonucu."""

    cognitive_load_estimate: float  # 0.0 - 1.0
    intrinsic_load: float  # Konunun dogal karmasikligi
    extraneous_load: float  # Gereksiz bilissel yuk
    germane_load: float  # Ogrenmeye katki saglayan yuk (tahmini)
    load_category: LoadCategory
    word_count: int
    sentence_count: int
    step_count: int  # Tahmini cozum adim sayisi
    element_interactivity: int  # Etkilesen bilgi parcasi sayisi
    has_visual: bool
    optimization_suggestions: list[str]

    def to_dict(self) -> dict:
        return {
            "cognitive_load_estimate": round(self.cognitive_load_estimate, 3),
            "intrinsic_load": round(self.intrinsic_load, 3),
            "extraneous_load": round(self.extraneous_load, 3),
            "germane_load": round(self.germane_load, 3),
            "load_category": self.load_category.value,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "step_count": self.step_count,
            "element_interactivity": self.element_interactivity,
            "has_visual": self.has_visual,
            "optimization_suggestions": self.optimization_suggestions,
        }


# --- Karmasiklik sinyalleri ---

MULTI_STEP_SIGNALS = [
    r"\bad\u0131m\w*\b",
    r"\b\u00f6nce\w*\b.*\bsonra\w*\b",
    r"\bbulunuz\b.*\bhesaplay\u0131n\u0131z\b",
    r"\byerine\s+yaz\w*\b",
    r"\bdenklem\w*\b.*\b\u00e7\u00f6z\w*\b",
]

ELEMENT_SIGNALS = [
    r"\bform\u00fcl\w*\b",
    r"\btablo\w*\b",
    r"\bgrafik\w*\b",
    r"\b\u015fekil\w*\b",
    r"\bdenklem\w*\b",
    r"\be\u015fitsizlik\w*\b",
    r"\bfonksiyon\w*\b",
    r"\bmatris\w*\b",
    r"\bvekt\u00f6r\w*\b",
    r"\bt\u00fcrev\w*\b",
    r"\bintegral\w*\b",
    r"\blogaritma\w*\b",
    r"\b\u00fc\u00e7gen\w*\b",
    r"\bdaire\w*\b",
    r"\bolas\u0131l\u0131k\w*\b",
    r"\bistatistik\w*\b",
    r"\bk\u00fcme\w*\b",
]

EXTRANEOUS_SIGNALS = [
    r"\byukar\u0131daki\s+(?:metne|tabloya|grafi\u011fe)\s+g\u00f6re\b",
    r"\ba\u015fa\u011f\u0131daki\w*\s+(?:bilgiler|veriler)\w*\b",
    r"\bbuna\s+g\u00f6re\b",
]


def _normalize(text: str) -> str:
    """Turkce metin normalizasyonu."""
    text = unicodedata.normalize("NFC", text)
    return text.replace("\u0130", "i").replace("I", "\u0131").lower()


def _count_sentences(text: str) -> int:
    """Cumle sayisi (basit)."""
    parts = re.split(r"[.!?]+", text)
    return len([p for p in parts if p.strip()])


def _estimate_steps(text: str) -> int:
    """Tahmini cozum adim sayisi."""
    norm = _normalize(text)
    count = 1  # en az 1 adim
    for pattern in MULTI_STEP_SIGNALS:
        if re.search(pattern, norm, re.UNICODE):
            count += 1
    return min(count, 8)


def _count_elements(text: str) -> int:
    """Etkilesen bilgi parcasi sayisi."""
    norm = _normalize(text)
    count = 0
    for pattern in ELEMENT_SIGNALS:
        if re.search(pattern, norm, re.UNICODE):
            count += 1
    return max(count, 1)


def _detect_visual(text: str) -> bool:
    """Gorsel icerik var mi."""
    norm = _normalize(text)
    visual_keywords = [
        r"\btablo\w*\b",
        r"\bgrafik\w*\b",
        r"\b\u015fekil\w*\b",
        r"\bg\u00f6rsel\w*\b",
    ]
    return any(re.search(p, norm, re.UNICODE) for p in visual_keywords)


def calculate_cognitive_load(
    question_text: str,
    options: Optional[list[str]] = None,
    subject: str = "",
) -> CLTResult:
    """Soru icin bilissel yuk hesapla.

    Args:
        question_text: Soru metni.
        options: Sik listesi (opsiyonel).
        subject: Ders adi (opsiyonel, agirlik icin).

    Returns:
        CLTResult with load estimates.
    """
    full_text = question_text
    if options:
        full_text += " " + " ".join(options)

    norm = _normalize(full_text)
    words = norm.split()
    word_count = len(words)
    sentence_count = _count_sentences(question_text)
    step_count = _estimate_steps(question_text)
    element_count = _count_elements(question_text)
    has_visual = _detect_visual(question_text)

    # --- Intrinsic Load ---
    # Element interactivity based
    intrinsic = min(1.0, element_count * 0.12 + step_count * 0.08)

    # --- Extraneous Load ---
    # Gereksiz metin yuku
    extraneous_count = sum(
        1 for p in EXTRANEOUS_SIGNALS if re.search(p, norm, re.UNICODE)
    )
    word_penalty = max(0, (word_count - 50) / 200)  # 50 kelimeyi asan kisim
    extraneous = min(1.0, extraneous_count * 0.15 + word_penalty)

    # --- Germane Load (tahmini) ---
    germane = max(0, intrinsic * 0.6 - extraneous * 0.3)

    # --- Overall ---
    overall = min(1.0, intrinsic * 0.5 + extraneous * 0.3 + (1 - germane) * 0.2)

    # --- Kategori ---
    if overall < 0.3:
        category = LoadCategory.DUSUK
    elif overall < 0.55:
        category = LoadCategory.ORTA
    elif overall < 0.8:
        category = LoadCategory.YUKSEK
    else:
        category = LoadCategory.ASIRI

    # --- Optimizasyon onerileri ---
    suggestions: list[str] = []
    if word_count > 120:
        suggestions.append(
            "Soru metni cok uzun (>120 kelime). Sadelestirmeyi dusunun."
        )
    if sentence_count > 5:
        suggestions.append("Cok fazla cumle var. Gereksiz bilgileri cikarin.")
    if extraneous > 0.4:
        suggestions.append(
            "Gereksiz bilissel yuk yuksek. "
            "'Yukaridaki metne gore' gibi yonlendirmeleri azaltin."
        )
    if step_count > 4:
        suggestions.append(
            "Cozum adim sayisi fazla. Soruyu parcalamayi dusunun."
        )
    if element_count > 5 and not has_visual:
        suggestions.append(
            "Bircok bilgi parcasi var ama gorsel yok. "
            "Tablo/sekil eklemeyi dusunun."
        )
    if category == LoadCategory.ASIRI:
        suggestions.append("Bilissel yuk asiri yuksek. Bu soru sadelestirilmeli.")

    return CLTResult(
        cognitive_load_estimate=overall,
        intrinsic_load=intrinsic,
        extraneous_load=extraneous,
        germane_load=germane,
        load_category=category,
        word_count=word_count,
        sentence_count=sentence_count,
        step_count=step_count,
        element_interactivity=element_count,
        has_visual=has_visual,
        optimization_suggestions=suggestions,
    )
