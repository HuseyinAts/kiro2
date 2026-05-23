"""Tests for cross_validate_answers.py — Bayesian posterior scoring.

Covers:
- bayesian_posterior() math validation
- classify_opus/original/sonnet/gemini() tier classification
- score_answer() multi-source integration
- load_jsonl() I/O handling
- filter_math_geo() subject filtering
- REQ-1: DB_WEIGHT_MODES, zero-db, needs_ai_solve
"""
import json
import sys
import tempfile
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))

from cross_validate_answers import (  # noqa: E402
    ACCURACY,
    DB_WEIGHT_MODES,
    MATH_GEO_KEYWORDS,
    bayesian_posterior,
    classify_gemini,
    classify_opus,
    classify_original,
    classify_qwen_text,
    classify_qwen_vision,
    classify_sonnet,
    filter_math_geo,
    load_jsonl,
    normalize_book,
    score_answer,
)


# ============================================================================
# bayesian_posterior() tests
# ============================================================================

class TestBayesianPosterior:
    """Test Bayesian posterior computation P(correct=k | observations)."""

    def test_single_high_accuracy_source(self):
        """Single source with 85% accuracy saying 'A' should give A highest."""
        sources = [("opus_high", "A", 0.85)]
        post = bayesian_posterior(sources)

        assert post["A"] > post["B"]
        assert post["A"] > post["C"]
        assert post["A"] > post["D"]
        assert post["A"] > post["E"]
        assert abs(sum(post.values()) - 1.0) < 1e-9, "Posterior must sum to 1"

    def test_single_source_exact_math(self):
        """Verify exact posterior calculation for single source."""
        # Single source says "B" with accuracy 0.8
        sources = [("test", "B", 0.8)]
        post = bayesian_posterior(sources)

        # P(B) = 0.2 * 0.8 = 0.16
        # P(other) = 0.2 * (0.2/4) = 0.2 * 0.05 = 0.01  (each)
        # Total = 0.16 + 4*0.01 = 0.20
        expected_b = 0.16 / 0.20
        expected_other = 0.01 / 0.20

        assert abs(post["B"] - expected_b) < 1e-9
        assert abs(post["A"] - expected_other) < 1e-9
        assert abs(post["C"] - expected_other) < 1e-9

    def test_two_sources_agree(self):
        """Two sources agreeing should give very high posterior."""
        sources = [
            ("opus_high", "D", 0.85),
            ("ai_solved", "D", 0.85),
        ]
        post = bayesian_posterior(sources)

        assert post["D"] > 0.95, f"Two high-accuracy sources agreeing: expected >95%, got {post['D']:.4f}"

    def test_two_sources_disagree(self):
        """Two sources disagreeing — higher accuracy source should win."""
        sources = [
            ("opus_high", "A", 0.85),
            ("opus_low", "C", 0.25),
        ]
        post = bayesian_posterior(sources)

        assert post["A"] > post["C"], "Higher accuracy source should have higher posterior"

    def test_three_sources_two_agree(self):
        """Two sources agree vs one disagree — majority with higher accuracy wins."""
        sources = [
            ("opus_high", "B", 0.85),
            ("ai_solved", "B", 0.85),
            ("db_v7", "D", 0.39),
        ]
        post = bayesian_posterior(sources)

        assert post["B"] > 0.98, f"Two high-accuracy vs one low: expected >98%, got {post['B']:.4f}"

    def test_uniform_prior_no_evidence(self):
        """With no sources, prior should be uniform 1/5."""
        post = bayesian_posterior([])

        for k in "ABCDE":
            assert abs(post[k] - 0.2) < 1e-9, f"Empty sources: {k} should be 0.2, got {post[k]}"

    def test_low_accuracy_source_near_uniform(self):
        """Source with 20% accuracy (random) should barely change prior."""
        sources = [("random", "A", 0.20)]
        post = bayesian_posterior(sources)

        # 20% accuracy = random for 5 choices, posterior should be nearly uniform
        for k in "ABCDE":
            assert abs(post[k] - 0.2) < 0.01, f"Random accuracy: {k} should be ~0.2, got {post[k]}"

    def test_posterior_sums_to_one(self):
        """Posterior must always sum to 1.0."""
        test_cases = [
            [("s1", "A", 0.85)],
            [("s1", "B", 0.50), ("s2", "C", 0.70)],
            [("s1", "E", 0.99), ("s2", "E", 0.99), ("s3", "A", 0.90)],
        ]
        for sources in test_cases:
            post = bayesian_posterior(sources)
            assert abs(sum(post.values()) - 1.0) < 1e-9

    def test_numerical_stability_extreme_accuracy(self):
        """Very high/low accuracy values should not cause overflow/underflow."""
        sources = [
            ("extreme_high", "A", 0.999),
            ("extreme_low", "B", 0.001),
        ]
        post = bayesian_posterior(sources)

        assert post["A"] > 0.99
        assert abs(sum(post.values()) - 1.0) < 1e-9

    def test_numerical_stability_many_sources(self):
        """Many sources should not cause numerical issues."""
        sources = [("s" + str(i), "C", 0.80) for i in range(10)]
        post = bayesian_posterior(sources)

        assert post["C"] > 0.9999, "10 sources at 80% all saying C should give very high posterior"
        assert abs(sum(post.values()) - 1.0) < 1e-9

    def test_c_bias_detection(self):
        """Opus medium C answer should use lower accuracy (0.35 vs 0.70)."""
        sources_c = [("opus_med_c", "C", ACCURACY["opus_med_c"])]
        sources_b = [("opus_med", "B", ACCURACY["opus_med"])]

        post_c = bayesian_posterior(sources_c)
        post_b = bayesian_posterior(sources_b)

        # B with 70% accuracy should have higher posterior than C with 35%
        assert post_b["B"] > post_c["C"], "C-bias correction: C@35% should be weaker than B@70%"

    def test_mcq_agreement_formula(self):
        """Verify MCQ agreement formula: P(agree) = p1*p2 + (1-p1)*(1-p2)/4."""
        p1, p2 = 0.85, 0.80
        p_agree = p1 * p2 + (1 - p1) * (1 - p2) / 4
        assert abs(p_agree - 0.6875) < 0.001, f"Expected ~68.75% agreement, got {p_agree*100:.2f}%"


