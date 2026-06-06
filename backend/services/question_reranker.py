"""
Keyword-Based Question Reranker

Based on DEEP_RESEARCH_FINDINGS_2024.md:
- Wave 1 Quick Win: 3h effort, +15-25% improvement
- BM25-like keyword matching for topic relevance
- Fast, zero cost, explainable
"""

import re

from core.turkish_nlp_utils import normalize_tr


class KeywordQuestionReranker:
    """
    Lightweight keyword-based reranker for ÖSYM questions

    Uses TF-IDF inspired scoring to rank questions by topic relevance.
    Best for Turkish domain-specific terms like "türev", "limit", etc.

    Based on research: EMNLP 2024, Microsoft Azure AI
    """

    def __init__(self):
        # Default weights (tunable)
        self.weights = {
            "topic_keyword_match": 0.40,  # Primary: Does question contain topic keywords?
            "length_similarity": 0.25,  # Secondary: Similar length to target
            "keyword_density": 0.20,  # Tertiary: How many topic words appear?
            "year_recency": 0.15,  # Quaternary: Prefer recent ÖSYM questions
        }

        # Turkish stop words (common words to ignore)
        self.turkish_stopwords = {
            "bir",
            "bu",
            "ve",
            "ile",
            "için",
            "olan",
            "olarak",
            "de",
            "da",
            "mi",
            "mı",
            "mu",
            "mü",
            "ne",
            "nasıl",
            "neden",
            "hangi",
            "kaç",
            "gibi",
            "göre",
            "daha",
            "en",
            "çok",
            "az",
            "veya",
            "ama",
            "fakat",
            "ancak",
            "aşağıdaki",
            "yukarıdaki",
            "şekil",
            "tablo",
        }

    def extract_keywords(self, text: str) -> list[str]:
        """
        Extract meaningful keywords from Turkish text

        Steps:
        1. Lowercase
        2. Remove punctuation
        3. Split into words
        4. Remove stopwords
        5. Keep words >= 3 chars
        """
        # Lowercase (Turkish locale-safe) and remove punctuation
        text = normalize_tr(text)
        text = re.sub(r"[^\w\sğüşıöçĞÜŞİÖÇ]", " ", text)

        # Split and filter
        words = text.split()
        keywords = [
            word
            for word in words
            if len(word) >= 3 and word not in self.turkish_stopwords
        ]

        return keywords

    def calculate_keyword_match_score(self, question_text: str, topic: str) -> float:
        """
        Calculate how well question matches topic keywords

        Returns: 0.0 to 1.0
        """
        # Extract keywords from both
        topic_keywords = set(self.extract_keywords(topic))
        question_keywords = set(self.extract_keywords(question_text))

        if not topic_keywords:
            return 0.5  # Neutral if no topic keywords

        # Count matches
        matches = topic_keywords & question_keywords
        match_ratio = len(matches) / len(topic_keywords)

        return match_ratio

    def calculate_length_similarity_score(
        self, question_length: int, target_length: int
    ) -> float:
        """
        Calculate how similar question length is to target

        Returns: 0.0 to 1.0 (1.0 = exact match)
        """
        if target_length == 0:
            return 0.5

        # Calculate percentage difference
        diff_ratio = abs(question_length - target_length) / target_length

        # Convert to similarity (less difference = higher score)
        # If diff is 0% → score 1.0
        # If diff is 50% → score 0.5
        # If diff is 100% → score 0.0
        similarity = max(0.0, 1.0 - diff_ratio)

        return similarity

    def calculate_keyword_density_score(self, question_text: str, topic: str) -> float:
        """
        Calculate keyword density (how many times topic words appear)

        Returns: 0.0 to 1.0
        """
        topic_keywords = self.extract_keywords(topic)
        question_text_lower = normalize_tr(question_text)

        if not topic_keywords:
            return 0.5

        # Count occurrences
        total_occurrences = sum(
            question_text_lower.count(keyword) for keyword in topic_keywords
        )

        # Normalize by question length (chars)
        if len(question_text) == 0:
            return 0.0

        # Density = occurrences per 100 chars (capped at 1.0)
        density = min(1.0, (total_occurrences * 100) / len(question_text))

        return density

    def calculate_year_recency_score(
        self, year: int | None, current_year: int = 2025
    ) -> float:
        """
        Calculate recency score (prefer recent ÖSYM questions)

        Returns: 0.0 to 1.0
        """
        if year is None:
            return 0.5  # Neutral if year unknown

        # Score: 1.0 for last 3 years, decay for older
        years_ago = current_year - year

        if years_ago <= 3:
            return 1.0
        if years_ago <= 10:
            return 1.0 - ((years_ago - 3) * 0.1)  # Decay by 0.1 per year
        return 0.3  # Minimum score for very old questions

    def calculate_relevance_score(
        self, question: dict, topic: str, target_length: int
    ) -> float:
        """
        Calculate overall relevance score for a question

        Args:
            question: Dict with 'stem', 'subject', 'year'
            topic: Target topic (e.g., "Türev", "Limit")
            target_length: Target question length

        Returns:
            Relevance score (0.0 to 1.0)
        """
        stem = question.get("stem", "")
        year = question.get("year")

        # Calculate component scores
        keyword_match = self.calculate_keyword_match_score(stem, topic)
        length_sim = self.calculate_length_similarity_score(len(stem), target_length)
        keyword_density = self.calculate_keyword_density_score(stem, topic)
        year_recency = self.calculate_year_recency_score(year)

        # Weighted combination
        relevance_score = (
            self.weights["topic_keyword_match"] * keyword_match
            + self.weights["length_similarity"] * length_sim
            + self.weights["keyword_density"] * keyword_density
            + self.weights["year_recency"] * year_recency
        )

        return relevance_score

    def rerank(
        self, candidates: list[dict], topic: str, target_length: int, top_k: int = 3
    ) -> list[dict]:
        """
        Rerank candidate questions by relevance

        Args:
            candidates: List of question dicts
            topic: Target topic
            target_length: Target question length
            top_k: How many questions to return

        Returns:
            Top-k most relevant questions (sorted by score, descending)
        """
        if not candidates:
            return []

        # Score each candidate
        scored_candidates = []
        for candidate in candidates:
            score = self.calculate_relevance_score(candidate, topic, target_length)
            scored_candidates.append({"question": candidate, "relevance_score": score})

        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Return top-k questions
        top_questions = [item["question"] for item in scored_candidates[:top_k]]

        return top_questions

    def explain_ranking(self, question: dict, topic: str, target_length: int) -> dict:
        """
        Explain why a question received its score (for debugging)

        Returns:
            Dict with score breakdown
        """
        stem = question.get("stem", "")
        year = question.get("year")

        # Calculate component scores
        keyword_match = self.calculate_keyword_match_score(stem, topic)
        length_sim = self.calculate_length_similarity_score(len(stem), target_length)
        keyword_density = self.calculate_keyword_density_score(stem, topic)
        year_recency = self.calculate_year_recency_score(year)

        # Overall score
        total_score = (
            self.weights["topic_keyword_match"] * keyword_match
            + self.weights["length_similarity"] * length_sim
            + self.weights["keyword_density"] * keyword_density
            + self.weights["year_recency"] * year_recency
        )

        return {
            "total_score": round(total_score, 3),
            "breakdown": {
                "keyword_match": {
                    "score": round(keyword_match, 3),
                    "weight": self.weights["topic_keyword_match"],
                    "contribution": round(
                        keyword_match * self.weights["topic_keyword_match"], 3
                    ),
                },
                "length_similarity": {
                    "score": round(length_sim, 3),
                    "weight": self.weights["length_similarity"],
                    "contribution": round(
                        length_sim * self.weights["length_similarity"], 3
                    ),
                    "actual_length": len(stem),
                    "target_length": target_length,
                    "diff": len(stem) - target_length,
                },
                "keyword_density": {
                    "score": round(keyword_density, 3),
                    "weight": self.weights["keyword_density"],
                    "contribution": round(
                        keyword_density * self.weights["keyword_density"], 3
                    ),
                },
                "year_recency": {
                    "score": round(year_recency, 3),
                    "weight": self.weights["year_recency"],
                    "contribution": round(
                        year_recency * self.weights["year_recency"], 3
                    ),
                    "year": year,
                },
            },
            "question_id": question.get("question_id", "unknown"),
            "stem_preview": stem[:100] + "..." if len(stem) > 100 else stem,
        }


