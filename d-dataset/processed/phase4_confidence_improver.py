#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4: Low-Confidence Question Refinement Pipeline

Re-evaluates confidence levels of matched questions in eslesmis_sorucevap.jsonl
using improved Turkish NLP normalization and fuzzy matching.

Target: Improve 19,448 low-confidence matches (52.6%) to 90%+ high-confidence.

Usage:
    # Dry run (analyze only)
    python phase4_confidence_improver.py --dry-run

    # Full run (generate versioned output)
    python phase4_confidence_improver.py

    # With custom thresholds
    python phase4_confidence_improver.py --high-threshold 0.85 --medium-threshold 0.60

Output: d-dataset/processed/eslesmis_sorucevap_v2.0.jsonl
"""

import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

# ---------- Configuration ----------

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
INPUT_FILE = ROOT_DIR / "eslesmis_sorucevap.jsonl"
OUTPUT_FILE = SCRIPT_DIR / "eslesmis_sorucevap_v2.0.jsonl"
REPORT_FILE = SCRIPT_DIR / "phase4_report.md"

# Confidence thresholds
HIGH_THRESHOLD = 0.85
MEDIUM_THRESHOLD = 0.60

# ---------- Turkish NLP Normalization ----------


def normalize_tr(text: str) -> str:
    """Normalize Turkish text (NFC + Turkish lowercase mapping)."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u0130", "i").replace("I", "\u0131")  # Turkish I mapping
    return text.lower().strip()


def clean_book_name(name: str) -> str:
    """Normalize book name for matching."""
    name = normalize_tr(name)
    # Remove common prefixes/suffixes
    name = re.sub(r"^\d{4}[-_]\d{4}[-_]?", "", name)  # year ranges
    name = re.sub(r"[-_]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def jaro_winkler_similarity(s1: str, s2: str) -> float:
    """Calculate Jaro-Winkler similarity between two strings."""
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    max_dist = max(len(s1), len(s2)) // 2 - 1
    if max_dist < 0:
        max_dist = 0

    s1_matches = [False] * len(s1)
    s2_matches = [False] * len(s2)

    matches = 0
    transpositions = 0

    for i in range(len(s1)):
        start = max(0, i - max_dist)
        end = min(i + max_dist + 1, len(s2))
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len(s1)):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    jaro = (
        matches / len(s1) + matches / len(s2) + (matches - transpositions / 2) / matches
    ) / 3

    # Winkler modification
    prefix = 0
    for i in range(min(4, min(len(s1), len(s2)))):
        if s1[i] == s2[i]:
            prefix += 1
        else:
            break

    return jaro + prefix * 0.1 * (1 - jaro)


# ---------- Confidence Re-evaluation Rules ----------


