#!/usr/bin/env python
"""
P4-A: Bayes-Optimal Cross-Validation Pipeline.

Merges up to 7 AI answer sources per question using Bayesian posterior:
1. opus_v2    - Claude Opus vision solve (high accuracy, 0.18/s)
2. sonnet     - Claude Sonnet vision solve (fast, lower accuracy)
3. gemini     - Gemini 2.5 Flash vision solve (free tier)
4. gemini_mg  - Gemini math/geo specific solve
5. qwen_text  - Qwen3 text-based solve (high throughput)
6. qwen_vision - Qwen3 vision solve (grouped screenshots)
7. qwen_crop  - Qwen3.5 crop-based solve (DashScope API)

Plus original sources from production JSONL (jsonl_v11, ai_solved, db_v7, rematch).

BAYESIAN APPROACH (Session 39-40 Research):
  P(correct=k | all observations) = P(k) * prod P(src_i | correct=k)

Using calibrated source accuracies:

  Source                   | Accuracy | Evidence
  -------------------------|----------|---------------------------
  Opus high conf (>=0.9)   | 85%      | High confidence validation
  Opus med conf, non-C     | 70%      | C-bias analysis
  Opus med conf, C answer  | 35%      | C-bias zone (39% C rate)
  Opus low conf (<0.7)     | 25%      | Near random
  Sonnet high (>=0.9)      | 80%      | Slightly below Opus
  Sonnet med (0.7-0.9)     | 60%      | C-bias not separated
  Sonnet low (<0.7)        | 25%      | Near random
  Gemini high (>=0.8)      | 77%      | Free tier, good coverage
  Gemini med (0.5-0.8)     | 55%      | Moderate confidence
  Gemini low (<0.5)        | 25%      | Near random
  ai_solved (curated)      | 85%      | Chi-sq 7.1, validated
  jsonl_v11 (original)     | 73%      | 60.7% AI agreement
  db_v7 (DB match)         | 39%      | 35.8% high-conf AI match
  rematch (qnum corrected) | 25%      | 19.1% AI match (HARMFUL)
  tier1_5 (low quality)    | 17.2%   | Below random (20%)

KEY RESULTS:
- Opus high conf -> 85% posterior probability of correctness
- Theoretical maximum with Bayes-optimal: ~90-95%
- vs. naive "always DB": +46pp improvement confirmed on real data

Usage:
    python cross_validate_answers.py                    # Full run, write output
    python cross_validate_answers.py --analyze          # Stats only, no output
    python cross_validate_answers.py --incremental      # OK with partial AI results
    python cross_validate_answers.py --simulate         # Show hybrid improvement
    python cross_validate_answers.py --zero-db          # Set db_v7 accuracy to 0
    python cross_validate_answers.py --calibrated       # Use calibrated accuracies
    python cross_validate_answers.py --pilot-math-geo   # Filter to math/geo only
    python cross_validate_answers.py --input FILE       # Custom input JSONL
    python cross_validate_answers.py --output FILE      # Custom output JSONL
    python cross_validate_answers.py --dry-run          # Analyze without writing
"""
import functools
import json
import math
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Fast JSON I/O: 2-3x speedup with orjson, stdlib fallback
# Turkish normalize: proper I/ı mapping for case-insensitive comparison
try:
    from script_common import fast_json_loads, fast_json_dump_str, normalize_tr as _normalize_tr
except ImportError:
    fast_json_loads = json.loads
    fast_json_dump_str = lambda obj: json.dumps(obj, ensure_ascii=False)  # noqa: E731
    _normalize_tr = None


BASE_DIR = Path(__file__).parent.parent
VALID_ANSWERS = set("ABCDE")

# Page penalty floor: when AI sees a full page with multiple questions,
# accuracy is divided by page_q_count. Without a floor, page_q_count=5
# gives accuracy=0.17 (below random=0.20), making the source harmful.
_PAGE_PENALTY_FLOOR = 0.21

# Valid MCQ candidate answers (tuple for immutability + iteration)
CANDIDATES = ("A", "B", "C", "D", "E")

