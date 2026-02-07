"""
Database ve Repository Test Coverage
Alembic migration ve repository pattern testleri
"""

from typing import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import db_manager
from models.database import ExamType, QuestionDifficulty, SubjectArea, User, UserRole
from repositories.base import BaseRepository
from repositories.question_repository import QuestionRepository
from repositories.user_repository import UserRepository


class TestDatabaseConnection:
    """Database bağlantı testleri"""

    @pytest.mark.asyncio
    async def test_database_initialization(self):
        """Database başlatma testi"""
        await db_manager.initialize()
        assert db_manager._initialized is True

        health = await db_manager.health_check()
        assert health["healthy"] is True
        assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_database_session_context_manager(self):
        """Session context manager testi"""
        async with db_manager.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_database_tables_creation(self):
        """Tablo oluşturma testi"""
        await db_manager.create_tables()

        # Tabloların var olduğunu kontrol et
        async with db_manager.get_session() as session:
            # Users tablosu kontrolü
            result = await session.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
                )
            )
            assert result.scalar() == "users"


class TestBaseRepository:
    """Base repository testleri"""

    @pytest.fixture
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Test session fixture"""
        await db_manager.initialize()
        await db_manager.create_tables()

        async with db_manager.get_session() as session:
            yield session

    @pytest.mark.asyncio
    async def test_base_repository_create(self, session: AsyncSession):
        """Base repository create testi"""
        repo = BaseRepository(User, session)

        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password_hash": "hashed_password",
            "first_name": "Test",
            "last_name": "User",
            "role": UserRole.STUDENT,
        }

        user = await repo.create(**user_data)
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.role == UserRole.STUDENT

    @pytest.mark.asyncio
    async def test_base_repository_get_by_id(self, session: AsyncSession):
        """Base repository get_by_id testi"""
        repo = BaseRepository(User, session)

        # Önce bir user oluştur
        user_data = {
            "email": "test2@example.com",
            "username": "testuser2",
            "password_hash": "hashed_password",
            "first_name": "Test2",
            "last_name": "User2",
            "role": UserRole.STUDENT,
        }

        created_user = await repo.create(**user_data)

        # ID ile getir
        retrieved_user = await repo.get_by_id(created_user.id)
        assert retrieved_user is not None
        assert retrieved_user.email == "test2@example.com"

    @pytest.mark.asyncio
    async def test_base_repository_update(self, session: AsyncSession):
        """Base repository update testi"""
        repo = BaseRepository(User, session)

        # User oluştur
        user_data = {
            "email": "test3@example.com",
            "username": "testuser3",
            "password_hash": "hashed_password",
            "first_name": "Test3",
            "last_name": "User3",
            "role": UserRole.STUDENT,
        }

        user = await repo.create(**user_data)

        # Update
        updated_user = await repo.update(user.id, first_name="Updated")
        assert updated_user.first_name == "Updated"

    @pytest.mark.asyncio
    async def test_base_repository_get_all(self, session: AsyncSession):
        """Base repository get_all testi"""
        repo = BaseRepository(User, session)

        # Birkaç user oluştur
        for i in range(3):
            user_data = {
                "email": f"test{i}@example.com",
                "username": f"testuser{i}",
                "password_hash": "hashed_password",
                "first_name": f"Test{i}",
                "last_name": f"User{i}",
                "role": UserRole.STUDENT,
            }
            await repo.create(**user_data)

        # Tümünü getir
        users = await repo.get_all(limit=10)
        assert len(users) >= 3

    @pytest.mark.asyncio
    async def test_base_repository_count(self, session: AsyncSession):
        """Base repository count testi"""
        repo = BaseRepository(User, session)

        initial_count = await repo.count()

        # Yeni user ekle
        user_data = {
            "email": "count_test@example.com",
            "username": "count_user",
            "password_hash": "hashed_password",
            "first_name": "Count",
            "last_name": "User",
            "role": UserRole.STUDENT,
        }
        await repo.create(**user_data)

        new_count = await repo.count()
        assert new_count == initial_count + 1


class TestUserRepository:
    """User repository testleri"""

    @pytest.fixture
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Test session fixture"""
        await db_manager.initialize()
        await db_manager.create_tables()

        async with db_manager.get_session() as session:
            yield session

    @pytest.mark.asyncio
    async def test_user_repository_get_by_email(self, session: AsyncSession):
        """Email ile user getirme testi"""
        repo = UserRepository(session)

        user_data = {
            "email": "email_test@example.com",
            "username": "email_user",
            "password_hash": "hashed_password",
            "first_name": "Email",
            "last_name": "User",
            "role": UserRole.STUDENT,
        }

        created_user = await repo.create(**user_data)

        # Email ile getir
        retrieved_user = await repo.get_by_email("email_test@example.com")
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id

    @pytest.mark.asyncio
    async def test_user_repository_get_by_username(self, session: AsyncSession):
        """Username ile user getirme testi"""
        repo = UserRepository(session)

        user_data = {
            "email": "username_test@example.com",
            "username": "unique_username",
            "password_hash": "hashed_password",
            "first_name": "Username",
            "last_name": "User",
            "role": UserRole.STUDENT,
        }

        created_user = await repo.create(**user_data)

        # Username ile getir
        retrieved_user = await repo.get_by_username("unique_username")
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id

    @pytest.mark.asyncio
    async def test_user_repository_create_with_profile(self, session: AsyncSession):
        """Profile ile user oluşturma testi"""
        repo = UserRepository(session)

        user_data = {
            "email": "profile_test@example.com",
            "username": "profile_user",
            "password_hash": "hashed_password",
            "first_name": "Profile",
            "last_name": "User",
            "role": UserRole.STUDENT,
        }

        profile_data = {
            "grade_level": 12,
            "school_name": "Test Lisesi",
            "target_university": "Test Üniversitesi",
        }

        user = await repo.create_user_with_profile(
            user_data, profile_data, UserRole.STUDENT
        )

        assert user.role == UserRole.STUDENT
        # Profile'ın oluşturulduğunu kontrol et
        user_with_profile = await repo.get_with_profile(user.id)
        assert user_with_profile.student_profile is not None
        assert user_with_profile.student_profile.grade_level == 12