# Usage example
if __name__ == "__main__":
    # Example usage
    reranker = KeywordQuestionReranker()

    # Mock questions
    questions = [
        {
            "question_id": "q1",
            "stem": "f(x) = x² + 2x fonksiyonunun türevi kaçtır?",
            "subject": "Matematik",
            "year": 2023,
        },
        {
            "question_id": "q2",
            "stem": "Limit kavramı ile ilgili olan ifade hangisidir?",
            "subject": "Matematik",
            "year": 2020,
        },
        {
            "question_id": "q3",
            "stem": "y = 3x + 5 doğrusunun türevi nedir? Bu fonksiyonun x = 2 noktasındaki değişim hızı kaçtır?",
            "subject": "Matematik",
            "year": 2024,
        },
    ]

    # Rerank for "Türev" topic
    top_questions = reranker.rerank(
        candidates=questions, topic="Türev fonksiyonları", target_length=388, top_k=3
    )

    print("=== RERANKING RESULTS ===\n")
    for i, q in enumerate(top_questions, 1):
        explanation = reranker.explain_ranking(q, "Türev fonksiyonları", 388)
        print(f"{i}. Score: {explanation['total_score']}")
        print(f"   Question: {q['question_id']} ({q['year']})")
        print(f"   Preview: {explanation['stem_preview']}")
        print(
            f"   Breakdown: Keyword={explanation['breakdown']['keyword_match']['contribution']:.3f}, "
            f"Length={explanation['breakdown']['length_similarity']['contribution']:.3f}, "
            f"Density={explanation['breakdown']['keyword_density']['contribution']:.3f}, "
            f"Recency={explanation['breakdown']['year_recency']['contribution']:.3f}"
        )
        print()