# Tiers considered unreliable for standalone use — questions with only these sources
# get flagged as needs_ai_solve. See L3 in optimization plan.
_UNRELIABLE_TIERS = frozenset({"db_v7", "rematch", "other", "tier1_5"})

# When posteriors are near-uniform (max - min < threshold), keep original answer.
# Prevents alphabetical bias from max() tie-breaking when all sources are uninformative.
_TIE_BREAK_THRESHOLD = 0.02

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
    # Contaminated tiers (measured via pilot — BELOW random baseline)
    "tier1_5":     0.172, # page_inline_unique: 17.2% pilot accuracy (< 20% random)
    "tier1":       0.85,  # page_inline exact: reliable (placeholder until human GT)
    "tier5_qindex": 0.60, # question_index fallback to page_inline (YOLO order, less reliable)
    # Qwen text-solve — group-aware accuracy weights (Step 1 pilot calibration)
    "qwen_text_rich_high":      0.85,  # G1 TEXT_RICH, conf >= 0.8
    "qwen_text_rich_med":       0.65,  # G1 TEXT_RICH, conf 0.4-0.8
    "qwen_text_medium_high":    0.75,  # G2 TEXT_MEDIUM, conf >= 0.8
    "qwen_text_medium_med":     0.50,  # G2 TEXT_MEDIUM, conf 0.4-0.8
    "qwen_text_deneme_high":    0.80,  # G3 DENEME_TEXT, conf >= 0.8
    "qwen_text_deneme_med":     0.60,  # G3 DENEME_TEXT, conf 0.4-0.8
    "qwen_text_geo_high":       0.30,  # G4 GEO_FIGURE — text nearly useless
    "qwen_text_other_fig_high": 0.55,  # G5 OTHER_FIGURE — physics/chem text sometimes ok
    "qwen_text_short_high":     0.25,  # G6 SHORT — minimal text
    "qwen_text_low":            0.20,  # Any group, conf < 0.4
    # Qwen vision-solve — text-anchored (Step 4)
    "qwen_vision_high":  0.80,  # conf >= 0.8
    "qwen_vision_med":   0.60,  # conf 0.5-0.8
    "qwen_vision_low":   0.30,  # conf < 0.5
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
    dup_count = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            q = fast_json_loads(stripped)
            key = make_key(q)
            if key in questions:
                dup_count += 1
            questions[key] = q
    if dup_count > 0:
        print(f"  WARNING: {dup_count} duplicate keys in {path.name} (last entry kept)")
    return questions


def load_vision_results(path: Path) -> Dict[Tuple[str, int, int], Dict]:
    """Load vision AI results, skipping errors and no-answer entries."""
    results = {}
    if not path.exists():
        return results
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                r = fast_json_loads(stripped)
            except (json.JSONDecodeError, ValueError):
                continue
            if not isinstance(r, dict):
                continue
            if r.get("error") or r.get("status") == "error":
                continue
            ai_ans = (r.get("ai_answer") or r.get("answer") or "").upper().strip()
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
    """Classify Gemini observation into accuracy tier.

    Note: `answer` parameter is accepted for API consistency with classify_opus/classify_sonnet
    (which use it for C-bias detection) but is not used here — Gemini does not exhibit C-bias.
    """
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
    # v3 match tiers from match_crop_answers.py output
    # answer_source stores DB source ("page_inline", "page_inline_unique")
    # match_tier stores tier name ("tier1_page_inline", "tier1b_position_page_inline", etc.)
    # Handle BOTH fields since cross_validate may receive either format.
    # IMPORTANT: tier5 q_index matches are LESS reliable (~0.60) than exact matches (0.85).
    # When caller passes match_tier, we can distinguish; when only answer_source="page_inline"
    # is available, all page_inline records get tier1 (acceptable fallback).
    if "tier5" in source or "qindex" in source:
        return "tier5_qindex"  # q_index fallback, less reliable than exact match
    if "page_inline_unique" in source or "tier1_5" in source:
        return "tier1_5"  # 17.2% pilot accuracy — BELOW random baseline
    # Guard: "tier1" must be a prefix, not a substring — prevents false matches
    # from hypothetical sources like "sometier1x". Existing "tier1_page_inline" and
    # "tier1b_position_page_inline" both start with "tier1".
    if "page_inline" in source or source.startswith("tier1"):
        return "tier1"  # page_inline exact + position (tier1, tier1b): reliable
    if "db" in source or "match" in source:
        return "db_v7"
    return "other"


