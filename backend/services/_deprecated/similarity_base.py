"""
Similarity Base Module - Shared Foundation for Question Similarity Services

This module provides common functionality for:
- duplicate_detection_service.py
- similar_question_service.py
- plagiarism_detection_service.py

Shared Features:
- Common embedding generation interface
- Cosine similarity calculation
- Threshold management
- Result dataclasses

Author: KIRO2 Team
Date: 2026-01-23
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol, TypeVar

import numpy as np

logger = logging.getLogger(__name__)

# Type variable for generic embedding
T = TypeVar("T")


# =============================================================================
# Common Enums
# =============================================================================


class SimilarityLevel(str, Enum):
    """Similarity level classification."""

    UNIQUE = "unique"  # No significant similarity
    LOW = "low"  # 0.50-0.75 similarity
    MODERATE = "moderate"  # 0.75-0.85 similarity
    HIGH = "high"  # 0.85-0.90 similarity
    VERY_HIGH = "very_high"  # 0.90-0.95 similarity
    DUPLICATE = "duplicate"  # 0.95-0.99 similarity
    EXACT_MATCH = "exact_match"  # >= 0.99 similarity


# =============================================================================
# Shared Threshold Configuration
# =============================================================================


@dataclass
class SimilarityThresholds:
    """
    Configurable similarity thresholds.

    Standard KIRO2 Platform thresholds:
    - exact_match: 0.99 (block completely)
    - duplicate: 0.95 (block, requires manual review)
    - near_duplicate: 0.90 (warn, allow with flag)
    - paraphrase: 0.85 (inform, allow)
    - similar: 0.75 (low priority flag)
    """

    exact_match: float = 0.99
    duplicate: float = 0.95
    near_duplicate: float = 0.90
    paraphrase: float = 0.85
    similar: float = 0.75

    def classify(self, similarity: float) -> SimilarityLevel:
        """Classify similarity score into level."""
        if similarity >= self.exact_match:
            return SimilarityLevel.EXACT_MATCH
        if similarity >= self.duplicate:
            return SimilarityLevel.DUPLICATE
        if similarity >= self.near_duplicate:
            return SimilarityLevel.VERY_HIGH
        if similarity >= self.paraphrase:
            return SimilarityLevel.HIGH
        if similarity >= self.similar:
            return SimilarityLevel.MODERATE
        if similarity >= 0.50:
            return SimilarityLevel.LOW
        return SimilarityLevel.UNIQUE

    def should_block(self, similarity: float) -> bool:
        """Check if similarity warrants blocking."""
        return similarity >= self.duplicate

    def needs_review(self, similarity: float) -> bool:
        """Check if similarity needs manual review."""
        return self.near_duplicate <= similarity < self.duplicate


# Default thresholds instance
DEFAULT_THRESHOLDS = SimilarityThresholds()


# =============================================================================
# Common Result Dataclasses
# =============================================================================


@dataclass
class SimilarItem:
    """A similar item found during similarity search."""

    id: str
    content_preview: str
    similarity: float
    metadata: dict = field(default_factory=dict)

    @property
    def similarity_percentage(self) -> float:
        """Get similarity as percentage."""
        return round(self.similarity * 100, 2)


@dataclass
class SimilarityCheckResult:
    """
    Unified result for all similarity checks.

    Works for duplicate detection, similar questions, and plagiarism.
    """

    # Core results
    level: SimilarityLevel
    similarity_score: float
    similar_items: list[SimilarItem] = field(default_factory=list)

    # Decision flags
    is_blocked: bool = False
    needs_review: bool = False
    is_safe: bool = True

    # Recommendations
    recommendation: str = ""
    action: str = "allow"  # "allow", "warn", "review", "block"

    # Metadata
    checked_at: datetime = field(default_factory=datetime.now)
    check_type: str = ""  # "duplicate", "plagiarism", "similarity"
    processing_time_ms: float = 0.0

    @property
    def top_match(self) -> SimilarItem | None:
        """Get the most similar item."""
        return self.similar_items[0] if self.similar_items else None

    @property
    def merge_candidates(self) -> list[str]:
        """Get IDs suitable for merging (>= near_duplicate)."""
        return [
            item.id
            for item in self.similar_items
            if item.similarity >= DEFAULT_THRESHOLDS.near_duplicate
        ]


# =============================================================================
# Embedding Provider Protocol
# =============================================================================


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers (ChromaDB, BERTurk, SentenceTransformer)."""

    def encode(self, text: str) -> np.ndarray:
        """Encode text to embedding vector."""
        ...

    def encode_batch(self, texts: list[str]) -> list[np.ndarray]:
        """Encode multiple texts to embedding vectors."""
        ...