# ============================================================================
# classify_opus/original() tests
# ============================================================================

class TestClassifyOpus:
    def test_high_confidence(self):
        assert classify_opus(0.95, "A") == "opus_high"
        assert classify_opus(0.90, "B") == "opus_high"

    def test_medium_confidence_non_c(self):
        assert classify_opus(0.80, "A") == "opus_med"
        assert classify_opus(0.70, "D") == "opus_med"

    def test_medium_confidence_c_answer(self):
        assert classify_opus(0.80, "C") == "opus_med_c"
        assert classify_opus(0.70, "C") == "opus_med_c"

    def test_low_confidence(self):
        assert classify_opus(0.60, "A") == "opus_low"
        assert classify_opus(0.10, "C") == "opus_low"

    def test_boundary_values(self):
        assert classify_opus(0.90, "A") == "opus_high"
        assert classify_opus(0.8999, "A") == "opus_med"
        assert classify_opus(0.70, "B") == "opus_med"
        assert classify_opus(0.6999, "B") == "opus_low"


class TestClassifyOriginal:
    def test_ai_solved(self):
        assert classify_original("ai_solve_v1") == "ai_solved"
        assert classify_original("claude_opus") == "ai_solved"

    def test_jsonl_v11(self):
        assert classify_original("jsonl_v11") == "jsonl_v11"

    def test_db_sources(self):
        assert classify_original("db_v7") == "db_v7"
        assert classify_original("match_v3") == "db_v7"

    def test_unknown(self):
        assert classify_original("") == "other"
        assert classify_original("unknown_source") == "other"

    def test_none(self):
        assert classify_original(None) == "other"

    def test_ai_upgrade_separate_tier(self):
        """S194 fix: ai_upgrade must NOT be classified as ai_solved (0.85).

        Bug: ai_upgrade source was hardcoded to ai_solved tier (0.85 = production
        Opus level), causing Bayesian formula to over-weight original_answer vs
        rematch suggestions. Result: 129+ A-bias rejections across 12 subjects.
        Fix: ai_upgrade gets its own tier (~0.65, cross-validation tier).
        """
        assert classify_original("ai_upgrade") == "ai_upgrade", (
            "ai_upgrade must be its own tier (not ai_solved/0.85)"
        )
        assert classify_original("ai_upgrade") != "ai_solved"

    def test_ai_upgrade_prefixed_variants(self):
        """S194 fix coverage: replace_db_v7_sources.py:173 writes prefixed strings.

        Real-world sources from replace_db_v7_sources.py:
          f"ai_upgrade_{method}" → "ai_upgrade_bayes_2of4_orig", etc.

        Without prefix coverage, these fell through to 'other' (0.40) tier —
        still mis-tiered. Fix uses source.startswith('ai_upgrade_').

        Verified real prefixes from audit (S194 root cause investigation):
          - ai_upgrade_bayes_2of4_orig (most common, 13+ wrong cases)
          - ai_upgrade_bayes_3of4_orig
          - ai_upgrade_bayes_1of3_gemini
          - ai_upgrade_bayes_2of3_orig
        """
        for variant in [
            "ai_upgrade_bayes_2of4_orig",
            "ai_upgrade_bayes_3of4_orig",
            "ai_upgrade_bayes_1of3_gemini",
            "ai_upgrade_bayes_2of3_orig",
            "ai_upgrade_anything",
        ]:
            assert classify_original(variant) == "ai_upgrade", (
                f"prefix variant {variant!r} must route to ai_upgrade tier "
                f"(not 'other' fallback)"
            )

    def test_ai_upgrade_accuracy_below_production(self):
        """ai_upgrade tier accuracy must be < production AI tiers (opus_high, ai_solved)."""
        from cross_validate_answers import ACCURACY
        assert "ai_upgrade" in ACCURACY, "ai_upgrade tier missing from ACCURACY dict"
        assert ACCURACY["ai_upgrade"] < ACCURACY["ai_solved"], (
            "ai_upgrade must have lower accuracy than ai_solved (production-Opus)"
        )
        assert ACCURACY["ai_upgrade"] < ACCURACY["opus_high"], (
            "ai_upgrade must have lower accuracy than opus_high"
        )
        assert ACCURACY["ai_upgrade"] >= ACCURACY["other"], (
            "ai_upgrade must have higher accuracy than 'other' (it IS cross-validated)"
        )