@functools.lru_cache(maxsize=256)
def classify_qwen_text(confidence: float, solve_group: str) -> str:
    """Classify Qwen text-solve observation into accuracy tier.

    Group-aware: geometry text is nearly useless (0.30),
    rich text with high confidence is strong (0.85).
    """
    if confidence < 0.4:
        return "qwen_text_low"
    if solve_group == "GEO_FIGURE":
        return "qwen_text_geo_high"
    if solve_group == "OTHER_FIGURE":
        return "qwen_text_other_fig_high"
    if solve_group == "SHORT":
        return "qwen_text_short_high"
    if confidence >= 0.8:
        if solve_group == "DENEME_TEXT":
            return "qwen_text_deneme_high"
        if solve_group == "TEXT_RICH":
            return "qwen_text_rich_high"
        return "qwen_text_medium_high"
    # Medium confidence (0.4-0.8)
    if solve_group == "DENEME_TEXT":
        return "qwen_text_deneme_med"
    if solve_group == "TEXT_RICH":
        return "qwen_text_rich_med"
    return "qwen_text_medium_med"


@functools.lru_cache(maxsize=128)
def classify_qwen_vision(confidence: float) -> str:
    """Classify Qwen vision-solve observation into accuracy tier."""
    if confidence >= 0.8:
        return "qwen_vision_high"
    if confidence >= 0.5:
        return "qwen_vision_med"
    return "qwen_vision_low"


# Source → classifier dispatcher (replaces if/elif chain in score_answer)
# Key: source name from AI observation. Value: callable(conf, answer) → tier string.
_SOURCE_CLASSIFIERS = {
    "sonnet": lambda c, a: classify_sonnet(c, a),
    "opus_v2": lambda c, a: classify_opus(c, a),
    "opus_v1": lambda c, a: classify_opus(c, a),
    "opus": lambda c, a: classify_opus(c, a),
    "gemini": lambda c, a: classify_gemini(c, a),
    "gemini_mg": lambda c, a: classify_gemini(c, a),
    "qwen_vision": lambda c, _: classify_qwen_vision(c),
    "qwen_crop": lambda c, _: classify_qwen_vision(c),
}

# Source → label mapping for method description string
_SOURCE_LABELS = {
    "sonnet": "sonnet",
    "opus_v2": "opus", "opus_v1": "opus", "opus": "opus",
    "gemini": "gemini", "gemini_mg": "gemini",
    "qwen_vision": "qwen_vision", "qwen_crop": "qwen_crop",
}


# Observed answer bias from pipeline v3 output (eslesmis_sorucevap_v3.jsonl, March 2026)
# Measured from 61,190 matched questions (Tier 1 + 1B + 1.5). Chi-sq 1526.42, A=26.3%.
# Used to construct anti-bias prior: P(k) proportional to 1/GT_BIAS[k]
# This compensates for systematic over-representation of certain answers
# in the answer key extraction process.
GT_BIAS: Dict[str, float] = {
    "A": 0.263,
    "B": 0.127,
    "C": 0.191,
    "D": 0.175,
    "E": 0.244,
}

# Anti-bias prior: inversely proportional to sqrt(observed bias), normalized to sum=1.
# Full inverse (1/bias) is too aggressive — B=12.7% gets 2x the prior of A=26.3%,
# causing B to dominate at 54%. sqrt dampening keeps correction proportional
# without over-compensating: B prior = 1.44x A prior (vs 2.07x with full inverse).
# Rationale from Session 40 Bayesian Research: sqrt is the geometric mean between
# uniform (no correction) and full inverse (max correction).
_inv = {k: 1.0 / math.sqrt(v) for k, v in GT_BIAS.items()}
_inv_sum = sum(_inv.values())
ANTI_BIAS_PRIOR: Dict[str, float] = {k: v / _inv_sum for k, v in _inv.items()}


