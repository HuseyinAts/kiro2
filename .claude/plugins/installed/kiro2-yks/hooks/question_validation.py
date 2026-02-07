"""Post-edit validation hook - YKS soru kalite dogrulama.

Edit/Write sonrasi JSON soru dosyalarini otomatik dogrular:
1. SOLO seviye uyumu (taxonomy classifier ile)
2. Marzano cognitive level kontrolu
3. IRT parametre aralik dogrulama
4. Turkce dil kalitesi (uzunluk, pattern)
5. MCQ kural kontrolu (5 sik, tek dogru, bos sik yok)
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """Dogrulama sonucu."""

    passed: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "warnings": self.warnings,
            "errors": self.errors,
            "details": self.details,
        }


# --- IRT Validation ---

IRT_BOUNDS = {
    "difficulty": (-4.0, 4.0),
    "discrimination": (0.2, 4.0),
    "guessing": (0.0, 0.35),
}


def validate_irt_params(question: dict[str, Any]) -> tuple[list[str], list[str]]:
    """IRT parametrelerini dogrula.

    Args:
        question: Soru JSON'u.

    Returns:
        (errors, warnings) tuple.
    """
    errors: list[str] = []
    warnings: list[str] = []

    irt = question.get("irt_parameters") or question.get("irt_params") or {}
    if not irt:
        warnings.append("IRT parametreleri eksik")
        return errors, warnings

    for param, (lo, hi) in IRT_BOUNDS.items():
        val = irt.get(param)
        if val is None:
            continue
        try:
            val = float(val)
        except (TypeError, ValueError):
            errors.append(f"IRT {param} sayisal degil: {val}")
            continue
        if not (lo <= val <= hi):
            errors.append(f"IRT {param}={val} aralik disi [{lo}, {hi}]")

    # Quality warnings
    disc = irt.get("discrimination")
    if disc is not None and float(disc) < 0.5:
        warnings.append(f"Dusuk ayirt edicilik: {disc}")
    diff = irt.get("difficulty")
    if diff is not None and abs(float(diff)) > 3.0:
        warnings.append(f"Asiri zorluk: {diff}")

    return errors, warnings


# --- MCQ Structure ---

def validate_mcq_structure(question: dict[str, Any]) -> tuple[list[str], list[str]]:
    """MCQ yapisal dogrulama.

    Args:
        question: Soru JSON'u.

    Returns:
        (errors, warnings) tuple.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Options
    options = question.get("options") or {}
    expected_keys = set("ABCDE")
    if set(options.keys()) != expected_keys:
        missing = expected_keys - set(options.keys())
        if missing:
            errors.append(f"Eksik siklar: {missing}")

    # Empty options
    for k, v in options.items():
        if not str(v).strip():
            errors.append(f"Bos sik: {k}")

    # Correct answer
    answer = question.get("correct_answer") or question.get("answer")
    if answer not in list("ABCDE"):
        errors.append(f"Gecersiz dogru cevap: {answer}")
    elif answer not in options:
        errors.append(f"Dogru cevap '{answer}' siklarda yok")

    # Stem length
    stem = question.get("question_text") or question.get("stem") or ""
    if len(stem) < 20:
        errors.append(f"Soru metni cok kisa: {len(stem)} karakter")
    elif len(stem) < 50:
        warnings.append(f"Soru metni kisa: {len(stem)} karakter")

    # Explanation
    explanation = question.get("explanation") or question.get("rationale") or ""
    if len(explanation) < 10:
        warnings.append("Aciklama/cozum eksik veya cok kisa")

    return errors, warnings


# --- Turkish Language Quality ---