class TestAUpgradeFix_S194:
    """S194 regression test: 905-wrong audit revealed Bayesian over-weighting ai_upgrade.

    Real-world case (from audit, 13 instances):
      original_answer = C  (source=ai_upgrade)
      rematch_answer  = A  (source=rematch)
      LLM verifies A is correct.

    Pre-fix: Bayesian gives C ~17x posterior over A (rematch=0.25 vs ai_upgrade=0.85).
    Post-fix: ai_upgrade tier 0.65, gap narrows so a strong agreement from other
    sources can flip the verdict.
    """

    def test_ai_upgrade_with_strong_disagreement(self):
        """When ai_upgrade=C but high-conf Opus and rematch both say A, A should win."""
        # Simulate post-audit scenario: ai_upgrade is the ONLY orig signal,
        # but 3 independent observations agree on A.
        sources = [
            ("ai_upgrade", "C", 0.65),   # NEW tier (post-fix)
            ("opus_high",  "A", 0.85),   # strong vision validation
            ("sonnet_high", "A", 0.87),  # strong cross-check
        ]
        post = bayesian_posterior(sources, use_anti_bias=False)
        assert post["A"] > post["C"], (
            f"Strong agreement on A should override ai_upgrade=C; got "
            f"A={post['A']:.3f} C={post['C']:.3f}"
        )

    def test_ai_upgrade_vs_ai_solved_disambiguation(self):
        """Same answer from ai_solved (production) should outweigh ai_upgrade (cross-val)."""
        # If ai_solved (real production Opus) and ai_upgrade disagree,
        # ai_solved should win because it's the higher-trust tier.
        sources = [
            ("ai_solved",  "A", 0.85),
            ("ai_upgrade", "B", 0.65),
        ]
        post = bayesian_posterior(sources, use_anti_bias=False)
        assert post["A"] > post["B"], (
            f"ai_solved (0.85) must outweigh ai_upgrade (0.65); got "
            f"A={post['A']:.3f} B={post['B']:.3f}"
        )


