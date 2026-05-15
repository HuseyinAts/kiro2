"""Judge prompts v1.0 — Opus + Pro double check.

DESIGN NOTES:
  - Turkish prompts: content is YKS Turkish exam, model needs cultural context
  - JSON schema in English: precision over localization for structure
  - Few-shot: 2 examples (1 PASS, 1 FAIL with wrong_answer) to anchor verdict format
  - Temperature 0.0: deterministic
  - Reasoning before verdict: chain-of-thought improves accuracy
  - Output strict JSON: parser-friendly, no prose escape hatches

PROMPT VERSION: v1.0 (taslak — Faz 5.3 calibration sonrası v1.1 revize)
SPEC REFERANSI: docs/llm_judge_spec.md §3 (Output Contract), §4 (Verdict Logic)
"""

from __future__ import annotations

import json
from textwrap import dedent
from typing import Literal

PROMPT_VERSION = "v1.0"

# ============================================================================
# SYSTEM PROMPTS (Opus + Pro paylaşılan persona)
# ============================================================================

JUDGE_PERSONA_TR = dedent("""
    Sen Türkiye'de YKS (TYT/AYT) sınavlarına hazırlık materyali kalitesini
    denetleyen kıdemli bir ÖSYM uzmanı eğitimcisin. Görevin:

    Bir test sorusu + 5 seçenek + "kitap cevabı" verildiğinde, bu sorunun
    öğrenciye gösterilmeye HAZIR olup olmadığına yargı vermek.

    Kalite kriterlerin:
    1. Sorudaki kitap cevabı GERÇEKTEN doğru mu?
    2. Soru metni eksiksiz, anlaşılır, çelişkisiz mi?
    3. 5 seçeneğin hepsi ayırt edici ve anlamlı mı?
    4. Şekil/grafik referansı varsa metinden takip edilebiliyor mu?
       (Bu sürümde image input YOK; "şekildeki üçgen" gibi referanslar
       ancak metin yeterliyse PASS, değilse missing_diagram FAIL.)
    5. Subject (Matematik/Türkçe/...) ile içerik tutarlı mı?

    OUTPUT: SADECE JSON. Açıklama, prelude, suffix YASAK.
    Reasoning JSON'un içinde "reasoning" alanında 1-2 Türkçe cümle.

    Şüphe/sınır vakası → UNCERTAIN ver. PASS ve FAIL için kanıt iste kendinden.
""").strip()

# ============================================================================
# OUTPUT JSON SCHEMA (her iki model için aynı)
# ============================================================================

OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["verdict", "agreed_answer", "issue", "confidence", "reasoning"],
    "properties": {
        "verdict": {"enum": ["PASS", "FAIL", "UNCERTAIN"]},
        "agreed_answer": {
            "anyOf": [{"enum": ["A", "B", "C", "D", "E"]}, {"type": "null"}]
        },
        "issue": {
            "anyOf": [
                {
                    "enum": [
                        "wrong_answer",
                        "ambiguous_question",
                        "missing_diagram",
                        "incomplete_options",
                        "ocr_garbage",
                        "off_topic",
                        "other",
                    ]
                },
                {"type": "null"},
            ]
        },
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "reasoning": {"type": "string", "maxLength": 400},
    },
}

OUTPUT_FORMAT_INSTRUCTION = dedent("""
    OUTPUT FORMAT (JSON only, no other text):

    {
      "verdict": "PASS" | "FAIL" | "UNCERTAIN",
      "agreed_answer": "A" | "B" | "C" | "D" | "E" | null,
      "issue": null | "wrong_answer" | "ambiguous_question" | "missing_diagram"
             | "incomplete_options" | "ocr_garbage" | "off_topic" | "other",
      "confidence": 0.0-1.0,
      "reasoning": "1-2 Türkçe cümle"
    }

    RULES:
    - PASS → agreed_answer == book_answer AND issue == null
    - FAIL → en az 1 net hata; issue null OLAMAZ
    - UNCERTAIN → şüphe varsa; agreed_answer null veya tahminin
    - Confidence: 0.9+ kesin, 0.6-0.9 makul, 0.6 altı şüpheli
""").strip()

# ============================================================================
# FEW-SHOT EXAMPLES (2 ornek, ~150 token toplam)
# ============================================================================

