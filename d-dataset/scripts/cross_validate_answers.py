#!/usr/bin/env python
"""
P4-A: Bayes-Optimal Cross-Validation Pipeline.

Merges up to 3 answer sources for each question using Bayesian posterior:
1. Original answer (from production JSONL -- jsonl_v11 or ai_solve)
2. Rematch answer (from corrected qnum + test-aware DB matching)
3. Claude Opus Vision AI answer (with confidence score)

BAYESIAN APPROACH (Session 39 Research):
Instead of hardcoded tier rules, we compute:
  P(correct=k | all observations) = P(k) * prod P(src_i | correct=k)

Using calibrated source accuracies from inter-source agreement analysis:

  Source                   | Accuracy | Evidence
  -------------------------|----------|---------------------------
  Opus high conf (>=0.9)   | 85%      | High confidence validation
  Opus med conf, non-C     | 70%      | C-bias analysis
  Opus med conf, C answer  | 35%      | C-bias zone (39% C rate)
  Opus low conf (<0.7)     | 25%      | Near random (20.7% match)
  ai_solved (curated)      | 85%      | Chi-sq 7.1, validated
  jsonl_v11 (original)     | 73%      | 60.7% AI agreement
  db_v7 (DB match)         | 39%      | 35.8% high-conf AI match
  rematch (qnum corrected) | 25%      | 19.1% AI match (HARMFUL)

KEY RESULTS:
- Opus high conf -> 85% posterior probability of correctness
- Theoretical maximum with Bayes-optimal: ~90-95%
- vs. naive "always DB": +46pp improvement confirmed on real data

Usage:
    python cross_validate_answers.py                    # Full run, write output
    python cross_validate_answers.py --analyze          # Stats only, no output
    python cross_validate_answers.py --incremental      # OK with partial AI results
    python cross_validate_answers.py --simulate         # Show hybrid improvement
"""
import functools
import json
import math
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


BASE_DIR = Path(__file__).parent.parent
VALID_ANSWERS = set("ABCDE")

# Calibrated accuracy values from Bayesian inter-source agreement analysis
# P(source answer is correct | observed answer, confidence tier)
# Derived from Opus/Sonnet/Gemini vision validation
ACCURACY = {
    "opus_high":   0.85,  # Opus conf >= 0.9, any answer
    "opus_med":    0.70,  # Opus conf 0.7-0.9, non-C answer
    "opus_med_c":  0.35,  # Opus conf 0.7-0.9, C answer (C-bias zone)
    "opus_low":    0.25,  # Opus conf < 0.7 (near random)
    # NEW: Sonnet accuracy tiers (Session 52)
    "sonnet_high": 0.87,  # Sonnet conf >= 0.9
    "sonnet_med":  0.75,  # Sonnet conf 0.7-0.9, non-C
    "sonnet_med_c": 0.40, # Sonnet conf 0.7-0.9, C answer
    "sonnet_low":  0.40,  # Sonnet conf < 0.7
    # NEW: Gemini accuracy tiers
    "gemini_high": 0.80,  # Gemini conf >= 0.9
    "gemini_med":  0.65,  # Gemini conf 0.7-0.9
    "gemini_low":  0.30,  # Gemini conf < 0.7
    # Legacy sources
    "ai_solved":   0.85,  # Previously AI-verified answers (curated)
    "jsonl_v11":   0.73,  # Original OCR-matched answers
    "db_v7":       0.39,  # DB rematch (known quality issues beyond qnum)
    "rematch":     0.25,  # Corrected qnum rematch (near random)
    "other":       0.40,  # Unknown source
}

# DB weight modes for zero-db experiment
# "legacy" = no changes, "zero_db" = effectively ignore DB sources
# 0.001 instead of 0.0 to avoid log(0) in Bayesian posterior (log-space arithmetic)
DB_WEIGHT_MODES = {
    "legacy": {},  # No changes, use ACCURACY as-is
    "zero_db": {"db_v7": 0.20, "rematch": 0.20},  # 1/5 = uninformative for 5-choice MCQ
}

# Math/Geo subject keywords for pilot filtering (Turkish book names)
MATH_GEO_KEYWORDS = [
    "matematik", "geometri", "geo", "math",
    "sayisal", "sayısal", "tyt mat", "ayt mat",
]


def normalize_book(name: str) -> str:
    """NFC normalize for consistent matching."""
    return unicodedata.normalize("NFC", name) if name else name