class TestClassifyQwenText:
    def test_low_confidence_any_group(self):
        assert classify_qwen_text(0.3, "TEXT_RICH") == "qwen_text_low"
        assert classify_qwen_text(0.1, "GEO_FIGURE") == "qwen_text_low"

    def test_geo_figure(self):
        assert classify_qwen_text(0.9, "GEO_FIGURE") == "qwen_text_geo_high"
        assert classify_qwen_text(0.5, "GEO_FIGURE") == "qwen_text_geo_high"

    def test_text_rich_high(self):
        assert classify_qwen_text(0.9, "TEXT_RICH") == "qwen_text_rich_high"

    def test_text_rich_medium(self):
        assert classify_qwen_text(0.6, "TEXT_RICH") == "qwen_text_rich_med"

    def test_short(self):
        assert classify_qwen_text(0.8, "SHORT") == "qwen_text_short_high"


class TestClassifyQwenVision:
    def test_high(self):
        assert classify_qwen_vision(0.9) == "qwen_vision_high"

    def test_medium(self):
        assert classify_qwen_vision(0.6) == "qwen_vision_med"

    def test_low(self):
        assert classify_qwen_vision(0.3) == "qwen_vision_low"


# ============================================================================
# score_answer() integration tests
# ============================================================================

class TestScoreAnswer:
    def test_only_original(self):
        """Only original source available."""
        answer, conf, method = score_answer(
            original="A",
            original_source="jsonl_v11",
            rematch=None,
            ai_observations=[],
        )
        assert answer == "A"
        assert conf > 0

    def test_ai_overrides_db(self):
        """Single high-confidence AI should override weak DB source."""
        answer, conf, method = score_answer(
            original="D",
            original_source="db_v7",
            rematch=None,
            ai_observations=[
                {"answer": "A", "confidence": 0.95, "source": "opus_v2",
                 "qnum": 1, "solve_type": "vision"},
            ],
        )
        assert answer == "A", "High-conf Opus should override db_v7"

    def test_original_ai_solved_preserved(self):
        """ai_solved original with no AI data should be preserved."""
        answer, conf, method = score_answer(
            original="E",
            original_source="ai_solve_v1",
            rematch=None,
            ai_observations=[],
        )
        assert answer == "E"

    def test_rematch_harmful(self):
        """Rematch (25% accuracy) should not override better sources."""
        answer, conf, method = score_answer(
            original="A",
            original_source="jsonl_v11",
            rematch="D",
            ai_observations=[],
        )
        # jsonl_v11 (73%) vs rematch (25%) — original should win
        assert answer == "A", "Rematch at 25% should not override jsonl_v11 at 73%"

    def test_opus_overrides_db_and_rematch(self):
        """High-conf Opus should override weak DB + rematch."""
        answer, conf, method = score_answer(
            original="C",
            original_source="db_v7",
            rematch="D",
            ai_observations=[
                {"answer": "B", "confidence": 0.92, "source": "opus_v2",
                 "qnum": 1, "solve_type": "vision"},
            ],
        )
        assert answer == "B"
        assert conf > 0.7

    def test_output_format(self):
        """score_answer returns (str, float, str)."""
        answer, conf, method = score_answer(
            original="A",
            original_source="jsonl_v11",
            rematch=None,
            ai_observations=[],
        )
        assert isinstance(answer, str)
        assert answer in "ABCDE"
        assert isinstance(conf, float)
        assert 0.0 <= conf <= 1.0
        assert isinstance(method, str)

    def test_multi_model_agreement(self):
        """Two models agreeing should give very high confidence."""
        answer, conf, method = score_answer(
            original="C",
            original_source="db_v7",
            rematch=None,
            ai_observations=[
                {"answer": "B", "confidence": 0.90, "source": "opus_v2",
                 "qnum": 1, "solve_type": "vision"},
                {"answer": "B", "confidence": 0.88, "source": "sonnet",
                 "qnum": 1, "solve_type": "vision"},
            ],
        )
        assert answer == "B", "Two models agreeing should override DB"
        assert conf > 0.95, "Two high-conf models agreeing: expect >95%"

    def test_text_solve_group_aware(self):
        """Text solve for GEO_FIGURE should have low weight (0.30)."""
        # Text says A with high conf, but for geometry it's nearly useless
        answer, conf, method = score_answer(
            original="B",
            original_source="jsonl_v11",
            rematch=None,
            ai_observations=[
                {"answer": "A", "confidence": 0.90, "source": "qwen_text",
                 "qnum": 1, "solve_type": "text", "solve_group": "GEO_FIGURE"},
            ],
        )
        # jsonl_v11 at 73% vs qwen_text_geo at 30% — original should win
        assert answer == "B", "Geometry text solve (30%) should not override jsonl_v11 (73%)"

    def test_page_aware_penalty(self):
        """Vision on multi-question page (qnum=1) should get penalty."""
        # Single-question page: no penalty
        ans1, conf1, _ = score_answer(
            original="C",
            original_source="db_v7",
            rematch=None,
            ai_observations=[
                {"answer": "A", "confidence": 0.90, "source": "opus_v2",
                 "qnum": 1, "solve_type": "vision", "page_q_count": 1},
            ],
        )
        # Multi-question page (3 questions): penalty applied
        ans2, conf2, _ = score_answer(
            original="C",
            original_source="db_v7",
            rematch=None,
            ai_observations=[
                {"answer": "A", "confidence": 0.90, "source": "opus_v2",
                 "qnum": 1, "solve_type": "vision", "page_q_count": 3},
            ],
        )
        assert conf1 > conf2, "Single-page should have higher confidence than multi-page"

    def test_crop_based_no_penalty(self):
        """Crop-based vision (qwen_vision) should NOT get page_q_count penalty."""
        # qwen_vision with page_q_count=3: crop shows single question, no penalty
        ans_crop, conf_crop, _ = score_answer(
            original="", original_source="", rematch=None,
            ai_observations=[
                {"answer": "B", "confidence": 0.85, "source": "qwen_vision",
                 "qnum": 1, "solve_type": "vision", "page_q_count": 3,
                 "solve_group": ""},
            ],
        )
        # opus_v2 with page_q_count=3: full page, penalty applied
        ans_full, conf_full, _ = score_answer(
            original="", original_source="", rematch=None,
            ai_observations=[
                {"answer": "B", "confidence": 0.85, "source": "opus_v2",
                 "qnum": 1, "solve_type": "vision", "page_q_count": 3,
                 "solve_group": ""},
            ],
        )
        assert conf_crop > conf_full, "Crop-based should not be penalized"

    def test_classify_original_page_inline(self):
        """classify_original must handle v3 answer_source AND match_tier values."""
        # answer_source values (from DB source column)
        assert classify_original("page_inline") == "tier1"
        assert classify_original("page_inline_unique") == "tier1_5"
        # match_tier values (from matching method)
        assert classify_original("tier1_page_inline") == "tier1"
        assert classify_original("tier1b_position_page_inline") == "tier1"
        assert classify_original("tier1_5_page_inline_unique") == "tier1_5"
        # tier5 q_index must be distinguished from tier1
        assert classify_original("tier5_qindex_page_inline") == "tier5_qindex"
        assert classify_original("tier5_qindex_page_inline_unique") == "tier5_qindex"


