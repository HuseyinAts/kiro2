#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_sample.py v2.0 — KIRO2 Dataset Quality Validator

Validates YKS question dataset with 13 quality checks:
  - 7 original structural checks (v1)
  - 6 new content-level checks (v2): hallucination, letter-only options,
    answer twin, cross duplicates, generic AI text, subject consistency

Usage:
    # Sample validation (default 200 questions)
    python scripts/validate_sample.py d-dataset/eslesmis_sorucevap.jsonl

    # Full dataset validation with all checks
    python scripts/validate_sample.py d-dataset/eslesmis_sorucevap.jsonl --all

    # JSON report output
    python scripts/validate_sample.py d-dataset/eslesmis_sorucevap.jsonl --all --report json

    # Show rescuable twin questions
    python scripts/validate_sample.py d-dataset/eslesmis_sorucevap.jsonl --all --rescue-twins

Exit codes:
    0 = QA passed (>95% accuracy)
    1 = QA failed (<95% accuracy)
"""

import argparse
import json
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

# ---------- Configuration ----------

DEFAULT_FILE = Path(__file__).parent.parent / "d-dataset" / "eslesmis_sorucevap.jsonl"
SAMPLE_SIZE = 200
PASS_THRESHOLD = 0.95
SEED = 42

# Severity levels (ordered by priority)
SEVERITY_CRITICAL = "critical"              # Must be deleted
SEVERITY_CRITICAL_RESCUABLE = "critical_rescuable"  # Can be rescued with twin removal
SEVERITY_WARNING = "warning"                # Flagged but kept

# Issue → severity mapping
CRITICAL_PREFIXES = [
    "missing_field", "empty_answer", "invalid_answer", "empty_text",
    "no_options", "answer_not_in_options", "not_nfc_normalized",
    "hallucination_loop", "letter_only_options", "generic_ai_text",
    "exact_duplicate",
]
CRITICAL_RESCUABLE_PREFIXES = [
    "answer_has_twin",
]

# ---------- Turkish NLP Helpers ----------


def is_nfc_normalized(text: str) -> bool:
    """Check if text is NFC normalized."""
    return text == unicodedata.normalize("NFC", text)


def has_turkish_chars(text: str) -> bool:
    """Check if text contains Turkish-specific characters."""
    turkish_chars = set("\u00e7\u00c7\u011f\u011e\u0131\u0130\u00f6\u00d6\u015f\u015e\u00fc\u00dc")
    return any(c in turkish_chars for c in text)


def detect_ocr_artifacts(text: str) -> list[str]:
    """Detect common OCR artifacts in text."""
    issues = []
    if re.search(r"(.)\1{4,}", text):
        issues.append("repeated_chars")
    if "\ufffd" in text:
        issues.append("replacement_char")
    if re.search(r"[\u0430-\u044f\u0410-\u042f]", text):
        issues.append("cyrillic_chars")
    if re.search(r"\s{5,}", text):
        issues.append("excessive_whitespace")
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text):
        issues.append("control_chars")
    return issues


# ---------- V1 Checks (structural) ----------


def check_structure(q: dict) -> list[str]:
    """Check structural validity of a question entry."""
    issues = []
    required_fields = ["book_name", "answer", "text", "confidence", "confidence_level"]
    for field in required_fields:
        if field not in q:
            issues.append(f"missing_field:{field}")
    return issues


def check_answer(q: dict) -> list[str]:
    """Validate answer field."""
    issues = []
    answer = q.get("answer", "")
    if not answer:
        issues.append("empty_answer")
    elif answer.upper() not in "ABCDE":
        issues.append(f"invalid_answer:{answer}")
    elif len(answer) != 1:
        issues.append(f"answer_too_long:{answer}")
    return issues


def check_text_quality(q: dict) -> list[str]:
    """Validate question text quality."""
    issues = []
    text = q.get("text", "")
    if not text:
        issues.append("empty_text")
        return issues
    if len(text) < 10:
        issues.append("text_too_short")
    if not is_nfc_normalized(text):
        issues.append("not_nfc_normalized")
    artifacts = detect_ocr_artifacts(text)
    for a in artifacts:
        issues.append(f"ocr:{a}")
    if text.strip() in ("...", "???", "N/A", "null", "None"):
        issues.append("placeholder_text")
    return issues


def check_options(q: dict) -> list[str]:
    """Validate answer options."""
    issues = []
    options = q.get("options", {})
    if not options:
        issues.append("no_options")
        return issues
    if not isinstance(options, dict):
        issues.append("options_not_dict")
        return issues
    if len(options) < 4:
        issues.append(f"too_few_options:{len(options)}")
    empty_opts = [k for k, v in options.items() if not v or not str(v).strip()]
    if empty_opts:
        issues.append(f"empty_options:{','.join(empty_opts)}")
    answer = q.get("answer", "").upper()
    if answer and options and answer not in options:
        issues.append(f"answer_not_in_options:{answer}")
    values = [str(v).strip().lower() for v in options.values()]
    if len(values) != len(set(values)):
        issues.append("duplicate_option_values")
    return issues


def check_confidence_consistency(q: dict) -> list[str]:
    """Check confidence score matches confidence level."""
    issues = []
    confidence = q.get("confidence", 0.0)
    level = q.get("confidence_level", "")
    if level == "high" and confidence < 0.85:
        issues.append(f"level_mismatch:high_but_{confidence:.2f}")
    elif level == "medium" and (confidence < 0.60 or confidence >= 0.85):
        issues.append(f"level_mismatch:medium_but_{confidence:.2f}")
    elif level == "low" and confidence >= 0.60:
        issues.append(f"level_mismatch:low_but_{confidence:.2f}")
    return issues


def check_book_metadata(q: dict) -> list[str]:
    """Validate book metadata."""
    issues = []
    book_name = q.get("book_name", "")
    if not book_name:
        issues.append("empty_book_name")
    page = q.get("page_number")
    if page is not None and (not isinstance(page, (int, float)) or page < 1):
        issues.append(f"invalid_page:{page}")
    qnum = q.get("question_number")
    if qnum is not None and (not isinstance(qnum, (int, float)) or qnum < 1):
        issues.append(f"invalid_question_number:{qnum}")
    return issues


def check_answer_correctness(q: dict) -> list[str]:
    """Semantic check: does the correct answer make sense with the question?"""
    issues = []
    text = q.get("text", "")
    answer = q.get("answer", "").upper()
    options = q.get("options", {})
    if not text or not answer or not options:
        return issues
    correct_option = options.get(answer, "")
    if not correct_option:
        return issues
    if re.search(r"ka[c\u00e7]\s*(tane|t[\u0131i]r|d[\u0131i]r)", text.lower()):
        if not re.search(r"\d", str(correct_option)):
            issues.append("numeric_q_nonnumeric_a")
    return issues


# ---------- V2 Checks (content-level) ----------


def check_hallucination(q: dict) -> list[str]:
    """Detect AI hallucination loops via 5-gram repetition.

    When the OCR model (Qwen3-8B) hallucinates, it produces repeating n-gram
    patterns. A 5-gram appearing 3+ times in a single question text is a strong
    signal of hallucination (verified 0% false positive on production data).
    """
    text = q.get("text", "")
    if not text or len(text) < 50:
        return []

    words = text.split()
    if len(words) < 15:
        return []

    ngram_counts: dict[str, int] = {}
    for i in range(len(words) - 4):
        ng = " ".join(words[i : i + 5])
        ngram_counts[ng] = ngram_counts.get(ng, 0) + 1

    max_repeat = max(ngram_counts.values()) if ngram_counts else 0
    if max_repeat >= 3:
        return [f"hallucination_loop:5gram_x{max_repeat}"]

    return []


def check_letter_only_options(q: dict) -> list[str]:
    """Detect options that are just letter labels (A/B/C/D/E).

    When OCR fails to extract option content, it captures only the option
    labels themselves. These records have zero educational value.
    Handles formats: "A", "A)", "A.", "(A)" etc.
    """
    options = q.get("options", {})
    if not options or len(options) < 4:
        return []

    letter_set = {"a", "b", "c", "d", "e"}
    vals_clean = set()
    for v in options.values():
        cleaned = str(v).strip().lower()
        # Strip common formatting: "A)", "A.", "(A)"
        cleaned = cleaned.lstrip("(").rstrip(")").rstrip(".").strip()
        vals_clean.add(cleaned)

    if vals_clean.issubset(letter_set):
        return ["letter_only_options"]

    return []


def check_answer_twin(q: dict) -> list[str]:
    """Detect when correct answer has an identical twin option.

    OCR often duplicates the last line, creating a twin of one option
    (usually E). If the correct answer has a twin, the question is ambiguous.
    Some can be rescued by removing the twin (critical_rescuable severity).
    """
    options = q.get("options", {})
    answer = q.get("answer", "").upper()

    if not options or not answer or answer not in options:
        return []

    correct_val = str(options[answer]).strip().lower()
    if not correct_val:
        return []

    twins = []
    for k, v in options.items():
        if k != answer and str(v).strip().lower() == correct_val:
            twins.append(k)

    if twins:
        return [f"answer_has_twin:{','.join(twins)}"]

    return []


def check_subject_consistency(q: dict) -> list[str]:
    """Heuristic: detect potential subject mismatch.

    Flags questions where the book subject doesn't match the content.
    E.g., a biology book containing math formulas in options.
    """
    book_name = q.get("book_name", "").lower()
    text = q.get("text", "").lower()
    options = q.get("options", {})

    math_keywords = {
        "denklem", "fonksiyon", "integral", "t\u00fcrev", "polinom",
        "logaritma", "matris", "determinant", "limit", "asimptot",
    }
    non_math_subjects = {
        "biyoloji", "kimya", "tarih", "co\u011frafya", "edebiyat",
        "felsefe", "sosyoloji", "psikoloji", "din",
    }

    is_non_math = any(subj in book_name for subj in non_math_subjects)
    if not is_non_math:
        return []

    opt_text = " ".join(str(v).lower() for v in options.values())
    combined = f"{text} {opt_text}"
    math_count = sum(1 for kw in math_keywords if kw in combined)

    if math_count >= 2:
        return ["subject_mismatch_heuristic"]

    return []


# ---------- Batch-Level Checks ----------


def build_batch_index(questions: list[dict]) -> dict[int, list[str]]:
    """Build batch-level issue index over all questions.

    Runs cross-record checks that need the full dataset:
    1. Exact duplicates (same text + answer + options)
    2. Generic AI text (same text, different answers)

    Returns: {question_index: [issue_strings]}
    """
    batch_issues: dict[int, list[str]] = defaultdict(list)

    # --- Exact Duplicates ---
    fingerprints: dict[str, list[int]] = defaultdict(list)
    for i, q in enumerate(questions):
        text = q.get("text", "").strip()
        answer = q.get("answer", "").strip()
        opts = json.dumps(q.get("options", {}), sort_keys=True, ensure_ascii=False)
        fp = f"{text}|{answer}|{opts}"
        fingerprints[fp].append(i)

    for fp, indices in fingerprints.items():
        if len(indices) > 1:
            # Keep highest confidence, mark rest as exact duplicate
            best_idx = max(indices, key=lambda i: questions[i].get("confidence", 0))
            for idx in indices:
                if idx != best_idx:
                    batch_issues[idx].append(
                        f"exact_duplicate:of_idx_{best_idx}_group_{len(indices)}"
                    )

    # --- Generic AI Text / Answer Uncertain ---
    # Two categories based on text length:
    #   - generic_ai_text (CRITICAL): short text (<50 chars) with different answers
    #     across books = AI-generated filler, not real questions
    #   - answer_uncertain (WARNING): longer text with different answers = possibly
    #     real questions matched to wrong answer keys
    text_groups: dict[str, list[int]] = defaultdict(list)
    for i, q in enumerate(questions):
        text = q.get("text", "").strip().lower()
        if text and len(text) > 5:
            text_groups[text].append(i)

    for text, indices in text_groups.items():
        if len(indices) < 2:
            continue
        answers = set(questions[i].get("answer", "") for i in indices)
        if len(answers) > 1:
            is_short = len(text) < 50
            for idx in indices:
                if is_short:
                    batch_issues[idx].append(
                        f"generic_ai_text:short_{len(text)}ch_{len(indices)}_records"
                    )
                else:
                    batch_issues[idx].append(
                        f"answer_uncertain:same_text_{len(indices)}_answers_{len(answers)}"
                    )

    return dict(batch_issues)


# ---------- Twin Rescue Analysis ----------


def analyze_twin_rescue(q: dict) -> dict | None:
    """Analyze if an answer-twin question can be rescued.

    A question is rescuable if:
    1. It has exactly one twin of the correct answer
    2. Removing the twin leaves 4 clean options
    3. No other duplicate options remain
    4. No hallucination detected

    Returns rescue info dict or None if not rescuable.
    """
    options = q.get("options", {})
    answer = q.get("answer", "").upper()

    if not options or not answer or answer not in options:
        return None

    correct_val = str(options[answer]).strip().lower()
    twins = [k for k, v in options.items()
             if k != answer and str(v).strip().lower() == correct_val]

    if not twins:
        return None

    # Check hallucination (not rescuable if hallucinated)
    if check_hallucination(q):
        return None

    # Try removing twin(s) and check remaining options
    remaining = {k: v for k, v in options.items() if k not in twins}
    remaining_vals = [str(v).strip().lower() for v in remaining.values()]

    # Check if remaining options still have duplicates
    if len(remaining_vals) != len(set(remaining_vals)):
        return None

    # Need at least 4 options after removal
    if len(remaining) < 4:
        return None

    return {
        "original_options": options,
        "removed_twins": twins,
        "remaining_options": remaining,
        "remaining_count": len(remaining),
    }


# ---------- Validation Engine ----------


def classify_severity(issue: str) -> str:
    """Classify an issue string into severity level."""
    for prefix in CRITICAL_PREFIXES:
        if issue.startswith(prefix):
            return SEVERITY_CRITICAL
    for prefix in CRITICAL_RESCUABLE_PREFIXES:
        if issue.startswith(prefix):
            return SEVERITY_CRITICAL_RESCUABLE
    return SEVERITY_WARNING


def validate_question(
    q: dict,
    idx: int,
    batch_issues: dict[int, list[str]] | None = None,
) -> dict:
    """Run all validation checks on a single question."""
    all_issues = []

    # V1 checks (per-question structural)
    checks = {
        "structure": check_structure,
        "answer": check_answer,
        "text_quality": check_text_quality,
        "options": check_options,
        "confidence": check_confidence_consistency,
        "metadata": check_book_metadata,
        "correctness": check_answer_correctness,
    }

    # V2 checks (per-question content)
    v2_checks = {
        "hallucination": check_hallucination,
        "letter_only": check_letter_only_options,
        "answer_twin": check_answer_twin,
        "subject_consistency": check_subject_consistency,
    }

    check_results = {}
    for name, func in {**checks, **v2_checks}.items():
        issues = func(q)
        check_results[name] = "PASS" if not issues else issues
        all_issues.extend(issues)

    # Batch-level issues (if available)
    if batch_issues and idx in batch_issues:
        bi = batch_issues[idx]
        check_results["batch"] = bi
        all_issues.extend(bi)
    elif batch_issues is not None:
        check_results["batch"] = "PASS"

    # Classify by severity
    critical = [i for i in all_issues if classify_severity(i) == SEVERITY_CRITICAL]
    rescuable = [i for i in all_issues if classify_severity(i) == SEVERITY_CRITICAL_RESCUABLE]
    warnings = [i for i in all_issues if classify_severity(i) == SEVERITY_WARNING]

    # A question passes if it has no critical AND no rescuable issues
    passed = len(critical) == 0 and len(rescuable) == 0

    return {
        "index": idx,
        "book_name": q.get("book_name", "?"),
        "page": q.get("page_number", "?"),
        "question_number": q.get("question_number", "?"),
        "confidence": q.get("confidence", 0),
        "confidence_level": q.get("confidence_level", "?"),
        "passed": passed,
        "critical_issues": critical,
        "rescuable_issues": rescuable,
        "warnings": warnings,
        "checks": check_results,
    }


def load_jsonl(path: Path) -> list[dict]:
    """Load JSONL file."""
    questions = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    questions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return questions


# ---------- Report Generators ----------


def print_text_report(
    results: list[dict],
    questions: list[dict],
    rescue_twins: bool = False,
    verbose: bool = False,
) -> None:
    """Print human-readable text report."""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    accuracy = passed / total if total > 0 else 0

    # Count by severity
    n_critical = sum(1 for r in results if r["critical_issues"])
    n_rescuable = sum(1 for r in results
                      if r["rescuable_issues"] and not r["critical_issues"])
    n_warnings_only = sum(1 for r in results
                          if r["warnings"] and not r["critical_issues"]
                          and not r["rescuable_issues"])

    print(f"\n{'=' * 70}")
    print("RESULTS")
    print(f"{'=' * 70}")
    print(f"  Total validated:   {total}")
    print(f"  Passed:            {passed} ({accuracy:.1%})")
    print(f"  Failed:            {failed} ({1 - accuracy:.1%})")
    print(f"    Critical:        {n_critical}")
    print(f"    Rescuable:       {n_rescuable}")
    print(f"  Warnings only:     {n_warnings_only}")
    print(f"  Threshold:         {PASS_THRESHOLD:.0%}")
    print(f"  Status:            {'PASS' if accuracy >= PASS_THRESHOLD else 'FAIL'}")

    # Issue breakdown
    all_critical = Counter()
    all_rescuable = Counter()
    all_warnings = Counter()
    for r in results:
        for issue in r["critical_issues"]:
            # Group by prefix (strip detail after colon)
            key = issue.split(":")[0]
            all_critical[key] += 1
        for issue in r["rescuable_issues"]:
            key = issue.split(":")[0]
            all_rescuable[key] += 1
        for issue in r["warnings"]:
            key = issue.split(":")[0]
            all_warnings[key] += 1

    if all_critical:
        print("\n  Critical Issues (must delete):")
        for issue, count in all_critical.most_common(20):
            pct = count / total * 100
            print(f"    {issue}: {count} ({pct:.1f}%)")

    if all_rescuable:
        print("\n  Rescuable Issues (can fix with twin removal):")
        for issue, count in all_rescuable.most_common(10):
            pct = count / total * 100
            print(f"    {issue}: {count} ({pct:.1f}%)")

    if all_warnings:
        print("\n  Warnings (non-blocking):")
        for issue, count in all_warnings.most_common(20):
            pct = count / total * 100
            print(f"    {issue}: {count} ({pct:.1f}%)")

    # Confidence distribution
    conf_levels = Counter(r["confidence_level"] for r in results)
    print("\n  Confidence Distribution:")
    for level in ["high", "medium", "low"]:
        count = conf_levels.get(level, 0)
        print(f"    {level}: {count} ({count / total:.1%})")

    # Per-check pass rates
    all_check_names = set()
    for r in results:
        all_check_names.update(r["checks"].keys())
    print("\n  Check Pass Rates:")
    for check_name in sorted(all_check_names):
        pass_count = sum(1 for r in results if r["checks"].get(check_name) == "PASS")
        print(f"    {check_name}: {pass_count}/{total} ({pass_count / total:.1%})")

    # Twin rescue analysis
    if rescue_twins:
        print(f"\n{'=' * 70}")
        print("TWIN RESCUE ANALYSIS")
        print(f"{'=' * 70}")
        rescuable_count = 0
        not_rescuable_count = 0
        for r in results:
            if not r["rescuable_issues"]:
                continue
            idx = r["index"]
            q = questions[idx] if idx < len(questions) else None
            if q is None:
                continue
            rescue = analyze_twin_rescue(q)
            if rescue:
                rescuable_count += 1
                if verbose:
                    print(f"\n  [{idx}] {r['book_name']} p.{r['page']} q.{r['question_number']}")
                    print(f"       Twins removed: {rescue['removed_twins']}")
                    print(f"       Remaining: {rescue['remaining_count']} options")
            else:
                not_rescuable_count += 1

        print(f"\n  Rescuable (twin removal): {rescuable_count}")
        print(f"  Not rescuable:            {not_rescuable_count}")
        if not verbose and rescuable_count > 0:
            print("  (Use --verbose to see individual rescue details)")

    # Failed question details
    if failed > 0 and verbose:
        print(f"\n{'=' * 70}")
        print(f"FAILED QUESTIONS (first 50 of {failed})")
        print(f"{'=' * 70}")
        shown = 0
        for r in results:
            if not r["passed"] and shown < 50:
                print(f"\n  [{r['index']}] {r['book_name']} p.{r['page']} q.{r['question_number']}")
                print(f"       Confidence: {r['confidence']} ({r['confidence_level']})")
                if r["critical_issues"]:
                    print(f"       Critical: {', '.join(r['critical_issues'])}")
                if r["rescuable_issues"]:
                    print(f"       Rescuable: {', '.join(r['rescuable_issues'])}")
                shown += 1
    elif failed > 0:
        print("\n  (Use --verbose to see failed question details)")

    # Final verdict
    print(f"\n{'=' * 70}")
    if accuracy >= PASS_THRESHOLD:
        print(f"QA PASSED ({accuracy:.1%} >= {PASS_THRESHOLD:.0%})")
    else:
        print(f"QA FAILED ({accuracy:.1%} < {PASS_THRESHOLD:.0%})")
        print(f"\nRecommended: Run v2.2 pipeline to filter {n_critical} critical + rescue {n_rescuable}.")


def generate_json_report(
    results: list[dict],
    questions: list[dict],
    filepath: str,
) -> dict:
    """Generate structured JSON report."""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    accuracy = passed / total if total > 0 else 0

    # Aggregate issues
    critical_agg = Counter()
    rescuable_agg = Counter()
    warning_agg = Counter()
    for r in results:
        for issue in r["critical_issues"]:
            critical_agg[issue.split(":")[0]] += 1
        for issue in r["rescuable_issues"]:
            rescuable_agg[issue.split(":")[0]] += 1
        for issue in r["warnings"]:
            warning_agg[issue.split(":")[0]] += 1

    # Twin rescue stats
    rescuable_indices = []
    not_rescuable_indices = []
    for r in results:
        if not r["rescuable_issues"]:
            continue
        idx = r["index"]
        q = questions[idx] if idx < len(questions) else None
        if q and analyze_twin_rescue(q):
            rescuable_indices.append(idx)
        else:
            not_rescuable_indices.append(idx)

    # Per-check pass rates
    all_check_names = set()
    for r in results:
        all_check_names.update(r["checks"].keys())
    check_pass_rates = {}
    for check_name in sorted(all_check_names):
        pass_count = sum(1 for r in results if r["checks"].get(check_name) == "PASS")
        check_pass_rates[check_name] = {
            "passed": pass_count,
            "total": total,
            "rate": round(pass_count / total, 4) if total > 0 else 0,
        }

    # Book-level breakdown
    book_issues: dict[str, dict] = defaultdict(lambda: {"total": 0, "failed": 0, "issues": Counter()})
    for r in results:
        book = r["book_name"]
        book_issues[book]["total"] += 1
        if not r["passed"]:
            book_issues[book]["failed"] += 1
            for issue in r["critical_issues"] + r["rescuable_issues"]:
                book_issues[book]["issues"][issue.split(":")[0]] += 1

    # Top problematic books
    problematic_books = []
    for book, stats in book_issues.items():
        if stats["failed"] > 0:
            fail_rate = stats["failed"] / stats["total"]
            problematic_books.append({
                "book_name": book,
                "total": stats["total"],
                "failed": stats["failed"],
                "fail_rate": round(fail_rate, 4),
                "top_issues": dict(stats["issues"].most_common(5)),
            })
    problematic_books.sort(key=lambda x: x["fail_rate"], reverse=True)

    report = {
        "version": "2.0",
        "file": str(filepath),
        "total_questions": total,
        "summary": {
            "passed": passed,
            "failed": total - passed,
            "accuracy": round(accuracy, 4),
            "threshold": PASS_THRESHOLD,
            "status": "PASS" if accuracy >= PASS_THRESHOLD else "FAIL",
        },
        "severity_breakdown": {
            "critical": sum(critical_agg.values()),
            "critical_rescuable": sum(rescuable_agg.values()),
            "warning": sum(warning_agg.values()),
        },
        "critical_issues": dict(critical_agg.most_common()),
        "rescuable_issues": dict(rescuable_agg.most_common()),
        "warnings": dict(warning_agg.most_common()),
        "twin_rescue": {
            "rescuable_count": len(rescuable_indices),
            "not_rescuable_count": len(not_rescuable_indices),
        },
        "check_pass_rates": check_pass_rates,
        "problematic_books": problematic_books[:20],
        "failed_indices": [r["index"] for r in results if not r["passed"]],
    }

    return report


# ---------- Main ----------


def main():
    parser = argparse.ArgumentParser(
        description="KIRO2 Dataset Quality Validator v2.0 (13 checks)",
    )
    parser.add_argument(
        "file", nargs="?", default=str(DEFAULT_FILE),
        help="JSONL file to validate",
    )
    parser.add_argument("--sample-size", type=int, default=SAMPLE_SIZE)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--all", action="store_true",
        help="Validate all questions (enables batch checks)",
    )
    parser.add_argument(
        "--report", choices=["text", "json"], default="text",
        help="Output format: text (default) or json",
    )
    parser.add_argument(
        "--rescue-twins", action="store_true",
        help="Show twin rescue analysis",
    )
    args = parser.parse_args()

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    if args.report == "text":
        print("=" * 70)
        print("KIRO2 Dataset Quality Validator v2.0")
        print("=" * 70)

    # Load data
    if args.report == "text":
        print(f"\nLoading: {filepath}")
    questions = load_jsonl(filepath)
    if args.report == "text":
        print(f"Total questions: {len(questions)}")

    # Build batch index (always, for full dataset awareness)
    if args.report == "text":
        print("Building batch index (cross-record checks)...")
    batch_issues = build_batch_index(questions)
    batch_flagged = len(batch_issues)
    if args.report == "text":
        print(f"Batch checks flagged: {batch_flagged} questions")

    # Determine validation set
    if args.all:
        sample = questions
        sample_indices = list(range(len(questions)))
        if args.report == "text":
            print(f"Validating ALL {len(sample)} questions (13 checks each)")
    else:
        random.seed(args.seed)
        sample_indices = random.sample(range(len(questions)), min(args.sample_size, len(questions)))
        sample = [questions[i] for i in sample_indices]
        if args.report == "text":
            print(f"Sampled: {len(sample)} questions (seed={args.seed})")

    # Validate
    if args.report == "text":
        print("\nRunning 13 validation checks...")
    results = []
    for i, idx in enumerate(sample_indices):
        q = questions[idx]
        result = validate_question(q, idx, batch_issues)
        results.append(result)

        # Progress indicator for large datasets
        if args.report == "text" and len(sample) > 1000 and (i + 1) % 5000 == 0:
            print(f"  ...{i + 1}/{len(sample)}")

    # Output
    accuracy = sum(1 for r in results if r["passed"]) / len(results) if results else 0

    if args.report == "json":
        report = generate_json_report(results, questions, str(filepath))
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text_report(results, questions, args.rescue_twins, args.verbose)

    sys.exit(0 if accuracy >= PASS_THRESHOLD else 1)


if __name__ == "__main__":
    main()