def bayesian_posterior(
    sources: List[Tuple[str, str, float]],
    use_anti_bias: bool = True,
) -> Dict[str, float]:
    """
    Compute Bayesian posterior P(correct=k | observations) for k in {A,B,C,D,E}.

    Formula: P(correct=k | obs) = P(k) * prod_i P(src_i says x_i | correct=k)

    Where P(src says x | correct=k) = accuracy if x==k, else (1-accuracy)/4

    Prior P(k):
      - use_anti_bias=True (default): Inversely proportional to sqrt(observed GT bias).
        Compensates for A=26.3% systematic over-representation.
        ONLY applied when at least 2 sources agree (evidence-supported correction).
        When 0 sources agree, uniform prior prevents prior-only B-dominance.
      - use_anti_bias=False: Uniform P(k) = 1/5.

    Uses log-space arithmetic for numerical stability.
    """
    # Check if any answer has 2+ strong sources agreeing (evidence-supported)
    # If no strong agreement, anti-bias prior would dominate → use uniform instead
    # Only count sources with accuracy >= 0.50 (opus_high, sonnet_high, ai_solved, jsonl_v11, etc.)
    # Weak sources (rematch=0.25, db_v7=0.39) should not trigger bias correction
    if use_anti_bias and sources:
        strong_counts: Dict[str, int] = {}
        for _, answer, acc in sources:
            if acc >= 0.50:
                strong_counts[answer] = strong_counts.get(answer, 0) + 1
        has_strong_agreement = any(c >= 2 for c in strong_counts.values())
        effective_anti_bias = has_strong_agreement
    else:
        # No sources or anti-bias disabled → uniform prior (no correction without evidence)
        effective_anti_bias = False

    log_posts = {}

    for k in CANDIDATES:
        prior = ANTI_BIAS_PRIOR[k] if effective_anti_bias else 0.2
        lp = math.log(prior)
        for _, answer, accuracy in sources:
            if answer == k:
                lp += math.log(max(accuracy, 1e-10))
            else:
                lp += math.log(max((1 - accuracy) / 4, 1e-10))
        log_posts[k] = lp

    # Log-sum-exp normalization
    max_lp = max(log_posts.values())
    total = sum(math.exp(v - max_lp) for v in log_posts.values())

    return {k: math.exp(log_posts[k] - max_lp) / total for k in CANDIDATES}


