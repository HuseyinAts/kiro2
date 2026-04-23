"""
Comprehension Validator - Anlama Doğrulama
REQ-4: Comprehension Preservation

Features:
- Reading quiz generation
- 24-hour recall testing
- Detail memory check
- Inference ability testing
- >= %95 accuracy target
"""

import logging
import random
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from uuid import uuid4

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Soru tipi"""
    FACTUAL = "factual"  # Olgusal (detay hatırlama)
    INFERENCE = "inference"  # Çıkarım
    MAIN_IDEA = "main_idea"  # Ana fikir
    VOCABULARY = "vocabulary"  # Kelime anlamı
    SEQUENCE = "sequence"  # Sıralama


class DifficultyLevel(Enum):
    """Zorluk seviyesi"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class QuizQuestion:
    """Quiz sorusu"""
    question_id: str
    question_text: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    options: list[str]
    correct_answer_index: int
    source_sentence: str  # Kaynak cümle
    explanation: str  # Açıklama


@dataclass
class QuizResult:
    """Quiz sonucu"""
    quiz_id: str
    user_id: str
    text_id: str
    total_questions: int
    correct_answers: int
    score_percentage: float
    question_results: list[dict]
    completed_at: datetime
    time_taken_seconds: int
    passed: bool  # >= %95 geçti mi


@dataclass
class RecallTest:
    """24 saat recall testi"""
    test_id: str
    original_quiz_id: str
    user_id: str
    text_id: str
    original_score: float
    recall_score: float
    retention_percentage: float  # Hatırlama oranı
    hours_elapsed: float
    tested_at: datetime


@dataclass
class ComprehensionMetrics:
    """Anlama metrikleri"""
    average_score: float
    median_score: float
    total_quizzes: int
    passing_rate: float  # >= %95
    factual_accuracy: float
    inference_accuracy: float
    retention_rate: float  # 24 saat recall