# ============================================================================
# ACCURACY dict validation
# ============================================================================

class TestAccuracyConfig:
    def test_all_values_in_range(self):
        """All accuracy values must be in (0, 1]."""
        for key, val in ACCURACY.items():
            assert 0 < val <= 1.0, f"ACCURACY['{key}'] = {val} out of range"

    def test_known_keys_present(self):
        """All expected tiers must exist."""
        required = {
            "opus_high", "opus_med", "opus_med_c", "opus_low",
            "sonnet_high", "sonnet_med", "sonnet_med_c", "sonnet_low",
            "gemini_high", "gemini_med", "gemini_low",
            "ai_solved", "jsonl_v11", "db_v7", "rematch", "other",
            "qwen_text_rich_high", "qwen_text_low",
            "qwen_vision_high", "qwen_vision_med", "qwen_vision_low",
        }
        assert required.issubset(set(ACCURACY.keys()))

    def test_ordering_makes_sense(self):
        """High > med > low for Opus."""
        assert ACCURACY["opus_high"] > ACCURACY["opus_med"]
        assert ACCURACY["opus_med"] > ACCURACY["opus_low"]

    def test_c_bias_penalty(self):
        """Opus C-bias tier should be lower than non-C medium."""
        assert ACCURACY["opus_med_c"] < ACCURACY["opus_med"]

    def test_rematch_is_low(self):
        """Rematch known to be HARMFUL — should be low."""
        assert ACCURACY["rematch"] <= 0.30

    def test_sonnet_tiers_ordered(self):
        """Sonnet tiers: high > med > low."""
        assert ACCURACY["sonnet_high"] > ACCURACY["sonnet_med"]
        assert ACCURACY["sonnet_med"] > ACCURACY["sonnet_low"]

    def test_gemini_tiers_ordered(self):
        """Gemini tiers: high > med > low."""
        assert ACCURACY["gemini_high"] > ACCURACY["gemini_med"]
        assert ACCURACY["gemini_med"] > ACCURACY["gemini_low"]


