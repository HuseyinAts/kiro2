import pytest

"""
KIRO2 Comprehensive Test Fixtures
Complete test fixtures for Turkish exam platform testing
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import json
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pytest_asyncio
from core.auth_middleware import AuthUser, PermissionManager, UserRole
from core.structured_logging import LogCategory, get_logger
from core.unified_api_gateway import APIRequest, APIResponse, HTTPMethod, RouteType
from models import TurkishExamType

logger = get_logger(__name__, LogCategory.TESTING)


@dataclass
class UserFixture:
    """User fixture data"""

    user: AuthUser
    password: str
    profile_data: Dict[str, Any]
    exam_history: List[Dict[str, Any]]
    session_data: Dict[str, Any]


@dataclass
class ExamFixture:
    """Exam fixture data"""

    exam_id: str
    exam_type: TurkishExamType
    questions: List[Dict[str, Any]]
    answers: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    session_config: Dict[str, Any]


@dataclass
class APIRequestFixture:
    """API request fixture data"""

    request: APIRequest
    expected_response: APIResponse
    user_context: Optional[AuthUser]
    test_scenario: str
    validation_rules: List[Dict[str, Any]]


class TurkishExamFixtures:
    """Comprehensive Turkish exam platform test fixtures"""

    def __init__(self):
        self.permission_manager = PermissionManager()
        self._cached_fixtures = {}

    # User Fixtures

    def create_student_fixture(self, student_id: int = None) -> UserFixture:
        """Create comprehensive student user fixture"""
        student_id = student_id or random.randint(10000, 99999)

        user = AuthUser(
            user_id=student_id,
            username=f"student_{student_id}",
            email=f"student_{student_id}@test.edu.tr",
            role=UserRole.STUDENT,
            permissions=self.permission_manager.get_user_permissions(UserRole.STUDENT),
            is_active=True,
            is_verified=True,
            session_id=f"session_{uuid.uuid4()}",
            last_login=datetime.now(timezone.utc) - timedelta(hours=2),
            profile_data={
                "first_name": f"Test{student_id}",
                "last_name": "Öğrenci",
                "birth_date": "2005-05-15",
                "school": "Atatürk Anadolu Lisesi",
                "class": "12-A",
                "city": "İstanbul",
                "phone": f"555{student_id:04d}",
                "parent_phone": f"533{student_id:04d}",
                "target_university": "İstanbul Üniversitesi",
                "target_department": "Tıp Fakültesi",
                "preferred_language": "tr",
                "timezone": "Europe/Istanbul",
            },
            exam_context={
                "target_exam": "YKS 2024",
                "registration_number": f"YKS{student_id}",
                "exam_center": "İstanbul Üniversitesi",
                "preparation_start_date": "2024-01-15",
                "study_plan": {
                    "daily_hours": 6,
                    "subjects": ["matematik", "turkce", "fizik", "kimya"],
                    "weekly_tests": 2,
                },
            },
        )

        exam_history = [
            {
                "exam_id": f"tyt_practice_{i}",
                "exam_type": "tyt",
                "date": (
                    datetime.now(timezone.utc) - timedelta(days=i * 7)
                ).isoformat(),
                "score": random.randint(300, 500),
                "duration_minutes": 135,
                "completed": True,
                "subjects": {
                    "matematik": {
                        "correct": random.randint(25, 40),
                        "wrong": random.randint(0, 15),
                        "empty": random.randint(0, 5),
                    },
                    "turkce": {
                        "correct": random.randint(30, 40),
                        "wrong": random.randint(0, 10),
                        "empty": random.randint(0, 5),
                    },
                    "fen": {
                        "correct": random.randint(15, 20),
                        "wrong": random.randint(0, 5),
                        "empty": random.randint(0, 3),
                    },
                    "sosyal": {
                        "correct": random.randint(15, 20),
                        "wrong": random.randint(0, 5),
                        "empty": random.randint(0, 3),
                    },
                },
            }
            for i in range(1, 6)
        ]

        return UserFixture(
            user=user,
            password="TestPass123!",
            profile_data=user.profile_data,
            exam_history=exam_history,
            session_data={
                "login_count": random.randint(50, 200),
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "device_info": {
                    "browser": "Chrome",
                    "os": "Windows 11",
                    "screen_resolution": "1920x1080",
                },
                "preferences": {
                    "theme": "light",
                    "font_size": "medium",
                    "sound_enabled": True,
                    "notifications_enabled": True,
                },
            },
        )

    def create_teacher_fixture(self, teacher_id: int = None) -> UserFixture:
        """Create comprehensive teacher user fixture"""
        teacher_id = teacher_id or random.randint(20000, 29999)

        user = AuthUser(
            user_id=teacher_id,
            username=f"teacher_{teacher_id}",
            email=f"teacher_{teacher_id}@school.edu.tr",
            role=UserRole.TEACHER,
            permissions=self.permission_manager.get_user_permissions(UserRole.TEACHER),
            is_active=True,
            is_verified=True,
            session_id=f"teacher_session_{uuid.uuid4()}",
            last_login=datetime.now(timezone.utc) - timedelta(minutes=30),
            profile_data={
                "first_name": f"Öğretmen{teacher_id}",
                "last_name": "Test",
                "title": "Matematik Öğretmeni",
                "subjects": ["matematik", "geometri"],
                "school": "Atatürk Anadolu Lisesi",
                "experience_years": random.randint(5, 25),
                "education": "Matematik Eğitimi Yüksek Lisans",
                "phone": f"532{teacher_id:04d}",
                "city": "Ankara",
            },
            exam_context={
                "teaching_subjects": ["matematik", "geometri"],
                "class_codes": ["12A", "12B", "11A"],
                "student_count": random.randint(60, 120),
                "content_creation": True,
            },
        )

        return UserFixture(
            user=user,
            password="TeacherPass456!",
            profile_data=user.profile_data,
            exam_history=[],  # Teachers don't take exams
            session_data={
                "content_created": random.randint(20, 100),
                "students_supervised": random.randint(50, 150),
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "permissions_level": "content_creator",
            },
        )

    def create_admin_fixture(self, admin_id: int = None) -> UserFixture:
        """Create comprehensive admin user fixture"""
        admin_id = admin_id or random.randint(30000, 39999)

        user = AuthUser(
            user_id=admin_id,
            username=f"admin_{admin_id}",
            email=f"admin_{admin_id}@kiro2.com",
            role=UserRole.ADMIN,
            permissions=self.permission_manager.get_user_permissions(UserRole.ADMIN),
            is_active=True,
            is_verified=True,
            session_id=f"admin_session_{uuid.uuid4()}",
            last_login=datetime.now(timezone.utc) - timedelta(minutes=10),
            profile_data={
                "first_name": f"Admin{admin_id}",
                "last_name": "System",
                "title": "Platform Yöneticisi",
                "department": "IT Operations",
                "access_level": "full",
                "phone": f"541{admin_id:04d}",
                "location": "İstanbul",
            },
            exam_context={
                "administrative_access": True,
                "monitoring_dashboard": True,
                "system_configuration": True,
            },
        )

        return UserFixture(
            user=user,
            password="AdminSecure789!",
            profile_data=user.profile_data,
            exam_history=[],
            session_data={
                "admin_actions_count": random.randint(100, 500),
                "system_monitoring": True,
                "last_login_ip": "192.168.1.100",
                "security_clearance": "level_5",
            },
        )

    # Exam Fixtures

    def create_tyt_exam_fixture(self, difficulty: str = "orta") -> ExamFixture:
        """Create comprehensive TYT exam fixture"""
        exam_id = f"tyt_exam_{uuid.uuid4().hex[:8]}"

        # Generate realistic TYT questions
        questions = []
        subjects = {"matematik": 40, "turkce": 40, "fen": 20, "sosyal": 20}

        question_id = 1
        for subject, count in subjects.items():
            for i in range(count):
                question = {
                    "question_id": question_id,
                    "subject": subject,
                    "subject_tr": {
                        "matematik": "Matematik",
                        "turkce": "Türkçe-Edebiyat",
                        "fen": "Fen Bilimleri",
                        "sosyal": "Sosyal Bilimler",
                    }.get(subject, subject),
                    "difficulty": difficulty,
                    "question_text": f"TYT {subject.title()} sorusu #{question_id}",
                    "question_text_tr": f"TYT {subject.title()} sorusu #{question_id}",
                    "options": [
                        {
                            "key": "A",
                            "text": f"Seçenek A - {question_id}",
                            "value": "option_a",
                        },
                        {
                            "key": "B",
                            "text": f"Seçenek B - {question_id}",
                            "value": "option_b",
                        },
                        {
                            "key": "C",
                            "text": f"Seçenek C - {question_id}",
                            "value": "option_c",
                        },
                        {
                            "key": "D",
                            "text": f"Seçenek D - {question_id}",
                            "value": "option_d",
                        },
                        {
                            "key": "E",
                            "text": f"Seçenek E - {question_id}",
                            "value": "option_e",
                        },
                    ],
                    "correct_answer": random.choice(["A", "B", "C", "D", "E"]),
                    "points": 1.0,
                    "explanation": f"Bu sorunun açıklaması #{question_id}",
                    "keywords": [subject, difficulty, "tyt"],
                    "estimated_time_seconds": random.randint(45, 90),
                    "statistics": {
                        "success_rate": random.uniform(0.3, 0.8),
                        "avg_time": random.randint(50, 80),
                        "attempted_count": random.randint(1000, 5000),
                    },
                }
                questions.append(question)
                question_id += 1

        # Generate realistic answers
        answers = []
        for question in questions:
            answer = {
                "question_id": question["question_id"],
                "selected_answer": random.choice(
                    ["A", "B", "C", "D", "E", None]
                ),  # Some unanswered
                "time_spent_seconds": random.randint(30, 120),
                "is_correct": None,  # Will be calculated
                "points_earned": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence_level": random.choice(["high", "medium", "low"]),
                "review_marked": random.choice([True, False]),
            }

            # Calculate correctness
            if answer["selected_answer"]:
                answer["is_correct"] = (
                    answer["selected_answer"] == question["correct_answer"]
                )
                answer["points_earned"] = (
                    question["points"] if answer["is_correct"] else 0
                )

            answers.append(answer)

        return ExamFixture(
            exam_id=exam_id,
            exam_type=TurkishExamType.TYT,
            questions=questions,
            answers=answers,
            metadata={
                "name": "Temel Yeterlilik Testi",
                "name_en": "Basic Proficiency Test",
                "duration_minutes": 135,
                "total_questions": 120,
                "subjects": ["matematik", "turkce", "fen", "sosyal"],
                "difficulty": difficulty,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "version": "2024.1",
                "instructions": {
                    "tr": "TYT sınavı talimatları...",
                    "en": "TYT exam instructions...",
                },
                "scoring": {
                    "correct_points": 4,
                    "wrong_penalty": -1,
                    "empty_points": 0,
                    "max_score": 500,
                },
            },
            session_config={
                "time_limit_minutes": 135,
                "allow_review": True,
                "show_timer": True,
                "auto_submit": True,
                "shuffle_questions": False,
                "shuffle_options": False,
                "pause_allowed": False,
                "calculator_allowed": False,
            },
        )

    def create_ayt_exam_fixture(
        self, field: str = "sayisal", difficulty: str = "orta"
    ) -> ExamFixture:
        """Create comprehensive AYT exam fixture"""
        exam_id = f"ayt_exam_{uuid.uuid4().hex[:8]}"

        # Subject distribution based on field
        subject_distributions = {
            "sayisal": {"matematik": 40, "fizik": 14, "kimya": 13, "biyoloji": 13},
            "sozel": {"tarih": 20, "cografya": 20, "felsefe": 20, "din": 20},
            "esit_agirlik": {
                "matematik": 40,
                "edebiyat": 24,
                "tarih": 10,
                "cografya": 6,
            },
        }

        subjects = subject_distributions.get(field, subject_distributions["sayisal"])
        questions = []

        question_id = 1
        for subject, count in subjects.items():
            for i in range(count):
                question = {
                    "question_id": question_id,
                    "subject": subject,
                    "subject_tr": {
                        "matematik": "Matematik",
                        "fizik": "Fizik",
                        "kimya": "Kimya",
                        "biyoloji": "Biyoloji",
                        "tarih": "Tarih",
                        "cografya": "Coğrafya",
                        "felsefe": "Felsefe",
                        "din": "Din Kültürü ve Ahlak Bilgisi",
                        "edebiyat": "Edebiyat",
                    }.get(subject, subject),
                    "field": field,
                    "difficulty": difficulty,
                    "question_text": f"AYT {subject.title()} sorusu #{question_id}",
                    "options": [
                        {"key": "A", "text": f"A seçeneği - {question_id}"},
                        {"key": "B", "text": f"B seçeneği - {question_id}"},
                        {"key": "C", "text": f"C seçeneği - {question_id}"},
                        {"key": "D", "text": f"D seçeneği - {question_id}"},
                        {"key": "E", "text": f"E seçeneği - {question_id}"},
                    ],
                    "correct_answer": random.choice(["A", "B", "C", "D", "E"]),
                    "points": 1.0,
                    "explanation": f"AYT {subject} sorusu açıklaması",
                    "estimated_time_seconds": random.randint(60, 180),
                }
                questions.append(question)
                question_id += 1

        return ExamFixture(
            exam_id=exam_id,
            exam_type=TurkishExamType.AYT,
            questions=questions,
            answers=[],  # Will be generated during test
            metadata={
                "name": "Alan Yeterlilik Testi",
                "field": field,
                "field_tr": {
                    "sayisal": "Sayısal",
                    "sozel": "Sözel",
                    "esit_agirlik": "Eşit Ağırlık",
                }.get(field, field),
                "duration_minutes": 180,
                "total_questions": sum(subjects.values()),
                "difficulty": difficulty,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            session_config={
                "time_limit_minutes": 180,
                "allow_review": True,
                "show_timer": True,
                "calculator_allowed": True if field == "sayisal" else False,
            },
        )

    # API Request Fixtures

    def create_login_request_fixture(
        self, user_fixture: UserFixture
    ) -> APIRequestFixture:
        """Create login API request fixture"""
        request = APIRequest(
            id=str(uuid.uuid4()),
            method=HTTPMethod.POST,
            path="/auth/login",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "KIRO2-Test-Client/1.0",
                "Accept-Language": "tr-TR,tr;q=0.9",
            },
            query_params={},
            body={
                "email": user_fixture.user.email,
                "password": user_fixture.password,
                "remember_me": False,
                "client_info": {
                    "browser": "Chrome",
                    "version": "120.0",
                    "os": "Windows 11",
                    "screen_size": "1920x1080",
                },
            },
            client_ip="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            route_type=RouteType.AUTH,
            metadata={},
        )

        expected_response = APIResponse(
            request_id=request.id,
            status_code=200,
            headers={"Content-Type": "application/json"},
            body={
                "success": True,
                "message": "Login successful",
                "message_tr": "Giriş başarılı",
                "user": {
                    "id": user_fixture.user.user_id,
                    "username": user_fixture.user.username,
                    "role": user_fixture.user.role.value,
                    "permissions": [p.value for p in user_fixture.user.permissions],
                },
                "tokens": {
                    "access_token": "mock_access_token",
                    "refresh_token": "mock_refresh_token",
                    "session_id": user_fixture.user.session_id,
                    "expires_in": 1800,
                },
                "platform_info": {
                    "name": "KIRO2 - Türkiye Üniversite Sınavları Hazırlık Platformu",
                    "version": "2024.1",
                },
            },
            processing_time_ms=50.0,
            cached=False,
        )

        return APIRequestFixture(
            request=request,
            expected_response=expected_response,
            user_context=user_fixture.user,
            test_scenario="successful_login",
            validation_rules=[
                {"field": "email", "required": True, "type": "email"},
                {"field": "password", "required": True, "min_length": 8},
            ],
        )

    def create_exam_start_request_fixture(
        self, user_fixture: UserFixture, exam_fixture: ExamFixture
    ) -> APIRequestFixture:
        """Create exam start API request fixture"""
        exam_path = f"/exams/{exam_fixture.exam_type.value}/start"

        request = APIRequest(
            id=str(uuid.uuid4()),
            method=HTTPMethod.POST,
            path=exam_path,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {user_fixture.user.session_id}",
                "X-User-ID": str(user_fixture.user.user_id),
                "Accept-Language": "tr-TR",
            },
            query_params={},
            body={
                "exam_type": exam_fixture.exam_type.value,
                "session_type": "practice",
                "difficulty": exam_fixture.metadata.get("difficulty", "orta"),
                "duration_minutes": exam_fixture.metadata["duration_minutes"],
                "settings": {
                    "show_timer": True,
                    "allow_review": True,
                    "shuffle_questions": False,
                },
            },
            client_ip="192.168.1.100",
            user_agent="KIRO2-Exam-Client/1.0",
            route_type=RouteType.TYT_EXAM
            if exam_fixture.exam_type == TurkishExamType.TYT
            else RouteType.AYT_EXAM,
            user_id=user_fixture.user.user_id,
            session_id=user_fixture.user.session_id,
            metadata={"auth_context": user_fixture.user},
        )

        expected_response = APIResponse(
            request_id=request.id,
            status_code=200,
            headers={"Content-Type": "application/json"},
            body={
                "success": True,
                "message": "Exam session started",
                "message_tr": "Sınav oturumu başlatıldı",
                "session_id": exam_fixture.exam_id,
                "exam_info": {
                    "exam_type": exam_fixture.exam_type.value,
                    "exam_name": exam_fixture.metadata["name"],
                    "total_questions": exam_fixture.metadata["total_questions"],
                    "duration_minutes": exam_fixture.metadata["duration_minutes"],
                    "subjects": exam_fixture.metadata["subjects"],
                },
                "first_question": exam_fixture.questions[0]
                if exam_fixture.questions
                else None,
                "navigation": {
                    "current_question": 1,
                    "total_questions": len(exam_fixture.questions),
                    "can_go_back": True,
                    "can_skip": True,
                },
                "timer": {
                    "total_seconds": exam_fixture.metadata["duration_minutes"] * 60,
                    "remaining_seconds": exam_fixture.metadata["duration_minutes"] * 60,
                    "show_warnings": True,
                },
            },
            processing_time_ms=100.0,
            cached=False,
        )

        return APIRequestFixture(
            request=request,
            expected_response=expected_response,
            user_context=user_fixture.user,
            test_scenario="exam_start_success",
            validation_rules=[
                {
                    "field": "exam_type",
                    "required": True,
                    "allowed_values": ["tyt", "ayt"],
                },
                {
                    "field": "session_type",
                    "required": True,
                    "allowed_values": ["practice", "simulation", "real"],
                },
            ],
        )

    # Database Test Data Fixtures

    def create_database_fixtures(self) -> Dict[str, List[Dict[str, Any]]]:
        """Create comprehensive database test fixtures"""
        return {
            "users": [
                {
                    "id": 10001,
                    "username": "test_student_1",
                    "email": "student1@test.edu.tr",
                    "password_hash": "$2b$12$hash1",
                    "role": "student",
                    "is_active": True,
                    "is_verified": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "profile_data": json.dumps(
                        {"name": "Test Öğrenci 1", "school": "Test Lisesi", "grade": 12}
                    ),
                },
                {
                    "id": 20001,
                    "username": "test_teacher_1",
                    "email": "teacher1@school.edu.tr",
                    "password_hash": "$2b$12$hash2",
                    "role": "teacher",
                    "is_active": True,
                    "is_verified": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "profile_data": json.dumps(
                        {
                            "name": "Test Öğretmen 1",
                            "subjects": ["matematik"],
                            "school": "Test Lisesi",
                        }
                    ),
                },
            ],
            "exam_sessions": [
                {
                    "id": "session_001",
                    "user_id": 10001,
                    "exam_type": "tyt",
                    "status": "completed",
                    "started_at": "2024-01-15T10:00:00Z",
                    "completed_at": "2024-01-15T12:15:00Z",
                    "score": 450,
                    "answers": json.dumps(
                        [
                            {"question_id": 1, "selected": "A", "correct": True},
                            {"question_id": 2, "selected": "B", "correct": False},
                        ]
                    ),
                }
            ],
            "exam_questions": [
                {
                    "id": 1,
                    "subject": "matematik",
                    "difficulty": "orta",
                    "question_text": "Test matematik sorusu",
                    "options": json.dumps(
                        [
                            {"key": "A", "text": "Seçenek A"},
                            {"key": "B", "text": "Seçenek B"},
                            {"key": "C", "text": "Seçenek C"},
                            {"key": "D", "text": "Seçenek D"},
                            {"key": "E", "text": "Seçenek E"},
                        ]
                    ),
                    "correct_answer": "A",
                    "explanation": "Matematik sorusu açıklaması",
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
            "system_logs": [
                {
                    "id": 1,
                    "level": "INFO",
                    "message": "User login successful",
                    "user_id": 10001,
                    "timestamp": "2024-01-15T10:00:00Z",
                    "metadata": json.dumps({"ip": "192.168.1.100"}),
                }
            ],
            "cache_entries": [
                {
                    "key": "user_session:10001",
                    "value": json.dumps(
                        {
                            "user_id": 10001,
                            "session_id": "session_123",
                            "expires_at": "2024-01-15T12:00:00Z",
                        }
                    ),
                    "ttl": 3600,
                    "created_at": "2024-01-15T10:00:00Z",
                }
            ],
        }

    # Performance Test Data

    def create_load_test_users(self, count: int = 1000) -> List[UserFixture]:
        """Create users for load testing"""
        users = []

        for i in range(count):
            student_id = 50000 + i
            user_fixture = self.create_student_fixture(student_id)

            # Vary user characteristics for realistic load testing
            user_fixture.user.profile_data["city"] = random.choice(
                ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya"]
            )
            user_fixture.user.exam_context["target_exam"] = random.choice(
                ["YKS 2024", "YKS 2025"]
            )

            users.append(user_fixture)

        return users

    # Error Scenario Fixtures

    def create_error_scenarios(self) -> List[Dict[str, Any]]:
        """Create comprehensive error scenario fixtures"""
        return [
            {
                "scenario": "invalid_login_credentials",
                "request": {
                    "path": "/auth/login",
                    "method": "POST",
                    "body": {"email": "invalid@test.com", "password": "wrongpass"},
                },
                "expected_status": 401,
                "expected_error": "Invalid credentials",
            },
            {
                "scenario": "unauthorized_exam_access",
                "request": {
                    "path": "/exams/tyt/start",
                    "method": "POST",
                    "headers": {"Authorization": "Bearer invalid_token"},
                },
                "expected_status": 401,
                "expected_error": "Authentication Required",
            },
            {
                "scenario": "exam_session_expired",
                "request": {
                    "path": "/exams/tyt/question/1",
                    "method": "GET",
                    "session_expired": True,
                },
                "expected_status": 408,
                "expected_error": "Session expired",
            },
            {
                "scenario": "rate_limit_exceeded",
                "request": {
                    "path": "/auth/login",
                    "method": "POST",
                    "repeat_count": 20,  # Exceed rate limit
                },
                "expected_status": 429,
                "expected_error": "Rate Limit Exceeded",
            },
            {
                "scenario": "invalid_request_validation",
                "request": {
                    "path": "/exams/tyt/start",
                    "method": "POST",
                    "body": {
                        "exam_type": "invalid",
                        "duration_minutes": "not_a_number",
                    },
                },
                "expected_status": 400,
                "expected_error": "Validation Failed",
            },
        ]


# Global fixture instances
turkish_exam_fixtures = TurkishExamFixtures()

# Pytest fixtures


@pytest.fixture
def student_fixture():
    """Student user fixture"""
    return turkish_exam_fixtures.create_student_fixture()


@pytest.fixture
def teacher_fixture():
    """Teacher user fixture"""
    return turkish_exam_fixtures.create_teacher_fixture()


@pytest.fixture
def admin_fixture():
    """Admin user fixture"""
    return turkish_exam_fixtures.create_admin_fixture()


@pytest.fixture
def tyt_exam_fixture():
    """TYT exam fixture"""
    return turkish_exam_fixtures.create_tyt_exam_fixture()


@pytest.fixture
def ayt_exam_fixture():
    """AYT exam fixture"""
    return turkish_exam_fixtures.create_ayt_exam_fixture()


@pytest.fixture
def login_request_fixture(student_fixture):
    """Login API request fixture"""
    return turkish_exam_fixtures.create_login_request_fixture(student_fixture)


@pytest.fixture
def exam_start_request_fixture(student_fixture, tyt_exam_fixture):
    """Exam start API request fixture"""
    return turkish_exam_fixtures.create_exam_start_request_fixture(
        student_fixture, tyt_exam_fixture
    )


@pytest.fixture
def database_fixtures():
    """Database test data fixtures"""
    return turkish_exam_fixtures.create_database_fixtures()


@pytest.fixture
def load_test_users():
    """Load test users fixture"""
    return turkish_exam_fixtures.create_load_test_users(
        100
    )  # Smaller count for regular tests


@pytest.fixture
def error_scenarios():
    """Error scenario fixtures"""
    return turkish_exam_fixtures.create_error_scenarios()


# Async fixtures for system components


@pytest_asyncio.fixture
async def monitoring_middleware():
    """Monitoring middleware fixture"""
    config = {"monitoring_level": "comprehensive"}
    return create_monitoring_middleware(config)


@pytest_asyncio.fixture
async def turkish_language_middleware():
    """Turkish language middleware fixture"""
    return create_turkish_language_middleware()


@pytest_asyncio.fixture
async def exam_security_middleware():
    """Exam security middleware fixture"""
    return create_exam_security_middleware()


@pytest_asyncio.fixture
async def exam_session_middleware():
    """Exam session middleware fixture"""
    return create_exam_session_middleware()


# Fixture combinations for complex testing scenarios


@pytest.fixture
def complete_exam_scenario(student_fixture, tyt_exam_fixture):
    """Complete exam scenario with user, exam, and expected flow"""
    return {
        "user": student_fixture,
        "exam": tyt_exam_fixture,
        "expected_duration": 135,  # minutes
        "expected_questions": 120,
        "success_criteria": {
            "min_score": 200,
            "completion_rate": 0.8,
            "avg_time_per_question": 60,  # seconds
        },
    }


@pytest.fixture
def multi_user_scenario():
    """Multi-user testing scenario"""
    return {
        "students": [
            turkish_exam_fixtures.create_student_fixture(i) for i in range(10001, 10011)
        ],
        "teachers": [
            turkish_exam_fixtures.create_teacher_fixture(i) for i in range(20001, 20003)
        ],
        "admin": turkish_exam_fixtures.create_admin_fixture(30001),
        "concurrent_exam_sessions": 5,
        "expected_system_load": "moderate",
    }


@pytest.fixture
def turkish_localization_test_data():
    """Turkish localization test data"""
    return {
        "exam_terms": {
            "tyt": "Temel Yeterlilik Testi",
            "ayt": "Alan Yeterlilik Testi",
            "yks": "Yükseköğretim Kurumları Sınavı",
        },
        "subjects": {
            "matematik": "Matematik",
            "turkce": "Türkçe-Edebiyat",
            "fizik": "Fizik",
            "kimya": "Kimya",
            "biyoloji": "Biyoloji",
            "tarih": "Tarih",
            "cografya": "Coğrafya",
        },
        "messages": {
            "exam_started": "Sınav başlatıldı",
            "exam_completed": "Sınav tamamlandı",
            "time_warning": "Zaman uyarısı",
            "session_expired": "Oturum süresi doldu",
        },
        "date_formats": {"turkish": "%d.%m.%Y %H:%M", "timezone": "Europe/Istanbul"},
    }


if __name__ == "__main__":
    # Example usage and testing of fixtures
    fixtures = TurkishExamFixtures()

    # Create sample fixtures
    student = fixtures.create_student_fixture()
    teacher = fixtures.create_teacher_fixture()
    tyt_exam = fixtures.create_tyt_exam_fixture()

    print(f"Created student: {student.user.username}")
    print(f"Created teacher: {teacher.user.username}")
    print(f"Created TYT exam with {len(tyt_exam.questions)} questions")

    # Test API request fixtures
    login_fixture = fixtures.create_login_request_fixture(student)
    print(f"Login request for: {login_fixture.request.body['email']}")

    exam_start_fixture = fixtures.create_exam_start_request_fixture(student, tyt_exam)
    print(f"Exam start request: {exam_start_fixture.request.path}")

    def test_basic_assertion(self):
        # Verify fixtures module is working
        assert fixtures is not None
        assert callable(fixtures.create_exam_start_request_fixture)