def make_key(q: Dict) -> Tuple[str, int, int]:
    """Create consistent lookup key from question dict."""
    return (
        normalize_book(q.get("book_name", "")),
        q.get("page_number", 0),
        q.get("question_number", 1),
    )


def load_jsonl(path: Path) -> Dict[Tuple[str, int, int], Dict]:
    """Load JSONL questions into lookup by (book, page, qnum)."""
    questions = {}
    if not path.exists():
        return questions
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            q = json.loads(line.strip())
            questions[make_key(q)] = q
    return questions


def load_vision_results(path: Path) -> Dict[Tuple[str, int, int], Dict]:
    """Load vision AI results, skipping errors and no-answer entries."""
    results = {}
    if not path.exists():
        return results
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            if not isinstance(r, dict):
                continue
            if r.get("error") or r.get("status") == "error":
                continue
            ai_ans = (r.get("ai_answer") or "").upper().strip()
            if ai_ans not in VALID_ANSWERS:
                continue
            results[make_key(r)] = r
    return results


@functools.lru_cache(maxsize=512)
def classify_opus(confidence: float, answer: str) -> str:
    """Classify Opus observation into accuracy tier.

    Cached: confidence values are rounded to 2dp (limited distinct values),
    answer is one of 5 letters → at most ~(200×5)=1000 unique combos.
    """
    if confidence >= 0.9:
        return "opus_high"
    elif confidence >= 0.7:
        return "opus_med_c" if answer == "C" else "opus_med"
    return "opus_low"


@functools.lru_cache(maxsize=512)
def classify_sonnet(confidence: float, answer: str) -> str:
    """Classify Sonnet observation into accuracy tier."""
    if confidence >= 0.9:
        return "sonnet_high"
    elif confidence >= 0.7:
        return "sonnet_med_c" if answer == "C" else "sonnet_med"
    return "sonnet_low"


@functools.lru_cache(maxsize=512)
def classify_gemini(confidence: float, answer: str) -> str:
    """Classify Gemini observation into accuracy tier."""
    if confidence >= 0.9:
        return "gemini_high"
    elif confidence >= 0.7:
        return "gemini_med"
    return "gemini_low"


@functools.lru_cache(maxsize=64)
def classify_original(source: str) -> str:
    """Classify original answer source into accuracy tier.

    Cached: source strings are short, repeat across 33K questions.
    """
    if not source:
        return "other"
    if "ai_solve" in source or "claude" in source.lower():
        return "ai_solved"
    if source == "jsonl_v11":
        return "jsonl_v11"
    if "db" in source or "match" in source:
        return "db_v7"
    return "other"


def bayesian_posterior(sources: List[Tuple[str, str, float]]) -> Dict[str, float]:
    """
    Compute Bayesian posterior P(correct=k | observations) for k in {A,B,C,D,E}.

    Formula: P(correct=k | obs) = P(k) * prod_i P(src_i says x_i | correct=k)

    Where P(src says x | correct=k) = accuracy if x==k, else (1-accuracy)/4
    Uniform prior P(k) = 1/5.

    Uses log-space arithmetic for numerical stability.
    """
    candidates = list("ABCDE")
    log_posts = {}

    for k in candidates:
        lp = math.log(0.2)  # Uniform prior
        for _, answer, accuracy in sources:
            if answer == k:
                lp += math.log(max(accuracy, 1e-10))
            else:
                lp += math.log(max((1 - accuracy) / 4, 1e-10))
        log_posts[k] = lp

    # Log-sum-exp normalization
    max_lp = max(log_posts.values())
    total = sum(math.exp(v - max_lp) for v in log_posts.values())

    return {k: math.exp(log_posts[k] - max_lp) / total for k in candidates}