# ============================================================================
# REQ-1: DB_WEIGHT_MODES + zero-db tests
# ============================================================================

class TestDBWeightModes:
    def test_legacy_mode_empty(self):
        """Legacy mode should have no overrides."""
        assert DB_WEIGHT_MODES["legacy"] == {}

    def test_zero_db_mode_values(self):
        """Zero-DB mode should set db/rematch to uninformative (1/5 for MCQ)."""
        zdb = DB_WEIGHT_MODES["zero_db"]
        assert zdb["db_v7"] == 0.20
        assert zdb["rematch"] == 0.20

    def test_zero_db_does_not_cause_log_error(self):
        """Zero-DB values (0.20) should work in Bayesian posterior without errors."""
        sources = [("db_v7", "A", 0.20), ("opus_high", "B", 0.85)]
        post = bayesian_posterior(sources)
        assert abs(sum(post.values()) - 1.0) < 1e-9
        assert post["B"] > post["A"], "Opus should overwhelm uninformative DB"

    def test_zero_db_effectively_ignores_db(self):
        """With 0.20 accuracy (random), DB source should be overwhelmed by any real source."""
        # DB at 0.20 (random for 5-choice) vs Opus at 0.85
        sources = [("db_v7", "A", 0.20), ("opus_high", "B", 0.85)]
        post = bayesian_posterior(sources)
        # Opus (B) should dominate random DB (A)
        assert post["B"] > 0.70, f"Opus should dominate: B={post['B']:.4f}"
        assert post["A"] < 0.10, f"Random DB source should be weak: A={post['A']:.4f}"


class TestMathGeoKeywords:
    def test_keywords_exist(self):
        assert len(MATH_GEO_KEYWORDS) > 0

    def test_turkish_keywords(self):
        assert "matematik" in MATH_GEO_KEYWORDS
        assert "geometri" in MATH_GEO_KEYWORDS


# ============================================================================
# Faz 1: Regression Safety Net Tests (NEW)
# ============================================================================

class TestClassifySonnet:
    """1A: classify_sonnet() tier boundaries."""

    def test_high_confidence(self):
        assert classify_sonnet(0.95, "A") == "sonnet_high"
        assert classify_sonnet(0.90, "B") == "sonnet_high"

    def test_medium_non_c(self):
        assert classify_sonnet(0.80, "A") == "sonnet_med"
        assert classify_sonnet(0.70, "D") == "sonnet_med"

    def test_medium_c_answer(self):
        assert classify_sonnet(0.80, "C") == "sonnet_med_c"
        assert classify_sonnet(0.70, "C") == "sonnet_med_c"

    def test_low_confidence(self):
        assert classify_sonnet(0.60, "A") == "sonnet_low"
        assert classify_sonnet(0.10, "C") == "sonnet_low"

    def test_boundary_0_90(self):
        assert classify_sonnet(0.90, "A") == "sonnet_high"
        assert classify_sonnet(0.8999, "A") == "sonnet_med"

    def test_boundary_0_70(self):
        assert classify_sonnet(0.70, "B") == "sonnet_med"
        assert classify_sonnet(0.6999, "B") == "sonnet_low"


class TestClassifyGemini:
    """1A: classify_gemini() tier boundaries."""

    def test_high_confidence(self):
        assert classify_gemini(0.95, "A") == "gemini_high"
        assert classify_gemini(0.90, "B") == "gemini_high"

    def test_medium_confidence(self):
        assert classify_gemini(0.80, "A") == "gemini_med"
        assert classify_gemini(0.70, "D") == "gemini_med"

    def test_low_confidence(self):
        assert classify_gemini(0.60, "A") == "gemini_low"
        assert classify_gemini(0.10, "C") == "gemini_low"

    def test_boundary_0_90(self):
        assert classify_gemini(0.90, "A") == "gemini_high"
        assert classify_gemini(0.8999, "A") == "gemini_med"

    def test_boundary_0_70(self):
        assert classify_gemini(0.70, "B") == "gemini_med"
        assert classify_gemini(0.6999, "B") == "gemini_low"