def score_answer(
    original: str,
    original_source: str,
    rematch: Optional[str],
    ai_observations: Optional[List[Dict]] = None,
    accuracy_dict: Optional[Dict[str, float]] = None,
) -> Tuple[str, float, str]:
    """
    Bayes-optimal scoring using calibrated source accuracies.

    Accepts ALL AI observations (not just one) for true multi-model ensemble.
    Each observation: {"answer": "B", "confidence": 0.85, "source": "opus_v2",
                       "qnum": 1, "solve_type": "vision", "solve_group": "",
                       "page_q_count": 1}

    Computes posterior probability for each candidate answer {A,B,C,D,E}
    using all available evidence sources. Naturally handles:
    - C-bias correction (lower accuracy for Opus C at medium confidence)
    - Multi-source integration (multiply likelihoods)
    - Page-aware penalty for multi-question pages (only ~0.2% of questions)
    - Group-aware text solve weighting

    Args:
        accuracy_dict: Override accuracy values (e.g. from --zero-db or --calibrated).
                       Falls back to module-level ACCURACY if None.

    Returns: (best_answer, posterior_confidence, method_description)
    """
    acc = accuracy_dict if accuracy_dict is not None else ACCURACY

    orig = original.upper().strip() if original else ""
    rem = (rematch or "").upper().strip()

    if ai_observations is None:
        ai_observations = []

    # Build evidence list: (source_tier, answer, accuracy)
    sources = []
    labels = []

    # Original answer
    if orig in VALID_ANSWERS:
        tier = classify_original(original_source)
        sources.append((tier, orig, acc[tier]))
        labels.append("orig")

    # Rematch answer — no sub-tier: rematch pipeline does not produce confidence scores
    if rem in VALID_ANSWERS:
        sources.append(("rematch", rem, acc["rematch"]))
        labels.append("rematch")

    # ALL AI observations (multi-model ensemble)
    for obs in ai_observations:
        ans = (obs.get("answer") or "").upper().strip()
        if ans not in VALID_ANSWERS:
            continue

        conf = round(obs.get("confidence", 0.0), 2)
        src = obs.get("source", "")
        solve_type = obs.get("solve_type", "vision")
        solve_group = obs.get("solve_group", "")
        page_q_count = obs.get("page_q_count", 1)
        qnum = obs.get("qnum", 1)

        # Classify based on source and solve type (dispatcher dict)
        if solve_type == "text":
            tier = classify_qwen_text(conf, solve_group)
            label = "qwen_text"
        else:
            classifier = _SOURCE_CLASSIFIERS.get(src)
            if classifier:
                tier = classifier(conf, ans)
                label = _SOURCE_LABELS.get(src, src)
            else:
                # Unknown source — classify as "other" tier, use source name as label
                tier = "other"
                label = src or "ai"

        accuracy = acc.get(tier, acc.get("other", 0.40))

        # Page-aware penalty: ONLY for full-page vision solve (AI sees entire page).
        # Crop-based sources (qwen_vision) show single questions — no penalty needed.
        is_full_page = solve_type == "vision" and src not in ("qwen_vision", "qwen_crop")
        if is_full_page and page_q_count > 1:
            accuracy = max(accuracy / page_q_count, _PAGE_PENALTY_FLOOR)

        sources.append((tier, ans, accuracy))
        labels.append(label)

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
    if max(vals) - min(vals) < _TIE_BREAK_THRESHOLD and orig in VALID_ANSWERS:
        best = orig
        confidence = posteriors[orig]

    # Build descriptive method string: bayes_{agreeing}of{total}_{primary_source}
    agreeing = [lbl for lbl, (_, ans, _) in zip(labels, sources) if ans == best]
    n_agree = len(agreeing)
    n_total = len(sources)
    primary = agreeing[0] if agreeing else "prior"
    method = f"bayes_{n_agree}of{n_total}_{primary}"

    return best, round(confidence, 4), method


def _score_all(
    production: Dict[Tuple, Dict],
    ai_results: Dict[Tuple, List[Dict]],
    accuracy_dict: Optional[Dict[str, float]] = None,
) -> Tuple[List[Dict], Counter, Counter, Counter, Counter, Counter, Counter, float, int]:
    """Score all questions and collect statistics (pure computation, no I/O)."""
    stats = Counter()
    method_stats = Counter()
    confidence_buckets = Counter()
    answer_dist = Counter()
    change_details = Counter()
    tier_counts = Counter()
    conf_sum = 0.0
    has_answer_count = 0
    results: List[Dict] = []

    for key, q in production.items():
        original = q.get("answer", "")
        original_source = q.get("match_tier") or q.get("answer_source", "")
        rematch = q.get("db_rematch_answer")
        ai_observations = ai_results.get(key, [])

        best_answer, confidence, method = score_answer(
            original, original_source, rematch,
            ai_observations,
            accuracy_dict=accuracy_dict,
        )

        stats["total"] += 1
        method_stats[method] += 1

        if best_answer:
            conf_sum += confidence
            has_answer_count += 1
            answer_dist[best_answer] += 1
            stats["has_answer"] += 1
        else:
            stats["no_answer"] += 1

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

        if ai_observations:
            stats["has_ai"] += 1

        ai_sources = [obs["source"] for obs in ai_observations]
        ai_count = len(ai_observations)

        result = {
            **q,
            "best_answer": best_answer,
            "best_confidence": round(confidence, 4),
            "best_method": method,
            "ai_sources": ai_sources if ai_sources else None,
            "ai_count": ai_count,
            "rematch_answer": rematch,
            "original_answer": original,
            "original_source": original_source,
        }

        if best_answer and best_answer != orig_upper:
            result["answer"] = best_answer
            result["answer_source"] = f"crossval_{method}"

        # REQ-1: Flag questions that only have DB source (no AI validation)
        has_ai = ai_count > 0
        orig_tier = classify_original(original_source)
        is_db_only = orig_tier in _UNRELIABLE_TIERS and not has_ai
        if is_db_only:
            result["needs_ai_solve"] = True
            result["needs_ai_solve_reason"] = "only_db_source"
            stats["needs_ai_solve"] += 1

        results.append(result)

    return (results, stats, method_stats, confidence_buckets,
            answer_dist, change_details, tier_counts, conf_sum, has_answer_count)