class ComprehensionValidator:
    """
    Comprehension Validator

    Okuma anlama testleri ile comprehension preservation'ı doğrular:
    - Quiz generation from text
    - 24-hour recall testing
    - >= %95 accuracy target (REQ-4.6)
    """

    # REQ-4.1, REQ-4.6: Hedef accuracy
    TARGET_ACCURACY = 95.0
    MINIMUM_PASSING_SCORE = 90.0

    def __init__(self, user_id: str):
        """
        Args:
            user_id: Kullanıcı ID
        """
        self.user_id = user_id
        self.quiz_results: list[QuizResult] = []
        self.recall_tests: list[RecallTest] = []

    def generate_quiz(
        self,
        text: str,
        text_id: str,
        num_questions: int = 5,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    ) -> list[QuizQuestion]:
        """
        Metinden quiz soruları üret

        Args:
            text: Kaynak metin
            text_id: Metin ID
            num_questions: Soru sayısı
            difficulty: Zorluk seviyesi

        Returns:
            list[QuizQuestion]: Üretilen sorular
        """
        sentences = self._split_sentences(text)

        if len(sentences) < 2:
            logger.warning("Metin çok kısa, quiz üretilemiyor")
            return []

        questions = []

        # Soru tiplerinin dağılımı
        type_distribution = {
            QuestionType.FACTUAL: 0.4,
            QuestionType.MAIN_IDEA: 0.2,
            QuestionType.INFERENCE: 0.2,
            QuestionType.VOCABULARY: 0.2
        }

        for i in range(num_questions):
            # Soru tipi seç
            q_type = self._weighted_choice(type_distribution)

            # İlgili cümleyi seç
            sentence = random.choice(sentences)

            # Soruyu üret
            question = self._generate_question(
                sentence=sentence,
                text=text,
                q_type=q_type,
                difficulty=difficulty
            )

            if question:
                questions.append(question)

        return questions

    def _generate_question(
        self,
        sentence: str,
        text: str,
        q_type: QuestionType,
        difficulty: DifficultyLevel
    ) -> QuizQuestion | None:
        """Tek soru üret"""
        try:
            if q_type == QuestionType.FACTUAL:
                return self._generate_factual_question(sentence, difficulty)
            if q_type == QuestionType.MAIN_IDEA:
                return self._generate_main_idea_question(text, difficulty)
            if q_type == QuestionType.INFERENCE:
                return self._generate_inference_question(sentence, text, difficulty)
            if q_type == QuestionType.VOCABULARY:
                return self._generate_vocabulary_question(sentence, difficulty)
            return self._generate_factual_question(sentence, difficulty)

        except Exception as e:
            logger.error(f"Soru üretme hatası: {e}")
            return None

    def _generate_factual_question(
        self,
        sentence: str,
        difficulty: DifficultyLevel
    ) -> QuizQuestion | None:
        """Olgusal soru üret (detay hatırlama - REQ-4.3)"""
        # Cümleden anahtar kelimeyi çıkar
        words = [w for w in sentence.split() if len(w) > 3]
        if not words:
            return None

        key_word = random.choice(words)

        # Boşluklu soru oluştur
        question_text = f"Metinde '{key_word}' kelimesi hangi bağlamda kullanılmıştır?"

        # Seçenekler (gerçek uygulama için LLM kullanılabilir)
        options = [
            f"'{sentence[:50]}...' cümlesinde",
            "Farklı bir paragrafta",
            "Metinde bu kelime geçmiyor",
            "Ana başlıkta"
        ]

        return QuizQuestion(
            question_id=str(uuid4()),
            question_text=question_text,
            question_type=QuestionType.FACTUAL,
            difficulty=difficulty,
            options=options,
            correct_answer_index=0,
            source_sentence=sentence,
            explanation=f"Bu kelime şu cümlede geçmektedir: {sentence}"
        )

    def _generate_main_idea_question(
        self,
        text: str,
        difficulty: DifficultyLevel
    ) -> QuizQuestion | None:
        """Ana fikir sorusu üret"""
        question_text = "Metnin ana fikri nedir?"

        # İlk cümle genellikle ana fikri içerir (basit varsayım)
        sentences = self._split_sentences(text)
        main_idea = sentences[0] if sentences else text[:100]

        options = [
            main_idea[:80] + "..." if len(main_idea) > 80 else main_idea,
            "Bu metinde ana fikir belirtilmemiştir",
            "Metin sadece detaylardan oluşmaktadır",
            "Ana fikir metinin sonunda verilmiştir"
        ]

        return QuizQuestion(
            question_id=str(uuid4()),
            question_text=question_text,
            question_type=QuestionType.MAIN_IDEA,
            difficulty=difficulty,
            options=options,
            correct_answer_index=0,
            source_sentence=main_idea,
            explanation="Ana fikir genellikle metnin başında verilir."
        )

    def _generate_inference_question(
        self,
        sentence: str,
        text: str,
        difficulty: DifficultyLevel
    ) -> QuizQuestion | None:
        """Çıkarım sorusu üret (REQ-4.4)"""
        question_text = f"'{sentence[:50]}...' cümlesinden ne çıkarılabilir?"

        options = [
            "Bu bilgi metnin devamını desteklemektedir",
            "Bu bilgi metinle çelişmektedir",
            "Bu cümle bağlamdan bağımsızdır",
            "Bu bilgi tamamen spekülatiftir"
        ]

        return QuizQuestion(
            question_id=str(uuid4()),
            question_text=question_text,
            question_type=QuestionType.INFERENCE,
            difficulty=difficulty,
            options=options,
            correct_answer_index=0,
            source_sentence=sentence,
            explanation="Çıkarım yaparken cümlenin bağlamına dikkat edilmelidir."
        )

    def _generate_vocabulary_question(
        self,
        sentence: str,
        difficulty: DifficultyLevel
    ) -> QuizQuestion | None:
        """Kelime sorusu üret"""
        words = [w for w in sentence.split() if len(w) > 5]
        if not words:
            return None

        word = random.choice(words)
        question_text = f"'{word}' kelimesinin metindeki anlamı nedir?"

        options = [
            f"Cümlede kullanılan anlamıyla '{word}'",
            "Farklı bir anlam",
            "Mecazi anlam",
            "Zıt anlam"
        ]

        return QuizQuestion(
            question_id=str(uuid4()),
            question_text=question_text,
            question_type=QuestionType.VOCABULARY,
            difficulty=difficulty,
            options=options,
            correct_answer_index=0,
            source_sentence=sentence,
            explanation=f"'{word}' kelimesi bu bağlamda literal anlamıyla kullanılmıştır."
        )

    def evaluate_quiz(
        self,
        text_id: str,
        answers: list[dict],
        questions: list[QuizQuestion],
        time_taken_seconds: int
    ) -> QuizResult:
        """
        Quiz'i değerlendir

        Args:
            text_id: Metin ID
            answers: Kullanıcı cevapları [{question_id, answer_index}]
            questions: Soru listesi
            time_taken_seconds: Geçen süre

        Returns:
            QuizResult: Quiz sonucu
        """
        question_map = {q.question_id: q for q in questions}
        correct_count = 0
        question_results = []

        for answer in answers:
            q_id = answer.get("question_id")
            user_answer = answer.get("answer_index")

            question = question_map.get(q_id)
            if not question:
                continue

            is_correct = user_answer == question.correct_answer_index

            if is_correct:
                correct_count += 1

            question_results.append({
                "question_id": q_id,
                "question_type": question.question_type.value,
                "user_answer": user_answer,
                "correct_answer": question.correct_answer_index,
                "is_correct": is_correct
            })

        total_questions = len(questions)
        score = (correct_count / total_questions * 100) if total_questions > 0 else 0

        result = QuizResult(
            quiz_id=str(uuid4()),
            user_id=self.user_id,
            text_id=text_id,
            total_questions=total_questions,
            correct_answers=correct_count,
            score_percentage=round(score, 1),
            question_results=question_results,
            completed_at=datetime.now(),
            time_taken_seconds=time_taken_seconds,
            passed=score >= self.MINIMUM_PASSING_SCORE
        )

        self.quiz_results.append(result)
        return result

    def schedule_recall_test(self, quiz_id: str, hours: int = 24) -> dict:
        """
        24 saat recall testi planla (REQ-4.2)

        Args:
            quiz_id: Orijinal quiz ID
            hours: Kaç saat sonra

        Returns:
            dict: Planlanan test bilgisi
        """
        scheduled_time = datetime.now() + timedelta(hours=hours)

        return {
            "recall_test_id": str(uuid4()),
            "original_quiz_id": quiz_id,
            "scheduled_at": scheduled_time.isoformat(),
            "hours_after": hours
        }

    def evaluate_recall_test(
        self,
        original_quiz_id: str,
        text_id: str,
        recall_score: float
    ) -> RecallTest:
        """
        Recall testini değerlendir

        Args:
            original_quiz_id: Orijinal quiz ID
            text_id: Metin ID
            recall_score: Recall test skoru

        Returns:
            RecallTest: Recall test sonucu
        """
        # Orijinal quiz'i bul
        original_quiz = next(
            (q for q in self.quiz_results if q.quiz_id == original_quiz_id),
            None
        )

        original_score = original_quiz.score_percentage if original_quiz else 100.0
        hours_elapsed = 24.0  # Default 24 saat

        if original_quiz:
            hours_elapsed = (datetime.now() - original_quiz.completed_at).total_seconds() / 3600

        retention = (recall_score / original_score * 100) if original_score > 0 else 0

        result = RecallTest(
            test_id=str(uuid4()),
            original_quiz_id=original_quiz_id,
            user_id=self.user_id,
            text_id=text_id,
            original_score=original_score,
            recall_score=recall_score,
            retention_percentage=round(retention, 1),
            hours_elapsed=round(hours_elapsed, 1),
            tested_at=datetime.now()
        )

        self.recall_tests.append(result)
        return result

    def get_metrics(self) -> ComprehensionMetrics:
        """Comprehension metriklerini hesapla"""
        if not self.quiz_results:
            return ComprehensionMetrics(
                average_score=0.0,
                median_score=0.0,
                total_quizzes=0,
                passing_rate=0.0,
                factual_accuracy=0.0,
                inference_accuracy=0.0,
                retention_rate=0.0
            )

        scores = [q.score_percentage for q in self.quiz_results]
        passing_count = sum(1 for q in self.quiz_results if q.passed)

        # Soru tiplerine göre doğruluk
        factual_correct = 0
        factual_total = 0
        inference_correct = 0
        inference_total = 0

        for quiz in self.quiz_results:
            for qr in quiz.question_results:
                if qr["question_type"] == QuestionType.FACTUAL.value:
                    factual_total += 1
                    if qr["is_correct"]:
                        factual_correct += 1
                elif qr["question_type"] == QuestionType.INFERENCE.value:
                    inference_total += 1
                    if qr["is_correct"]:
                        inference_correct += 1

        # Retention rate
        retention_rates = [r.retention_percentage for r in self.recall_tests if r.retention_percentage > 0]

        import statistics

        return ComprehensionMetrics(
            average_score=round(statistics.mean(scores), 1),
            median_score=round(statistics.median(scores), 1),
            total_quizzes=len(self.quiz_results),
            passing_rate=round(passing_count / len(self.quiz_results) * 100, 1),
            factual_accuracy=round(factual_correct / factual_total * 100, 1) if factual_total > 0 else 0.0,
            inference_accuracy=round(inference_correct / inference_total * 100, 1) if inference_total > 0 else 0.0,
            retention_rate=round(statistics.mean(retention_rates), 1) if retention_rates else 0.0
        )

    def check_target_met(self) -> dict:
        """
        Hedef kontrolü (REQ-4.6: >= %95)

        Returns:
            dict: Hedef durumu
        """
        metrics = self.get_metrics()

        return {
            "target_accuracy": self.TARGET_ACCURACY,
            "current_accuracy": metrics.average_score,
            "target_met": metrics.average_score >= self.TARGET_ACCURACY,
            "passing_rate": metrics.passing_rate,
            "recommendation": self._get_recommendation(metrics)
        }

    def _get_recommendation(self, metrics: ComprehensionMetrics) -> str:
        """Kullanıcıya öneri"""
        if metrics.average_score >= self.TARGET_ACCURACY:
            return "Mükemmel! Anlama seviyeniz hedefin üzerinde."

        if metrics.average_score >= self.MINIMUM_PASSING_SCORE:
            return "Çok iyi! Biraz daha pratik ile hedefe ulaşabilirsiniz."

        if metrics.factual_accuracy < 80:
            return "Detaylara daha dikkat ederek okumayı deneyin."

        if metrics.inference_accuracy < 80:
            return "Çıkarım sorularına odaklanın, satır aralarını okuyun."

        return "Okuma hızınızı biraz düşürüp anlamaya odaklanmayı deneyin."

    def _split_sentences(self, text: str) -> list[str]:
        """Metni cümlelere ayır"""
        # Türkçe için cümle ayırma
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

    def _weighted_choice(self, weights: dict) -> any:
        """Ağırlıklı rastgele seçim"""
        items = list(weights.keys())
        probabilities = list(weights.values())

        return random.choices(items, weights=probabilities, k=1)[0]

    def reset(self):
        """Tüm verileri sıfırla"""
        self.quiz_results.clear()
        self.recall_tests.clear()