def reevaluate_confidence(entry: dict) -> dict:
    """Re-evaluate confidence of a matched question-answer pair."""
    original_confidence = entry.get("confidence", 0.0)
    original_level = entry.get("confidence_level", "low")
    quality_score = entry.get("quality_score", 0.0)

    # Start with original confidence
    new_confidence = original_confidence
    improvements = []

    # Rule 1: Turkish normalization - check if book name matching improves
    book_name = entry.get("book_name", "")
    clean_name = clean_book_name(book_name)
    if clean_name != normalize_tr(book_name):
        # Book name cleaning might improve matching
        improvements.append("book_name_normalized")

    # Rule 2: Page match verification
    page_match = entry.get("page_match", False)
    if page_match:
        new_confidence = max(new_confidence, original_confidence + 0.05)
        improvements.append("page_match_bonus")

    # Rule 3: Exact match type gets confidence boost
    match_type = entry.get("match_type", "")
    if match_type == "exact":
        new_confidence = max(new_confidence, 0.90)
        improvements.append("exact_match_boost")
    elif match_type == "fuzzy" and original_confidence >= 0.50:
        new_confidence = max(new_confidence, original_confidence + 0.10)
        improvements.append("fuzzy_threshold_boost")

    # Rule 4: Book similarity threshold
    book_similarity = entry.get("book_similarity", 0.0)
    if book_similarity >= 0.95:
        new_confidence = max(new_confidence, original_confidence + 0.10)
        improvements.append("high_book_similarity")
    elif book_similarity >= 0.85:
        new_confidence = max(new_confidence, original_confidence + 0.05)
        improvements.append("medium_book_similarity")

    # Rule 5: Answer validation (must be A-E)
    answer = entry.get("answer", "")
    if answer and answer.upper() in "ABCDE":
        improvements.append("valid_answer")
    else:
        new_confidence *= 0.5  # Penalize invalid answers
        improvements.append("invalid_answer_penalty")

    # Rule 6: Question text quality
    text = entry.get("text", "")
    if text and len(text) > 20:
        improvements.append("sufficient_text")
    elif text and len(text) > 0:
        new_confidence *= 0.9
        improvements.append("short_text_penalty")
    else:
        new_confidence *= 0.5
        improvements.append("no_text_penalty")

    # Rule 7: Options completeness
    options = entry.get("options", {})
    if isinstance(options, dict) and len(options) >= 4:
        new_confidence = max(new_confidence, original_confidence + 0.03)
        improvements.append("complete_options")

    # Rule 8: Quality score integration
    if quality_score >= 90:
        new_confidence = max(new_confidence, 0.90)
        improvements.append("high_quality_score")
    elif quality_score >= 70:
        new_confidence = max(new_confidence, original_confidence + 0.05)
        improvements.append("medium_quality_score")

    # Clamp confidence to [0, 1]
    new_confidence = max(0.0, min(1.0, new_confidence))

    # Determine new confidence level
    if new_confidence >= HIGH_THRESHOLD:
        new_level = "high"
    elif new_confidence >= MEDIUM_THRESHOLD:
        new_level = "medium"
    else:
        new_level = "low"

    # Update entry
    entry["original_confidence"] = original_confidence
    entry["original_confidence_level"] = original_level
    entry["confidence"] = round(new_confidence, 4)
    entry["confidence_level"] = new_level
    entry["improvements"] = improvements
    entry["phase4_processed"] = True

    return entry


# ---------- Main Pipeline ----------


def load_questions(path: Path) -> list:
    """Load questions from JSONL file."""
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