def _print_report(
    results: List[Dict],
    stats: Counter,
    method_stats: Counter,
    confidence_buckets: Counter,
    answer_dist: Counter,
    change_details: Counter,
    tier_counts: Counter,
    avg_conf: float,
    simulate: bool = False,
) -> float:
    """Print cross-validation report. Returns chi_sq value."""
    total = stats["total"]
    print("\n" + "=" * 72)
    print("  BAYES-OPTIMAL CROSS-VALIDATION RESULTS")
    print("=" * 72)

    print(f"\n  Total questions:       {total:>8,}")
    print(f"  Has AI observations:   {stats['has_ai']:>8,} ({stats['has_ai']/total*100:.1f}%)")
    print(f"  Has answer:            {stats['has_answer']:>8,} ({stats['has_answer']/total*100:.1f}%)")
    print(f"  Changed from original: {stats['changed']:>8,} ({stats['changed']/total*100:.1f}%)")
    print(f"  Unchanged:             {stats['unchanged']:>8,} ({stats['unchanged']/total*100:.1f}%)")
    print(f"  Needs AI solve:        {stats['needs_ai_solve']:>8,} ({stats['needs_ai_solve']/total*100:.1f}%)")

    print(f"\n  ESTIMATED ACCURACY (mean Bayesian posterior): {avg_conf:.1%}")

    print("\n  BAYESIAN POSTERIOR CONFIDENCE TIERS:")
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

    print("\n  SCORING METHODS (Bayesian source combinations):")
    for method, count in method_stats.most_common(20):
        bar = "#" * max(1, int(count / total * 200))
        print(f"    {method:40s} {count:>6,} ({count/total*100:5.1f}%) {bar}")

    print("\n  POSTERIOR DISTRIBUTION (binned):")
    for bucket in sorted(confidence_buckets.keys()):
        count = confidence_buckets[bucket]
        bar = "#" * max(1, int(count / total * 200))
        print(f"    {bucket:.1f}: {count:>6,} ({count/total*100:5.1f}%) {bar}")

    print("\n  FINAL ANSWER DISTRIBUTION:")
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

    print("\n  CALIBRATED SOURCE ACCURACIES (Bayesian research):")
    for src, acc in sorted(ACCURACY.items(), key=lambda x: -x[1]):
        bar = "#" * int(acc * 40)
        print(f"    {src:15s}: {acc:4.0%} {bar}")

    if simulate or stats["has_ai"] > 0:
        ai_questions = [r for r in results if r.get("ai_count", 0) > 0]
        if ai_questions:
            def get_original(r):
                return (r.get("original_answer") or "").upper()

            agree_orig = sum(
                1 for r in ai_questions
                if r["best_answer"].upper() == get_original(r)
            )
            changed = len(ai_questions) - agree_orig
            print(f"\n  BAYES ENSEMBLE ({len(ai_questions)} AI-answered questions):")
            print(f"    Avg AI sources/question: {sum(r.get('ai_count', 0) for r in ai_questions) / len(ai_questions):.1f}")
            print(f"    Agrees with original:  {agree_orig:>6,} ({agree_orig/len(ai_questions)*100:.1f}%)")
            print(f"    Changed from original: {changed:>6,} ({changed/len(ai_questions)*100:.1f}%)")
            multi_src = [r for r in ai_questions if r.get("ai_count", 0) >= 2]
            if multi_src:
                multi_changed = sum(1 for r in multi_src if r["best_answer"].upper() != get_original(r))
                print(f"    Multi-source (2+):     {len(multi_src):,} questions, {multi_changed} changed")

    if stats["changed"] > 0:
        print("\n  TOP ANSWER CHANGES (original -> new):")
        for change, count in change_details.most_common(15):
            print(f"    {change}: {count}")

    print("\n" + "=" * 72)
    return chi_sq


