"""
OSYM Question Quality Scorer
Comprehensive quality assessment for OSYM questions

Author: KIRO AI Team
Date: 2025-10-19
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from services.quality.metrics import QualityMetrics


@dataclass
class QualityScore:
    """Quality score breakdown"""

    total_score: float  # 0-100
    format_compliance: float  # 0-20
    language_quality: float  # 0-20
    distractor_quality: float  # 0-20
    topic_relevance: float  # 0-20
    difficulty_appropriate: float  # 0-20
    feedback: List[str]
    improvements: List[str]


class OSYMQualityScorer:
    """
    OSYM Question Quality Scorer

    Evaluates questions on:
    1. Format compliance (OSYM standards)
    2. Language quality (Turkish grammar, clarity)
    3. Distractor quality (plausibility, diversity)
    4. Topic relevance
    5. Difficulty appropriateness
    """

    def __init__(self):
        """Initialize quality scorer"""
        self.metrics = QualityMetrics()

    def score_question(
        self,
        question_stem: str,
        options: List[str],
        correct_answer_index: int,
        topic: str,
        difficulty_target: float,
        exam_type: str = "TYT",
        reference_questions: Optional[List[str]] = None,
    ) -> QualityScore:
        """
        Score OSYM question quality

        Args:
            question_stem: Question text
            options: List of 5 options (A-E)
            correct_answer_index: Index of correct answer (0-4)
            topic: Question topic
            difficulty_target: Target difficulty (0-1)
            exam_type: TYT/AYT/YDT
            reference_questions: Reference questions for comparison

        Returns:
            Quality score breakdown
        """
        feedback = []
        improvements = []

        # 1. Format Compliance (0-20)
        format_score, format_feedback = self._score_format_compliance(
            question_stem, options, exam_type
        )
        feedback.extend(format_feedback)

        # 2. Language Quality (0-20)
        language_score, language_feedback = self._score_language_quality(
            question_stem, options
        )
        feedback.extend(language_feedback)

        # 3. Distractor Quality (0-20)
        distractor_score, distractor_feedback = self._score_distractor_quality(
            options, correct_answer_index
        )
        feedback.extend(distractor_feedback)

        # 4. Topic Relevance (0-20)
        relevance_score, relevance_feedback = self._score_topic_relevance(
            question_stem, topic
        )
        feedback.extend(relevance_feedback)

        # 5. Difficulty Appropriateness (0-20)
        difficulty_score, difficulty_feedback = self._score_difficulty(
            question_stem, options, difficulty_target
        )
        feedback.extend(difficulty_feedback)

        # Generate improvements
        improvements = self._generate_improvements(
            format_score,
            language_score,
            distractor_score,
            relevance_score,
            difficulty_score,
        )

        # Total score
        total = (
            format_score
            + language_score
            + distractor_score
            + relevance_score
            + difficulty_score
        )

        return QualityScore(
            total_score=total,
            format_compliance=format_score,
            language_quality=language_score,
            distractor_quality=distractor_score,
            topic_relevance=relevance_score,
            difficulty_appropriate=difficulty_score,
            feedback=feedback,
            improvements=improvements,
        )

    def _score_format_compliance(
        self, question_stem: str, options: List[str], exam_type: str
    ) -> tuple[float, List[str]]:
        """
        Score format compliance (0-20)

        OSYM format requirements:
        - Clear question stem
        - 5 options (A-E)
        - Proper Turkish punctuation
        - Appropriate length
        """
        score = 20.0
        feedback = []

        # Check number of options
        if len(options) != 5:
            score -= 5
            feedback.append(f"OSYM soruları 5 şık içermeli (mevcut: {len(options)})")

        # Check question stem length (50-500 characters ideal)
        stem_length = len(question_stem)
        if stem_length < 20:
            score -= 3
            feedback.append("Soru metni çok kısa")
        elif stem_length > 1000:
            score -= 2
            feedback.append("Soru metni çok uzun")

        # Check if question ends with question mark
        if not question_stem.strip().endswith("?"):
            score -= 2
            feedback.append("Soru soru işareti ile bitmeli")

        # Check option format (should start with letters or numbers)
        for i, option in enumerate(options):
            if len(option.strip()) < 2:
                score -= 1
                feedback.append(f"Şık {chr(65+i)} çok kısa")

        # Check Turkish characters (ş, ğ, ü, ö, ç, İ)
        turkish_chars = set("şğüöçıİŞĞÜÖÇ")
        has_turkish = any(
            char in turkish_chars for char in question_stem + " ".join(options)
        )

        if score == 20.0:
            feedback.append("Format OSYM standartlarına uygun")

        return score, feedback

    def _score_language_quality(
        self, question_stem: str, options: List[str]
    ) -> tuple[float, List[str]]:
        """
        Score language quality (0-20)

        Checks:
        - Turkish grammar
        - Clarity
        - No ambiguity
        - Professional terminology
        """
        score = 20.0
        feedback = []

        full_text = question_stem + " " + " ".join(options)

        # Check for common Turkish grammar mistakes
        # (Simplified - would use Zemberek in production)

        # Check sentence structure
        sentences = re.split(r"[.!?]", question_stem)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Avoid very long sentences
        for sentence in sentences:
            if len(sentence) > 200:
                score -= 2
                feedback.append("Bazı cümleler çok uzun, anlaşılırlık azalabilir")
                break

        # Check for common clarity issues
        ambiguous_words = ["bazı", "çoğu", "birçok", "genellikle", "bazen"]
        ambiguity_count = sum(word in full_text.lower() for word in ambiguous_words)
        if ambiguity_count > 3:
            score -= 3
            feedback.append("Belirsiz ifadeler azaltılmalı")

        # Check capitalization
        if question_stem[0].islower():
            score -= 1
            feedback.append("Soru büyük harfle başlamalı")

        # Check for spelling patterns (simplified)
        # Would use Zemberek spell checker in production

        if score >= 18:
            feedback.append("Dil kalitesi yüksek")
        elif score >= 15:
            feedback.append("Dil kalitesi orta seviye")
        else:
            feedback.append("Dil kalitesi geliştirilmeli")

        return score, feedback

    def _score_distractor_quality(
        self, options: List[str], correct_answer_index: int
    ) -> tuple[float, List[str]]:
        """
        Score distractor quality (0-20)

        Good distractors:
        - Plausible (look correct)
        - Different from each other
        - Similar length to correct answer
        - Not obviously wrong
        """
        score = 20.0
        feedback = []

        correct_answer = options[correct_answer_index]
        distractors = [
            opt for i, opt in enumerate(options) if i != correct_answer_index
        ]

        # Check length similarity
        correct_length = len(correct_answer)
        distractor_lengths = [len(d) for d in distractors]

        length_variance = np.var(distractor_lengths + [correct_length])
        if length_variance > 500:  # High variance
            score -= 3
            feedback.append("Şık uzunlukları çok farklı (ipucu olabilir)")

        # Check for identical distractors
        if len(distractors) != len(set(distractors)):
            score -= 5
            feedback.append("Bazı çeldiriciler aynı (kabul edilemez)")

        # Check for very similar distractors
        for i in range(len(distractors)):
            for j in range(i + 1, len(distractors)):
                similarity = self._text_similarity(distractors[i], distractors[j])
                if similarity > 0.9:
                    score -= 2
                    feedback.append(f"Şık {chr(65+i)} ve {chr(65+j)} çok benzer")

        # Check for obvious patterns
        # (e.g., all numbers, all "Yukarıdakilerden hiçbiri")
        none_of_above = ["hiçbiri", "hepsi yanlış", "cevap yok"]
        if any(pattern in " ".join(distractors).lower() for pattern in none_of_above):
            if (
                len(
                    [
                        d
                        for d in distractors
                        if any(p in d.lower() for p in none_of_above)
                    ]
                )
                > 1
            ):
                score -= 3
                feedback.append("Birden fazla 'hiçbiri' tipi şık var")

        if score >= 17:
            feedback.append("Çeldiriciler kaliteli ve çeşitli")
        elif score >= 13:
            feedback.append("Çeldiriciler kabul edilebilir")
        else:
            feedback.append("Çeldiriciler geliştirilmeli")

        return score, feedback

    def _score_topic_relevance(
        self, question_stem: str, topic: str
    ) -> tuple[float, List[str]]:
        """
        Score topic relevance (0-20)

        Checks if question is relevant to stated topic
        """
        score = 20.0
        feedback = []

        # Simple keyword matching (would use embeddings in production)
        topic_keywords = topic.lower().split()

        # Check if topic keywords appear in question
        matches = sum(
            1 for keyword in topic_keywords if keyword in question_stem.lower()
        )

        relevance_ratio = matches / len(topic_keywords) if topic_keywords else 0

        if relevance_ratio < 0.3:
            score -= 8
            feedback.append(f"Soru '{topic}' konusuyla ilgisiz görünüyor")
        elif relevance_ratio < 0.5:
            score -= 4
            feedback.append(f"Soru '{topic}' konusuyla kısmen ilgili")
        else:
            feedback.append(f"Soru '{topic}' konusuyla uyumlu")

        return score, feedback

    def _score_difficulty(
        self, question_stem: str, options: List[str], target_difficulty: float
    ) -> tuple[float, List[str]]:
        """
        Score difficulty appropriateness (0-20)

        Estimates difficulty and compares to target
        """
        score = 20.0
        feedback = []

        # Estimate difficulty based on heuristics
        estimated_difficulty = self._estimate_difficulty(question_stem, options)

        # Compare to target
        difficulty_diff = abs(estimated_difficulty - target_difficulty)

        if difficulty_diff < 0.1:
            feedback.append(
                f"Zorluk hedefle mükemmel uyumlu ({estimated_difficulty:.2f} vs {target_difficulty:.2f})"
            )
        elif difficulty_diff < 0.2:
            score -= 3
            feedback.append(
                f"Zorluk hedefle uyumlu ({estimated_difficulty:.2f} vs {target_difficulty:.2f})"
            )
        elif difficulty_diff < 0.3:
            score -= 6
            feedback.append(
                f"Zorluk hedeften biraz farklı ({estimated_difficulty:.2f} vs {target_difficulty:.2f})"
            )
        else:
            score -= 10
            feedback.append(
                f"Zorluk hedefle uyumsuz ({estimated_difficulty:.2f} vs {target_difficulty:.2f})"
            )

        return score, feedback

    def _estimate_difficulty(self, question_stem: str, options: List[str]) -> float:
        """
        Estimate question difficulty (0-1)

        Based on:
        - Question length
        - Vocabulary complexity
        - Number of steps required
        """
        # Length factor (longer questions often harder)
        length_score = min(1.0, len(question_stem) / 300)

        # Multi-step indicator
        multi_step_keywords = [
            "önce",
            "sonra",
            "ardından",
            "daha sonra",
            "ilk",
            "ikinci",
        ]
        multi_step_count = sum(
            1 for kw in multi_step_keywords if kw in question_stem.lower()
        )
        step_score = min(1.0, multi_step_count / 3)

        # Complexity keywords
        complex_keywords = [
            "analiz",
            "sentez",
            "değerlendirme",
            "karşılaştırma",
            "yorumlama",
        ]
        complexity_count = sum(
            1 for kw in complex_keywords if kw in question_stem.lower()
        )
        complexity_score = min(1.0, complexity_count / 2)

        # Weighted average
        difficulty = 0.3 * length_score + 0.3 * step_score + 0.4 * complexity_score

        # Adjust to 0.2-0.8 range (avoid extremes)
        difficulty = 0.2 + (difficulty * 0.6)

        return difficulty

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity (Jaccard)"""
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _generate_improvements(
        self,
        format_score: float,
        language_score: float,
        distractor_score: float,
        relevance_score: float,
        difficulty_score: float,
    ) -> List[str]:
        """Generate improvement suggestions"""
        improvements = []

        if format_score < 18:
            improvements.append("OSYM format standartlarını gözden geçirin")

        if language_score < 15:
            improvements.append(
                "Dil kalitesini artırın: cümleleri kısaltın, netleştirin"
            )

        if distractor_score < 15:
            improvements.append(
                "Çeldiricileri geliştirin: daha akla yatkın ve çeşitli yapın"
            )

        if relevance_score < 15:
            improvements.append("Soruyu konu ile daha ilgili hale getirin")

        if difficulty_score < 15:
            improvements.append("Zorluk seviyesini ayarlayın")

        if not improvements:
            improvements.append(
                "Soru yüksek kalitede, küçük iyileştirmeler yapılabilir"
            )

        return improvements


# Import numpy for calculations
import numpy as np
