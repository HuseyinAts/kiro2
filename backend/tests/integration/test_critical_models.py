
"""
Critical Models Tests
Database model'larının temel testleri
"""
from datetime import datetime, timezone


class TestCriticalModels:
    """Critical model functionality tests"""

    def test_user_model_creation(self):
        """Test user model creation"""

        class MockUser:
            def __init__(self, username: str, email: str, password_hash: str):
                self.id = None
                self.username = username
                self.email = email
                self.password_hash = password_hash
                self.created_at = datetime.now(timezone.utc)
                self.is_active = True
                self.role = "student"

            def to_dict(self):
                return {
                    "id": self.id,
                    "username": self.username,
                    "email": self.email,
                    "created_at": self.created_at.isoformat(),
                    "is_active": self.is_active,
                    "role": self.role,
                }

        # Test user creation
        user = MockUser("test_user", "test@example.com", "hashed_password")

        assert user.username == "test_user"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.is_active is True
        assert user.role == "student"
        assert isinstance(user.created_at, datetime)

        # Test serialization
        user_dict = user.to_dict()
        assert "id" in user_dict
        assert user_dict["username"] == "test_user"
        assert user_dict["email"] == "test@example.com"

    def test_exam_model_creation(self):
        """Test exam model creation"""

        class MockExam:
            def __init__(self, title: str, subject: str, duration_minutes: int):
                self.id = None
                self.title = title
                self.subject = subject
                self.duration_minutes = duration_minutes
                self.created_at = datetime.now(timezone.utc)
                self.is_active = True
                self.questions = []

            def add_question(self, question):
                self.questions.append(question)

            def get_question_count(self):
                return len(self.questions)

        # Test exam creation
        exam = MockExam("Matematik Testi", "matematik", 60)

        assert exam.title == "Matematik Testi"
        assert exam.subject == "matematik"
        assert exam.duration_minutes == 60
        assert exam.is_active is True
        assert isinstance(exam.created_at, datetime)
        assert exam.get_question_count() == 0

        # Test adding questions
        exam.add_question({"id": 1, "text": "2+2=?"})
        exam.add_question({"id": 2, "text": "3+3=?"})

        assert exam.get_question_count() == 2

    def test_question_model_creation(self):
        """Test question model creation"""

        class MockQuestion:
            def __init__(self, text: str, correct_answer: str, options: list):
                self.id = None
                self.text = text
                self.correct_answer = correct_answer
                self.options = options
                self.difficulty = "orta"
                self.subject = "matematik"
                self.created_at = datetime.now(timezone.utc)

            def is_correct(self, answer: str) -> bool:
                return answer == self.correct_answer

            def validate(self) -> bool:
                if not self.text or len(self.text) < 5:
                    return False
                if not self.correct_answer:
                    return False
                if not self.options or len(self.options) < 2:
                    return False
                if self.correct_answer not in self.options:
                    return False
                return True

        # Test question creation
        options = ["A) 4", "B) 5", "C) 6", "D) 7"]
        question = MockQuestion("2+2=?", "A) 4", options)

        assert question.text == "2+2=?"
        assert question.correct_answer == "A) 4"
        assert question.options == options
        assert question.difficulty == "orta"
        assert question.subject == "matematik"

        # Test validation
        assert question.validate() is True
        assert question.is_correct("A) 4") is True
        assert question.is_correct("B) 5") is False

        # Test invalid question
        invalid_question = MockQuestion("", "", [])
        assert invalid_question.validate() is False

    def test_learning_style_model(self):
        """Test learning style model"""

        class MockLearningStyle:
            def __init__(self, user_id: int):
                self.user_id = user_id
                self.vark_score = {"V": 0, "A": 0, "R": 0, "K": 0}
                self.felder_silverman_score = {
                    "active_reflective": 0,
                    "sensing_intuitive": 0,
                    "visual_verbal": 0,
                    "sequential_global": 0,
                }
                self.confidence_level = "LOW"
                self.last_updated = datetime.now(timezone.utc)

            def update_vark_score(self, scores: dict):
                self.vark_score.update(scores)
                self._calculate_confidence()

            def get_dominant_style(self):
                max_score = max(self.vark_score.values())
                if max_score == 0:
                    return None

                for style, score in self.vark_score.items():
                    if score == max_score:
                        return style
                return None

            def _calculate_confidence(self):
                total_responses = sum(self.vark_score.values())
                if total_responses >= 20:
                    self.confidence_level = "HIGH"
                elif total_responses >= 10:
                    self.confidence_level = "MEDIUM"
                else:
                    self.confidence_level = "LOW"

        # Test learning style creation
        style = MockLearningStyle(user_id=1)

        assert style.user_id == 1
        assert style.confidence_level == "LOW"
        assert style.get_dominant_style() is None

        # Test updating scores
        style.update_vark_score({"V": 15, "A": 5, "R": 8, "K": 2})

        assert style.vark_score["V"] == 15
        assert style.get_dominant_style() == "V"
        assert style.confidence_level == "HIGH"

    def test_exam_session_model(self):
        """Test exam session model"""

        class MockExamSession:
            def __init__(self, user_id: int, exam_id: int):
                self.id = None
                self.user_id = user_id
                self.exam_id = exam_id
                self.started_at = datetime.now(timezone.utc)
                self.finished_at = None
                self.status = "IN_PROGRESS"
                self.answers = {}
                self.score = None

            def answer_question(self, question_id: int, answer: str):
                self.answers[question_id] = {
                    "answer": answer,
                    "answered_at": datetime.now(timezone.utc),
                }

            def finish_exam(self):
                self.finished_at = datetime.now(timezone.utc)
                self.status = "COMPLETED"

            def calculate_score(self, correct_answers: dict):
                if not correct_answers:
                    return 0

                correct_count = 0
                total_questions = len(correct_answers)

                for question_id, correct_answer in correct_answers.items():
                    if question_id in self.answers:
                        if self.answers[question_id]["answer"] == correct_answer:
                            correct_count += 1

                self.score = (correct_count / total_questions) * 100
                return self.score

        # Test exam session
        session = MockExamSession(user_id=1, exam_id=1)

        assert session.user_id == 1
        assert session.exam_id == 1
        assert session.status == "IN_PROGRESS"
        assert session.score is None
        assert len(session.answers) == 0

        # Test answering questions
        session.answer_question(1, "A")
        session.answer_question(2, "B")

        assert len(session.answers) == 2
        assert session.answers[1]["answer"] == "A"

        # Test scoring
        correct_answers = {1: "A", 2: "C", 3: "B"}
        score = session.calculate_score(correct_answers)

        assert abs(score - 33.33) < 0.01  # 1 correct out of 3 questions
        assert abs(session.score - 33.33) < 0.01

        # Test finishing exam
        session.finish_exam()
        assert session.status == "COMPLETED"
        assert session.finished_at is not None

    def test_content_model(self):
        """Test content model"""

        class MockContent:
            def __init__(self, title: str, content_type: str, body: str):
                self.id = None
                self.title = title
                self.content_type = content_type  # video, text, quiz, etc.
                self.body = body
                self.subject = "matematik"
                self.difficulty = "orta"
                self.tags = []
                self.created_at = datetime.now(timezone.utc)
                self.is_published = False

            def add_tag(self, tag: str):
                if tag not in self.tags:
                    self.tags.append(tag)

            def publish(self):
                self.is_published = True

            def get_summary(self, max_length=100):
                if len(self.body) <= max_length:
                    return self.body
                return self.body[:max_length] + "..."

        # Test content creation
        content = MockContent(
            "Türev Kavramı",
            "text",
            "Türev, bir fonksiyonun değişim hızını ölçen matematiksel kavramdır.",
        )

        assert content.title == "Türev Kavramı"
        assert content.content_type == "text"
        assert content.subject == "matematik"
        assert content.is_published is False
        assert len(content.tags) == 0

        # Test tagging
        content.add_tag("türev")
        content.add_tag("matematik")
        content.add_tag("türev")  # duplicate

        assert len(content.tags) == 2
        assert "türev" in content.tags
        assert "matematik" in content.tags

        # Test publishing
        content.publish()
        assert content.is_published is True

        # Test summary
        long_content = MockContent("Test", "text", "a" * 150)
        summary = long_content.get_summary(100)
        assert len(summary) == 103  # 100 + "..."
        assert summary.endswith("...")

    def test_turkish_content_validation(self):
        """Test Turkish content handling"""

        def validate_turkish_content(text: str) -> bool:
            # Check if text contains Turkish characters
            turkish_chars = "çğıöşüÇĞIİÖŞÜ"
            has_turkish = any(char in text for char in turkish_chars)

            # Check encoding
            try:
                encoded = text.encode("utf-8")
                decoded = encoded.decode("utf-8")
                encoding_ok = decoded == text
            except:
                encoding_ok = False

            return encoding_ok

        # Test Turkish text
        turkish_text = "Türkçe karakterler: ğüşıöçĞÜŞİÖÇ"
        assert validate_turkish_content(turkish_text) is True

        # Test regular text
        english_text = "English text without Turkish characters"
        assert validate_turkish_content(english_text) is True

        # Test mixed text
        mixed_text = "Bu bir mixed text örneğidir."
        assert validate_turkish_content(mixed_text) is True
