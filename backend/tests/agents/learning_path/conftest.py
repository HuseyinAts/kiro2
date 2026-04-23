"""
Test Fixtures for Learning Path Agent
Teknofest 2025 - Eğitim Eylemci Projesi

Provides reusable test fixtures, factories, and mock objects for
testing the Learning Path Agent and its components.

Fixture Categories:
- Student Profile fixtures
- Learning Resource fixtures (YouTube, Khan Academy, OER)
- Learning Path fixtures
- Assessment fixtures
- Mock external services (DB, Redis, LLM)
- Factory functions for customizable test data

Turkish Data Support:
- All fixtures contain Turkish characters (İ, ı, ş, ğ, ü, ö, ç)
- YKS/TYT/AYT exam topics
- Maarif curriculum subjects
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest

from agents.learning_path.models import (
    KnowledgeLevel,
    LearningResource,
    LearningStyle,
    StudentProfile,
)

# =============================================================================
# STUDENT PROFILE FIXTURES
# =============================================================================


@pytest.fixture
def mock_student_profile() -> dict[str, Any]:
    """
    Mock student profile data with Turkish content.

    Returns a typical 12th grade YKS-AYT student profile
    with visual learning preference and mathematics focus.

    Example:
        >>> def test_something(mock_student_profile):
        ...     student_id = mock_student_profile["student_id"]
    """
    return {
        "student_id": "test-student-001",
        "name": "Ahmet Yılmaz",
        "grade": "12",
        "exam_target": "YKS-AYT",
        "learning_goal": "Matematik ve Fizik konularında YKS'ye hazırlanmak",
        "learning_style": "visual",
        "knowledge_level": "intermediate",
        "interests": ["matematik", "fizik", "geometri", "türev ve integral"],
        "available_time": 240,  # 4 hours
        "metadata": {
            "province": "İstanbul",
            "school_type": "Anadolu Lisesi",
            "target_university": "İTÜ Mühendislik",
            "weak_subjects": ["kimya organik", "biyoloji hücre"],
            "strong_subjects": ["matematik analiz", "fizik mekanik"],
        },
    }


@pytest.fixture
def mock_student_profile_beginner() -> dict[str, Any]:
    """Mock beginner level student profile (9th grade, LGS prep)"""
    return {
        "student_id": "test-student-beginner",
        "name": "Zeynep Şahin",
        "grade": "9",
        "exam_target": "LGS",
        "learning_goal": "Matematik temellerini güçlendirmek",
        "learning_style": "kinesthetic",
        "knowledge_level": "beginner",
        "interests": ["matematik", "fen bilimleri"],
        "available_time": 120,  # 2 hours
        "metadata": {
            "province": "Ankara",
            "school_type": "Ortaokul",
        },
    }


@pytest.fixture
def mock_student_profile_advanced() -> dict[str, Any]:
    """Mock advanced level student profile (12th grade, top performer)"""
    return {
        "student_id": "test-student-advanced",
        "name": "Mehmet Özdemir",
        "grade": "12",
        "exam_target": "YKS-TYT-AYT",
        "learning_goal": "Üniversite sınavında ilk 1000'e girmek",
        "learning_style": "mixed",
        "knowledge_level": "advanced",
        "interests": [
            "ileri matematik",
            "fizik elektrik",
            "kimya",
            "biyoloji",
        ],
        "available_time": 360,  # 6 hours
        "metadata": {
            "province": "İzmir",
            "school_type": "Fen Lisesi",
            "target_university": "Boğaziçi Üniversitesi",
            "current_rank": 2500,
        },
    }


def create_student_profile(**overrides) -> dict[str, Any]:
    """
    Factory function to create customizable student profiles.

    Args:
        **overrides: Any field to override in the default profile

    Returns:
        Dict containing student profile data

    Example:
        >>> profile = create_student_profile(
        ...     name="Ayşe Yılmaz",
        ...     grade="10",
        ...     learning_style="auditory"
        ... )
    """
    defaults = {
        "student_id": f"test-student-{uuid4().hex[:8]}",
        "name": "Test Öğrenci",
        "grade": "11",
        "exam_target": "YKS-TYT",
        "learning_goal": "Matematik ve Türkçe konularında gelişmek",
        "learning_style": "visual",
        "knowledge_level": "intermediate",
        "interests": ["matematik", "türkçe", "tarih"],
        "available_time": 180,
        "metadata": {},
    }
    return {**defaults, **overrides}


@pytest.fixture
def student_profile_obj(mock_student_profile: dict[str, Any]) -> StudentProfile:
    """
    StudentProfile object fixture (actual dataclass instance).

    Useful for testing methods that require StudentProfile objects
    rather than dictionaries.
    """
    return StudentProfile(
        student_id=mock_student_profile["student_id"],
        name=mock_student_profile["name"],
        grade=mock_student_profile["grade"],
        exam_target=mock_student_profile["exam_target"],
        learning_goal=mock_student_profile["learning_goal"],
        learning_style=LearningStyle(mock_student_profile["learning_style"]),
        knowledge_level=KnowledgeLevel(mock_student_profile["knowledge_level"]),
        interests=mock_student_profile["interests"],
        available_time=mock_student_profile["available_time"],
        metadata=mock_student_profile["metadata"],
    )


# =============================================================================
# LEARNING RESOURCE FIXTURES
# =============================================================================


@pytest.fixture
def mock_youtube_resource() -> dict[str, Any]:
    """Mock YouTube video resource (Turkish mathematics content)"""
    return {
        "resource_id": "yt-video-001",
        "title": "Türev ve İntegral - Konu Anlatımı",
        "source": "YouTube",
        "url": "https://youtube.com/watch?v=example001",
        "resource_type": "video",
        "difficulty_level": "intermediate",
        "estimated_time": 15,
        "language": "tr",
        "description": "Türev ve integral kavramlarının temellerini anlatan kapsamlı video",
        "tags": ["matematik", "türev", "integral", "YKS", "AYT"],
        "rating": 4.5,
        "metadata": {
            "views": 125000,
            "likes": 5800,
            "channel": "Matematik Hocası",
            "duration_seconds": 900,
            "thumbnail_url": "https://example.com/thumb.jpg",
            "upload_date": "2024-01-15",
        },
    }


@pytest.fixture
def mock_khan_resource() -> dict[str, Any]:
    """Mock Khan Academy resource (Turkish localized)"""
    return {
        "resource_id": "khan-exercise-001",
        "title": "Fonksiyonlar - Alıştırma Seti",
        "source": "Khan Academy",
        "url": "https://tr.khanacademy.org/math/functions",
        "resource_type": "interactive",
        "difficulty_level": "beginner",
        "estimated_time": 20,
        "language": "tr",
        "description": "Fonksiyonlar konusunda interaktif alıştırmalar",
        "tags": ["matematik", "fonksiyonlar", "alıştırma"],
        "rating": 4.8,
        "metadata": {
            "exercise_count": 15,
            "difficulty_progression": True,
            "hints_available": True,
        },
    }


@pytest.fixture
def mock_oer_resource() -> dict[str, Any]:
    """Mock Open Educational Resource (OER)"""
    return {
        "resource_id": "oer-article-001",
        "title": "Osmanlı İmparatorluğu Tarihi",
        "source": "Wikipedia",
        "url": "https://tr.wikipedia.org/wiki/Osmanli_Imparatorlugu",
        "resource_type": "article",
        "difficulty_level": "intermediate",
        "estimated_time": 25,
        "language": "tr",
        "description": "Osmanlı İmparatorluğu'nun kuruluşundan yıkılışına detaylı makale",
        "tags": ["tarih", "osmanlı", "YKS", "TYT"],
        "rating": 4.2,
        "metadata": {
            "word_count": 5000,
            "references": 45,
            "last_updated": "2024-02-10",
        },
    }


@pytest.fixture
def mock_eba_resource() -> dict[str, Any]:
    """Mock EBA (Eğitim Bilişim Ağı) resource"""
    return {
        "resource_id": "eba-video-001",
        "title": "Fizik - Hareket ve Kuvvet",
        "source": "EBA",
        "url": "https://eba.gov.tr/fizik/hareket-kuvvet",
        "resource_type": "video",
        "difficulty_level": "intermediate",
        "estimated_time": 18,
        "language": "tr",
        "description": "MEB onaylı fizik dersi - hareket ve kuvvet konuları",
        "tags": ["fizik", "hareket", "kuvvet", "MEB", "Maarif"],
        "rating": 4.6,
        "metadata": {
            "meb_approved": True,
            "curriculum_aligned": True,
            "grade_levels": ["9", "10", "11"],
        },
    }


def create_learning_resource(
    platform: str = "youtube",
    difficulty: str = "intermediate",
    **overrides
) -> dict[str, Any]:
    """
    Factory function to create customizable learning resources.

    Args:
        platform: Platform name (youtube, khan, oer, eba)
        difficulty: Difficulty level (beginner, intermediate, advanced)
        **overrides: Any field to override

    Returns:
        Dict containing learning resource data

    Example:
        >>> resource = create_learning_resource(
        ...     platform="khan",
        ...     title="Özel Fonksiyonlar",
        ...     estimated_time=30
        ... )
    """
    platform_defaults = {
        "youtube": {
            "source": "YouTube",
            "resource_type": "video",
            "url": f"https://youtube.com/watch?v={uuid4().hex[:8]}",
        },
        "khan": {
            "source": "Khan Academy",
            "resource_type": "interactive",
            "url": "https://tr.khanacademy.org/",
        },
        "oer": {
            "source": "Wikipedia",
            "resource_type": "article",
            "url": "https://tr.wikipedia.org/",
        },
        "eba": {
            "source": "EBA",
            "resource_type": "video",
            "url": "https://eba.gov.tr/",
        },
    }

    defaults = {
        "resource_id": f"{platform}-{uuid4().hex[:8]}",
        "title": "Test Kaynağı - Matematik",
        "difficulty_level": difficulty,
        "estimated_time": 15,
        "language": "tr",
        "description": "Test amaçlı eğitim kaynağı",
        "tags": ["matematik", "test"],
        "rating": 4.0,
        "metadata": {},
        **platform_defaults.get(platform.lower(), {}),
    }

    return {**defaults, **overrides}


@pytest.fixture
def learning_resource_obj(mock_youtube_resource: dict[str, Any]) -> LearningResource:
    """LearningResource object fixture (actual dataclass instance)"""
    return LearningResource(
        resource_id=mock_youtube_resource["resource_id"],
        title=mock_youtube_resource["title"],
        source=mock_youtube_resource["source"],
        url=mock_youtube_resource["url"],
        resource_type=mock_youtube_resource["resource_type"],
        difficulty_level=KnowledgeLevel(mock_youtube_resource["difficulty_level"]),
        estimated_time=mock_youtube_resource["estimated_time"],
        language=mock_youtube_resource["language"],
        description=mock_youtube_resource["description"],
        tags=mock_youtube_resource["tags"],
        rating=mock_youtube_resource["rating"],
        metadata=mock_youtube_resource["metadata"],
    )


# =============================================================================
# LEARNING PATH FIXTURES
# =============================================================================


@pytest.fixture
def mock_learning_path() -> dict[str, Any]:
    """Mock complete learning path with multiple phases"""
    return {
        "path_id": "path-001",
        "student_id": "test-student-001",
        "goal": "Matematik ve Fizik YKS Hazırlık",
        "resources": [
            create_learning_resource(platform="youtube", title="Türev Giriş"),
            create_learning_resource(platform="khan", title="Türev Alıştırma"),
            create_learning_resource(platform="youtube", title="İntegral Giriş"),
            create_learning_resource(platform="khan", title="İntegral Alıştırma"),
        ],
        "phases": [
            {
                "phase_id": "phase-001",
                "name": "Temel Kavramlar",
                "description": "Türev ve integral temel kavramlarını öğrenme",
                "order": 1,
                "resources": [],
                "learning_objectives": [
                    "Türev kavramını anlama",
                    "Türev alma kurallarını öğrenme",
                ],
                "metadata": {},
            },
            {
                "phase_id": "phase-002",
                "name": "Uygulama ve Alıştırma",
                "description": "Konuları pekiştirmek için alıştırmalar",
                "order": 2,
                "resources": [],
                "learning_objectives": [
                    "Türev sorularını çözme",
                    "İntegral hesaplama",
                ],
                "metadata": {},
            },
        ],
        "created_at": datetime.now().isoformat(),
        "reasoning": "Öğrencinin görsel öğrenme stiline uygun, matematik odaklı yol",
        "metadata": {
            "total_duration_minutes": 60,
            "estimated_completion_days": 7,
            "difficulty_distribution": {
                "beginner": 1,
                "intermediate": 2,
                "advanced": 1,
            },
        },
    }


def create_learning_path(
    num_phases: int = 3,
    resources_per_phase: int = 2,
    **overrides
) -> dict[str, Any]:
    """
    Factory function to create customizable learning paths.

    Args:
        num_phases: Number of phases to create
        resources_per_phase: Resources per phase
        **overrides: Any field to override

    Returns:
        Dict containing learning path data

    Example:
        >>> path = create_learning_path(
        ...     num_phases=4,
        ...     resources_per_phase=3,
        ...     goal="Fizik Hazırlık"
        ... )
    """
    resources = []
    phases = []

    for phase_idx in range(num_phases):
        phase_resources = [
            create_learning_resource(title=f"Kaynak {phase_idx}-{r}")
            for r in range(resources_per_phase)
        ]
        resources.extend(phase_resources)

        phases.append({
            "phase_id": f"phase-{phase_idx:03d}",
            "name": f"Aşama {phase_idx + 1}",
            "description": f"Öğrenme aşaması {phase_idx + 1}",
            "order": phase_idx + 1,
            "resources": phase_resources,
            "learning_objectives": [f"Hedef {phase_idx}-{i}" for i in range(2)],
            "metadata": {},
        })

    defaults = {
        "path_id": f"path-{uuid4().hex[:8]}",
        "student_id": "test-student-001",
        "goal": "Test Öğrenme Yolu",
        "resources": resources,
        "phases": phases,
        "created_at": datetime.now().isoformat(),
        "reasoning": "Test amaçlı oluşturulmuş öğrenme yolu",
        "metadata": {},
    }

    return {**defaults, **overrides}


# =============================================================================
# ASSESSMENT FIXTURES
# =============================================================================


@pytest.fixture
def mock_assessment() -> dict[str, Any]:
    """Mock assessment/quiz data"""
    return {
        "assessment_id": "assessment-001",
        "title": "Türev Değerlendirme Testi",
        "subject": "Matematik - Türev",
        "difficulty": "intermediate",
        "questions": [
            {
                "question_id": "q001",
                "text": "f(x) = x² + 3x fonksiyonunun türevi nedir?",
                "type": "multiple_choice",
                "options": [
                    "2x + 3",
                    "x² + 3",
                    "2x",
                    "x + 3",
                ],
                "correct_answer": "2x + 3",
                "explanation": "Türev alma kuralları gereği x²'nin türevi 2x, 3x'in türevi 3'tür.",
                "irt_difficulty": 0.2,
                "irt_discrimination": 1.5,
            },
            {
                "question_id": "q002",
                "text": "f(x) = sin(x) fonksiyonunun türevi nedir?",
                "type": "multiple_choice",
                "options": [
                    "cos(x)",
                    "-cos(x)",
                    "sin(x)",
                    "-sin(x)",
                ],
                "correct_answer": "cos(x)",
                "explanation": "sin(x) fonksiyonunun türevi cos(x)'dir.",
                "irt_difficulty": -0.5,
                "irt_discrimination": 1.8,
            },
        ],
        "estimated_time": 10,
        "metadata": {
            "topic": "Türev Alma Kuralları",
            "curriculum": "YKS-AYT Matematik",
        },
    }


def create_assessment(
    num_questions: int = 5,
    difficulty: str = "intermediate",
    **overrides
) -> dict[str, Any]:
    """
    Factory function to create customizable assessments.

    Args:
        num_questions: Number of questions to generate
        difficulty: Assessment difficulty level
        **overrides: Any field to override

    Returns:
        Dict containing assessment data
    """
    questions = []
    for i in range(num_questions):
        questions.append({
            "question_id": f"q{i:03d}",
            "text": f"Test sorusu {i + 1}",
            "type": "multiple_choice",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "explanation": f"Açıklama {i + 1}",
            "irt_difficulty": (i - num_questions / 2) / num_questions,
            "irt_discrimination": 1.5,
        })

    defaults = {
        "assessment_id": f"assessment-{uuid4().hex[:8]}",
        "title": "Test Değerlendirme",
        "subject": "Matematik",
        "difficulty": difficulty,
        "questions": questions,
        "estimated_time": num_questions * 2,
        "metadata": {},
    }

    return {**defaults, **overrides}


# =============================================================================
# MOCK EXTERNAL SERVICES
# =============================================================================


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """
    Mock AsyncSession for database operations.

    Provides async context manager support and common DB methods.
    """
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.query = MagicMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """
    Mock Redis client for caching operations.

    Provides get, set, delete, and TTL operations.
    """
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.expire = AsyncMock(return_value=True)
    redis_mock.ttl = AsyncMock(return_value=-1)
    redis_mock.keys = AsyncMock(return_value=[])
    return redis_mock


@pytest.fixture
def mock_llm_service() -> Mock:
    """
    Mock LLM (Language Model) service for AI operations.

    Provides text generation, embeddings, and reasoning capabilities.
    """
    llm_mock = Mock()

    # Text generation
    llm_mock.generate_text = AsyncMock(
        return_value="Mocked LLM response in Turkish"
    )

    # Chat completion
    llm_mock.chat_completion = AsyncMock(
        return_value={
            "response": "Mocked chat response",
            "tokens_used": 150,
        }
    )

    # Embeddings
    llm_mock.create_embedding = AsyncMock(
        return_value=[0.1] * 768  # 768-dim embedding
    )

    # Reasoning
    llm_mock.reason = AsyncMock(
        return_value={
            "reasoning": "Mocked reasoning process",
            "conclusion": "Mocked conclusion",
        }
    )

    return llm_mock


@pytest.fixture
def mock_youtube_api() -> Mock:
    """Mock YouTube API client"""
    youtube_mock = Mock()
    youtube_mock.search_videos = AsyncMock(
        return_value=[
            create_learning_resource(platform="youtube", title=f"Video {i}")
            for i in range(5)
        ]
    )
    youtube_mock.get_video_details = AsyncMock(
        return_value=create_learning_resource(platform="youtube")
    )
    return youtube_mock


@pytest.fixture
def mock_khan_api() -> Mock:
    """Mock Khan Academy API client"""
    khan_mock = Mock()
    khan_mock.search_resources = AsyncMock(
        return_value=[
            create_learning_resource(platform="khan", title=f"Exercise {i}")
            for i in range(5)
        ]
    )
    return khan_mock


# =============================================================================
# TURKISH TEST DATA COLLECTIONS
# =============================================================================


@pytest.fixture
def turkish_subjects() -> list[str]:
    """Common Turkish education subjects with Turkish characters"""
    return [
        "Matematik",
        "Fizik",
        "Kimya",
        "Biyoloji",
        "Türkçe",
        "Edebiyat",
        "Tarih",
        "Coğrafya",
        "Felsefe",
        "İngilizce",
    ]


@pytest.fixture
def yks_topics() -> dict[str, list[str]]:
    """YKS exam topics by subject"""
    return {
        "matematik": [
            "Türev ve İntegral",
            "Fonksiyonlar",
            "Limit ve Süreklilik",
            "Geometri",
            "Olasılık",
        ],
        "fizik": [
            "Hareket ve Kuvvet",
            "Enerji",
            "Elektrik ve Manyetizma",
            "Dalgalar",
            "Modern Fizik",
        ],
        "kimya": [
            "Atom ve Periyodik Sistem",
            "Kimyasal Bağlar",
            "Asit-Baz Dengeleri",
            "Elektrokimya",
            "Organik Kimya",
        ],
        "biyoloji": [
            "Hücre Bölünmesi",
            "Genetik",
            "Ekosistem",
            "İnsan Fizyolojisi",
            "Evrim",
        ],
    }


@pytest.fixture
def turkish_names() -> list[str]:
    """Common Turkish student names with Turkish characters"""
    return [
        "Ahmet Yılmaz",
        "Ayşe Demir",
        "Mehmet Şahin",
        "Fatma Öztürk",
        "Mustafa Çelik",
        "Zeynep Kaya",
        "Ali Özdemir",
        "Emine Yıldız",
        "Hüseyin Arslan",
        "Hatice Aydın",
    ]


# =============================================================================
# COMPOSITE FIXTURES (Full Test Scenarios)
# =============================================================================


@pytest.fixture
def complete_learning_scenario(
    mock_student_profile: dict[str, Any],
    mock_learning_path: dict[str, Any],
    mock_assessment: dict[str, Any],
) -> dict[str, Any]:
    """
    Complete learning scenario with student, path, and assessment.

    Useful for integration tests that need a full workflow.
    """
    return {
        "student": mock_student_profile,
        "learning_path": mock_learning_path,
        "assessment": mock_assessment,
        "completed_resources": [],
        "progress_percentage": 0.0,
    }


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


@pytest.fixture(autouse=True)
def reset_caches():
    """
    Auto-use fixture to reset any module-level caches between tests.

    Ensures test isolation.
    """
    # Clear any LRU caches
    from agents.learning_path.config import get_learning_path_config
    get_learning_path_config.cache_clear()

    yield

    # Cleanup after test
    get_learning_path_config.cache_clear()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Student fixtures
    "mock_student_profile",
    "mock_student_profile_beginner",
    "mock_student_profile_advanced",
    "student_profile_obj",
    "create_student_profile",
    # Resource fixtures
    "mock_youtube_resource",
    "mock_khan_resource",
    "mock_oer_resource",
    "mock_eba_resource",
    "learning_resource_obj",
    "create_learning_resource",
    # Path fixtures
    "mock_learning_path",
    "create_learning_path",
    # Assessment fixtures
    "mock_assessment",
    "create_assessment",
    # Mock services
    "mock_db_session",
    "mock_redis_client",
    "mock_llm_service",
    "mock_youtube_api",
    "mock_khan_api",
    # Turkish data
    "turkish_subjects",
    "yks_topics",
    "turkish_names",
    # Composite scenarios
    "complete_learning_scenario",
]
