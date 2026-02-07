#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 v2.0 Manual QA Validation Script

Samples random questions from eslesmis_sorucevap_v2.0.jsonl and runs
automated quality checks to determine if the dataset is ready for production.

Usage:
    python scripts/validate_sample.py [JSONL_FILE] [--sample-size N] [--seed S]

    # Default: validates d-dataset/processed/eslesmis_sorucevap_v2.0.jsonl
    python scripts/validate_sample.py

    # Custom file and sample size
    python scripts/validate_sample.py d-dataset/processed/eslesmis_sorucevap_v2.0.jsonl --sample-size 200

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

DEFAULT_FILE = Path(__file__).parent.parent / "d-dataset" / "processed" / "eslesmis_sorucevap_v2.0.jsonl"
SAMPLE_SIZE = 200
PASS_THRESHOLD = 0.95  # 95% accuracy required
SEED = 42

# ---------- Turkish NLP Helpers ----------


def is_nfc_normalized(text: str) -> bool:
    """Check if text is NFC normalized."""
    return text == unicodedata.normalize("NFC", text)


def has_turkish_chars(text: str) -> bool:
    """Check if text contains Turkish-specific characters (expected in Turkish content)."""
    turkish_chars = set("çÇğĞıİöÖşŞüÜ")
    return any(c in turkish_chars for c in text)


def detect_ocr_artifacts(text: str) -> list[str]:
    """Detect common OCR artifacts in text."""
    issues = []
    # Repeated characters (likely OCR error)
    if re.search(r"(.)\1{4,}", text):
        issues.append("repeated_chars")
    # Broken Unicode
    if "\ufffd" in text:
        issues.append("replacement_char")
    # Mixed scripts (Latin + Cyrillic confusion)
    if re.search(r"[а-яА-Я]", text):
        issues.append("cyrillic_chars")
    # Excessive whitespace
    if re.search(r"\s{5,}", text):
        issues.append("excessive_whitespace")
    # Control characters (except newline, tab)
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text):
        issues.append("control_chars")
    return issues


# ---------- Validation Checks ----------


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

    # Check NFC normalization
    if not is_nfc_normalized(text):
        issues.append("not_nfc_normalized")

    # OCR artifacts
    artifacts = detect_ocr_artifacts(text)
    for a in artifacts:
        issues.append(f"ocr:{a}")

    # Check for placeholder/template text
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

    # Check that options have content
    empty_opts = [k for k, v in options.items() if not v or not str(v).strip()]
    if empty_opts:
        issues.append(f"empty_options:{','.join(empty_opts)}")

    # Check answer exists in options
    answer = q.get("answer", "").upper()
    if answer and options and answer not in options:
        issues.append(f"answer_not_in_options:{answer}")

    # Check for duplicate option values
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

    # Check: if question asks "kactir/kactiR" and answer is not a number
    # This is a heuristic - not all "kactir" questions need numeric answers
    if re.search(r"ka[cç]\s*(tane|t[ıi]r|d[ıi]r)", text.lower()):
        # Question asks for a count/number - answer should contain a digit
        if not re.search(r"\d", str(correct_option)):
            # Not necessarily wrong, but flag for review
            issues.append("numeric_q_nonnumeric_a")

    return issues


# ---------- Main Validation ----------