# =============================================================================
# Common Similarity Calculator
# =============================================================================


class SimilarityCalculator:
    """
    Unified similarity calculation utility.

    Provides:
    - Cosine similarity
    - Euclidean distance
    - Batch similarity matrix
    """

    @staticmethod
    def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0.0 to 1.0)
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(np.clip(similarity, 0.0, 1.0))

    @staticmethod
    def euclidean_distance(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate Euclidean distance between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Distance (lower = more similar)
        """
        return float(np.linalg.norm(embedding1 - embedding2))

    @staticmethod
    def distance_to_similarity(distance: float) -> float:
        """
        Convert Euclidean distance to similarity score (0-1).

        Uses the formula: similarity = 1 / (1 + distance)
        """
        return 1.0 / (1.0 + distance)

    @classmethod
    def batch_cosine_similarity(
        cls, query_embedding: np.ndarray, candidate_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Calculate cosine similarity between query and multiple candidates.

        Args:
            query_embedding: Query vector (1D)
            candidate_embeddings: Matrix of candidate vectors (2D)

        Returns:
            Array of similarity scores
        """
        # Normalize vectors
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        candidate_norms = candidate_embeddings / np.linalg.norm(
            candidate_embeddings, axis=1, keepdims=True
        )

        # Dot product for cosine similarity
        similarities = np.dot(candidate_norms, query_norm)
        return np.clip(similarities, 0.0, 1.0)

    @classmethod
    def build_similarity_matrix(cls, embeddings: np.ndarray) -> np.ndarray:
        """
        Build a full similarity matrix for all embeddings.

        Args:
            embeddings: Matrix of embedding vectors (N x D)

        Returns:
            Similarity matrix (N x N)
        """
        try:
            from sklearn.metrics.pairwise import cosine_similarity

            return cosine_similarity(embeddings)
        except ImportError:
            # Fallback implementation
            n = embeddings.shape[0]
            matrix = np.zeros((n, n))
            for i in range(n):
                for j in range(i, n):
                    sim = cls.cosine_similarity(embeddings[i], embeddings[j])
                    matrix[i, j] = sim
                    matrix[j, i] = sim
            return matrix


# =============================================================================
# Base Similarity Service
# =============================================================================


class BaseSimilarityService(ABC):
    """
    Abstract base class for all similarity-based services.

    Subclasses should implement:
    - _get_embedding(): Generate embedding for content
    - _search_similar(): Find similar items in storage
    """

    def __init__(
        self,
        thresholds: SimilarityThresholds | None = None,
        service_name: str = "similarity",
    ):
        """
        Initialize base similarity service.

        Args:
            thresholds: Custom similarity thresholds
            service_name: Name for logging
        """
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.service_name = service_name
        self.calculator = SimilarityCalculator()
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the service (load models, connect to storage)."""

    @abstractmethod
    def _get_embedding(self, content: str) -> np.ndarray:
        """Generate embedding for content."""

    @abstractmethod
    async def _search_similar(
        self, embedding: np.ndarray, limit: int = 10
    ) -> list[tuple[str, dict, float]]:
        """
        Search for similar items in storage.

        Args:
            embedding: Query embedding
            limit: Maximum results

        Returns:
            List of (id, metadata, distance) tuples
        """

    async def check_similarity(
        self,
        content: str,
        limit: int = 10,
        custom_threshold: float | None = None,
    ) -> SimilarityCheckResult:
        """
        Check content for similar items.

        Args:
            content: Content to check
            limit: Maximum similar items to return
            custom_threshold: Override default threshold

        Returns:
            SimilarityCheckResult with findings
        """
        import time

        start_time = time.time()

        # Ensure initialized
        if not self._initialized:
            await self.initialize()

        # Generate embedding
        embedding = self._get_embedding(content)

        # Search for similar items
        results = await self._search_similar(embedding, limit)

        # Process results
        similar_items = []
        max_similarity = 0.0

        for item_id, metadata, distance in results:
            similarity = self.calculator.distance_to_similarity(distance)
            max_similarity = max(max_similarity, similarity)

            # Create preview
            content_preview = metadata.get("content", "")[:200]
            if len(metadata.get("content", "")) > 200:
                content_preview += "..."

            similar_items.append(
                SimilarItem(
                    id=item_id,
                    content_preview=content_preview,
                    similarity=round(similarity, 4),
                    metadata=metadata,
                )
            )

        # Classify and determine action
        level = self.thresholds.classify(max_similarity)
        is_blocked = self.thresholds.should_block(max_similarity)
        needs_review = self.thresholds.needs_review(max_similarity)

        # Generate recommendation
        recommendation = self._generate_recommendation(level, max_similarity)
        action = self._determine_action(level)

        processing_time = (time.time() - start_time) * 1000

        return SimilarityCheckResult(
            level=level,
            similarity_score=round(max_similarity, 4),
            similar_items=similar_items,
            is_blocked=is_blocked,
            needs_review=needs_review,
            is_safe=not is_blocked,
            recommendation=recommendation,
            action=action,
            check_type=self.service_name,
            processing_time_ms=round(processing_time, 2),
        )

    def _generate_recommendation(
        self, level: SimilarityLevel, similarity: float
    ) -> str:
        """Generate human-readable recommendation."""
        recommendations = {
            SimilarityLevel.EXACT_MATCH: f"ENGELLENDI: Tam eşleşme tespit edildi ({similarity:.2%} benzerlik).",
            SimilarityLevel.DUPLICATE: f"ENGELLENDI: Çok yüksek benzerlik ({similarity:.2%}). Manuel inceleme gerekli.",
            SimilarityLevel.VERY_HIGH: f"UYARI: Yüksek benzerlik ({similarity:.2%}). Ekleme yapılabilir ama inceleme önerilir.",
            SimilarityLevel.HIGH: f"BİLGİ: Anlamlı benzerlik ({similarity:.2%}). Muhtemelen paraphrase.",
            SimilarityLevel.MODERATE: f"BİLGİ: Orta düzeyde benzerlik ({similarity:.2%}).",
            SimilarityLevel.LOW: f"GÜVENLİ: Düşük benzerlik ({similarity:.2%}).",
            SimilarityLevel.UNIQUE: "GÜVENLİ: Benzersiz içerik.",
        }
        return recommendations.get(level, "Değerlendirme yapılamadı.")

    def _determine_action(self, level: SimilarityLevel) -> str:
        """Determine action based on similarity level."""
        actions = {
            SimilarityLevel.EXACT_MATCH: "block",
            SimilarityLevel.DUPLICATE: "block",
            SimilarityLevel.VERY_HIGH: "review",
            SimilarityLevel.HIGH: "warn",
            SimilarityLevel.MODERATE: "allow",
            SimilarityLevel.LOW: "allow",
            SimilarityLevel.UNIQUE: "allow",
        }
        return actions.get(level, "allow")


# =============================================================================
# Fallback Embedding Generator (Hash-based)
# =============================================================================


class FallbackEmbeddingGenerator:
    """
    Hash-based embedding generator for when ML models are unavailable.

    Uses SHA-256 hash to create deterministic 128-dimensional embeddings.
    Not semantically meaningful but useful for exact match detection.
    """

    @staticmethod
    def generate(text: str, dimension: int = 128) -> np.ndarray:
        """
        Generate hash-based embedding.

        Args:
            text: Input text
            dimension: Embedding dimension

        Returns:
            Normalized embedding vector
        """
        import hashlib

        hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()

        # Extend hash if needed
        while len(hash_bytes) < dimension:
            hash_bytes += hashlib.sha256(hash_bytes).digest()

        # Convert to float array and normalize
        embedding = np.array([float(b) / 255.0 for b in hash_bytes[:dimension]])
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding


# =============================================================================
# Utility Functions
# =============================================================================


def format_similarity_percentage(similarity: float) -> str:
    """Format similarity as percentage string."""
    return f"{similarity * 100:.1f}%"


def get_default_thresholds() -> SimilarityThresholds:
    """Get default similarity thresholds."""
    return DEFAULT_THRESHOLDS


def create_thresholds(
    exact_match: float = 0.99,
    duplicate: float = 0.95,
    near_duplicate: float = 0.90,
    paraphrase: float = 0.85,
    similar: float = 0.75,
) -> SimilarityThresholds:
    """Create custom similarity thresholds."""
    return SimilarityThresholds(
        exact_match=exact_match,
        duplicate=duplicate,
        near_duplicate=near_duplicate,
        paraphrase=paraphrase,
        similar=similar,
    )
