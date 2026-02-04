"""
BERTScore Semantic Similarity Evaluator
Wave 2B - Priority 1: Advanced Evaluation Metrics

Purpose:
- Measure semantic similarity between AI-generated and ÖSYM questions
- Turkish BERT-based contextual embedding comparison
- More robust than lexical overlap (BLEU/ROUGE)

Based on: SORU_URETIM_DEGERLENDIRME_CERCEVESI.md
Research: BERTScore paper (Zhang et al., 2020)
Model: dbmdz/bert-base-turkish-cased
"""

import logging
import os
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


# HuggingFace authentication
def _login_huggingface():
    """Login to HuggingFace Hub if token available"""
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    if token:
        try:
            from huggingface_hub import login

            login(token=token, add_to_git_credential=False)
            logger.info("✓ HuggingFace authentication successful")
            return True
        except Exception as e:
            logger.warning(f"HuggingFace login failed: {e}")
            return False
    return False


class BERTScoreEvaluator:
    """
    Semantic similarity evaluation using BERTScore

    Thresholds (based on research):
    - F1 > 0.85: Excellent semantic similarity
    - F1 > 0.80: Good semantic similarity
    - F1 > 0.75: Acceptable semantic similarity
    - F1 < 0.75: Needs improvement
    """

    def __init__(self, model_type: str = "dbmdz/bert-base-turkish-cased"):
        """
        Initialize BERTScore evaluator

        Args:
            model_type: Turkish BERT model to use
        """
        self.model_type = model_type
        self._scorer = None
        self.logger = logger

        # Alternative models to try if primary fails (in order of preference)
        self._fallback_models = [
            "dbmdz/bert-base-turkish-cased",
            "bert-base-multilingual-cased",  # Fallback: supports Turkish
            "distilbert-base-multilingual-cased",  # Lighter fallback
        ]

        # Lazy loading - only import if needed
        try:
            from bert_score import BERTScorer

            self._BERTScorer = BERTScorer
            self._available = True
        except ImportError:
            self._BERTScorer = None
            self._available = False
            logger.warning(
                "bert-score not installed. Run: pip install bert-score\n"
                "BERTScore evaluation will be disabled."
            )

    def _get_scorer(self):
        """Lazy initialization of BERTScorer with fallback models"""
        if self._scorer is None and self._available:
            # Login to HuggingFace first
            _login_huggingface()

            # Try models in order of preference
            models_to_try = [self.model_type] + [
                m for m in self._fallback_models if m != self.model_type
            ]

            for model in models_to_try:
                try:
                    logger.info(f"Trying to initialize BERTScorer with model: {model}")

                    # Determine language setting based on model
                    # Note: Baseline rescaling disabled due to missing baseline files for Turkish
                    if "turkish" in model.lower():
                        lang = "tr"
                        rescale = False  # No baseline available for Turkish BERT
                    elif "multilingual" in model.lower():
                        lang = "tr"  # Specify Turkish for multilingual models
                        rescale = False  # Disable to avoid baseline issues
                    else:
                        lang = None
                        rescale = False

                    self._scorer = self._BERTScorer(
                        model_type=model,
                        lang=lang,
                        rescale_with_baseline=rescale,
                        idf=False,  # Disable IDF to avoid additional downloads
                    )
                    logger.info(
                        f"✓ BERTScorer initialized successfully with model: {model}"
                    )
                    self.model_type = model  # Update to working model
                    return self._scorer
                except Exception as e:
                    logger.warning(f"Failed to initialize with {model}: {e}")
                    continue

            # If all models failed
            logger.error(
                "All BERTScore models failed to initialize. Disabling BERTScore."
            )
            self._available = False

        return self._scorer

    def is_available(self) -> bool:
        """Check if BERTScore is available"""
        return self._available

    def evaluate_single(
        self, candidate: str, reference: str
    ) -> Optional[Dict[str, float]]:
        """
        Evaluate semantic similarity between one candidate and one reference

        Args:
            candidate: AI-generated question text
            reference: ÖSYM reference question text

        Returns:
            Dict with precision, recall, f1 scores (0-1 range)
            None if BERTScore not available
        """
        if not self._available:
            logger.warning("BERTScore not available")
            return None

        scorer = self._get_scorer()
        if scorer is None:
            return None

        try:
            # BERTScore expects lists
            P, R, F1 = scorer.score([candidate], [reference])

            result = {
                "precision": float(P.item()),
                "recall": float(R.item()),
                "f1": float(F1.item()),
                "interpretation": self._interpret_f1(float(F1.item())),
            }

            logger.debug(
                f"BERTScore: F1={result['f1']:.3f}, P={result['precision']:.3f}, R={result['recall']:.3f}"
            )
            return result

        except Exception as e:
            logger.error(f"BERTScore evaluation failed: {e}")
            return None

    def evaluate_batch(
        self, candidates: List[str], references: List[str]
    ) -> Optional[Dict]:
        """
        Evaluate semantic similarity for multiple question pairs

        Args:
            candidates: List of AI-generated questions
            references: List of corresponding ÖSYM questions

        Returns:
            Dict with individual scores and aggregate statistics
            None if BERTScore not available
        """
        if not self._available:
            logger.warning("BERTScore not available")
            return None

        if len(candidates) != len(references):
            raise ValueError(
                f"Candidate count ({len(candidates)}) must match "
                f"reference count ({len(references)})"
            )

        scorer = self._get_scorer()
        if scorer is None:
            return None

        try:
            P, R, F1 = scorer.score(candidates, references)

            # Convert to numpy for statistics
            p_scores = P.numpy()
            r_scores = R.numpy()
            f1_scores = F1.numpy()

            result = {
                "scores": [
                    {
                        "precision": float(p),
                        "recall": float(r),
                        "f1": float(f),
                        "interpretation": self._interpret_f1(float(f)),
                    }
                    for p, r, f in zip(p_scores, r_scores, f1_scores)
                ],
                "statistics": {
                    "mean_precision": float(np.mean(p_scores)),
                    "mean_recall": float(np.mean(r_scores)),
                    "mean_f1": float(np.mean(f1_scores)),
                    "std_f1": float(np.std(f1_scores)),
                    "min_f1": float(np.min(f1_scores)),
                    "max_f1": float(np.max(f1_scores)),
                    "median_f1": float(np.median(f1_scores)),
                },
                "quality_distribution": self._quality_distribution(f1_scores),
                "overall_interpretation": self._interpret_f1(float(np.mean(f1_scores))),
            }

            logger.info(
                f"Batch BERTScore: Mean F1={result['statistics']['mean_f1']:.3f} "
                f"(n={len(candidates)})"
            )

            return result

        except Exception as e:
            logger.error(f"Batch BERTScore evaluation failed: {e}")
            return None

    def find_best_match(
        self, candidate: str, reference_pool: List[str], top_k: int = 5
    ) -> Optional[List[Dict]]:
        """
        Find most similar ÖSYM questions from a pool

        Useful for:
        - Finding similar examples for learning
        - Identifying potential duplicates
        - Quality benchmarking

        Args:
            candidate: AI-generated question
            reference_pool: Pool of ÖSYM questions to compare against
            top_k: Return top K most similar questions

        Returns:
            List of dicts with {reference, f1_score, rank}
            None if BERTScore not available
        """
        if not self._available:
            logger.warning("BERTScore not available")
            return None

        scorer = self._get_scorer()
        if scorer is None:
            return None

        try:
            # Compare candidate against all references
            candidates = [candidate] * len(reference_pool)
            P, R, F1 = scorer.score(candidates, reference_pool)

            # Get F1 scores and sort
            f1_scores = F1.numpy()
            sorted_indices = np.argsort(f1_scores)[::-1]  # Descending

            # Return top K matches
            top_matches = []
            for rank, idx in enumerate(sorted_indices[:top_k], 1):
                top_matches.append(
                    {
                        "rank": rank,
                        "reference": reference_pool[idx],
                        "f1_score": float(f1_scores[idx]),
                        "precision": float(P[idx]),
                        "recall": float(R[idx]),
                        "interpretation": self._interpret_f1(float(f1_scores[idx])),
                    }
                )

            logger.info(
                f"Best match: F1={top_matches[0]['f1_score']:.3f} "
                f"(searched {len(reference_pool)} references)"
            )

            return top_matches

        except Exception as e:
            logger.error(f"Best match search failed: {e}")
            return None

    def _interpret_f1(self, f1_score: float) -> str:
        """Interpret F1 score based on thresholds"""
        if f1_score >= 0.85:
            return "Excellent"
        elif f1_score >= 0.80:
            return "Good"
        elif f1_score >= 0.75:
            return "Acceptable"
        elif f1_score >= 0.70:
            return "Marginal"
        else:
            return "Needs Improvement"

    def _quality_distribution(self, f1_scores: np.ndarray) -> Dict[str, int]:
        """Calculate distribution of quality levels"""
        return {
            "excellent": int(np.sum(f1_scores >= 0.85)),
            "good": int(np.sum((f1_scores >= 0.80) & (f1_scores < 0.85))),
            "acceptable": int(np.sum((f1_scores >= 0.75) & (f1_scores < 0.80))),
            "marginal": int(np.sum((f1_scores >= 0.70) & (f1_scores < 0.75))),
            "needs_improvement": int(np.sum(f1_scores < 0.70)),
        }