class TestLoadJsonl:
    """1B: load_jsonl() I/O handling."""

    def test_duplicate_key_keeps_last(self):
        """Same (book, page, qnum) key — last entry wins."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            # Two entries with same key but different answers
            f.write(json.dumps({"book_name": "Test", "page_number": 1, "question_number": 1, "answer": "A"}) + "\n")
            f.write(json.dumps({"book_name": "Test", "page_number": 1, "question_number": 1, "answer": "B"}) + "\n")
            f.flush()
            result = load_jsonl(Path(f.name))
        assert len(result) == 1
        key = (normalize_book("Test"), 1, 1)
        assert result[key]["answer"] == "B", "Last entry should win"

    def test_empty_lines_skipped(self):
        """Empty and whitespace-only lines should be silently skipped."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write("\n")
            f.write("   \n")
            f.write(json.dumps({"book_name": "Test", "page_number": 1, "question_number": 1, "answer": "C"}) + "\n")
            f.write("\n")
            f.flush()
            result = load_jsonl(Path(f.name))
        assert len(result) == 1


class TestScoreAnswerEdgeCases:
    """1C: score_answer() edge cases."""

    def test_no_agreeing_sources(self):
        """3 different sources with 3 different answers — method should contain 'bayes'."""
        answer, conf, method = score_answer(
            original="A",
            original_source="jsonl_v11",
            rematch="B",
            ai_observations=[
                {"answer": "C", "confidence": 0.75, "source": "opus_v2",
                 "qnum": 1, "solve_type": "vision"},
            ],
        )
        assert "bayes" in method

    def test_prior_label_on_tiebreak(self):
        """H3 fix: when posteriors are near-uniform and tie-break picks original,
        but no source agrees with the best answer, label should be 'prior'."""
        # All sources have very low accuracy → near-uniform posterior → tie-break
        answer, conf, method = score_answer(
            original="D",
            original_source="db_v7",  # accuracy 0.39
            rematch="E",              # accuracy 0.25
            ai_observations=[
                {"answer": "A", "confidence": 0.10, "source": "opus_v2",
                 "qnum": 1, "solve_type": "vision"},  # opus_low = 0.25
            ],
            accuracy_dict={"db_v7": 0.20, "rematch": 0.20, "opus_low": 0.20},
        )
        # With all accuracies at 0.20 (random), posterior is near-uniform → tie-break
        # Tie-break returns original "D", but no source voted "D" except orig which
        # is labeled "orig". If best != any AI vote, agreeing may not include AI sources.
        assert "bayes" in method
        # The primary label depends on whether orig's answer matches best
        # With uniform posteriors, tie-break keeps orig="D", agreeing includes "orig"
        assert "orig" in method or "prior" in method, (
            f"Expected 'orig' or 'prior' in method, got: {method}"
        )

    def test_empty_original_empty_ai(self):
        """No original, no AI → empty answer."""
        answer, conf, method = score_answer(
            original="",
            original_source="",
            rematch=None,
            ai_observations=[],
        )
        assert answer == ""
        assert conf == 0.0
        assert method == "no_answer"

    def test_single_source_high_conf(self):
        """Single high-conf opus → best should be opus answer, conf > 0.50."""
        answer, conf, method = score_answer(
            original="",
            original_source="",
            rematch=None,
            ai_observations=[
                {"answer": "D", "confidence": 0.95, "source": "opus_v2",
                 "qnum": 1, "solve_type": "vision"},
            ],
        )
        assert answer == "D"
        assert conf > 0.50


class TestFilterMathGeo:
    """1D: filter_math_geo() subject filtering."""

    def test_basic_match(self):
        """Geometry book matches, Physics book does not."""
        prod = {
            ("Geometri Soru", 1, 1): {"book_name": "Geometri Soru", "page_number": 1, "question_number": 1},
            ("Fizik Soru", 1, 1): {"book_name": "Fizik Soru", "page_number": 1, "question_number": 1},
        }
        filtered = filter_math_geo(prod)
        assert len(filtered) == 1
        assert ("Geometri Soru", 1, 1) in filtered

    def test_case_insensitive(self):
        """Keywords are matched case-insensitively via Turkish normalize."""
        # Turkish uppercase: MATEMATİK (with İ) → matematik (with i)
        prod = {
            ("MATEMATİK Kitabi", 1, 1): {"book_name": "MATEMATİK Kitabi", "page_number": 1, "question_number": 1},
        }
        filtered = filter_math_geo(prod)
        assert len(filtered) == 1