FEW_SHOT_EXAMPLES = [
    {
        "label": "PASS example (matematik, kitap cevabı doğru)",
        "user_input": dedent("""
            SUBJECT: MATEMATIK | EXAM: TYT
            QUESTION: Bir kenarı 6 cm olan eşkenar üçgenin alanı kaç cm²'dir?
            OPTIONS:
              A) 6√3
              B) 9√3
              C) 12√3
              D) 18√3
              E) 36
            BOOK_ANSWER: B
        """).strip(),
        "expected_output": {
            "verdict": "PASS",
            "agreed_answer": "B",
            "issue": None,
            "confidence": 0.98,
            "reasoning": (
                "Eşkenar üçgen alanı = (a²√3)/4 = (36√3)/4 = 9√3. Kitap cevabı (B) doğru."
            ),
        },
    },
    {
        "label": "FAIL example (Türkçe, kitap cevabı yanlış)",
        "user_input": dedent("""
            SUBJECT: TURKCE | EXAM: TYT
            QUESTION: "Çocuk, bahçedeki çiçekleri sevgiyle suluyordu." cümlesinde
                      altı çizili sözcüğün türü nedir?
            OPTIONS:
              A) Belirtili nesne
              B) Belirtisiz nesne
              C) Dolaylı tümleç
              D) Zarf tümleci
              E) Edat tümleci
            BOOK_ANSWER: C
        """).strip(),
        "expected_output": {
            "verdict": "FAIL",
            "agreed_answer": "A",
            "issue": "wrong_answer",
            "confidence": 0.95,
            "reasoning": (
                "'Çiçekleri' belirtili nesnedir (-i hâli + 'neyi' sorusu). "
                "Kitap cevabı (C dolaylı tümleç) yanlış; doğru cevap A."
            ),
        },
    },
]


def format_few_shot() -> str:
    """Render few-shot examples as a single string for prompt injection."""
    parts = ["EXAMPLES (study these to calibrate your verdict format):", ""]
    for ex in FEW_SHOT_EXAMPLES:
        parts.append(f"### {ex['label']}")
        parts.append("INPUT:")
        parts.append(ex["user_input"])
        parts.append("")
        parts.append("OUTPUT:")
        parts.append(json.dumps(ex["expected_output"], ensure_ascii=False, indent=2))
        parts.append("")
    return "\n".join(parts)


# ============================================================================
# USER PROMPT TEMPLATE (per-question payload)
# ============================================================================

USER_PROMPT_TEMPLATE = dedent("""
    SUBJECT: {subject_area} | EXAM: {exam_type}
    QUESTION: {question_text}
    OPTIONS:
      A) {option_a}
      B) {option_b}
      C) {option_c}
      D) {option_d}
      E) {option_e}
    BOOK_ANSWER: {book_answer}

    Yargını yukarıdaki schema'da JSON olarak ver. SADECE JSON, başka metin yok.
""").strip()


def build_user_prompt(
    *,
    subject_area: str,
    exam_type: str,
    question_text: str,
    options: dict[str, str],
    book_answer: Literal["A", "B", "C", "D", "E"],
) -> str:
    """
    Build the per-question user prompt.

    Args:
        subject_area: 'MATEMATIK' | 'TURKCE' | ...
        exam_type: 'TYT' | 'AYT' | 'YDT'
        question_text: NFC-normalized full question text
        options: {"A": "...", "B": "...", ...} all 5 keys required
        book_answer: One of "A".."E"

    Returns:
        Formatted string ready for API call.
    """
    missing = {"A", "B", "C", "D", "E"} - set(options.keys())
    if missing:
        raise ValueError(f"options dict missing keys: {missing}")
    if book_answer not in {"A", "B", "C", "D", "E"}:
        raise ValueError(f"book_answer must be A-E, got {book_answer!r}")

    return USER_PROMPT_TEMPLATE.format(
        subject_area=subject_area,
        exam_type=exam_type,
        question_text=question_text.strip(),
        option_a=options["A"].strip(),
        option_b=options["B"].strip(),
        option_c=options["C"].strip(),
        option_d=options["D"].strip(),
        option_e=options["E"].strip(),
        book_answer=book_answer,
    )


# ============================================================================
# COMBINED PROMPT BUILDERS (per-model)
# ============================================================================