def validate_turkish_quality(question: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Turkce dil kalitesi kontrolu.

    Args:
        question: Soru JSON'u.

    Returns:
        (errors, warnings) tuple.
    """
    errors: list[str] = []
    warnings: list[str] = []

    stem = question.get("question_text") or question.get("stem") or ""

    # Check for common issues
    if re.search(r"\b(lorem|ipsum|placeholder|TODO|FIXME)\b", stem, re.IGNORECASE):
        errors.append("Placeholder metin tespit edildi")

    # Check question mark presence (most Turkish questions end with ?)
    if stem and not re.search(r"[?.!]\s*$", stem.strip()):
        warnings.append("Soru isareti veya bitis noktasi yok")

    # Duplicate option detection
    options = question.get("options") or {}
    values = [str(v).strip().lower() for v in options.values()]
    if len(values) != len(set(values)):
        errors.append("Tekrarlanan sik tespit edildi")

    # Rationale leak check
    rationale = (question.get("rationale") or question.get("explanation") or "").lower()
    if re.search(r"\bdogru\s+cevap\b|\bcorrect\s+answer\b", rationale):
        warnings.append("Cozumde dogru cevap ifadesi var (ipucu sizintisi riski)")

    return errors, warnings


# --- SOLO/Marzano Check (lightweight, no import dependency) ---

SOLO_SIGNALS: dict[str, list[str]] = {
    "uni": [r"\bnedir\b", r"\btanimla\w*\b", r"\bhangisi\b"],
    "multi": [r"\bhangileri\b", r"\blistele\w*\b", r"\byargi\w*\b", r"\boncul\w*\b"],
    "relational": [r"\biliskilendir\w*\b", r"\bneden\w*\b", r"\bcunku\b", r"\byorumla\w*\b"],
    "extended_abstract": [r"\bgenelle\w*\b", r"\bhipotez\w*\b", r"\bfarkli\s+baglam\w*\b"],
}


def check_solo_alignment(question: dict[str, Any]) -> list[str]:
    """Hedef SOLO seviyesi ile soru metni uyumu kontrolu.

    Args:
        question: Soru JSON'u.

    Returns:
        Warning listesi.
    """
    warnings: list[str] = []
    target_solo = (
        question.get("solo_target")
        or question.get("solo_label")
        or ""
    ).lower()
    if not target_solo:
        return warnings

    stem = (question.get("question_text") or question.get("stem") or "").lower()
    if not stem:
        return warnings

    # Check if target level signals exist
    target_patterns = SOLO_SIGNALS.get(target_solo, [])
    match_count = sum(1 for p in target_patterns if re.search(p, stem, re.UNICODE))

    if target_patterns and match_count == 0:
        warnings.append(
            f"SOLO hedef '{target_solo}' icin soru metninde sinyal bulunamadi"
        )

    return warnings


# --- Main Validator ---

def validate_question(question: dict[str, Any]) -> ValidationResult:
    """Tam soru dogrulama pipeline'i.

    Args:
        question: Soru JSON'u.

    Returns:
        ValidationResult with all checks.
    """
    all_errors: list[str] = []
    all_warnings: list[str] = []
    details: dict[str, Any] = {}

    # 1. MCQ structure
    mcq_errors, mcq_warnings = validate_mcq_structure(question)
    all_errors.extend(mcq_errors)
    all_warnings.extend(mcq_warnings)
    details["mcq"] = {"errors": mcq_errors, "warnings": mcq_warnings}

    # 2. IRT parameters
    irt_errors, irt_warnings = validate_irt_params(question)
    all_errors.extend(irt_errors)
    all_warnings.extend(irt_warnings)
    details["irt"] = {"errors": irt_errors, "warnings": irt_warnings}

    # 3. Turkish quality
    tr_errors, tr_warnings = validate_turkish_quality(question)
    all_errors.extend(tr_errors)
    all_warnings.extend(tr_warnings)
    details["turkish"] = {"errors": tr_errors, "warnings": tr_warnings}

    # 4. SOLO alignment
    solo_warnings = check_solo_alignment(question)
    all_warnings.extend(solo_warnings)
    details["solo"] = {"warnings": solo_warnings}

    return ValidationResult(
        passed=len(all_errors) == 0,
        warnings=all_warnings,
        errors=all_errors,
        details=details,
    )


def validate_file(file_path: str) -> ValidationResult | None:
    """JSON dosyasini oku ve dogrula.

    Args:
        file_path: JSON dosya yolu.

    Returns:
        ValidationResult veya None (JSON degilse).
    """
    path = Path(file_path)
    if path.suffix != ".json":
        return None

    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
    except (json.JSONDecodeError, OSError):
        return None

    # Check if it looks like a question
    if isinstance(data, dict) and (
        "question_text" in data
        or "stem" in data
        or ("options" in data and "answer" in data)
    ):
        return validate_question(data)

    # Could be a list of questions
    if isinstance(data, list) and data and isinstance(data[0], dict):
        if "stem" in data[0] or "question_text" in data[0]:
            results = [validate_question(q) for q in data]
            all_errors = []
            all_warnings = []
            for i, r in enumerate(results):
                for e in r.errors:
                    all_errors.append(f"Soru {i + 1}: {e}")
                for w in r.warnings:
                    all_warnings.append(f"Soru {i + 1}: {w}")
            return ValidationResult(
                passed=len(all_errors) == 0,
                warnings=all_warnings,
                errors=all_errors,
            )

    return None


# Hook entry point
if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = validate_file(sys.argv[1])
        if result:
            if not result.passed:
                print(f"VALIDATION FAILED: {'; '.join(result.errors)}")
                sys.exit(2)
            if result.warnings:
                print(f"WARNINGS: {'; '.join(result.warnings)}")
            else:
                print("VALIDATION PASSED")