class TestQuestionRepository:
    """Question repository testleri"""

    @pytest.fixture
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Test session fixture"""
        await db_manager.initialize()
        await db_manager.create_tables()

        async with db_manager.get_session() as session:
            yield session

    @pytest.mark.asyncio
    async def test_question_repository_create(self, session: AsyncSession):
        """Soru oluşturma testi"""
        repo = QuestionRepository(session)

        question_data = {
            "question_text": "Test sorusu?",
            "option_a": "A şıkkı",
            "option_b": "B şıkkı",
            "option_c": "C şıkkı",
            "option_d": "D şıkkı",
            "correct_answer": "A",
            "exam_type": ExamType.TYT,
            "subject_area": SubjectArea.MATEMATIK,
            "topic": "Cebir",
            "difficulty": QuestionDifficulty.MEDIUM,
        }

        question = await repo.create(**question_data)
        assert question.question_text == "Test sorusu?"
        assert question.correct_answer == "A"
        assert question.exam_type == ExamType.TYT

    @pytest.mark.asyncio
    async def test_question_repository_get_by_exam_type(self, session: AsyncSession):
        """Sınav tipine göre soru getirme testi"""
        repo = QuestionRepository(session)

        # TYT sorusu oluştur
        tyt_question_data = {
            "question_text": "TYT sorusu?",
            "option_a": "A şıkkı",
            "option_b": "B şıkkı",
            "option_c": "C şıkkı",
            "option_d": "D şıkkı",
            "correct_answer": "A",
            "exam_type": ExamType.TYT,
            "subject_area": SubjectArea.MATEMATIK,
            "topic": "Cebir",
            "difficulty": QuestionDifficulty.MEDIUM,
        }

        await repo.create(**tyt_question_data)

        # TYT sorularını getir
        tyt_questions = await repo.get_by_exam_type(ExamType.TYT)
        assert len(tyt_questions) >= 1
        assert all(q.exam_type == ExamType.TYT for q in tyt_questions)

    @pytest.mark.asyncio
    async def test_question_repository_get_random_questions(
        self, session: AsyncSession
    ):
        """Rastgele soru getirme testi"""
        repo = QuestionRepository(session)

        # Birkaç soru oluştur
        for i in range(5):
            question_data = {
                "question_text": f"Soru {i}?",
                "option_a": "A şıkkı",
                "option_b": "B şıkkı",
                "option_c": "C şıkkı",
                "option_d": "D şıkkı",
                "correct_answer": "A",
                "exam_type": ExamType.TYT,
                "subject_area": SubjectArea.MATEMATIK,
                "topic": "Cebir",
                "difficulty": QuestionDifficulty.MEDIUM,
            }
            await repo.create(**question_data)

        # Rastgele 3 soru getir
        random_questions = await repo.get_random_questions(
            ExamType.TYT, SubjectArea.MATEMATIK, 3
        )

        assert len(random_questions) <= 3
        assert all(q.exam_type == ExamType.TYT for q in random_questions)
        assert all(q.subject_area == SubjectArea.MATEMATIK for q in random_questions)


class TestAlembicMigration:
    """Alembic migration testleri"""

    @pytest.mark.asyncio
    async def test_alembic_env_configuration(self):
        """Alembic environment konfigürasyon testi"""
        from alembic.config import Config

        # Alembic config dosyasını test et
        config = Config("backend/alembic.ini")
        assert config.get_main_option("script_location") == "alembic"

        # Database URL'in doğru ayarlandığını kontrol et
        from alembic.env import get_url

        url = get_url()
        assert url is not None
        assert isinstance(url, str)

    def test_alembic_models_import(self):
        """Alembic'in modelleri doğru import ettiğini test et"""
        from alembic.env import target_metadata
        from models.database import Base

        assert target_metadata is Base.metadata

        # Tüm tabloların metadata'da olduğunu kontrol et
        table_names = list(Base.metadata.tables.keys())
        expected_tables = [
            "users",
            "student_profiles",
            "teacher_profiles",
            "parent_profiles",
            "questions",
            "exam_sessions",
            "exam_questions",
            "student_answers",
            "learning_analytics",
            "educational_contents",
            "classrooms",
            "system_configurations",
            "audit_logs",
        ]

        for table in expected_tables:
            assert table in table_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