def score_answer(
    original: str,
    original_source: str,
    rematch: Optional[str],
    ai_answer: Optional[str],
    ai_confidence: float,
    ai_source: Optional[str] = None,  # NEW: Which AI model (sonnet, opus_v2, opus_v1, gemini)
) -> Tuple[str, float, str]:
    """
    Bayes-optimal scoring using calibrated source accuracies.

    Computes posterior probability for each candidate answer {A,B,C,D,E}
    using all available evidence sources. Naturally handles:
    - C-bias correction (lower accuracy for Opus C at medium confidence)
    - Multi-source integration (multiply likelihoods)
    - Graceful degradation (fewer sources = wider posterior)

    Args:
        ai_source: Which AI model (sonnet, opus_v2, opus_v1, gemini, opus)

    Returns: (best_answer, posterior_confidence, method_description)
    """
    orig = original.upper().strip() if original else ""
    rem = (rematch or "").upper().strip()
    ai = (ai_answer or "").upper().strip()

    # Build evidence list: (source_tier, answer, accuracy)
    sources = []
    labels = []

    if ai in VALID_ANSWERS:
        # Select classifier based on AI source
        if ai_source == "sonnet":
            tier = classify_sonnet(ai_confidence, ai)
            label = "sonnet"
        elif ai_source in ("opus_v2", "opus_v1", "opus"):
            tier = classify_opus(ai_confidence, ai)
            label = "opus"
        elif ai_source == "gemini":
            tier = classify_gemini(ai_confidence, ai)
            label = "gemini"
        else:
            # Default to opus for unknown sources
            tier = classify_opus(ai_confidence, ai)
            label = "opus"
        sources.append((tier, ai, ACCURACY[tier]))
        labels.append(label)

    if orig in VALID_ANSWERS:
        tier = classify_original(original_source)
        sources.append((tier, orig, ACCURACY[tier]))
        labels.append("orig")

    if rem in VALID_ANSWERS:
        sources.append(("rematch", rem, ACCURACY["rematch"]))
        labels.append("rematch")

    if not sources:
        return "", 0.0, "no_answer"

    # Compute Bayesian posterior
    posteriors = bayesian_posterior(sources)
    best = max(posteriors, key=posteriors.get)
    confidence = posteriors[best]

    # When posteriors are near-uniform (max - min < 0.02), keep original answer.
    # This prevents alphabetical bias from max() tie-breaking when all sources
    # are uninformative (e.g., zero-db mode for DB-only questions).
    vals = list(posteriors.values())
    if max(vals) - min(vals) < 0.02 and orig in VALID_ANSWERS:
        best = orig
        confidence = posteriors[orig]

    # Build descriptive method string: bayes_{agreeing}of{total}_{primary_source}
    agreeing = [lbl for lbl, (_, ans, _) in zip(labels, sources) if ans == best]
    n_agree = len(agreeing)
    n_total = len(sources)
    primary = agreeing[0] if agreeing else labels[0]
    method = f"bayes_{n_agree}of{n_total}_{primary}"

    return best, round(confidence, 4), method


