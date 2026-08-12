"""Sokratik AI Sohbet, LLM Guardrails ve RAG Bağlam Servisi (KIRO2)

Öğrenci sorularında Sokratik pedagojik yöntemin (direkt cevap vermeden yönlendirme)
uygulanmasını, RAG müfredat bağlamı ile halüsinasyonların engellenmesini ve
güvenlik/müfredat dışı prompt injection engellemesini yönetir.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Direct answer patterns in Turkish YKS context
DIRECT_ANSWER_PATTERNS = [
    r"doğru (cevap|yanıt)\s*[:=]?\s*([a-eA-E]|\d+)",
    r"cevap\s*[:=]?\s*([a-eA-E]|\d+)\s*(şıkkı)?",
    r"sonuç\s*[:=]?\s*\d+",
    r"\bx\s*=\s*-?\d+\b",
    r"bu sorunun cevabı\b",
]

# X08 (12 Ağu 2026): modelin GERÇEKTE ürettiği çıplak-harf sızıntısı ("C", "C) 4")
# mevcut regex'lerin ("cevap C" gibi kelime-bağımlı) YAKALAYAMADIĞI biçim.
# fullmatch kullanılır (search DEĞİL) — "C vitamini alman lazım" gibi cümle
# İÇİNDE geçen harfleri YANLIŞ-POZİTİF olarak yakalamamak için: gerçek Sokratik
# yanıt asla SADECE bir harf/şıktan ibaret olmaz, her zaman açıklayıcı/soru
# metni taşır. (audit-methodology.md "Ucuz Filtre Tuzağı": pozitif kanıt ara,
# yokluk değil — burada pozitif kanıt "yanıtın TAMAMI bu kalıba uyuyor mu".)
_BARE_ANSWER_RE = re.compile(r"^[A-E]\)?(\s*-?\d+(?:[.,]\d+)?)?$", re.IGNORECASE)


def _is_bare_answer_leak(response_text: str) -> bool:
    """Yanıtın TAMAMI yalnız bir şık harfi (+ opsiyonel sayı) mı?"""
    stripped = response_text.strip().rstrip(".!")
    return bool(_BARE_ANSWER_RE.fullmatch(stripped))


PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"bütün talimatları unut",
    r"system prompt",
    r"senin sistem talimatın ne",
    r"pretend to be",
    r"jailbreak",
]

# YKS MEB Curriculum grounding keywords
CURRICULUM_KNOWLEDGE_BASE: dict[str, dict[str, list[str]]] = {
    "matematik": {
        "fonksiyonlar": [
            "Fonksiyon tanım kümesi ve değer kümesi bağıntısı",
            "Birebir ve örten fonksiyon özellikleri",
            "Bileşke fonksiyon (f o g)(x) hesaplama adımları",
            "Ters fonksiyon f^-1(x) bulma yöntemi",
        ],
        "türev": [
            "Limit ve süreklilik tanımı",
            "Türev alma kuralları ve teğet eğimi",
            "Maksimum ve minimum noktaları (Ekstremum)",
        ],
        "küme": [
            "Kümelerde birleşim, kesişim ve fark işlemleri",
            "De Morgan kuralları",
            "Alt küme sayısı formula: 2^n",
        ],
    },
    "fizik": {
        "kuvvet_ve_hareket": [
            "Newton'ın hareket yasaları (F = m * a)",
            "Vektörel büyüklükler ve bileşenlerine ayırma",
            "Sürtünme kuvveti f_s = k * N",
        ],
        "elektrik": [
            "Ohm Yasası (V = I * R)",
            "Seri ve paralel bağlama direnç eşdeğeri",
            "Elektriksel güç P = V * I",
        ],
    },
    "turkce": {
        "paragraf": [
            "Ana düşünce ve yardımcı düşünceler",
            "Paragrafta akışı bozan cümle tespiti",
            "Anlatım biçimleri (Açıklayıcı, Tartışmacı, Betimleyici, Öyküleyici)",
        ],
        "dil_bilgisi": [
            "Cümlenin ögeleri (Özne, Yüklem, Nesne, Tümleç)",
            "Ses olayları (Ünlü düşmesi, Ünsüz yumuşaması)",
            "Yazım kuralları ve noktala işaretleri",
        ],
    },
}


class SocraticRAGGuardrailService:
    """Sokratik AI Sohbet Guardrail ve RAG Bağlam Yöneticisi."""

    def __init__(self) -> None:
        self.direct_answer_regexes = [
            re.compile(p, re.IGNORECASE) for p in DIRECT_ANSWER_PATTERNS
        ]
        self.prompt_injection_regexes = [
            re.compile(p, re.IGNORECASE) for p in PROMPT_INJECTION_PATTERNS
        ]

    def inspect_input_safety(self, prompt: str) -> dict[str, Any]:
        """Girdi prompt injection ve güvenlik denetimi.

        Returns:
            is_safe (bool), reason (str | None)
        """
        if not prompt or not prompt.strip():
            return {"is_safe": False, "reason": "Boş mesaj verilemez."}

        for regex in self.prompt_injection_regexes:
            if regex.search(prompt):
                logger.warning(f"Prompt injection engellendi: {prompt[:50]}")
                return {
                    "is_safe": False,
                    "reason": "Güvenlik uyarısı: Sistem talimatlarını değiştirmeye yönelik ifadeler engellendi.",
                }

        return {"is_safe": True, "reason": None}

    def validate_socratic_compliance(self, response_text: str) -> dict[str, Any]:
        """AI yanıtının Sokratik ilkelere uygunluğunu ve direkt cevap sızıntısını denetler.

        Returns:
            is_compliant (bool), socratic_score (float), direct_answer_detected (bool), suggestions (list[str])
        """
        if not response_text:
            return {
                "is_compliant": False,
                "socratic_score": 0.0,
                "direct_answer_detected": False,
                "suggestions": ["Yanıt boş olamaz."],
            }

        # Direct answer check
        direct_answer_detected = _is_bare_answer_leak(response_text)
        if not direct_answer_detected:
            for regex in self.direct_answer_regexes:
                if regex.search(response_text):
                    direct_answer_detected = True
                    break

        # Question ratio evaluation
        questions = [q for q in response_text.split("?") if q.strip()]
        has_question = len(questions) > 1 or "?" in response_text

        # Scoring
        if direct_answer_detected:
            socratic_score = 0.2
            is_compliant = False
            suggestions = [
                "Cevabı doğrudan açıklamak yerine adım adım düşündüren bir soru sorun."
            ]
        elif not has_question:
            socratic_score = 0.5
            is_compliant = False
            suggestions = [
                "Öğrencinin konuyu kavrayıp kavramadığını ölçmek için yanıtın sonuna açık uçlu bir soru ekleyin."
            ]
        else:
            socratic_score = 0.95
            is_compliant = True
            suggestions = []

        return {
            "is_compliant": is_compliant,
            "socratic_score": socratic_score,
            "direct_answer_detected": direct_answer_detected,
            "suggestions": suggestions,
        }

    def validate_latex_formatting(self, text: str) -> dict[str, Any]:
        """LaTeX matematik sembollerinin ($ ve $$) dengeli kapatıldığını kontrol eder."""
        single_dollar_count = text.count("$") - (text.count("$$") * 2)
        double_dollar_count = text.count("$$")

        is_balanced = (single_dollar_count % 2 == 0) and (double_dollar_count % 2 == 0)
        return {
            "is_valid": is_balanced,
            "single_dollar_count": single_dollar_count,
            "double_dollar_count": double_dollar_count,
        }

    def get_curriculum_grounding(self, subject: str, query: str) -> dict[str, Any]:
        """MEB YKS müfredat bağlamı retrieval (RAG Grounding)."""
        subj_clean = subject.lower().strip()
        query_clean = query.lower().strip()

        matched_concepts: list[str] = []
        subj_data = CURRICULUM_KNOWLEDGE_BASE.get(subj_clean, {})

        for topic, concepts in subj_data.items():
            if topic in query_clean or any(
                word in query_clean for word in topic.split("_")
            ):
                matched_concepts.extend(concepts)

        if not matched_concepts and subj_data:
            # Fallback to first available topic concepts for grounding
            first_topic = next(iter(subj_data))
            matched_concepts = subj_data[first_topic]

        return {
            "subject": subject,
            "grounded_concepts": matched_concepts[:5],
            "rag_context_text": (
                f"MEB Müfredat Bağlamı ({subject.upper()}): "
                + "; ".join(matched_concepts[:5])
                if matched_concepts
                else f"{subject.upper()} Genel YKS Müfredat İlkeleri."
            ),
        }


# Singleton instance
socratic_rag_guardrail_service = SocraticRAGGuardrailService()
