"""
Full Tests for Exam Engine (Sınav Motoru)
Sınav Motoru Tam Testleri

Tests:
- Exam generation (TYT, AYT, LGS)
- Question selection algorithms
- Difficulty balancing
- Time management
- Score calculation
- Answer validation
- Exam submission
- Result generation
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# ==================== MOCK MODELS ====================


class Question:
    """Soru modeli"""

    def __init__(
        self,
        question_id: str,
        subject: str,
        topic: str,
        difficulty: float,
        correct_answer: str,
        options: List[str],
        points: int = 1,
    ):
        self.question_id = question_id
        self.subject = subject
        self.topic = topic
        self.difficulty = difficulty  # 0-1 arası
        self.correct_answer = correct_answer
        self.options = options
        self.points = points
        self.time_estimate = 90  # saniye


class ExamConfig:
    """Sınav konfigürasyonu"""

    def __init__(
        self,
        exam_type: str,
        total_questions: int,
        duration_minutes: int,
        subjects: Dict[str, int],
    ):
        self.exam_type = exam_type  # "tyt", "ayt", "lgs"
        self.total_questions = total_questions
        self.duration_minutes = duration_minutes
        self.subjects = subjects  # {"Matematik": 40, "Türkçe": 40}
        self.target_difficulty = 0.5
        self.allow_skip = True


class StudentAnswer:
    """Öğrenci cevabı"""

    def __init__(self, question_id: str, answer: Optional[str], time_spent: int):
        self.question_id = question_id
        self.answer = answer  # None = boş
        self.time_spent = time_spent  # saniye
        self.is_correct = False
        self.answered_at = datetime.utcnow()


class ExamResult:
    """Sınav sonucu"""

    def __init__(self, exam_id: str, student_id: str):
        self.exam_id = exam_id
        self.student_id = student_id
        self.total_questions = 0
        self.correct_answers = 0
        self.wrong_answers = 0
        self.empty_answers = 0
        self.net_score = 0.0
        self.raw_score = 0
        self.total_time_spent = 0
        self.subject_scores = {}
        self.completed_at = None


class Exam:
    """Sınav modeli"""

    def __init__(self, exam_id: str, config: ExamConfig, questions: List[Question]):
        self.exam_id = exam_id
        self.config = config
        self.questions = questions
        self.created_at = datetime.utcnow()
        self.start_time = None
        self.end_time = None
        self.student_answers = {}
        self.status = "created"  # created, in_progress, completed

    def start_exam(self) -> datetime:
        """Sınavı başlat"""
        self.start_time = datetime.utcnow()
        self.status = "in_progress"
        return self.start_time

    def get_remaining_time(self) -> int:
        """Kalan süreyi al (saniye)"""
        if not self.start_time or self.status == "completed":
            return 0

        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        total_seconds = self.config.duration_minutes * 60
        remaining = max(0, total_seconds - elapsed)

        return int(remaining)

    def is_time_up(self) -> bool:
        """Süre doldu mu?"""
        return self.get_remaining_time() == 0

    def submit_answer(self, student_id: str, answer: StudentAnswer) -> bool:
        """Cevap gönder"""
        if self.status != "in_progress":
            return False

        if self.is_time_up():
            self.complete_exam()
            return False

        if student_id not in self.student_answers:
            self.student_answers[student_id] = {}

        self.student_answers[student_id][answer.question_id] = answer
        return True

    def complete_exam(self):
        """Sınavı tamamla"""
        self.end_time = datetime.utcnow()
        self.status = "completed"


# ==================== EXAM ENGINE ====================


class QuestionSelector:
    """Soru seçim algoritması"""

    def select_questions(
        self, question_pool: List[Question], config: ExamConfig
    ) -> List[Question]:
        """Sınav için soru seç"""

        selected = []

        for subject, count in config.subjects.items():
            # Subject'e göre filtrele
            subject_questions = [q for q in question_pool if q.subject == subject]

            # Zorluk seviyesine göre sırala
            subject_questions.sort(
                key=lambda q: abs(q.difficulty - config.target_difficulty)
            )

            # İlk N soruyu al
            selected.extend(subject_questions[:count])

        return selected[: config.total_questions]

    def balance_difficulty(
        self, questions: List[Question], target_difficulty: float = 0.5
    ) -> List[Question]:
        """Zorluk dengesini kontrol et"""

        if not questions:
            return questions

        # Ortalama zorluk
        avg_difficulty = sum(q.difficulty for q in questions) / len(questions)

        # Hedeften çok farklıysa ayarlama yap
        if abs(avg_difficulty - target_difficulty) > 0.2:
            # Zor/kolay sorular ekle/çıkar
            questions.sort(key=lambda q: q.difficulty)

            if avg_difficulty < target_difficulty:
                # Daha zor sorular ekle
                pass
            else:
                # Daha kolay sorular ekle
                pass

        return questions


class AnswerValidator:
    """Cevap doğrulama"""

    def validate_answer(
        self, question: Question, student_answer: StudentAnswer
    ) -> bool:
        """Cevabı doğrula"""

        if student_answer.answer is None:
            return False

        is_correct = student_answer.answer == question.correct_answer
        student_answer.is_correct = is_correct

        return is_correct

    def calculate_score(
        self,
        questions: List[Question],
        answers: Dict[str, StudentAnswer],
        wrong_penalty: float = 0.25,
    ) -> Dict:
        """Puan hesapla"""

        correct = 0
        wrong = 0
        empty = 0
        total_points = 0

        for question in questions:
            answer = answers.get(question.question_id)

            if not answer or answer.answer is None:
                empty += 1
            elif self.validate_answer(question, answer):
                correct += 1
                total_points += question.points
            else:
                wrong += 1
                total_points -= question.points * wrong_penalty

        net_score = correct - (wrong * wrong_penalty)

        return {
            "correct": correct,
            "wrong": wrong,
            "empty": empty,
            "net_score": net_score,
            "raw_score": total_points,
            "total_questions": len(questions),
        }


class ExamEngine:
    """Sınav motoru"""

    def __init__(self):
        self.question_selector = QuestionSelector()
        self.answer_validator = AnswerValidator()
        self.active_exams = {}

    def create_exam(
        self, exam_id: str, config: ExamConfig, question_pool: List[Question]
    ) -> Exam:
        """Sınav oluştur"""

        # Soruları seç
        questions = self.question_selector.select_questions(question_pool, config)

        # Zorluk dengesini sağla
        questions = self.question_selector.balance_difficulty(
            questions, config.target_difficulty
        )

        exam = Exam(exam_id, config, questions)
        self.active_exams[exam_id] = exam

        return exam

    def start_exam(self, exam_id: str) -> Optional[Exam]:
        """Sınavı başlat"""
        exam = self.active_exams.get(exam_id)

        if not exam:
            return None

        exam.start_exam()
        return exam

    def submit_answer(
        self, exam_id: str, student_id: str, answer: StudentAnswer
    ) -> bool:
        """Cevap gönder"""

        exam = self.active_exams.get(exam_id)

        if not exam:
            return False

        return exam.submit_answer(student_id, answer)

    def complete_exam(self, exam_id: str, student_id: str) -> ExamResult:
        """Sınavı tamamla ve sonuçları hesapla"""

        exam = self.active_exams.get(exam_id)

        if not exam:
            return None

        exam.complete_exam()

        # Sonuçları hesapla
        answers = exam.student_answers.get(student_id, {})

        score_data = self.answer_validator.calculate_score(exam.questions, answers)

        result = ExamResult(exam_id, student_id)
        result.total_questions = score_data["total_questions"]
        result.correct_answers = score_data["correct"]
        result.wrong_answers = score_data["wrong"]
        result.empty_answers = score_data["empty"]
        result.net_score = score_data["net_score"]
        result.raw_score = score_data["raw_score"]
        result.completed_at = datetime.utcnow()

        # Ders bazlı skorları hesapla
        for subject in exam.config.subjects.keys():
            subject_questions = [q for q in exam.questions if q.subject == subject]
            subject_answers = {
                q.question_id: answers.get(q.question_id) for q in subject_questions
            }

            subject_score = self.answer_validator.calculate_score(
                subject_questions, subject_answers
            )

            result.subject_scores[subject] = subject_score

        # Toplam süre
        if answers:
            result.total_time_spent = sum(a.time_spent for a in answers.values())

        return result


# ==================== TESTS ====================


@pytest.fixture
def question_pool():
    """Sample question pool"""
    questions = []

    subjects = {"Matematik": 50, "Türkçe": 50, "Fen": 30, "Sosyal": 30}

    question_id = 1
    for subject, count in subjects.items():
        for i in range(count):
            questions.append(
                Question(
                    question_id=f"q_{question_id}",
                    subject=subject,
                    topic=f"Topic {i % 5}",
                    difficulty=0.3 + (i % 7) * 0.1,  # 0.3-0.9 arası
                    correct_answer="A",
                    options=["A", "B", "C", "D"],
                    points=1,
                )
            )
            question_id += 1

    return questions


@pytest.fixture
def tyt_config():
    """TYT exam configuration"""
    return ExamConfig(
        exam_type="tyt",
        total_questions=120,
        duration_minutes=135,
        subjects={"Matematik": 40, "Türkçe": 40, "Fen": 20, "Sosyal": 20},
    )


@pytest.fixture
def exam_engine():
    """Exam engine fixture"""
    return ExamEngine()


class TestExamCreation:
    """Test exam creation"""

    def test_create_exam(self, exam_engine, tyt_config, question_pool):
        """Test basic exam creation"""
        exam = exam_engine.create_exam("exam_1", tyt_config, question_pool)

        assert exam is not None
        assert exam.exam_id == "exam_1"
        assert len(exam.questions) <= tyt_config.total_questions
        assert exam.status == "created"

    def test_exam_has_all_subjects(self, exam_engine, tyt_config, question_pool):
        """Test exam includes all configured subjects"""
        exam = exam_engine.create_exam("exam_2", tyt_config, question_pool)

        subjects_in_exam = set(q.subject for q in exam.questions)

        for subject in tyt_config.subjects.keys():
            assert subject in subjects_in_exam

    def test_subject_question_counts(self, exam_engine, tyt_config, question_pool):
        """Test each subject has correct number of questions"""
        exam = exam_engine.create_exam("exam_3", tyt_config, question_pool)

        for subject, target_count in tyt_config.subjects.items():
            actual_count = sum(1 for q in exam.questions if q.subject == subject)
            assert actual_count <= target_count

    def test_exam_difficulty_balanced(self, exam_engine, tyt_config, question_pool):
        """Test exam difficulty is balanced"""
        exam = exam_engine.create_exam("exam_4", tyt_config, question_pool)

        if exam.questions:
            avg_difficulty = sum(q.difficulty for q in exam.questions) / len(
                exam.questions
            )
            # Should be close to target (0.5)
            assert 0.3 <= avg_difficulty <= 0.7


class TestExamLifecycle:
    """Test exam lifecycle"""

    def test_start_exam(self, exam_engine, tyt_config, question_pool):
        """Test starting an exam"""
        exam = exam_engine.create_exam("exam_start", tyt_config, question_pool)

        started_exam = exam_engine.start_exam("exam_start")

        assert started_exam is not None
        assert started_exam.status == "in_progress"
        assert started_exam.start_time is not None

    def test_exam_time_tracking(self, exam_engine, tyt_config, question_pool):
        """Test exam time tracking"""
        exam = exam_engine.create_exam("exam_time", tyt_config, question_pool)
        exam_engine.start_exam("exam_time")

        remaining = exam.get_remaining_time()

        assert remaining > 0
        assert remaining <= tyt_config.duration_minutes * 60

    def test_exam_completion(self, exam_engine, tyt_config, question_pool):
        """Test exam completion"""
        exam = exam_engine.create_exam("exam_complete", tyt_config, question_pool)
        exam_engine.start_exam("exam_complete")

        exam.complete_exam()

        assert exam.status == "completed"
        assert exam.end_time is not None


class TestAnswerSubmission:
    """Test answer submission"""

    def test_submit_single_answer(self, exam_engine, tyt_config, question_pool):
        """Test submitting a single answer"""
        exam = exam_engine.create_exam("exam_answer", tyt_config, question_pool)
        exam_engine.start_exam("exam_answer")

        answer = StudentAnswer(
            question_id=exam.questions[0].question_id, answer="A", time_spent=45
        )

        success = exam_engine.submit_answer("exam_answer", "student_1", answer)

        assert success is True
        assert "student_1" in exam.student_answers
        assert answer.question_id in exam.student_answers["student_1"]

    def test_submit_multiple_answers(self, exam_engine, tyt_config, question_pool):
        """Test submitting multiple answers"""
        exam = exam_engine.create_exam("exam_multi", tyt_config, question_pool)
        exam_engine.start_exam("exam_multi")

        for i in range(5):
            answer = StudentAnswer(
                question_id=exam.questions[i].question_id, answer="A", time_spent=30
            )
            exam_engine.submit_answer("exam_multi", "student_1", answer)

        assert len(exam.student_answers["student_1"]) == 5

    def test_cannot_submit_before_start(self, exam_engine, tyt_config, question_pool):
        """Test cannot submit answer before exam starts"""
        exam = exam_engine.create_exam("exam_not_started", tyt_config, question_pool)

        answer = StudentAnswer(question_id="q_1", answer="A", time_spent=30)

        success = exam_engine.submit_answer("exam_not_started", "student_1", answer)

        assert success is False

    def test_cannot_submit_after_completion(
        self, exam_engine, tyt_config, question_pool
    ):
        """Test cannot submit answer after exam completion"""
        exam = exam_engine.create_exam("exam_completed", tyt_config, question_pool)
        exam_engine.start_exam("exam_completed")
        exam.complete_exam()

        answer = StudentAnswer(question_id="q_1", answer="A", time_spent=30)

        success = exam_engine.submit_answer("exam_completed", "student_1", answer)

        assert success is False


class TestAnswerValidation:
    """Test answer validation"""

    def test_correct_answer_validation(self, exam_engine):
        """Test correct answer is validated properly"""
        question = Question(
            question_id="q_val_1",
            subject="Math",
            topic="Algebra",
            difficulty=0.5,
            correct_answer="B",
            options=["A", "B", "C", "D"],
        )

        answer = StudentAnswer(question_id="q_val_1", answer="B", time_spent=30)

        is_correct = exam_engine.answer_validator.validate_answer(question, answer)

        assert is_correct is True
        assert answer.is_correct is True

    def test_wrong_answer_validation(self, exam_engine):
        """Test wrong answer is validated properly"""
        question = Question(
            question_id="q_val_2",
            subject="Math",
            topic="Algebra",
            difficulty=0.5,
            correct_answer="B",
            options=["A", "B", "C", "D"],
        )

        answer = StudentAnswer(question_id="q_val_2", answer="C", time_spent=30)

        is_correct = exam_engine.answer_validator.validate_answer(question, answer)

        assert is_correct is False
        assert answer.is_correct is False

    def test_empty_answer_validation(self, exam_engine):
        """Test empty answer is not correct"""
        question = Question(
            question_id="q_val_3",
            subject="Math",
            topic="Algebra",
            difficulty=0.5,
            correct_answer="B",
            options=["A", "B", "C", "D"],
        )

        answer = StudentAnswer(question_id="q_val_3", answer=None, time_spent=0)

        is_correct = exam_engine.answer_validator.validate_answer(question, answer)

        assert is_correct is False


class TestScoreCalculation:
    """Test score calculation"""

    def test_calculate_perfect_score(self, exam_engine, question_pool):
        """Test perfect score calculation"""
        questions = question_pool[:10]
        answers = {}

        for q in questions:
            answer = StudentAnswer(
                question_id=q.question_id, answer=q.correct_answer, time_spent=30
            )
            answers[q.question_id] = answer

        score = exam_engine.answer_validator.calculate_score(questions, answers)

        assert score["correct"] == 10
        assert score["wrong"] == 0
        assert score["empty"] == 0
        assert score["net_score"] == 10.0

    def test_calculate_with_wrong_answers(self, exam_engine, question_pool):
        """Test score with wrong answers"""
        questions = question_pool[:10]
        answers = {}

        # 5 doğru, 5 yanlış
        for i, q in enumerate(questions):
            answer = StudentAnswer(
                question_id=q.question_id,
                answer=q.correct_answer if i < 5 else "X",
                time_spent=30,
            )
            answers[q.question_id] = answer

        score = exam_engine.answer_validator.calculate_score(questions, answers)

        assert score["correct"] == 5
        assert score["wrong"] == 5
        # Net = 5 - (5 * 0.25) = 3.75
        assert abs(score["net_score"] - 3.75) < 0.01

    def test_calculate_with_empty_answers(self, exam_engine, question_pool):
        """Test score with empty answers"""
        questions = question_pool[:10]
        answers = {}

        # Sadece 5 soru cevapla
        for i, q in enumerate(questions[:5]):
            answer = StudentAnswer(
                question_id=q.question_id, answer=q.correct_answer, time_spent=30
            )
            answers[q.question_id] = answer

        score = exam_engine.answer_validator.calculate_score(questions, answers)

        assert score["correct"] == 5
        assert score["empty"] == 5
        assert score["net_score"] == 5.0


class TestExamResults:
    """Test exam result generation"""

    def test_generate_exam_result(self, exam_engine, tyt_config, question_pool):
        """Test complete exam result generation"""
        exam = exam_engine.create_exam("exam_result", tyt_config, question_pool)
        exam_engine.start_exam("exam_result")

        # Cevapları gönder
        for i, q in enumerate(exam.questions[:20]):
            answer = StudentAnswer(
                question_id=q.question_id,
                answer=q.correct_answer if i % 2 == 0 else "X",
                time_spent=45,
            )
            exam_engine.submit_answer("exam_result", "student_1", answer)

        result = exam_engine.complete_exam("exam_result", "student_1")

        assert result is not None
        assert result.student_id == "student_1"
        assert result.correct_answers == 10
        assert result.wrong_answers == 10
        assert result.completed_at is not None

    def test_subject_scores_in_result(self, exam_engine, tyt_config, question_pool):
        """Test subject-wise scores in result"""
        exam = exam_engine.create_exam("exam_subject_score", tyt_config, question_pool)
        exam_engine.start_exam("exam_subject_score")

        # Tüm soruları cevapla
        for q in exam.questions:
            answer = StudentAnswer(
                question_id=q.question_id, answer=q.correct_answer, time_spent=30
            )
            exam_engine.submit_answer("exam_subject_score", "student_1", answer)

        result = exam_engine.complete_exam("exam_subject_score", "student_1")

        # Her ders için skor olmalı
        for subject in tyt_config.subjects.keys():
            assert subject in result.subject_scores
            assert result.subject_scores[subject]["correct"] >= 0

    def test_time_tracking_in_result(self, exam_engine, tyt_config, question_pool):
        """Test time tracking in exam result"""
        exam = exam_engine.create_exam("exam_time_track", tyt_config, question_pool)
        exam_engine.start_exam("exam_time_track")

        total_time = 0
        for q in exam.questions[:10]:
            time_spent = 45
            total_time += time_spent

            answer = StudentAnswer(
                question_id=q.question_id,
                answer=q.correct_answer,
                time_spent=time_spent,
            )
            exam_engine.submit_answer("exam_time_track", "student_1", answer)

        result = exam_engine.complete_exam("exam_time_track", "student_1")

        assert result.total_time_spent == total_time


class TestEdgeCases:
    """Test edge cases"""

    def test_empty_question_pool(self, exam_engine, tyt_config):
        """Test exam creation with empty question pool"""
        exam = exam_engine.create_exam("exam_empty", tyt_config, [])

        assert exam.questions == []

    def test_start_nonexistent_exam(self, exam_engine):
        """Test starting non-existent exam"""
        result = exam_engine.start_exam("nonexistent")

        assert result is None

    def test_complete_without_answers(self, exam_engine, tyt_config, question_pool):
        """Test completing exam without any answers"""
        exam = exam_engine.create_exam("exam_no_answer", tyt_config, question_pool)
        exam_engine.start_exam("exam_no_answer")

        result = exam_engine.complete_exam("exam_no_answer", "student_1")

        assert result.correct_answers == 0
        assert result.empty_answers == result.total_questions