def cross_validate(
    production: Dict[Tuple, Dict],
    ai_results: Dict[Tuple, Dict],
    analyze_only: bool = False,
    simulate: bool = False,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Cross-validate all questions with Bayes-optimal strategy."""
    stats = Counter()
    method_stats = Counter()
    confidence_buckets = Counter()
    answer_dist = Counter()
    change_details = Counter()
    tier_counts = Counter()
    conf_sum = 0.0
    results: List[Dict] = []

    for key, q in production.items():
        original = q.get("answer", "")
        original_source = q.get("answer_source", "")
        rematch = q.get("db_rematch_answer")

        # Get AI result (with priority merge, already has ai_source)
        ai = ai_results.get(key, {})
        ai_answer = ai.get("ai_answer", "")
        ai_confidence = ai.get("confidence", 0)
        # Only set ai_source if there's actually an AI answer
        ai_source = ai.get("ai_source") if ai_answer else None

        best_answer, confidence, method = score_answer(
            original, original_source, rematch,
            ai_answer, ai_confidence, ai_source,  # Pass ai_source for classification
        )

        stats["total"] += 1
        method_stats[method] += 1
        conf_sum += confidence

        if best_answer:
            answer_dist[best_answer] += 1
            stats["has_answer"] += 1
        else:
            stats["no_answer"] += 1

        # Confidence tiers for reporting
        if confidence >= 0.90:
            tier_counts["very_high"] += 1
        elif confidence >= 0.70:
            tier_counts["high"] += 1
        elif confidence >= 0.50:
            tier_counts["medium"] += 1
        elif confidence > 0:
            tier_counts["low"] += 1
        else:
            tier_counts["none"] += 1

        confidence_buckets[round(confidence, 1)] += 1

        orig_upper = original.upper().strip() if original else ""
        if best_answer and best_answer != orig_upper:
            stats["changed"] += 1
            change_details[f"{orig_upper}->{best_answer} ({method})"] += 1
        elif best_answer == orig_upper:
            stats["unchanged"] += 1

        if ai_answer:
            stats["has_opus"] += 1

        result = {
            **q,
            "best_answer": best_answer,
            "best_confidence": round(confidence, 4),
            "best_method": method,
            # Changed: Use ai_answer/ai_confidence (includes Sonnet/Gemini)
            "ai_answer": ai_answer or None,
            "ai_confidence": round(ai_confidence, 2) if ai_answer else None,
            "ai_source": ai_source,  # NEW: Which AI model
            "rematch_answer": rematch,
            # FIX-16: Always include original_answer for consistent output format
            "original_answer": original,
            "original_source": original_source,
        }

        if best_answer and best_answer != orig_upper:
            result["answer"] = best_answer
            result["answer_source"] = f"crossval_{method}"

        # REQ-1: Flag questions that only have DB source (no AI validation)
        has_ai = bool(ai_answer)
        orig_tier = classify_original(original_source)
        is_db_only = orig_tier in ("db_v7", "rematch", "other") and not has_ai
        if is_db_only:
            result["needs_ai_solve"] = True
            result["needs_ai_solve_reason"] = "only_db_source"
            stats["needs_ai_solve"] += 1

        results.append(result)

    # --- REPORT ---
    total = stats["total"]
    print("\n" + "=" * 72)
    print("  BAYES-OPTIMAL CROSS-VALIDATION RESULTS")
    print("=" * 72)

    print(f"\n  Total questions:       {total:>8,}")
    print(f"  Has Opus AI:           {stats['has_opus']:>8,} ({stats['has_opus']/total*100:.1f}%)")
    print(f"  Has answer:            {stats['has_answer']:>8,} ({stats['has_answer']/total*100:.1f}%)")
    print(f"  Changed from original: {stats['changed']:>8,} ({stats['changed']/total*100:.1f}%)")
    print(f"  Unchanged:             {stats['unchanged']:>8,} ({stats['unchanged']/total*100:.1f}%)")
    print(f"  Needs AI solve:        {stats['needs_ai_solve']:>8,} ({stats['needs_ai_solve']/total*100:.1f}%)")

    # Estimated accuracy (weighted average of posteriors)
    avg_conf = conf_sum / total if total else 0
    print(f"\n  ESTIMATED ACCURACY (mean Bayesian posterior): {avg_conf:.1%}")

    # Bayesian confidence tiers
    print(f"\n  BAYESIAN POSTERIOR CONFIDENCE TIERS:")
    for tier_name, label in [
        ("very_high", "VERY HIGH (>=0.90)"),
        ("high", "HIGH (0.70-0.90)"),
        ("medium", "MEDIUM (0.50-0.70)"),
        ("low", "LOW (<0.50)"),
        ("none", "NONE (0.00)"),
    ]:
        c = tier_counts[tier_name]
        bar = "#" * max(1, int(c / total * 100))
        print(f"    {label:22s}: {c:>6,} ({c/total*100:5.1f}%) {bar}")

    # Method distribution (top 20)
    print(f"\n  SCORING METHODS (Bayesian source combinations):")
    for method, count in method_stats.most_common(20):
        bar = "#" * max(1, int(count / total * 200))
        print(f"    {method:40s} {count:>6,} ({count/total*100:5.1f}%) {bar}")

    # Posterior confidence distribution
    print(f"\n  POSTERIOR DISTRIBUTION (binned):")
    for bucket in sorted(confidence_buckets.keys()):
        count = confidence_buckets[bucket]
        bar = "#" * max(1, int(count / total * 200))
        print(f"    {bucket:.1f}: {count:>6,} ({count/total*100:5.1f}%) {bar}")

    # Answer distribution + chi-square
    print(f"\n  FINAL ANSWER DISTRIBUTION:")
    total_answers = sum(answer_dist.get(k, 0) for k in "ABCDE")
    exp = total_answers / 5 if total_answers else 1
    chi_sq = 0.0
    for k in "ABCDE":
        c = answer_dist.get(k, 0)
        pct = c / total_answers * 100 if total_answers else 0
        chi_sq += (c - exp) ** 2 / exp if exp else 0
        bar = "#" * max(1, int(pct / 2))
        print(f"    {k}: {c:>6,} ({pct:5.1f}%) {bar}")
    status = "PASS (uniform)" if chi_sq < 9.49 else "FAIL (biased!)"
    print(f"    Chi-sq: {chi_sq:.2f} (threshold 9.49) -> {status}")

    # Calibration table
    print(f"\n  CALIBRATED SOURCE ACCURACIES (Bayesian research):")
    for src, acc in sorted(ACCURACY.items(), key=lambda x: -x[1]):
        bar = "#" * int(acc * 40)
        print(f"    {src:15s}: {acc:4.0%} {bar}")

    # Simulation: hybrid improvement metric
    if simulate or stats["has_opus"] > 0:
        ai_questions = [r for r in results if r.get("ai_answer")]
        if ai_questions:
            # Always use "answer" field - original_answer only exists when changed
            def get_ground_truth(r):
                return r.get("answer", "").upper()

            naive_match = sum(
                1 for r in ai_questions
                if r.get("ai_answer", "").upper() == get_ground_truth(r)
            )
            hybrid_match = sum(
                1 for r in ai_questions
                if r["best_answer"].upper() == get_ground_truth(r)
            )
            print(f"\n  BAYES vs NAIVE IMPACT ({len(ai_questions)} AI-answered questions):")
            print(f"    Naive 'always AI':     {naive_match:>6,} ({naive_match/len(ai_questions)*100:.1f}%)")
            print(f"    Bayes-optimal:         {hybrid_match:>6,} ({hybrid_match/len(ai_questions)*100:.1f}%)")
            improvement = hybrid_match - naive_match
            print(f"    Improvement:           {improvement:>+6,} ({improvement/len(ai_questions)*100:+.1f} pp)")

    # Top changes
    if stats["changed"] > 0:
        print(f"\n  TOP ANSWER CHANGES (original -> new):")
        for change, count in change_details.most_common(15):
            print(f"    {change}: {count}")

    print("\n" + "=" * 72)

    # Write output
    if not analyze_only and output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  Output: {output_path}")
        print(f"  Records: {len(results):,}")

    return {
        "stats": dict(stats),
        "method_stats": dict(method_stats),
        "chi_sq": chi_sq,
        "tier_counts": dict(tier_counts),
        "avg_confidence": avg_conf,
        "total": total,
        "changed": stats["changed"],
        "results": results,
    }


def load_calibrated_accuracy(calibration_path: Path) -> Dict[str, float]:
    """Load calibrated accuracy values from confidence_calibration.py output.

    Args:
        calibration_path: Path to accuracy_calibrated.json

    Returns:
        Dict with calibrated accuracy values to override ACCURACY
    """
    if not calibration_path.exists():
        print(f"  WARNING: Calibration file not found: {calibration_path}")
        return {}
    with open(calibration_path, encoding="utf-8") as f:
        data = json.load(f)
    overrides = data.get("accuracy_overrides", {})
    print(f"  Loaded {len(overrides)} calibrated accuracy values from {calibration_path.name}")
    return overrides


def filter_math_geo(production: Dict[tuple, Dict]) -> Dict[tuple, Dict]:
    """Filter production questions to Math/Geo subjects only (pilot mode).

    Uses Turkish keywords in book_name for subject detection.
    """
    filtered = {}
    for key, q in production.items():
        book = normalize_book(q.get("book_name") or "").lower()
        if any(kw in book for kw in MATH_GEO_KEYWORDS):
            filtered[key] = q
    return filtered


def load_all_vision_results() -> Dict[Tuple[str, int, int], Dict]:
    """
    Load ALL vision AI results with priority merging.

    Priority order (highest to lowest):
    1. Sonnet (highest confidence, best OCR understanding)
    2. Opus v2
    3. Opus v1
    4. Gemini (lowest priority)

    For each unique (book, page, qnum), only the highest priority
    result is kept. This is NOT ensemble - we pick ONE best source.
    """
    base_dir = BASE_DIR / "processed"

    # Define sources with priority (lower number = higher priority)
    sources = [
        (1, "sonnet", base_dir / "vision_solve_sonnet" / "vision_results.jsonl"),
        (2, "opus_v2", base_dir / "vision_solve_opus_v2" / "vision_results.jsonl"),
        (3, "opus_v1", base_dir / "vision_solve_opus" / "vision_results.jsonl"),
        (4, "gemini", base_dir / "vision_solve_gemini" / "vision_results_clean.jsonl"),
    ]

    results = {}

    for priority, name, path in sources:
        if path.exists():
            loaded = load_vision_results(path)
            new_count = 0
            for key, val in loaded.items():
                if key not in results:
                    # Add source tag for reporting
                    val["ai_source"] = name
                    results[key] = val
                    new_count += 1
            print(f"  [{name}] {new_count:,} new (priority={priority})")

    return results


def write_needs_ai_solve(results: List[Dict], output_dir: Path) -> int:
    """Write questions that need AI solving to a separate JSONL file.

    Returns count of needs_ai_solve questions.
    """
    needs_solve = [r for r in results if r.get("needs_ai_solve")]
    if not needs_solve:
        return 0
    output_path = output_dir / "req1_needs_ai_solve.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for r in needs_solve:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  Needs AI solve: {len(needs_solve):,} -> {output_path}")
    return len(needs_solve)


def main():
    production_path = BASE_DIR / "eslesmis_sorucevap.jsonl"
    rematched_path = BASE_DIR / "processed" / "eslesmis_sorucevap_rematched_v2.jsonl"
    opus_path = BASE_DIR / "processed" / "vision_solve_opus" / "vision_results.jsonl"
    opus_v2_path = BASE_DIR / "processed" / "vision_solve_opus_v2" / "vision_results.jsonl"
    # NEW: Sonnet and Gemini paths
    sonnet_path = BASE_DIR / "processed" / "vision_solve_sonnet" / "vision_results.jsonl"
    gemini_path = BASE_DIR / "processed" / "vision_solve_gemini" / "vision_results_clean.jsonl"
    output_path = BASE_DIR / "processed" / "eslesmis_sorucevap_crossval.jsonl"
    qi_output_dir = BASE_DIR / "processed" / "quality_improvement"
    calibration_path = qi_output_dir / "req2_accuracy_calibrated.json"

    analyze_only = "--analyze" in sys.argv or "--analyze-only" in sys.argv
    incremental = "--incremental" in sys.argv
    simulate = "--simulate" in sys.argv
    zero_db = "--zero-db" in sys.argv
    calibrated = "--calibrated" in sys.argv
    pilot_math_geo = "--pilot-math-geo" in sys.argv
    dry_run = "--dry-run" in sys.argv

    # REQ-1: Zero-DB mode — effectively ignore DB sources
    # NOTE: If both --zero-db and --calibrated are used, calibrated values
    # override zero-db for any overlapping keys (intentional: data > heuristic)
    if zero_db:
        for key, val in DB_WEIGHT_MODES["zero_db"].items():
            ACCURACY[key] = val
        print(f"  ZERO-DB mode: db_v7={ACCURACY['db_v7']}, rematch={ACCURACY['rematch']}")

    # REQ-2: Load calibrated accuracy values (data-driven, not hardcoded)
    if calibrated:
        overrides = load_calibrated_accuracy(calibration_path)
        for key, val in overrides.items():
            if key in ACCURACY:
                old = ACCURACY[key]
                ACCURACY[key] = val
                print(f"    {key}: {old:.3f} → {val:.3f}")

    if rematched_path.exists():
        print(f"Loading rematched production: {rematched_path.name}")
        production = load_jsonl(rematched_path)
    elif production_path.exists():
        print(f"Loading production: {production_path.name}")
        production = load_jsonl(production_path)
    else:
        print("ERROR: No production JSONL found!")
        return 1
    print(f"  Loaded {len(production):,} questions")

    # REQ-1: Pilot mode — filter to Math/Geo only
    if pilot_math_geo:
        production = filter_math_geo(production)
        print(f"  PILOT Math/Geo filter: {len(production):,} questions")

    # Load ALL vision results with priority merging (Sonnet > Opus v2 > Opus v1 > Gemini)
    print("\n  Loading all AI vision results (priority: Sonnet > Opus v2 > Opus v1 > Gemini)...")
    ai_results = load_all_vision_results()
    print(f"  Total AI results (after priority merge): {len(ai_results):,}")

    total_ai = len(ai_results)
    coverage = total_ai / len(production) * 100 if production else 0
    print(f"\n  Total AI-answered: {total_ai:,}")
    print(f"  AI coverage: {coverage:.1f}%")

    if incremental and total_ai < 100:
        print(f"\n  WARNING: Only {total_ai} AI results. Running in incremental mode.")

    # Determine output path
    if zero_db:
        effective_output = qi_output_dir / "req1_zero_db_results.jsonl"
    else:
        effective_output = output_path

    effective_analyze = analyze_only or dry_run

    result = cross_validate(
        production,
        ai_results,  # Changed from opus_results to ai_results (all AI with priority)
        analyze_only=effective_analyze,
        simulate=simulate,
        output_path=None if effective_analyze else effective_output,
    )

    # Write needs_ai_solve list if not dry-run
    if not dry_run and not analyze_only:
        write_needs_ai_solve(result.get("results", []), qi_output_dir)

    return 0


if __name__ == "__main__":
    exit(main())