def cross_validate(
    production: Dict[Tuple, Dict],
    ai_results: Dict[Tuple, List[Dict]],
    analyze_only: bool = False,
    simulate: bool = False,
    output_path: Optional[Path] = None,
    accuracy_dict: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Cross-validate all questions with Bayes-optimal multi-model ensemble.

    Facade: delegates to _score_all() (computation) and _print_report() (output).
    """
    (results, stats, method_stats, confidence_buckets,
     answer_dist, change_details, tier_counts, conf_sum, has_answer_count) = _score_all(
        production, ai_results, accuracy_dict
    )

    avg_conf = conf_sum / has_answer_count if has_answer_count else 0

    chi_sq = _print_report(
        results, stats, method_stats, confidence_buckets,
        answer_dist, change_details, tier_counts, avg_conf, simulate
    )

    # Write output
    if not analyze_only and output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(fast_json_dump_str(r) + "\n")
        print(f"  Output: {output_path}")
        print(f"  Records: {len(results):,}")

    return {
        "stats": dict(stats),
        "method_stats": dict(method_stats),
        "chi_sq": chi_sq,
        "tier_counts": dict(tier_counts),
        "avg_confidence": avg_conf,
        "total": stats["total"],
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
    Turkish lowercase via normalize_tr (I→ı, İ→i) when available.
    """
    filtered = {}
    for key, q in production.items():
        book_raw = normalize_book(q.get("book_name") or "")
        book = _normalize_tr(book_raw) if _normalize_tr else normalize_book(book_raw).lower()
        if any(kw in book for kw in MATH_GEO_KEYWORDS):
            filtered[key] = q
    return filtered


# AI source registry: (name, relative_path, solve_type)
# To add a new source: append one tuple here — no other code changes needed.
SOURCE_REGISTRY = [
    ("opus_v2", "vision_solve_opus_v2/vision_results.jsonl", "vision"),
    ("sonnet", "vision_solve_sonnet/vision_results.jsonl", "vision"),
    ("gemini", "vision_solve_gemini/vision_results.jsonl", "vision"),
    ("gemini_mg", "vision_solve_gemini_mathgeo/vision_results.jsonl", "vision"),
    ("qwen_text", "text_solve_qwen/text_results.jsonl", "text"),
    ("qwen_vision", "vision_solve_grouped/vision_results.jsonl", "vision"),
    ("qwen_crop", "vision_solve_crop/vision_results.jsonl", "vision"),
]


def load_all_vision_results() -> Dict[Tuple[str, int, int], List[Dict]]:
    """
    Load ALL vision/text AI results, returning per-question observation lists.

    Each question key maps to a list of ALL observations from ALL sources.
    This enables true multi-model Bayesian ensemble in score_answer().

    Returns: {(book, page, qnum): [obs1, obs2, ...]} where each obs is:
        {"answer": "B", "confidence": 0.85, "source": "opus_v2",
         "qnum": 1, "solve_type": "vision", "solve_group": "", "page_q_count": 1}
    """
    base_dir = BASE_DIR / "processed"

    sources = [
        (name, base_dir / rel_path, solve_type)
        for name, rel_path, solve_type in SOURCE_REGISTRY
    ]

    # Safety check: no duplicate source names in registry
    source_names = [name for name, _, _ in sources]
    if len(source_names) != len(set(source_names)):
        print("  WARNING: Duplicate source names in registry!")

    results: Dict[Tuple[str, int, int], List[Dict]] = {}

    for name, path, solve_type in sources:
        if not path.exists():
            continue
        loaded = load_vision_results(path)
        count = 0
        for key, val in loaded.items():
            obs = {
                "answer": (val.get("ai_answer") or val.get("answer") or "").upper().strip(),
                "confidence": val.get("confidence", val.get("ai_confidence", 0)),
                "source": name,
                "qnum": val.get("question_number", 1),
                "solve_type": solve_type,
                "solve_group": val.get("solve_group", ""),
                "page_q_count": val.get("page_q_count", 1),
            }
            if obs["answer"] in VALID_ANSWERS:
                results.setdefault(key, []).append(obs)
                count += 1
        print(f"  [{name}] {count:,} valid observations")

    print(f"  Total unique questions with AI: {len(results):,}")
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
            f.write(fast_json_dump_str(r) + "\n")
    print(f"  Needs AI solve: {len(needs_solve):,} -> {output_path}")
    return len(needs_solve)


def main():
    production_path = BASE_DIR / "eslesmis_sorucevap.jsonl"
    rematched_path = BASE_DIR / "processed" / "eslesmis_sorucevap_rematched_v2.jsonl"
    output_path = BASE_DIR / "processed" / "eslesmis_sorucevap_crossval.jsonl"
    qi_output_dir = BASE_DIR / "processed" / "quality_improvement"
    calibration_path = qi_output_dir / "req2_accuracy_calibrated.json"

    # CLI parsing: manual sys.argv instead of argparse for simplicity.
    # Limitation: no flag validation — unknown flags are silently ignored.
    # If this grows beyond ~10 flags, consider migrating to argparse.
    analyze_only = "--analyze" in sys.argv or "--analyze-only" in sys.argv
    incremental = "--incremental" in sys.argv
    simulate = "--simulate" in sys.argv
    zero_db = "--zero-db" in sys.argv
    calibrated = "--calibrated" in sys.argv
    pilot_math_geo = "--pilot-math-geo" in sys.argv
    dry_run = "--dry-run" in sys.argv

    # v3 support: --input and --output overrides
    input_override = None
    output_override = None
    for i, arg in enumerate(sys.argv):
        if arg == "--input" and i + 1 < len(sys.argv):
            input_override = Path(sys.argv[i + 1])
        if arg == "--output" and i + 1 < len(sys.argv):
            output_override = Path(sys.argv[i + 1])

    # REQ-1: Zero-DB mode — effectively ignore DB sources
    # NOTE: If both --zero-db and --calibrated are used, calibrated values
    # override zero-db for any overlapping keys (intentional: data > heuristic)
    # Use a copy to avoid mutating the module-level ACCURACY dict
    effective_accuracy = dict(ACCURACY)
    if zero_db:
        for key, val in DB_WEIGHT_MODES["zero_db"].items():
            effective_accuracy[key] = val
        print(f"  ZERO-DB mode: db_v7={effective_accuracy['db_v7']}, rematch={effective_accuracy['rematch']}")

    # REQ-2: Load calibrated accuracy values (data-driven, not hardcoded)
    if calibrated:
        overrides = load_calibrated_accuracy(calibration_path)
        for key, val in overrides.items():
            if key in effective_accuracy:
                old = effective_accuracy[key]
                effective_accuracy[key] = val
                print(f"    {key}: {old:.3f} → {val:.3f}")

    if input_override and input_override.exists():
        print(f"Loading override input: {input_override.name}")
        production = load_jsonl(input_override)
    elif rematched_path.exists():
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

    # Load ALL AI results as per-question observation lists (multi-model ensemble)
    print("\n  Loading all AI results (multi-model ensemble)...")
    ai_results = load_all_vision_results()
    total_questions_with_ai = len(ai_results)
    total_observations = sum(len(obs_list) for obs_list in ai_results.values())
    coverage = total_questions_with_ai / len(production) * 100 if production else 0
    print(f"  Questions with AI: {total_questions_with_ai:,} ({coverage:.1f}%)")
    print(f"  Total observations: {total_observations:,}")

    if incremental and total_questions_with_ai < 100:
        print(f"\n  WARNING: Only {total_questions_with_ai} AI results. Running in incremental mode.")

    # Determine output path
    if output_override:
        effective_output = output_override
    elif zero_db:
        effective_output = qi_output_dir / "req1_zero_db_results.jsonl"
    else:
        effective_output = output_path

    effective_analyze = analyze_only or dry_run

    result = cross_validate(
        production,
        ai_results,  # Per-question observation lists for multi-model ensemble
        analyze_only=effective_analyze,
        simulate=simulate,
        output_path=None if effective_analyze else effective_output,
        accuracy_dict=effective_accuracy,
    )

    # Write needs_ai_solve list if not dry-run
    if not dry_run and not analyze_only:
        ns_dir = output_override.parent / "quality_improvement" if output_override else qi_output_dir
        write_needs_ai_solve(result.get("results", []), ns_dir)

    return 0


if __name__ == "__main__":
    exit(main())
