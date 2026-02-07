"""
YZ Çalışma Arkadaşı ve Sınav Ustası Ajanı
Teknofest 2025 - Eğitim Eylemci Projesi

Bu ajan:
- Bilgi kartları (flashcard) oluşturur
- Kavramsal sorular sorar
- Yanlış cevaplar için açıklamalar sunar
- Adaptif sınavlar oluşturur
- Özetler çıkarır
"""

import asyncio
import json
import logging
import os
import random

# Core services
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.llm_service import llm_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Soru tipleri"""

    MULTIPLE_CHOICE = "multiple_choice"  # Çoktan seçmeli
    TRUE_FALSE = "true_false"  # Doğru/Yanlış
    FILL_BLANK = "fill_blank"  # Boşluk doldurma
    SHORT_ANSWER = "short_answer"  # Kısa cevap
    ESSAY = "essay"  # Açık uçlu
    MATCHING = "matching"  # Eşleştirme
    OPEN_ENDED = "open_ended"  # Açık uçlu (alternatif)


class DifficultyLevel(Enum):
    """Zorluk seviyeleri"""

    EASY = "easy"  # Kolay
    MEDIUM = "medium"  # Orta
    HARD = "hard"  # Zor
    EXPERT = "expert"  # Uzman


@dataclass
class Flashcard:
    """Bilgi kartı"""

    card_id: str
    front: str  # Ön yüz (soru/terim)
    back: str  # Arka yüz (cevap/açıklama)
    category: str
    difficulty: DifficultyLevel
    tags: List[str]
    review_count: int = 0  # Tekrar sayısı
    success_rate: float = 0.0  # Başarı oranı
    last_reviewed: Optional[datetime] = None  # Son tekrar tarihi
    next_review: Optional[datetime] = None  # Sonraki tekrar tarihi
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Question:
    """Soru"""

    question_id: str
    question_type: QuestionType
    question_text: str
    correct_answer: str
    explanation: str  # Açıklama
    difficulty: DifficultyLevel
    subject: str
    topic: str
    points: int
    options: Optional[List[str]] = None  # Seçenekler (çoktan seçmeli için)
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Quiz:
    """Sınav/Quiz"""

    quiz_id: str
    title: str
    description: str
    questions: List[Question]
    total_points: int
    time_limit: Optional[int]  # Dakika
    difficulty: DifficultyLevel
    adaptive: bool  # Adaptif mi?
    metadata: Dict[str, Any]


@dataclass
class StudentPerformance:
    """Öğrenci performansı"""

    student_id: str
    quiz_id: str = ""
    answers: Dict[str, str] = None  # {question_id: answer}
    scores: Dict[str, float] = None  # {question_id: score}
    total_score: float = 0.0
    percentage: float = 0.0
    time_spent: int = 0  # Saniye
    completed_at: datetime = None
    feedback: str = ""
    total_questions: int = 0  # Toplam soru sayısı
    correct_answers: int = 0  # Doğru cevap sayısı
    incorrect_answers: int = 0  # Yanlış cevap sayısı
    streak: int = 0  # Ardışık doğru sayısı
    topics_covered: Optional[Any] = None  # Kapsanan konular (dict or list)
    difficulty_performance: Optional[Dict[str, float]] = None  # Zorluk performansı
    last_updated: Optional[datetime] = None  # Son güncelleme
    metadata: Dict[str, Any] = None


class StudyBuddyAgent:
    """YZ Çalışma Arkadaşı ve Sınav Ustası Ajanı"""

    def __init__(self):
        self.flashcards = {}  # Flashcard cache
        self.questions = {}  # Soru bankası
        self.question_bank = {}  # Soru bankası (alternatif)
        self.quizzes = {}  # Sınavlar
        self.performances = {}  # Performans kayıtları
        self.student_performances = {}  # Öğrenci performansları
        self.adaptive_state = {}  # Adaptif sınav durumları

    async def generate_flashcards(
        self,
        content: str,
        count: int = 10,
        difficulty: Optional[DifficultyLevel] = None,
    ) -> List[Flashcard]:
        """
        İçerikten bilgi kartları oluştur

        Args:
            content: Kaynak içerik
            count: Kart sayısı
            difficulty: Zorluk seviyesi

        Returns:
            Flashcard listesi
        """
        try:
            # LLM ile flashcard oluştur
            prompt = f"""
            Aşağıdaki içerikten {count} adet bilgi kartı (flashcard) oluştur.
            Her kart için:
            - Ön yüz: Soru veya terim
            - Arka yüz: Cevap veya açıklama
            
            İçerik:
            {content[:2000]}  # İlk 2000 karakter
            
            JSON formatında yanıtla:
            {{
                "flashcards": [
                    {{
                        "front": "Soru/terim",
                        "back": "Cevap/açıklama",
                        "category": "Kategori",
                        "tags": ["etiket1", "etiket2"]
                    }}
                ]
            }}
            """

            result = await llm_service.generate_for_education(
                task_type="flashcard_generation",
                content=content,
                parameters={"count": count},
            )

            flashcards = []
            if result["success"]:
                try:
                    data = json.loads(result["content"])
                    for i, card_data in enumerate(data.get("flashcards", [])):
                        flashcard = Flashcard(
                            card_id=f"card_{datetime.now().timestamp()}_{i}",
                            front=card_data.get("front", ""),
                            back=card_data.get("back", ""),
                            category=card_data.get("category", "Genel"),
                            difficulty=difficulty or DifficultyLevel.MEDIUM,
                            tags=card_data.get("tags", []),
                            metadata={"source": "generated"},
                        )
                        flashcards.append(flashcard)
                        self.flashcards[flashcard.card_id] = flashcard
                except Exception as e:
                    logger.error(f"Flashcard parsing error: {str(e)}")

            # Yeterli kart oluşturulamazsa basit kartlar ekle
            while len(flashcards) < count:
                # İçerikten rastgele cümleler al
                sentences = content.split(". ")
                if sentences:
                    sentence = random.choice(sentences)
                    words = sentence.split()
                    if len(words) > 3:
                        # Basit bir soru-cevap oluştur
                        key_word = random.choice(words[1:-1])
                        flashcard = Flashcard(
                            card_id=f"card_{datetime.now().timestamp()}_{len(flashcards)}",
                            front=sentence.replace(key_word, "___"),
                            back=key_word,
                            category="Boşluk Doldurma",
                            difficulty=DifficultyLevel.EASY,
                            tags=["otomatik"],
                            metadata={"source": "simple"},
                        )
                        flashcards.append(flashcard)
                        self.flashcards[flashcard.card_id] = flashcard
                else:
                    break

            logger.info(f"Generated {len(flashcards)} flashcards")
            return flashcards[:count]

        except Exception as e:
            logger.error(f"Generate flashcards error: {str(e)}")
            return []

    async def generate_questions(
        self,
        content: str,
        question_types: List[QuestionType],
        count: int = 5,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        subject: str = "Genel",
        topic: str = "",
        language: str = "tr",
    ) -> List[Question]:
        """
        İçerikten soru oluştur

        Args:
            content: Kaynak içerik
            question_types: Soru tipleri
            count: Soru sayısı
            difficulty: Zorluk seviyesi
            subject: Ders
            topic: Konu

        Returns:
            Soru listesi
        """
        try:
            # Soru tiplerini string'e çevir
            types_str = ", ".join([qt.value for qt in question_types])

            # Dil ayarları
            lang_prompts = {
                "tr": "Aşağıdaki içerikten Türkçe {count} adet soru oluştur.",
                "en": "Generate {count} questions in English from the following content.",
            }

            # LLM ile soru oluştur
            prompt = f"""
            {lang_prompts.get(language, lang_prompts['tr']).format(count=count)}
            Soru tipleri: {types_str}
            Zorluk: {difficulty.value}
            Ders: {subject}
            Konu: {topic}
            Dil: {language.upper()}
            
            İçerik:
            {content[:2000]}
            
            Her soru için:
            1. Soru metni
            2. Tip (multiple_choice, true_false, fill_blank, short_answer)
            3. Seçenekler (çoktan seçmeli için 4 şık)
            4. Doğru cevap
            5. Açıklama
            
            JSON formatında yanıtla:
            {{
                "questions": [
                    {{
                        "type": "multiple_choice",
                        "text": "Soru metni",
                        "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
                        "correct": "A",
                        "explanation": "Açıklama"
                    }}
                ]
            }}
            """

            result = await llm_service.generate_for_education(
                task_type="question_generation",
                content=content,
                parameters={
                    "count": count,
                    "types": types_str,
                    "difficulty": difficulty.value,
                },
            )

            questions = []
            if result["success"]:
                try:
                    data = json.loads(result["content"])
                    for i, q_data in enumerate(data.get("questions", [])):
                        question = Question(
                            question_id=f"q_{datetime.now().timestamp()}_{i}",
                            question_type=QuestionType(
                                q_data.get("type", "multiple_choice")
                            ),
                            question_text=q_data.get("text", ""),
                            options=q_data.get("options"),
                            correct_answer=q_data.get("correct", ""),
                            explanation=q_data.get("explanation", ""),
                            difficulty=difficulty,
                            subject=subject,
                            topic=topic,
                            points=self._calculate_points(difficulty),
                            metadata={"source": "generated"},
                        )
                        questions.append(question)
                        self.questions[question.question_id] = question
                except Exception as e:
                    logger.error(f"Question parsing error: {str(e)}")

            logger.info(f"Generated {len(questions)} questions")
            return questions

        except Exception as e:
            logger.error(f"Generate questions error: {str(e)}")
            return []

    def _calculate_points(self, difficulty: DifficultyLevel) -> int:
        """Zorluk seviyesine göre puan hesapla"""
        points_map = {
            DifficultyLevel.EASY: 5,
            DifficultyLevel.MEDIUM: 10,
            DifficultyLevel.HARD: 15,
            DifficultyLevel.EXPERT: 20,
        }
        return points_map.get(difficulty, 10)

    async def create_quiz(
        self,
        title: str,
        content: str,
        question_count: int = 10,
        time_limit: Optional[int] = None,
        adaptive: bool = False,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
    ) -> Quiz:
        """
        Sınav/Quiz oluştur

        Args:
            title: Sınav başlığı
            content: İçerik
            question_count: Soru sayısı
            time_limit: Süre limiti (dakika)
            adaptive: Adaptif mi?
            difficulty: Başlangıç zorluk seviyesi

        Returns:
            Quiz objesi
        """
        try:
            # Farklı tipte sorular oluştur
            question_types = [
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.TRUE_FALSE,
                QuestionType.FILL_BLANK,
            ]

            # Soruları oluştur
            questions = await self.generate_questions(
                content=content,
                question_types=question_types,
                count=question_count,
                difficulty=difficulty,
            )

            # Quiz oluştur
            quiz_id = f"quiz_{datetime.now().timestamp()}"
            quiz = Quiz(
                quiz_id=quiz_id,
                title=title,
                description=f"{question_count} soruluk {difficulty.value} seviye sınav",
                questions=questions,
                total_points=sum([q.points for q in questions]),
                time_limit=time_limit,
                difficulty=difficulty,
                adaptive=adaptive,
                metadata={
                    "created_at": datetime.now().isoformat(),
                    "content_length": len(content),
                    "source": "generated",
                },
            )

            # Cache'e kaydet
            self.quizzes[quiz_id] = quiz

            # Adaptif sınav için başlangıç durumu
            if adaptive:
                self.adaptive_state[quiz_id] = {
                    "current_difficulty": difficulty,
                    "question_pool": questions.copy(),
                    "asked_questions": [],
                    "performance_history": [],
                }

            logger.info(f"Quiz created: {quiz_id}")
            return quiz

        except Exception as e:
            logger.error(f"Create quiz error: {str(e)}")
            raise

    async def evaluate_answer(
        self, question: Question, student_answer: str
    ) -> Tuple[float, str]:
        """
        Cevabı değerlendir

        Args:
            question: Soru
            student_answer: Öğrenci cevabı

        Returns:
            (Puan, Geri bildirim)
        """
        try:
            # Soru tipine göre değerlendirme
            if question.question_type == QuestionType.MULTIPLE_CHOICE:
                # Çoktan seçmeli - tam eşleşme
                if student_answer.upper() == question.correct_answer.upper():
                    return (question.points, "[CHECK] Doğru! " + question.explanation)
                else:
                    return (
                        0,
                        f"[X] Yanlış. Doğru cevap: {question.correct_answer}\n{question.explanation}",
                    )

            elif question.question_type == QuestionType.TRUE_FALSE:
                # Doğru/Yanlış
                student_bool = student_answer.lower() in ["doğru", "true", "d", "evet"]
                correct_bool = question.correct_answer.lower() in [
                    "doğru",
                    "true",
                    "d",
                    "evet",
                ]
                if student_bool == correct_bool:
                    return (question.points, "[CHECK] Doğru! " + question.explanation)
                else:
                    return (0, f"[X] Yanlış. {question.explanation}")

            elif question.question_type == QuestionType.FILL_BLANK:
                # Boşluk doldurma - benzerlik kontrolü
                if (
                    student_answer.lower().strip()
                    == question.correct_answer.lower().strip()
                ):
                    return (question.points, "[CHECK] Doğru! " + question.explanation)
                else:
                    # Kısmi puan verebiliriz
                    similarity = self._calculate_similarity(
                        student_answer, question.correct_answer
                    )
                    if similarity > 0.8:
                        partial_points = question.points * similarity
                        return (
                            partial_points,
                            f"⚠️ Kısmen doğru ({partial_points:.1f} puan). Tam cevap: {question.correct_answer}",
                        )
                    else:
                        return (
                            0,
                            f"[X] Yanlış. Doğru cevap: {question.correct_answer}\n{question.explanation}",
                        )

            else:
                # Kısa cevap veya essay - LLM ile değerlendirme
                eval_prompt = f"""
                Öğrenci cevabını değerlendir:
                
                Soru: {question.question_text}
                Doğru Cevap: {question.correct_answer}
                Öğrenci Cevabı: {student_answer}
                
                0-{question.points} arasında puan ver ve açıklama yap.
                
                JSON formatında yanıtla:
                {{
                    "score": puan,
                    "feedback": "Geri bildirim"
                }}
                """

                result = await llm_service.generate(prompt=eval_prompt, temperature=0.3)

                if result["success"]:
                    try:
                        eval_data = json.loads(result["text"])
                        score = min(eval_data.get("score", 0), question.points)
                        feedback = eval_data.get("feedback", "")
                        return (score, feedback)
                    except (json.JSONDecodeError, TypeError, KeyError) as e:
                        logger.debug(f"Evaluation JSON parsing failed: {e}")
                        return (0, "Değerlendirme yapılamadı")
                else:
                    return (0, "Değerlendirme hatası")

        except Exception as e:
            logger.error(f"Evaluate answer error: {str(e)}")
            return (0, "Değerlendirme hatası")

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Basit metin benzerliği hesapla"""
        # Basit Jaccard benzerliği
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    async def get_adaptive_question(
        self, quiz_id: str, previous_performance: Optional[float] = None
    ) -> Optional[Question]:
        """
        Adaptif soru seç

        Args:
            quiz_id: Quiz ID
            previous_performance: Önceki soru performansı (0-1)

        Returns:
            Sonraki soru
        """
        try:
            state = self.adaptive_state.get(quiz_id)
            if not state:
                return None

            # Performansa göre zorluk ayarla
            if previous_performance is not None:
                state["performance_history"].append(previous_performance)

                # Son 3 sorunun ortalaması
                recent_performance = state["performance_history"][-3:]
                avg_performance = sum(recent_performance) / len(recent_performance)

                # Zorluk seviyesini güncelle
                current_difficulty = state["current_difficulty"]
                if avg_performance < 0.4:  # %40'tan düşük
                    # Zorluğu azalt
                    if current_difficulty == DifficultyLevel.EXPERT:
                        state["current_difficulty"] = DifficultyLevel.HARD
                    elif current_difficulty == DifficultyLevel.HARD:
                        state["current_difficulty"] = DifficultyLevel.MEDIUM
                    elif current_difficulty == DifficultyLevel.MEDIUM:
                        state["current_difficulty"] = DifficultyLevel.EASY
                elif avg_performance > 0.8:  # %80'den yüksek
                    # Zorluğu artır
                    if current_difficulty == DifficultyLevel.EASY:
                        state["current_difficulty"] = DifficultyLevel.MEDIUM
                    elif current_difficulty == DifficultyLevel.MEDIUM:
                        state["current_difficulty"] = DifficultyLevel.HARD
                    elif current_difficulty == DifficultyLevel.HARD:
                        state["current_difficulty"] = DifficultyLevel.EXPERT

            # Uygun zorluktaki soruyu seç
            available_questions = [
                q
                for q in state["question_pool"]
                if q.question_id not in state["asked_questions"]
                and q.difficulty == state["current_difficulty"]
            ]

            # Eğer o zorlukta soru yoksa, yakın zorluktan seç
            if not available_questions:
                available_questions = [
                    q
                    for q in state["question_pool"]
                    if q.question_id not in state["asked_questions"]
                ]

            if available_questions:
                question = random.choice(available_questions)
                state["asked_questions"].append(question.question_id)
                return question

            return None

        except Exception as e:
            logger.error(f"Get adaptive question error: {str(e)}")
            return None

    async def summarize_content(self, content: str, max_length: int = 500) -> str:
        """
        İçeriği özetle

        Args:
            content: İçerik
            max_length: Maksimum özet uzunluğu

        Returns:
            Özet
        """
        try:
            result = await llm_service.generate_for_education(
                task_type="summarization",
                content=content,
                parameters={"max_length": max_length},
            )

            if result["success"]:
                return result["content"]
            else:
                # Basit özet
                sentences = content.split(". ")
                if len(sentences) > 3:
                    return ". ".join(sentences[:3]) + "..."
                return content[:max_length]

        except asyncio.TimeoutError:
            logger.error("Summarize error: Timeout")
            return ""  # Return empty string on timeout
        except Exception as e:
            logger.error(f"Summarize error: {str(e)}")
            return ""  # Return empty string on error

    async def provide_feedback(
        self, student_id: str, quiz_id: str, answers: Dict[str, str]
    ) -> StudentPerformance:
        """
        Öğrenci performansını değerlendir ve geri bildirim ver

        Args:
            student_id: Öğrenci ID
            quiz_id: Quiz ID
            answers: Cevaplar {question_id: answer}

        Returns:
            Performans raporu
        """
        try:
            quiz = self.quizzes.get(quiz_id)
            if not quiz:
                raise ValueError(f"Quiz not found: {quiz_id}")

            scores = {}
            feedbacks = []
            total_score = 0

            # Her soruyu değerlendir
            for question in quiz.questions:
                if question.question_id in answers:
                    score, feedback = await self.evaluate_answer(
                        question, answers[question.question_id]
                    )
                    scores[question.question_id] = score
                    total_score += score
                    feedbacks.append(f"Soru {question.question_id}: {feedback}")
                else:
                    scores[question.question_id] = 0
                    feedbacks.append(f"Soru {question.question_id}: Cevaplanmadı")

            # Performans hesapla
            percentage = (
                (total_score / quiz.total_points) * 100 if quiz.total_points > 0 else 0
            )

            # Genel geri bildirim
            if percentage >= 80:
                overall_feedback = (
                    "[PARTY] Harika! Çok başarılı bir performans gösterdiniz."
                )
            elif percentage >= 60:
                overall_feedback = (
                    "👍 İyi! Birkaç konuyu tekrar gözden geçirmeniz faydalı olabilir."
                )
            elif percentage >= 40:
                overall_feedback = (
                    "[BOOKS] Orta. Daha fazla çalışma ile geliştirebilirsiniz."
                )
            else:
                overall_feedback = "💪 Gayret! Konuları tekrar çalışmanızı öneririm."

            # Performans kaydı oluştur
            performance = StudentPerformance(
                student_id=student_id,
                quiz_id=quiz_id,
                answers=answers,
                scores=scores,
                total_score=total_score,
                percentage=percentage,
                time_spent=0,  # Bu örnek için 0
                completed_at=datetime.now(),
                feedback=overall_feedback + "\n\n" + "\n".join(feedbacks),
                metadata={
                    "quiz_title": quiz.title,
                    "question_count": len(quiz.questions),
                },
            )

            # Cache'e kaydet
            perf_id = f"{student_id}_{quiz_id}"
            self.performances[perf_id] = performance

            logger.info(f"Performance evaluated: {perf_id} - {percentage:.1f}%")
            return performance

        except Exception as e:
            logger.error(f"Provide feedback error: {str(e)}")
            raise

    def get_flashcards_by_category(self, category: str) -> List[Flashcard]:
        """Kategoriye göre flashcard'ları getir"""
        return [fc for fc in self.flashcards.values() if fc.category == category]

    def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Quiz getir"""
        return self.quizzes.get(quiz_id)

    def get_student_performance(
        self, student_id: str, quiz_id: str
    ) -> Optional[StudentPerformance]:
        """Öğrenci performansını getir"""
        perf_id = f"{student_id}_{quiz_id}"
        return self.performances.get(perf_id)

    def adjust_difficulty(
        self, quiz_id: str, student_id: Optional[str] = None
    ) -> DifficultyLevel:
        """
        Öğrenci performansına göre zorluk seviyesini ayarla

        Args:
            quiz_id: Quiz ID
            student_id: Öğrenci ID (opsiyonel)

        Returns:
            Ayarlanmış zorluk seviyesi
        """
        # Check adaptive state first
        if quiz_id in self.adaptive_state:
            state = self.adaptive_state[quiz_id]
            if "performance_history" in state and state["performance_history"]:
                avg_performance = sum(state["performance_history"]) / len(
                    state["performance_history"]
                )
                if avg_performance >= 0.8:
                    return DifficultyLevel.HARD
                elif avg_performance >= 0.6:
                    return DifficultyLevel.MEDIUM
                else:
                    return DifficultyLevel.EASY

        # Fall back to student performance
        if student_id:
            perf = self.get_student_performance(student_id, quiz_id)
            if perf:
                if perf.percentage >= 80:
                    return DifficultyLevel.HARD
                elif perf.percentage >= 60:
                    return DifficultyLevel.MEDIUM
                else:
                    return DifficultyLevel.EASY

        quiz = self.get_quiz(quiz_id)
        if quiz:
            return quiz.difficulty
        return DifficultyLevel.MEDIUM

    def get_time_remaining(self, quiz_id: str) -> int:
        """
        Quiz için kalan süreyi dakika olarak döndür

        Args:
            quiz_id: Quiz ID

        Returns:
            Kalan süre (dakika)
        """
        quiz = self.get_quiz(quiz_id)
        if quiz and quiz.time_limit:
            # Basit bir simülasyon - gerçekte zamanlayıcı tutulmalı
            return max(0, quiz.time_limit - 5)  # 5 dakika geçmiş varsayalım
        return 0

    async def generate_quiz_review(
        self, quiz_id: str, student_answers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Quiz için detaylı gözden geçirme raporu oluştur

        Args:
            quiz_id: Quiz ID
            student_answers: Öğrenci cevapları

        Returns:
            Gözden geçirme raporu
        """
        quiz = self.get_quiz(quiz_id)
        if not quiz:
            return {"error": "Quiz not found"}

        review = {
            "quiz_id": quiz_id,
            "total_questions": len(quiz.questions),
            "correct_answers": 0,
            "incorrect_answers": 0,
            "questions_review": [],
            "corrections": [],  # Add corrections field
        }

        for question in quiz.questions:
            student_answer = student_answers.get(question.question_id, "")
            is_correct = student_answer.lower() == question.correct_answer.lower()

            if is_correct:
                review["correct_answers"] += 1
            else:
                review["incorrect_answers"] += 1
                # Add to corrections
                review["corrections"].append(
                    {
                        "question_id": question.question_id,
                        "question": question.question_text,
                        "student_answer": student_answer,
                        "correct_answer": question.correct_answer,
                        "explanation": question.explanation,
                    }
                )

            review["questions_review"].append(
                {
                    "question_id": question.question_id,
                    "question": question.question_text,
                    "student_answer": student_answer,
                    "correct_answer": question.correct_answer,
                    "is_correct": is_correct,
                    "explanation": question.explanation,
                }
            )

        review["percentage"] = (
            review["correct_answers"] / review["total_questions"]
        ) * 100
        review["feedback"] = self._generate_review_feedback(review["percentage"])

        return review

    def _generate_review_feedback(self, percentage: float) -> str:
        """Yüzdeye göre geri bildirim oluştur"""
        if percentage >= 90:
            return "Mükemmel! Harika bir performans gösterdiniz."
        elif percentage >= 75:
            return "Çok iyi! Konuya hakim olduğunuz görülüyor."
        elif percentage >= 60:
            return "İyi! Biraz daha çalışmayla daha da iyileştirebilirsiniz."
        elif percentage >= 50:
            return "Fena değil! Zayıf olduğunuz konulara odaklanın."
        else:
            return (
                "Daha fazla çalışmaya ihtiyacınız var. Yanlış cevapları gözden geçirin."
            )

    def get_questions_by_topic(self, topic: str) -> List[Question]:
        """Konuya göre soruları getir"""
        result = []
        for q_id, question in self.question_bank.items():
            if hasattr(question, "topic") and question.topic == topic:
                result.append(question)
        return result

    def is_quiz_expired(self, quiz_id: str) -> bool:
        """Quiz süresinin dolup dolmadığını kontrol et"""
        quiz = self.get_quiz(quiz_id)
        if not quiz or not quiz.time_limit:
            return False

        # Check if start time is stored in metadata
        if quiz.metadata and "start_time" in quiz.metadata:
            # If start_time is a timestamp (float), check if expired
            if isinstance(quiz.metadata["start_time"], (int, float)):
                elapsed = datetime.now().timestamp() - quiz.metadata["start_time"]
                return elapsed > quiz.time_limit
            # If start_time is ISO string, parse and check
            elif isinstance(quiz.metadata["start_time"], str):
                try:
                    start = datetime.fromisoformat(quiz.metadata["start_time"])
                    elapsed = (datetime.now() - start).total_seconds()
                    return elapsed > quiz.time_limit
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse quiz start_time: {e}")
                    pass

        return False

    async def update_flashcard_review(self, card_id: str, success: bool) -> Flashcard:
        """Flashcard inceleme durumunu güncelle"""
        if card_id in self.flashcards:
            card = self.flashcards[card_id]
            card.review_count += 1
            # Update success rate
            if success:
                card.success_rate = min(1.0, card.success_rate + 0.1)
            else:
                card.success_rate = max(0.0, card.success_rate - 0.1)
            card.last_reviewed = datetime.now()
            return card
        return None

    def get_questions_by_criteria(
        self, subject: str = None, difficulty: DifficultyLevel = None
    ) -> List[Question]:
        """Kriterlere göre soruları getir"""
        result = []
        for q_id, question in self.question_bank.items():
            if subject and hasattr(question, "subject") and question.subject != subject:
                continue
            if (
                difficulty
                and hasattr(question, "difficulty")
                and question.difficulty != difficulty
            ):
                continue
            result.append(question)
        return result

    async def get_hint(self, question: Question, hint_level: int = 1) -> str:
        """Soru için ipucu oluştur"""
        # Generate hints using LLM if available
        try:
            result = await llm_service.generate_for_education(
                task_type="hint_generation",
                content=f"Question: {question.question_text}\nTopic: {question.topic}\nAnswer: {question.correct_answer}",
                parameters={"hint_level": hint_level},
            )
            if result.get("success"):
                return result["content"]
        except (KeyError, TypeError, AttributeError) as e:
            logger.debug(f"LLM hint generation failed: {e}")
            pass

        # Fallback hints
        hints = {
            1: f"Sorunun konusu: {question.topic}",
            2: f"Cevabın ilk harfi: {question.correct_answer[0] if question.correct_answer else '?'}",
            3: f"İpucu: {question.explanation[:50] if question.explanation else 'Açıklama yok'}",
        }
        return hints.get(hint_level, "Daha fazla ipucu yok")

    async def get_performance_insights(
        self, student_id: str
    ) -> Optional[Dict[str, Any]]:
        """Öğrenci performans analitiği"""
        if student_id not in self.student_performances:
            return None

        perf = self.student_performances[student_id]
        insights = {
            "overall_performance": perf.correct_answers / perf.total_questions
            if perf.total_questions > 0
            else 0,
            "strong_topics": [],
            "weak_topics": [],
            "recommended_difficulty": DifficultyLevel.MEDIUM,
        }

        # Analyze topics
        if perf.topics_covered:
            if isinstance(perf.topics_covered, dict):
                for topic, score in perf.topics_covered.items():
                    if score > 15:
                        insights["strong_topics"].append(topic)
                    else:
                        insights["weak_topics"].append(topic)

        # Recommend difficulty
        if insights["overall_performance"] >= 0.8:
            insights["recommended_difficulty"] = DifficultyLevel.HARD
        elif insights["overall_performance"] <= 0.5:
            insights["recommended_difficulty"] = DifficultyLevel.EASY

        return insights


# Singleton instance
study_buddy_agent = StudyBuddyAgent()