def build_opus_messages(*, user_prompt: str) -> list[dict]:
    """
    Anthropic Messages API format for Opus 4.7.

    Returns messages list with 1 user message. System prompt passed separately
    via Anthropic SDK's `system=` parameter.
    """
    return [{"role": "user", "content": user_prompt}]


def build_opus_system() -> str:
    """Opus system prompt = persona + few-shot + format instruction."""
    return "\n\n".join(
        [
            JUDGE_PERSONA_TR,
            format_few_shot(),
            OUTPUT_FORMAT_INSTRUCTION,
        ]
    )


def build_pro_full_prompt(*, user_prompt: str) -> str:
    """
    Gemini 2.5 Pro single-prompt format.

    Gemini SDK takes one prompt string (no separate system role pre-1.5).
    Concatenate persona + few-shot + format + user query.
    """
    return "\n\n".join(
        [
            JUDGE_PERSONA_TR,
            format_few_shot(),
            OUTPUT_FORMAT_INSTRUCTION,
            "---",
            "NOW JUDGE THIS QUESTION:",
            user_prompt,
        ]
    )


# ============================================================================
# RESPONSE PARSER (model output → validated dict)
# ============================================================================


class JudgeParseError(Exception):
    """Raised when LLM output cannot be parsed into the expected schema."""


def parse_response(raw_text: str) -> dict:
    """
    Parse LLM raw output into validated dict.

    Tolerates:
      - Code fences (```json ... ```)
      - Leading/trailing whitespace
      - One retry-friendly format error (caller decides retry)

    Raises JudgeParseError on:
      - No JSON found
      - Missing required keys
      - Invalid enum values
      - confidence out of [0, 1]
    """
    # Strip code fences
    text = raw_text.strip()
    if text.startswith("```"):
        # Remove first fence line + trailing fence
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise JudgeParseError(f"Not valid JSON: {e}") from e

    # Required keys
    required = {"verdict", "agreed_answer", "issue", "confidence", "reasoning"}
    missing = required - set(data.keys())
    if missing:
        raise JudgeParseError(f"Missing keys: {missing}")

    # Enum validation
    if data["verdict"] not in {"PASS", "FAIL", "UNCERTAIN"}:
        raise JudgeParseError(f"Invalid verdict: {data['verdict']!r}")

    if data["agreed_answer"] is not None and data["agreed_answer"] not in {
        "A",
        "B",
        "C",
        "D",
        "E",
    }:
        raise JudgeParseError(f"Invalid agreed_answer: {data['agreed_answer']!r}")

    valid_issues = {
        None,
        "wrong_answer",
        "ambiguous_question",
        "missing_diagram",
        "incomplete_options",
        "ocr_garbage",
        "off_topic",
        "other",
    }
    if data["issue"] not in valid_issues:
        raise JudgeParseError(f"Invalid issue: {data['issue']!r}")

    # Confidence range
    conf = data["confidence"]
    if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
        raise JudgeParseError(f"confidence out of [0,1]: {conf!r}")

    # Logical consistency
    if data["verdict"] == "PASS" and data["issue"] is not None:
        raise JudgeParseError("PASS cannot have non-null issue")
    if data["verdict"] == "FAIL" and data["issue"] is None:
        raise JudgeParseError("FAIL must have non-null issue")

    return data


# ============================================================================
# AGGREGATION (per-model verdicts → combined verdict)
# ============================================================================