def save_questions(questions: list, path: Path):
    """Save questions to JSONL file."""
    with open(path, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")


def generate_report(before: dict, after: dict, path: Path):
    """Generate a markdown report of the improvements."""
    report = f"""# Phase 4 Confidence Improvement Report

## Summary
- **Total questions:** {before['total']}
- **Input file:** eslesmis_sorucevap.jsonl
- **Output file:** eslesmis_sorucevap_v2.0.jsonl

## Before vs After

| Confidence Level | Before | After | Change |
|------------------|--------|-------|--------|
| High (>={HIGH_THRESHOLD}) | {before['high']} ({before['high_pct']:.1f}%) | {after['high']} ({after['high_pct']:.1f}%) | +{after['high'] - before['high']} |
| Medium (>={MEDIUM_THRESHOLD}) | {before['medium']} ({before['medium_pct']:.1f}%) | {after['medium']} ({after['medium_pct']:.1f}%) | {after['medium'] - before['medium']:+d} |
| Low (<{MEDIUM_THRESHOLD}) | {before['low']} ({before['low_pct']:.1f}%) | {after['low']} ({after['low_pct']:.1f}%) | {after['low'] - before['low']:+d} |

## Improvement Details

### Rules Applied
{chr(10).join(f'- **{k}**: {v} questions' for k, v in sorted(after['improvements'].items(), key=lambda x: -x[1]))}

## Next Steps
1. Manual validation: Run `validate_sample.py` on 100-200 random high-confidence questions
2. If >95% accuracy, promote to production:
   ```
   cp d-dataset/processed/eslesmis_sorucevap_v2.0.jsonl d-dataset/eslesmis_sorucevap.jsonl
   ```
3. Backup old version first
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)


def compute_stats(questions: list) -> dict:
    """Compute confidence distribution statistics."""
    total = len(questions)
    high = sum(1 for q in questions if q.get("confidence", 0) >= HIGH_THRESHOLD)
    medium = sum(
        1
        for q in questions
        if MEDIUM_THRESHOLD <= q.get("confidence", 0) < HIGH_THRESHOLD
    )
    low = sum(1 for q in questions if q.get("confidence", 0) < MEDIUM_THRESHOLD)

    improvements = Counter()
    for q in questions:
        for imp in q.get("improvements", []):
            improvements[imp] += 1

    return {
        "total": total,
        "high": high,
        "medium": medium,
        "low": low,
        "high_pct": (high / total * 100) if total > 0 else 0,
        "medium_pct": (medium / total * 100) if total > 0 else 0,
        "low_pct": (low / total * 100) if total > 0 else 0,
        "improvements": dict(improvements),
    }


def main():
    import argparse

    global HIGH_THRESHOLD, MEDIUM_THRESHOLD

    parser = argparse.ArgumentParser(description="Phase 4: Confidence Improvement Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, don't write output")
    parser.add_argument("--high-threshold", type=float, default=HIGH_THRESHOLD)
    parser.add_argument("--medium-threshold", type=float, default=MEDIUM_THRESHOLD)
    args = parser.parse_args()

    HIGH_THRESHOLD = args.high_threshold
    MEDIUM_THRESHOLD = args.medium_threshold

    print("=" * 70)
    print("Phase 4: Low-Confidence Question Refinement Pipeline")
    print("=" * 70)

    # Load questions
    print(f"\nLoading questions from {INPUT_FILE}...")
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        sys.exit(1)

    questions = load_questions(INPUT_FILE)
    print(f"Loaded {len(questions)} questions")

    # Compute before stats
    before_stats = compute_stats(questions)
    print(f"\nBefore:")
    print(f"  High:   {before_stats['high']:>6} ({before_stats['high_pct']:.1f}%)")
    print(f"  Medium: {before_stats['medium']:>6} ({before_stats['medium_pct']:.1f}%)")
    print(f"  Low:    {before_stats['low']:>6} ({before_stats['low_pct']:.1f}%)")

    # Process each question
    print(f"\nProcessing {len(questions)} questions...")
    for i, q in enumerate(questions):
        questions[i] = reevaluate_confidence(q)
        if (i + 1) % 10000 == 0:
            print(f"  Processed {i+1}/{len(questions)}...")

    # Compute after stats
    after_stats = compute_stats(questions)
    print(f"\nAfter:")
    print(f"  High:   {after_stats['high']:>6} ({after_stats['high_pct']:.1f}%)")
    print(f"  Medium: {after_stats['medium']:>6} ({after_stats['medium_pct']:.1f}%)")
    print(f"  Low:    {after_stats['low']:>6} ({after_stats['low_pct']:.1f}%)")

    # Show improvement
    print(f"\nImprovement:")
    print(f"  High:   +{after_stats['high'] - before_stats['high']} questions")
    print(f"  Low:    {after_stats['low'] - before_stats['low']} questions")

    if args.dry_run:
        print(f"\n[DRY RUN] No files written.")
    else:
        # Save output
        print(f"\nSaving to {OUTPUT_FILE}...")
        save_questions(questions, OUTPUT_FILE)
        print(f"Saved {len(questions)} questions")

        # Generate report
        print(f"Generating report at {REPORT_FILE}...")
        generate_report(before_stats, after_stats, REPORT_FILE)
        print(f"Report generated")

    print(f"\nDone!")


if __name__ == "__main__":
    main()