# Convenience function for quick evaluation
def evaluate_question_similarity(
    ai_question: str, osym_question: str
) -> Optional[float]:
    """
    Quick semantic similarity check

    Args:
        ai_question: AI-generated question text
        osym_question: ÖSYM reference question text

    Returns:
        F1 score (0-1), or None if unavailable
    """
    evaluator = BERTScoreEvaluator()
    if not evaluator.is_available():
        return None

    result = evaluator.evaluate_single(ai_question, osym_question)
    return result["f1"] if result else None


# Example usage
if __name__ == "__main__":
    # Test with sample questions
    evaluator = BERTScoreEvaluator()

    if not evaluator.is_available():
        print("❌ BERTScore not available. Install with: pip install bert-score")
        exit(1)

    # Example 1: Single question evaluation
    ai_q = "Bir maddenin mol kütlesi 40 g/mol'dür. 20 gram bu maddede kaç mol madde vardır?"
    osym_q = (
        "Mol kütlesi 32 g/mol olan bir elementin 16 gramında kaç mol element vardır?"
    )

    result = evaluator.evaluate_single(ai_q, osym_q)
    print(f"\n📊 Single Question Evaluation:")
    print(f"AI Question: {ai_q[:80]}...")
    print(f"ÖSYM Question: {osym_q[:80]}...")
    print(f"F1 Score: {result['f1']:.3f}")
    print(f"Precision: {result['precision']:.3f}")
    print(f"Recall: {result['recall']:.3f}")
    print(f"Quality: {result['interpretation']}")

    # Example 2: Batch evaluation
    ai_questions = [
        "İki vektörün iç çarpımı nasıl hesaplanır?",
        "Fotosentez olayında hangi gaz açığa çıkar?",
        "Newton'un ikinci yasası kuvvet ve ivme arasındaki ilişkiyi nasıl tanımlar?",
    ]

    osym_questions = [
        "Vektörlerin skaler çarpımı için hangi formül kullanılır?",
        "Bitkilerin fotosentez yapması sırasında atmosfere hangi gaz verilir?",
        "Bir cisme etki eden net kuvvet ile ivme arasındaki bağıntı nedir?",
    ]

    batch_result = evaluator.evaluate_batch(ai_questions, osym_questions)
    print(f"\n📊 Batch Evaluation ({len(ai_questions)} questions):")
    print(f"Mean F1: {batch_result['statistics']['mean_f1']:.3f}")
    print(f"Std F1: {batch_result['statistics']['std_f1']:.3f}")
    print(f"Quality Distribution:")
    for level, count in batch_result["quality_distribution"].items():
        print(f"  {level}: {count}")

    # Example 3: Find best match
    pool = [
        "Vektörlerin skaler çarpımı için hangi formül kullanılır?",
        "İki vektörün vektörel çarpımı nasıl yapılır?",
        "Koordinat sisteminde vektör toplama işlemi nasıl gerçekleştirilir?",
        "Birim vektör nedir ve nasıl hesaplanır?",
        "Paralel vektörlerin özellikleri nelerdir?",
    ]

    matches = evaluator.find_best_match(ai_questions[0], pool, top_k=3)
    print(f"\n📊 Best Match Search:")
    print(f"Query: {ai_questions[0]}")
    for match in matches:
        print(
            f"\nRank {match['rank']}: F1={match['f1_score']:.3f} ({match['interpretation']})"
        )
        print(f"  {match['reference'][:80]}...")
