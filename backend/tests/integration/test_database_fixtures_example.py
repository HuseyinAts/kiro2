"""
Example Integration Tests Using Database Fixtures
Demonstrates how to use the PostgreSQL fixtures for integration testing
"""
import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_creation_with_factory(user_factory):
    """Test creating a user using the user_factory fixture."""
    # Create a user
    user = await user_factory(
        email="integration_test@example.com",
        username="integrationuser",
        first_name="Integration",
        last_name="Test",
    )

    # Verify user was created
    assert user.id is not None
    assert user.email == "integration_test@example.com"
    assert user.username == "integrationuser"
    assert user.is_active is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_student_profile_creation(student_profile_factory, user_factory):
    """Test creating a student profile with associated user."""
    # Create a student profile (will auto-create user if not provided)
    profile = await student_profile_factory(grade_level=10, target_exam="AYT")

    # Verify profile was created
    assert profile.id is not None
    assert profile.grade_level == 10
    assert profile.target_exam == "AYT"
    assert profile.user_id is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_question_creation(question_factory):
    """Test creating questions using the question_factory fixture."""
    # Create a question
    question = await question_factory(
        question_text="What is 2+2?",
        subject_area="MATEMATIK",
        difficulty="EASY",
        correct_answer="A",
    )

    # Verify question was created
    assert question.id is not None
    assert question.question_text == "What is 2+2?"
    assert question.subject_area == "MATEMATIK"
    assert question.difficulty == "EASY"
    assert question.correct_answer == "A"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_session_rollback(db_session, user_factory):
    """
    Test that changes are rolled back after each test.
    This test creates a user but it should not exist in the next test.
    """
    from models.database import User
    from sqlalchemy import select

    # Create a user
    user = await user_factory(email="rollback_test@example.com")

    # Verify it exists in this session
    result = await db_session.execute(
        select(User).where(User.email == "rollback_test@example.com")
    )
    found_user = result.scalar_one_or_none()
    assert found_user is not None
    assert found_user.email == "rollback_test@example.com"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rollback_verification(db_session):
    """
    Verify that the user from previous test was rolled back.
    This test should NOT find the user created in the previous test.
    """
    from models.database import User
    from sqlalchemy import select

    # Try to find the user from the previous test
    result = await db_session.execute(
        select(User).where(User.email == "rollback_test@example.com")
    )
    found_user = result.scalar_one_or_none()

    # User should not exist (rolled back after previous test)
    assert found_user is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sample_user_fixture(sample_user):
    """Test using pre-created sample_user fixture."""
    assert sample_user.id is not None
    assert sample_user.email == "sample@example.com"
    assert sample_user.username == "sampleuser"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sample_questions_fixture(sample_questions):
    """Test using pre-created sample_questions fixture."""
    assert len(sample_questions) == 5

    # Verify all questions were created
    for question in sample_questions:
        assert question.id is not None
        assert question.subject_area == "MATEMATIK"
        assert question.difficulty in ["EASY", "MEDIUM", "HARD"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_clean_database_fixture(clean_database):
    """Test the clean_database fixture that truncates all tables."""
    from models.database import User
    from sqlalchemy import select, func

    # Count users in the clean database
    result = await clean_database.execute(select(func.count(User.id)))
    count = result.scalar()

    # Should be 0 since database was truncated
    assert count == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_users_with_relationships(user_factory, student_profile_factory):
    """Test creating multiple users with related profiles."""
    # Create 3 students
    students = []
    for i in range(3):
        profile = await student_profile_factory(grade_level=9 + i, target_exam="TYT")
        students.append(profile)

    # Verify all were created
    assert len(students) == 3
    assert students[0].grade_level == 9
    assert students[1].grade_level == 10
    assert students[2].grade_level == 11


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_created_data(db_session, user_factory, question_factory):
    """Test querying data that was created in the test."""
    from models.database import User, Question
    from sqlalchemy import select

    # Create test data
    user = await user_factory(username="querytest")
    q1 = await question_factory(difficulty="EASY")
    q2 = await question_factory(difficulty="HARD")

    # Query users
    result = await db_session.execute(select(User))
    users = result.scalars().all()
    assert len(users) >= 1
    assert any(u.username == "querytest" for u in users)

    # Query questions by difficulty
    result = await db_session.execute(
        select(Question).where(Question.difficulty == "EASY")
    )
    easy_questions = result.scalars().all()
    assert len(easy_questions) >= 1


# ============================================================================
# Running these tests:
# ============================================================================
#
# To run these integration tests with PostgreSQL:
#
# 1. Make sure PostgreSQL container is running:
#    docker ps | grep test-postgres
#
# 2. Run integration tests only:
#    pytest tests/integration/test_database_fixtures_example.py -v
#
# 3. Run with markers:
#    pytest -m integration -v
#
# 4. Run a specific test:
#    pytest tests/integration/test_database_fixtures_example.py::test_user_creation_with_factory -v
#
# ============================================================================
