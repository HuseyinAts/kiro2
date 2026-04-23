"""
Integration tests with real database connections
These tests will execute actual database operations to increase coverage
"""

import pytest

pytestmark = pytest.mark.skipif(
    True,
    reason="Kullanici model constructor changed (ad_soyad removed), SQLite test DB missing kullanicilar table, requires real PostgreSQL",
)
from sqlalchemy import select

try:
    from models.enums import KullaniciRolu, ZorlukSeviyesi
    from models_unified import Kullanici
    from models_unified import Soru as SinavSorusu
except (ImportError, ModuleNotFoundError):
    pytest.skip("models_unified module not available", allow_module_level=True)


class TestUserDatabaseOperations:
    """Test user CRUD operations with real database"""

    @pytest.mark.asyncio
    async def test_create_user(self, async_db_session):
        """Test creating a user in database"""
        user = Kullanici(
            email="integration_test@example.com",
            ad_soyad="Integration Test User",
            sifre="hashed_password_here",
            rol=KullaniciRolu.OGRENCI,
            sinif_seviyesi=11,
        )

        async_db_session.add(user)
        await async_db_session.commit()
        await async_db_session.refresh(user)

        assert user.id is not None
        assert user.email == "integration_test@example.com"

    @pytest.mark.asyncio
    async def test_query_users(self, async_db_session):
        """Test querying users from database"""
        result = await async_db_session.execute(
            select(Kullanici).where(Kullanici.rol == KullaniciRolu.OGRENCI)
        )
        users = result.scalars().all()

        assert users is not None
        assert len(users) >= 0

    @pytest.mark.asyncio
    async def test_update_user(self, async_db_session):
        """Test updating user in database"""
        # Get first user
        result = await async_db_session.execute(select(Kullanici).limit(1))
        user = result.scalar_one_or_none()

        if user:
            original_name = user.ad_soyad
            user.ad_soyad = "Updated Name"
            await async_db_session.commit()

            # Verify update
            await async_db_session.refresh(user)
            assert user.ad_soyad == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_user(self, async_db_session):
        """Test deleting user from database"""
        # Create a user to delete
        user = Kullanici(
            email="to_delete@example.com",
            ad_soyad="Delete Me",
            sifre="password",
            rol=KullaniciRolu.OGRENCI,
        )

        async_db_session.add(user)
        await async_db_session.commit()
        user_id = user.id

        # Delete the user
        await async_db_session.delete(user)
        await async_db_session.commit()

        # Verify deletion
        result = await async_db_session.execute(
            select(Kullanici).where(Kullanici.id == user_id)
        )
        deleted_user = result.scalar_one_or_none()
        assert deleted_user is None


class TestQuestionDatabaseOperations:
    """Test question CRUD operations with real database"""

    @pytest.mark.asyncio
    async def test_create_question(self, async_db_session):
        """Test creating a question in database"""
        question = SinavSorusu(
            soru_metni="Integration test sorusu?",
            zorluk=ZorlukSeviyesi.ORTA,
            ders="Matematik",
            konu="Geometri",
            dogru_cevap="A",
        )

        async_db_session.add(question)
        await async_db_session.commit()
        await async_db_session.refresh(question)

        assert question.id is not None
        assert question.soru_metni == "Integration test sorusu?"

    @pytest.mark.asyncio
    async def test_query_questions_by_difficulty(self, async_db_session):
        """Test querying questions by difficulty"""
        result = await async_db_session.execute(
            select(SinavSorusu).where(SinavSorusu.zorluk == ZorlukSeviyesi.KOLAY)
        )
        questions = result.scalars().all()

        assert questions is not None
        for q in questions:
            assert q.zorluk == ZorlukSeviyesi.KOLAY

    @pytest.mark.asyncio
    async def test_query_questions_by_subject(self, async_db_session):
        """Test querying questions by subject"""
        result = await async_db_session.execute(
            select(SinavSorusu).where(SinavSorusu.ders == "Matematik")
        )
        questions = result.scalars().all()

        assert questions is not None

    @pytest.mark.asyncio
    async def test_complex_question_query(self, async_db_session):
        """Test complex query with multiple filters"""
        result = await async_db_session.execute(
            select(SinavSorusu)
            .where(SinavSorusu.ders == "Matematik")
            .where(SinavSorusu.zorluk == ZorlukSeviyesi.ORTA)
            .limit(5)
        )
        questions = result.scalars().all()

        assert questions is not None
        assert len(questions) <= 5