def aggregate_verdicts(opus: dict, pro: dict, book_answer: str) -> dict:
    """
    Apply spec §4.1 aggregation table.

    Returns:
        {
          "combined": "PASS" | "FAIL" | "ESCALATE",
          "agreement": "match" | "answer_disagree" | "verdict_disagree" | "uncertain",
          "issue_primary": str | None,
          "issue_all": list[str],
        }
    """
    issue_priority = [
        "wrong_answer",
        "incomplete_options",
        "missing_diagram",
        "ocr_garbage",
        "ambiguous_question",
        "off_topic",
        "other",
    ]

    issues = [i for i in (opus.get("issue"), pro.get("issue")) if i]
    issue_all = sorted(set(issues))
    issue_primary = next((i for i in issue_priority if i in issue_all), None)

    # Any UNCERTAIN → ESCALATE
    if "UNCERTAIN" in (opus["verdict"], pro["verdict"]):
        return {
            "combined": "ESCALATE",
            "agreement": "uncertain",
            "issue_primary": issue_primary,
            "issue_all": issue_all,
        }

    # Both PASS
    if opus["verdict"] == "PASS" and pro["verdict"] == "PASS":
        if opus["agreed_answer"] == pro["agreed_answer"] == book_answer:
            return {
                "combined": "PASS",
                "agreement": "match",
                "issue_primary": None,
                "issue_all": [],
            }
        return {
            "combined": "ESCALATE",
            "agreement": "answer_disagree",
            "issue_primary": "wrong_answer",
            "issue_all": ["wrong_answer"],
        }

    # Both FAIL
    if opus["verdict"] == "FAIL" and pro["verdict"] == "FAIL":
        return {
            "combined": "FAIL",
            "agreement": "match",
            "issue_primary": issue_primary or "other",
            "issue_all": issue_all or ["other"],
        }

    # Mixed PASS / FAIL
    return {
        "combined": "ESCALATE",
        "agreement": "verdict_disagree",
        "issue_primary": issue_primary,
        "issue_all": issue_all,
    }


# ============================================================================
# SELF-TEST (manuel run: python -m backend.scripts.judge.prompt_v1)
# ============================================================================


def _self_test():
    """Quick smoke: build prompts + parse fake response + aggregate."""
    user = build_user_prompt(
        subject_area="MATEMATIK",
        exam_type="TYT",
        question_text="2 + 2 kaç eder?",
        options={"A": "3", "B": "4", "C": "5", "D": "6", "E": "22"},
        book_answer="B",
    )
    print("=" * 60)
    print("USER PROMPT:")
    print(user)
    print()

    opus_sys = build_opus_system()
    print(
        f"OPUS SYSTEM PROMPT length: {len(opus_sys)} chars (~{len(opus_sys) // 3.5:.0f} tokens)"
    )

    pro_full = build_pro_full_prompt(user_prompt=user)
    print(
        f"PRO FULL PROMPT length: {len(pro_full)} chars (~{len(pro_full) // 3.5:.0f} tokens)"
    )

    print()
    print("PARSE TEST:")
    fake_opus_raw = json.dumps(
        {
            "verdict": "PASS",
            "agreed_answer": "B",
            "issue": None,
            "confidence": 0.99,
            "reasoning": "2+2=4, B doğru.",
        }
    )
    fake_pro_raw = """```json
{
  "verdict": "PASS",
  "agreed_answer": "B",
  "issue": null,
  "confidence": 0.97,
  "reasoning": "Aritmetik temel."
}
```"""
    opus_data = parse_response(fake_opus_raw)
    pro_data = parse_response(fake_pro_raw)
    print(f"  Opus parsed: {opus_data}")
    print(f"  Pro parsed:  {pro_data}")

    combined = aggregate_verdicts(opus_data, pro_data, book_answer="B")
    print(f"  Combined:    {combined}")

    print()
    print("FAIL example aggregation:")
    fake_opus_fail = parse_response(
        json.dumps(
            {
                "verdict": "FAIL",
                "agreed_answer": "A",
                "issue": "wrong_answer",
                "confidence": 0.92,
                "reasoning": "Cevap A olmalı.",
            }
        )
    )
    fake_pro_fail = parse_response(
        json.dumps(
            {
                "verdict": "FAIL",
                "agreed_answer": "A",
                "issue": "wrong_answer",
                "confidence": 0.88,
                "reasoning": "Aynı sebep.",
            }
        )
    )
    combined_fail = aggregate_verdicts(fake_opus_fail, fake_pro_fail, book_answer="B")
    print(f"  Combined:    {combined_fail}")

    print()
    print("ESCALATE (verdict_disagree) test:")
    combined_disagree = aggregate_verdicts(opus_data, fake_pro_fail, book_answer="B")
    print(f"  Combined:    {combined_disagree}")

    print()
    print("PARSE ERROR test:")
    try:
        parse_response('{"verdict": "PASS", "issue": "wrong_answer"}')
    except JudgeParseError as e:
        print(f"  Caught (expected): {e}")


if __name__ == "__main__":
    _self_test()
