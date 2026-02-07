"""
Teknofest 2025 Eğitim Eylemci Platformu
Test Data Fixtures

Bu dosya testler için gerekli mock verileri içerir.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from models.enums_db import ExamType, UserRole


class TestDataFactory:
    """Test verileri oluşturmak için factory sınıfı"""
    __test__ = False

    @staticmethod
    def create_user(
        role: UserRole = UserRole.STUDENT,
        username: str = "test_user",
        email: str = "test@example.com",
        **kwargs,
    ) -> Dict[str, Any]:
        """Test kullanıcısı oluştur"""
        default_data = {
            "id": str(uuid.uuid4()),
            "username": username,
            "email": email,
            "password": "hashed_password",
            "firstName": "Test",
            "lastName": "User",
            "role": role.value,
            "isActive": True,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }
        default_data.update(kwargs)
        return default_data

    @staticmethod
    def create_student(**kwargs) -> Dict[str, Any]:
        """Test öğrencisi oluştur"""
        defaults = dict(
            role=UserRole.STUDENT,
            username="test_student",
            email="student@example.com",
            firstName="Test",
            lastName="Student",
        )
        defaults.update(kwargs)
        return TestDataFactory.create_user(**defaults)

    @staticmethod
    def create_teacher(**kwargs) -> Dict[str, Any]:
        """Test öğretmeni oluştur"""
        defaults = dict(
            role=UserRole.TEACHER,
            username="test_teacher",
            email="teacher@example.com",
            firstName="Test",
            lastName="Teacher",
        )
        defaults.update(kwargs)
        return TestDataFactory.create_user(**defaults
        )

    @staticmethod
    def create_admin(**kwargs) -> Dict[str, Any]:
        """Test admin oluştur"""
        defaults = dict(
            role=UserRole.ADMIN,
            username="test_admin",
            email="admin@example.com",
            firstName="Test",
            lastName="Admin",
        )
        defaults.update(kwargs)
        return TestDataFactory.create_user(**defaults
        )

    @staticmethod
    def create_exam(
        exam_type: ExamType = ExamType.TYT, subject: str = "Matematik", **kwargs
    ) -> Dict[str, Any]:
        """Test sınavı oluştur"""
        default_data = {
            "id": str(uuid.uuid4()),
            "title": f"{exam_type.value} {subject} Denemesi",
            "type": exam_type.value,
            "subject": subject,
            "duration": 165 if exam_type == ExamType.TYT else 210,
            "questionCount": 40 if exam_type == ExamType.TYT else 80,
            "status": "active",
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }
        default_data.update(kwargs)
        return default_data

    @staticmethod
    def create_tyt_exam(**kwargs) -> Dict[str, Any]:
        """TYT sınavı oluştur"""
        defaults = dict(exam_type=ExamType.TYT, subject="Matematik", duration=165, questionCount=40)
        defaults.update(kwargs)
        return TestDataFactory.create_exam(**defaults)

    @staticmethod
    def create_ayt_exam(**kwargs) -> Dict[str, Any]:
        """AYT sınavı oluştur"""
        defaults = dict(exam_type=ExamType.AYT, subject="Matematik", duration=210, questionCount=80)
        defaults.update(kwargs)
        return TestDataFactory.create_exam(**defaults)

    @staticmethod
    def create_question(
        subject: str = "Matematik", difficulty: str = "medium", **kwargs
    ) -> Dict[str, Any]:
        """Test sorusu oluştur"""
        default_data = {
            "id": str(uuid.uuid4()),
            "text": "Bu bir test sorusudur?",
            "options": ["Seçenek A", "Seçenek B", "Seçenek C", "Seçenek D"],
            "correctAnswer": 2,
            "subject": subject,
            "difficulty": difficulty,
            "explanation": "Bu sorunun açıklamasıdır.",
            "tags": ["test", subject.lower()],
            "createdAt": datetime.now(),
        }
        default_data.update(kwargs)
        return default_data

    @staticmethod
    def create_math_question(**kwargs) -> Dict[str, Any]:
        """Matematik sorusu oluştur"""
        defaults = dict(
            text="x + 2 = 5 ise x kaçtır?",
            options=["1", "2", "3", "4"],
            correctAnswer=2,
            subject="Matematik",
            explanation="x + 2 = 5 denkleminde x = 3 olur.",
        )
        defaults.update(kwargs)
        return TestDataFactory.create_question(**defaults)

    @staticmethod
    def create_turkish_question(**kwargs) -> Dict[str, Any]:
        """Türkçe sorusu oluştur"""
        defaults = dict(
            text="Aşağıdaki cümlelerden hangisi kurallı yazılmıştır?",
            options=[
                "Kitabı masanın üstüne koydum.",
                "Kitabı masanın üstünde koydum.",
                "Kitabı masanın üstüne koydım.",
                "Kitabı masanın üstünde koydım.",
            ],
            correctAnswer=0,
            subject="Türkçe",
            explanation="Doğru yazım 'masanın üstüne koydum' şeklindedir.",
        )
        defaults.update(kwargs)
        return TestDataFactory.create_question(**defaults)

    @staticmethod
    def create_exam_session(
        exam_id: str = None, user_id: str = None, status: str = "active", **kwargs
    ) -> Dict[str, Any]:
        """Test sınav oturumu oluştur"""
        default_data = {
            "id": str(uuid.uuid4()),
            "examId": exam_id or str(uuid.uuid4()),
            "userId": user_id or str(uuid.uuid4()),
            "startTime": datetime.now(),
            "endTime": None,
            "status": status,
            "currentQuestionIndex": 0,
            "answers": [],
            "createdAt": datetime.now(),
        }
        default_data.update(kwargs)
        return default_data

    @staticmethod
    def create_exam_result(
        session_id: str = None, user_id: str = None, score: int = 85, **kwargs
    ) -> Dict[str, Any]:
        """Test sınav sonucu oluştur"""
        default_data = {
            "id": str(uuid.uuid4()),
            "sessionId": session_id or str(uuid.uuid4()),
            "userId": user_id or str(uuid.uuid4()),
            "score": score,
            "correctAnswers": 34,
            "totalQuestions": 40,
            "timeSpent": 120,
            "completedAt": datetime.now(),
            "subjectScores": {
                "Matematik": {"correct": 15, "total": 20, "percentage": 75},
                "Geometri": {"correct": 12, "total": 15, "percentage": 80},
                "Fonksiyonlar": {"correct": 7, "total": 5, "percentage": 140},
            },
            "detailedResults": [
                {
                    "questionId": "q1",
                    "selectedAnswer": 2,
                    "correctAnswer": 2,
                    "isCorrect": True,
                    "timeSpent": 30,
                    "subject": "Matematik",
                }
            ],
        }
        default_data.update(kwargs)
        return default_data

    @staticmethod
    def create_learning_style(
        user_id: str = None, hybrid_code: str = "V-A-V-S", **kwargs
    ) -> Dict[str, Any]:
        """Test öğrenme stili oluştur"""
        default_data = {
            "id": str(uuid.uuid4()),
            "userId": user_id or str(uuid.uuid4()),
            "varkProfile": {
                "visual": 0.8,
                "auditory": 0.3,
                "reading": 0.6,
                "kinesthetic": 0.4,
            },
            "felderProfile": {
                "activeReflective": 0.7,
                "sensingIntuitive": 0.5,
                "visualVerbal": 0.8,
                "sequentialGlobal": 0.6,
            },
            "hybridCode": hybrid_code,
            "confidenceLevel": 0.85,
            "recommendations": [
                "Görsel materyaller kullanın",
                "Diyagramlar ve şemalar tercih edin",
                "Aktif öğrenme yöntemlerini deneyin",
            ],
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
        }
        default_data.update(kwargs)
        return default_data

    @staticmethod
    def create_fsrs_card(
        user_id: str = None, content: str = "Matematik - Türev Kuralları", **kwargs
    ) -> Dict[str, Any]:
        """Test FSRS kartı oluştur"""
        default_data = {
            "id": str(uuid.uuid4()),
            "userId": user_id or str(uuid.uuid4()),
            "content": content,
            "nextReview": datetime.now() + timedelta(days=1),
            "interval": 1,
            "easeFactor": 2.5,
            "repetitions": 1,
            "lastReviewed": datetime.now() - timedelta(days=1),
            "createdAt": datetime.now(),
        }
        default_data.update(kwargs)
        return default_data

    @staticmethod
    def create_chat_message(
        user_id: str = None,
        content: str = "Bu bir test mesajıdır.",
        sender: str = "user",
        **kwargs,
    ) -> Dict[str, Any]:
        """Test chat mesajı oluştur"""
        default_data = {
            "id": str(uuid.uuid4()),
            "userId": user_id or str(uuid.uuid4()),
            "content": content,
            "sender": sender,  # "user" or "ai"
            "timestamp": datetime.now(),
            "metadata": {"intent": "question", "confidence": 0.9, "language": "tr"},
        }
        default_data.update(kwargs)
        return default_data

    @staticmethod
    def create_admin_stats(**kwargs) -> Dict[str, Any]:
        """Test admin istatistikleri oluştur"""
        default_data = {
            "totalUsers": 1250,
            "activeUsers": 890,
            "totalExams": 45,
            "completedExams": 2340,
            "averageScore": 78.5,
            "dailyActiveUsers": 156,
            "weeklyActiveUsers": 678,
            "monthlyActiveUsers": 1100,
            "topSubjects": [
                {"subject": "Matematik", "count": 450},
                {"subject": "Fizik", "count": 320},
                {"subject": "Kimya", "count": 280},
            ],
            "recentActivity": [
                {
                    "type": "exam_completed",
                    "userId": str(uuid.uuid4()),
                    "examId": str(uuid.uuid4()),
                    "timestamp": datetime.now() - timedelta(minutes=5),
                }
            ],
        }
        default_data.update(kwargs)
        return default_data

    @staticmethod
    def create_revolutionary_features_data(
        user_id: str = None, **kwargs
    ) -> Dict[str, Any]:
        """Test devrimsel özellikler verisi oluştur"""
        default_data = {
            "userId": user_id or str(uuid.uuid4()),
            "learningStyle": TestDataFactory.create_learning_style(user_id),
            "fsrsSchedule": {
                "cards": [
                    TestDataFactory.create_fsrs_card(user_id),
                    TestDataFactory.create_fsrs_card(
                        user_id,
                        content="Fizik - Newton Yasaları",
                        nextReview=datetime.now() + timedelta(days=2),
                    ),
                ],
                "schedule": {"today": 5, "tomorrow": 3, "thisWeek": 15, "nextWeek": 8},
            },
            "multiAgentStatus": {
                "agents": [
                    {
                        "name": "LearningPathAgent",
                        "status": "active",
                        "lastUpdate": datetime.now() - timedelta(minutes=2),
                        "tasksCompleted": 45,
                        "currentTask": "Analyzing student performance",
                    },
                    {
                        "name": "StudyBuddyAgent",
                        "status": "active",
                        "lastUpdate": datetime.now() - timedelta(minutes=1),
                        "tasksCompleted": 38,
                        "currentTask": "Generating practice questions",
                    },
                    {
                        "name": "AccessibilityAgent",
                        "status": "active",
                        "lastUpdate": datetime.now() - timedelta(seconds=30),
                        "tasksCompleted": 22,
                        "currentTask": "Optimizing content accessibility",
                    },
                ],
                "coordination": {
                    "activeConnections": 3,
                    "messagesSent": 150,
                    "messagesReceived": 148,
                    "averageResponseTime": 0.25,
                    "successRate": 0.98,
                },
            },
            "bionicReading": {
                "enabled": True,
                "settings": {
                    "rootBoldRatio": 0.4,
                    "suffixBoldRatio": 0.0,
                    "minBoldChars": 2,
                    "maxBoldChars": 4,
                },
                "usage": {
                    "textsProcessed": 156,
                    "averageReadingSpeedImprovement": 0.23,
                },
            },
            "textSimplification": {
                "enabled": True,
                "levels": {"lexical": True, "syntactic": True, "semantic": True},
                "usage": {"textsSimplified": 89, "averageComplexityReduction": 0.35},
            },
        }
        default_data.update(kwargs)
        return default_data


class MockResponses:
    """Mock API yanıtları için yardımcı sınıf"""

    @staticmethod
    def success_response(data: Any, message: str = "İşlem başarılı") -> Dict[str, Any]:
        """Başarılı API yanıtı"""
        return {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def error_response(
        message: str = "Bir hata oluştu",
        error_code: str = "GENERAL_ERROR",
        status_code: int = 500,
    ) -> Dict[str, Any]:
        """Hata API yanıtı"""
        return {
            "success": False,
            "message": message,
            "error": {
                "code": error_code,
                "details": f"Error occurred at {datetime.now().isoformat()}",
            },
            "statusCode": status_code,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def validation_error_response(field_errors: Dict[str, str]) -> Dict[str, Any]:
        """Validasyon hatası yanıtı"""
        return {
            "success": False,
            "message": "Validasyon hatası",
            "error": {"code": "VALIDATION_ERROR", "fieldErrors": field_errors},
            "statusCode": 422,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def paginated_response(
        data: List[Any], page: int = 1, page_size: int = 10, total: int = None
    ) -> Dict[str, Any]:
        """Sayfalanmış API yanıtı"""
        if total is None:
            total = len(data)

        return {
            "success": True,
            "data": {
                "items": data,
                "pagination": {
                    "page": page,
                    "pageSize": page_size,
                    "total": total,
                    "totalPages": (total + page_size - 1) // page_size,
                    "hasNext": page * page_size < total,
                    "hasPrev": page > 1,
                },
            },
            "message": "Veriler başarıyla alındı",
            "timestamp": datetime.now().isoformat(),
        }


# Test verileri örnekleri
SAMPLE_USERS = [
    TestDataFactory.create_student(username="student1", email="student1@example.com"),
    TestDataFactory.create_student(username="student2", email="student2@example.com"),
    TestDataFactory.create_teacher(username="teacher1", email="teacher1@example.com"),
    TestDataFactory.create_admin(username="admin1", email="admin1@example.com"),
]

SAMPLE_EXAMS = [
    TestDataFactory.create_tyt_exam(subject="Matematik"),
    TestDataFactory.create_tyt_exam(subject="Türkçe"),
    TestDataFactory.create_ayt_exam(subject="Matematik"),
    TestDataFactory.create_ayt_exam(subject="Fizik"),
]

SAMPLE_QUESTIONS = [
    TestDataFactory.create_math_question(),
    TestDataFactory.create_turkish_question(),
    TestDataFactory.create_question(
        text="Işığın hızı yaklaşık kaç km/s'dir?",
        options=["300.000", "150.000", "450.000", "600.000"],
        correctAnswer=0,
        subject="Fizik",
    ),
]
