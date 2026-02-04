"""
Advanced Reranking Module for RAG
Cross-encoder based reranking for better accuracy
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """Reranking result"""

    content: str
    score: float
    original_score: float
    rerank_score: float
    metadata: Dict[str, Any]


class CrossEncoderReranker:
    """
    Cross-encoder based reranker
    Uses sentence-transformers cross-encoder for accurate relevance scoring
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cpu",
        batch_size: int = 32,
    ):
        """
        Initialize cross-encoder reranker

        Args:
            model_name: Cross-encoder model to use
            device: Device to run on (cpu/cuda)
            batch_size: Batch size for processing
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.model = None
        self._initialized = False

    def _lazy_init(self):
        """Lazy initialization of the model"""
        if self._initialized:
            return

        try:
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(
                self.model_name, device=self.device, max_length=512
            )
            self._initialized = True
            logger.info(f"Cross-encoder reranker initialized: {self.model_name}")

        except ImportError:
            logger.warning(
                "sentence-transformers not available. "
                "Install with: pip install sentence-transformers"
            )
            self.model = None
        except Exception as e:
            logger.error(f"Failed to initialize cross-encoder: {e}")
            self.model = None

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        combine_scores: bool = True,
        weight: float = 0.5,
    ) -> List[RerankResult]:
        """
        Rerank search results using cross-encoder

        Args:
            query: Search query
            results: Initial search results
            top_k: Number of results to keep after reranking
            combine_scores: Combine cross-encoder score with original score
            weight: Weight for cross-encoder score (0-1)

        Returns:
            Reranked results
        """
        self._lazy_init()

        if not self.model or not results:
            # Fallback to keyword-based reranking
            return self._fallback_rerank(query, results, top_k)

        try:
            # Prepare query-document pairs
            pairs = []
            for result in results:
                content = result.get("content") or result.get("text", "")
                pairs.append([query, content])

            # Get cross-encoder scores
            cross_scores = self.model.predict(
                pairs, batch_size=self.batch_size, show_progress_bar=False
            )

            # Build reranked results
            reranked = []
            for idx, result in enumerate(results):
                original_score = result.get("score", 0.5)
                cross_score = float(cross_scores[idx])

                # Combine scores if requested
                if combine_scores:
                    final_score = (1 - weight) * original_score + weight * cross_score
                else:
                    final_score = cross_score

                reranked.append(
                    RerankResult(
                        content=result.get("content") or result.get("text", ""),
                        score=final_score,
                        original_score=original_score,
                        rerank_score=cross_score,
                        metadata=result.get("metadata", {}),
                    )
                )

            # Sort by final score
            reranked.sort(key=lambda x: x.score, reverse=True)

            # Take top K
            if top_k:
                reranked = reranked[:top_k]

            return reranked

        except Exception as e:
            logger.error(f"Cross-encoder reranking failed: {e}")
            return self._fallback_rerank(query, results, top_k)

    def _fallback_rerank(
        self, query: str, results: List[Dict[str, Any]], top_k: Optional[int] = None
    ) -> List[RerankResult]:
        """Fallback keyword-based reranking"""
        query_terms = set(query.lower().split())

        reranked = []
        for result in results:
            content = result.get("content") or result.get("text", "")
            content_terms = set(content.lower().split())

            # Keyword overlap
            overlap = (
                len(query_terms & content_terms) / len(query_terms)
                if query_terms
                else 0
            )

            original_score = result.get("score", 0.5)
            final_score = (original_score * 0.7) + (overlap * 0.3)

            reranked.append(
                RerankResult(
                    content=content,
                    score=final_score,
                    original_score=original_score,
                    rerank_score=overlap,
                    metadata=result.get("metadata", {}),
                )
            )

        reranked.sort(key=lambda x: x.score, reverse=True)

        if top_k:
            reranked = reranked[:top_k]

        return reranked


class MultilingualReranker(CrossEncoderReranker):
    """
    Multilingual cross-encoder reranker optimized for Turkish
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        device: str = "cpu",
        batch_size: int = 32,
    ):
        """
        Initialize multilingual reranker

        Default model supports 100+ languages including Turkish
        """
        super().__init__(model_name, device, batch_size)