def validate_question(q: dict, idx: int) -> dict:
    """Run all validation checks on a single question."""
    all_issues = []
    checks = {
        "structure": check_structure,
        "answer": check_answer,
        "text_quality": check_text_quality,
        "options": check_options,
        "confidence": check_confidence_consistency,
        "metadata": check_book_metadata,
        "correctness": check_answer_correctness,
    }

    check_results = {}
    for name, func in checks.items():
        issues = func(q)
        check_results[name] = "PASS" if not issues else issues
        all_issues.extend(issues)

    # Severity classification
    critical_issues = [i for i in all_issues if any(i.startswith(p) for p in [
        "missing_field", "empty_answer", "invalid_answer", "empty_text",
        "no_options", "answer_not_in_options", "not_nfc_normalized"
    ])]
    warning_issues = [i for i in all_issues if i not in critical_issues]

    passed = len(critical_issues) == 0

    return {
        "index": idx,
        "book_name": q.get("book_name", "?"),
        "page": q.get("page_number", "?"),
        "question_number": q.get("question_number", "?"),
        "confidence": q.get("confidence", 0),
        "confidence_level": q.get("confidence_level", "?"),
        "passed": passed,
        "critical_issues": critical_issues,
        "warnings": warning_issues,
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


def main():
    parser = argparse.ArgumentParser(description="Phase 4 v2.0 Manual QA Validation")
    parser.add_argument("file", nargs="?", default=str(DEFAULT_FILE), help="JSONL file to validate")
    parser.add_argument("--sample-size", type=int, default=SAMPLE_SIZE, help="Number of questions to sample")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed for reproducibility")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show details of failed questions")
    parser.add_argument("--all", action="store_true", help="Validate all questions (not just sample)")
    args = parser.parse_args()

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    print("=" * 70)
    print("Phase 4 v2.0 - Manual QA Validation")
    print("=" * 70)

    # Load data
    print(f"\nLoading: {filepath}")
    questions = load_jsonl(filepath)
    print(f"Total questions: {len(questions)}")

    # Sample
    if args.all:
        sample = questions
        print(f"Validating ALL {len(sample)} questions")
    else:
        random.seed(args.seed)
        sample_size = min(args.sample_size, len(questions))
        sample = random.sample(questions, sample_size)
        print(f"Sampled: {sample_size} questions (seed={args.seed})")

    # Validate
    print(f"\nRunning 7 validation checks on each question...")
    results = []
    for i, q in enumerate(sample):
        results.append(validate_question(q, i))

    # Summary
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    total = len(results)
    accuracy = passed / total if total > 0 else 0

    print(f"\n{'=' * 70}")
    print(f"RESULTS")
    print(f"{'=' * 70}")
    print(f"  Total validated:  {total}")
    print(f"  Passed:           {passed} ({accuracy:.1%})")
    print(f"  Failed:           {failed} ({1 - accuracy:.1%})")
    print(f"  Threshold:        {PASS_THRESHOLD:.0%}")
    print(f"  Status:           {'PASS' if accuracy >= PASS_THRESHOLD else 'FAIL'}")

    # Issue breakdown
    all_critical = Counter()
    all_warnings = Counter()
    for r in results:
        for issue in r["critical_issues"]:
            all_critical[issue] += 1
        for issue in r["warnings"]:
            all_warnings[issue] += 1

    if all_critical:
        print(f"\n  Critical Issues:")
        for issue, count in all_critical.most_common(20):
            print(f"    {issue}: {count}")

    if all_warnings:
        print(f"\n  Warnings (non-blocking):")
        for issue, count in all_warnings.most_common(20):
            print(f"    {issue}: {count}")

    # Confidence distribution in sample
    conf_levels = Counter(r["confidence_level"] for r in results)
    print(f"\n  Confidence Distribution (sample):")
    for level in ["high", "medium", "low"]:
        count = conf_levels.get(level, 0)
        print(f"    {level}: {count} ({count/total:.1%})")

    # Failed question details
    if failed > 0 and args.verbose:
        print(f"\n{'=' * 70}")
        print(f"FAILED QUESTIONS ({failed})")
        print(f"{'=' * 70}")
        for r in results:
            if not r["passed"]:
                print(f"\n  [{r['index']}] {r['book_name']} p.{r['page']} q.{r['question_number']}")
                print(f"       Confidence: {r['confidence']} ({r['confidence_level']})")
                print(f"       Issues: {', '.join(r['critical_issues'])}")
    elif failed > 0:
        print(f"\n  (Use --verbose to see failed question details)")

    # Final verdict
    print(f"\n{'=' * 70}")
    if accuracy >= PASS_THRESHOLD:
        print(f"QA PASSED ({accuracy:.1%} >= {PASS_THRESHOLD:.0%})")
        print(f"\nSafe to promote to production:")
        print(f"  1. Backup: copy d-dataset/eslesmis_sorucevap.jsonl -> d-dataset/backups/")
        print(f"  2. Promote: copy d-dataset/processed/eslesmis_sorucevap_v2.0.jsonl -> d-dataset/eslesmis_sorucevap.jsonl")
        sys.exit(0)
    else:
        print(f"QA FAILED ({accuracy:.1%} < {PASS_THRESHOLD:.0%})")
        print(f"\nDO NOT promote to production. Fix issues first.")
        sys.exit(1)


if __name__ == "__main__":
    main()
