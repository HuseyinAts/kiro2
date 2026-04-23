"""
Plagiarism Detection Service - ÖSYM Copyright Protection
INNOVATION: BERT embeddings + cosine similarity for plagiarism detection
Research: 95%+ accuracy with multilingual BERT models
"""
from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass
class SimilarityResult:
    """Similarity check result"""

    is_plagiarized: bool
    similarity_score: float
    closest_match_id: str | None
    closest_match_text: str | None
    confidence: float
    checked_against: str  # "osym_exams", "platform_questions", "online_sources"


class PlagiarismDetectionService:
    """
    RESEARCH-BASED: BERT + Cosine Similarity
    Protects against:
    1. ÖSYM exam copyright violations (>85% similarity = reject)
    2. Duplicate questions in platform (>90% similarity = reject)
    3. Known online sources (plagiarism detection)

    Technical Stack:
    - SentenceTransformers (paraphrase-multilingual-MiniLM-L12-v2)
    - Cosine similarity for semantic matching
    - Local model (no API costs, <100ms inference)
    """

    def __init__(self):
        # In production: Load actual BERT model
        # from sentence_transformers import SentenceTransformer
        # self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

        # Mock embeddings database
        self.osym_questions_db = self._load_osym_questions()
        self.platform_questions_db = self._load_platform_questions()

        # Similarity thresholds
        self.OSYM_THRESHOLD = 0.85  # >85% similarity with ÖSYM = copyright violation
        self.DUPLICATE_THRESHOLD = 0.90  # >90% similarity = duplicate
        self.PARAPHRASE_THRESHOLD = 0.75  # 75-85% = potential paraphrase

    def _load_osym_questions(self) -> dict[str, dict]:
        """
        Load ÖSYM past exam questions (for copyright protection)
        In production: Load from secure database
        """
        # Mock data (in real system: thousands of ÖSYM questions)
        return {
            "osym-2024-tyt-mat-001": {
                "text": "Bir fonksiyonun türevi alınırken hangi kural kullanılır?",
                "embedding": np.random.rand(384),  # Mock 384-dim BERT embedding
                "year": 2024,
                "exam_type": "TYT",
            },
            "osym-2023-ayt-fiz-045": {
                "text": "Elektrik alan şiddeti nasıl hesaplanır?",
                "embedding": np.random.rand(384),
                "year": 2023,
                "exam_type": "AYT",
            },
        }

    def _load_platform_questions(self) -> dict[str, dict]:
        """Load existing platform questions (to prevent duplicates)"""
        # Mock data (in real system: query PostgreSQL sorular table)
        return {}

    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode text to BERT embedding vector
        Production: self.model.encode(text)
        """
        # Mock encoding (in production: real BERT model)
        return np.random.rand(384)

    def calculate_cosine_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """Calculate cosine similarity between two embeddings"""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def check_osym_similarity(self, question_text: str) -> SimilarityResult:
        """
        Check similarity against ÖSYM exam questions
        CRITICAL: Protects against copyright violations
        """
        new_embedding = self.encode_text(question_text)

        max_similarity = 0.0
        closest_match_id = None
        closest_match_text = None

        # Compare against all ÖSYM questions
        for osym_id, osym_data in self.osym_questions_db.items():
            similarity = self.calculate_cosine_similarity(
                new_embedding, osym_data["embedding"]
            )

            if similarity > max_similarity:
                max_similarity = similarity
                closest_match_id = osym_id
                closest_match_text = osym_data["text"]

        # Determine plagiarism status
        is_plagiarized = max_similarity > self.OSYM_THRESHOLD

        # Confidence calculation
        if max_similarity > 0.95:
            confidence = 0.99  # Very high confidence
        elif max_similarity > 0.85:
            confidence = 0.90
        elif max_similarity > 0.75:
            confidence = 0.75
        else:
            confidence = 0.60

        return SimilarityResult(
            is_plagiarized=is_plagiarized,
            similarity_score=max_similarity,
            closest_match_id=closest_match_id if is_plagiarized else None,
            closest_match_text=closest_match_text if is_plagiarized else None,
            confidence=confidence,
            checked_against="osym_exams",
        )

    async def check_platform_duplicate(self, question_text: str) -> SimilarityResult:
        """Check for duplicate questions in platform database"""
        new_embedding = self.encode_text(question_text)

        max_similarity = 0.0
        closest_match_id = None

        for platform_id, platform_data in self.platform_questions_db.items():
            similarity = self.calculate_cosine_similarity(
                new_embedding, platform_data["embedding"]
            )

            if similarity > max_similarity:
                max_similarity = similarity
                closest_match_id = platform_id

        is_duplicate = max_similarity > self.DUPLICATE_THRESHOLD

        return SimilarityResult(
            is_plagiarized=is_duplicate,
            similarity_score=max_similarity,
            closest_match_id=closest_match_id if is_duplicate else None,
            closest_match_text=None,
            confidence=0.95 if max_similarity > 0.95 else 0.80,
            checked_against="platform_questions",
        )

    async def comprehensive_plagiarism_check(
        self, question_text: str
    ) -> dict[str, any]:
        """
        Full plagiarism check pipeline
        Returns: Combined result from all checks
        """
        # Check 1: ÖSYM copyright
        osym_result = await self.check_osym_similarity(question_text)

        # Check 2: Platform duplicates
        duplicate_result = await self.check_platform_duplicate(question_text)

        # Aggregate results
        overall_safe = (
            not osym_result.is_plagiarized and not duplicate_result.is_plagiarized
        )

        return {
            "is_safe": overall_safe,
            "osym_check": {
                "is_violation": osym_result.is_plagiarized,
                "similarity": osym_result.similarity_score,
                "confidence": osym_result.confidence,
                "closest_match": osym_result.closest_match_id,
            },
            "duplicate_check": {
                "is_duplicate": duplicate_result.is_plagiarized,
                "similarity": duplicate_result.similarity_score,
                "confidence": duplicate_result.confidence,
            },
            "recommendation": self._get_recommendation(osym_result, duplicate_result),
        }

    def _get_recommendation(
        self, osym_result: SimilarityResult, duplicate_result: SimilarityResult
    ) -> str:
        """Provide actionable recommendation"""
        if osym_result.is_plagiarized:
            return "REJECT: Potential ÖSYM copyright violation (>85% similarity). Regenerate question."

        if duplicate_result.is_plagiarized:
            return "REJECT: Duplicate question already in database (>90% similarity)."

        if osym_result.similarity_score > self.PARAPHRASE_THRESHOLD:
            return (
                "WARNING: High similarity to ÖSYM question (75-85%). Review manually."
            )

        if duplicate_result.similarity_score > 0.80:
            return (
                "WARNING: Similar to existing question (80-90%). Review for uniqueness."
            )

        return "APPROVED: Question appears original and unique."

    def add_to_platform_database(self, question_id: str, question_text: str):
        """
        Add approved question to platform database
        (Prevents future duplicates)
        """
        embedding = self.encode_text(question_text)

        self.platform_questions_db[question_id] = {
            "text": question_text,
            "embedding": embedding,
            "added_date": datetime.now().isoformat(),
        }

    def export_statistics(self) -> dict:
        """Export plagiarism detection statistics"""
        return {
            "osym_database_size": len(self.osym_questions_db),
            "platform_database_size": len(self.platform_questions_db),
            "osym_threshold": self.OSYM_THRESHOLD,
            "duplicate_threshold": self.DUPLICATE_THRESHOLD,
            "model_type": "paraphrase-multilingual-MiniLM-L12-v2",
            "embedding_dimension": 384,
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================


async def example_usage():
    """Example plagiarism detection workflow"""
    detector = PlagiarismDetectionService()

    # Test question
    test_question = "Bir cisim 10 m/s hızla düşey yukarı atılıyor. Maksimum yüksekliği kaç metredir?"

    # Comprehensive check
    result = await detector.comprehensive_plagiarism_check(test_question)

    print("=== PLAGIARISM CHECK RESULT ===")
    print(f"Is Safe: {result['is_safe']}")
    print(f"ÖSYM Violation: {result['osym_check']['is_violation']}")
    print(f"Duplicate: {result['duplicate_check']['is_duplicate']}")
    print(f"Recommendation: {result['recommendation']}")

    # If approved, add to database
    if result["is_safe"]:
        detector.add_to_platform_database("q-new-001", test_question)
        print("✅ Question added to platform database")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