class TurkishOptimizedReranker:
    """
    Reranker optimized for Turkish educational content
    Combines cross-encoder with Turkish-specific features
    """

    def __init__(self, use_cross_encoder: bool = True):
        self.cross_encoder = None
        if use_cross_encoder:
            self.cross_encoder = MultilingualReranker()

        # Turkish stopwords (simplified)
        self.stopwords = {
            "bir",
            "bu",
            "şu",
            "ve",
            "veya",
            "için",
            "ile",
            "gibi",
            "kadar",
            "daha",
            "çok",
            "az",
            "de",
            "da",
            "mi",
            "mu",
            "mı",
            "mü",
            "ne",
            "nedir",
            "nasıl",
            "neden",
            "niçin",
        }

    def _extract_keywords(self, text: str) -> set:
        """Extract meaningful keywords from Turkish text"""
        words = text.lower().split()
        # Remove stopwords
        keywords = {w for w in words if w not in self.stopwords and len(w) > 2}
        return keywords

    def _calculate_turkish_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score for Turkish text"""
        query_keywords = self._extract_keywords(query)
        content_keywords = self._extract_keywords(content)

        if not query_keywords:
            return 0.0

        # Exact keyword matches
        exact_matches = query_keywords & content_keywords
        exact_score = len(exact_matches) / len(query_keywords)

        # Partial matches (prefix/suffix)
        partial_matches = 0
        for qk in query_keywords:
            for ck in content_keywords:
                if qk in ck or ck in qk:
                    partial_matches += 1
                    break

        partial_score = partial_matches / len(query_keywords)

        # Combined score
        relevance = (exact_score * 0.7) + (partial_score * 0.3)

        return relevance

    def rerank(
        self, query: str, results: List[Dict[str, Any]], top_k: Optional[int] = None
    ) -> List[RerankResult]:
        """
        Rerank results using Turkish-optimized strategy
        """
        reranked = []

        for result in results:
            content = result.get("content") or result.get("text", "")
            original_score = result.get("score", 0.5)

            # Turkish relevance score
            turkish_score = self._calculate_turkish_relevance(query, content)

            # Combine with original
            combined_score = (original_score * 0.5) + (turkish_score * 0.5)

            reranked.append(
                RerankResult(
                    content=content,
                    score=combined_score,
                    original_score=original_score,
                    rerank_score=turkish_score,
                    metadata=result.get("metadata", {}),
                )
            )

        # Apply cross-encoder if available
        if self.cross_encoder and self.cross_encoder.model:
            # Convert to dict format for cross-encoder
            ce_input = [
                {"content": r.content, "score": r.score, "metadata": r.metadata}
                for r in reranked
            ]

            ce_results = self.cross_encoder.rerank(
                query,
                ce_input,
                top_k=None,
                combine_scores=True,
                weight=0.4,  # Give more weight to Turkish features
            )

            reranked = ce_results

        # Sort by score
        reranked.sort(key=lambda x: x.score, reverse=True)

        if top_k:
            reranked = reranked[:top_k]

        return reranked


# Global reranker instances
_cross_encoder_reranker: Optional[CrossEncoderReranker] = None
_turkish_reranker: Optional[TurkishOptimizedReranker] = None


def get_cross_encoder_reranker() -> CrossEncoderReranker:
    """Get or create global cross-encoder reranker"""
    global _cross_encoder_reranker
    if _cross_encoder_reranker is None:
        _cross_encoder_reranker = CrossEncoderReranker()
    return _cross_encoder_reranker


def get_turkish_reranker() -> TurkishOptimizedReranker:
    """Get or create global Turkish-optimized reranker"""
    global _turkish_reranker
    if _turkish_reranker is None:
        _turkish_reranker = TurkishOptimizedReranker()
    return _turkish_reranker


# Example usage
"""
from core.reranker import get_turkish_reranker

# Get reranker
reranker = get_turkish_reranker()

# Rerank search results
reranked = reranker.rerank(
    query="Pythagoras teoremi nedir?",
    results=search_results,
    top_k=5
)

for result in reranked:
    print(f"Score: {result.score:.3f} (orig: {result.original_score:.3f})")
    print(f"Content: {result.content[:100]}...")
"""
