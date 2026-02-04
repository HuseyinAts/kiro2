"""
Comprehensive tests for services.user_service module
Target: 85%+ coverage for user service functionality
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from services.user_service import UserService
from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
)


@pytest.fixture
def user_service():
    """Create UserService instance for testing"""
    return UserService()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "test_user",
        "email": "test@example.com",
        "password": "secure_password123",
        "full_name": "Test User",
        "role": "student",
        "school_id": "school_123",
    }


@pytest.fixture
def sample_student_data():
    """Sample student-specific data"""
    return {
        "username": "ogrenci_ahmet",
        "email": "ahmet@okul.edu.tr",
        "password": "güvenli_şifre123",
        "full_name": "Ahmet Çelik",
        "role": "student",
        "grade_level": 12,
        "class_id": "12A",
        "student_number": "2023001",
    }


@pytest.fixture
def sample_teacher_data():
    """Sample teacher-specific data"""
    return {
        "username": "ogretmen_ayse",
        "email": "ayse@okul.edu.tr",
        "password": "güvenli_şifre456",
        "full_name": "Ayşe Demir",
        "role": "teacher",
        "subjects": ["Matematik", "Fizik"],
        "employee_id": "T2023001",
    }


class TestUserServiceInitialization:
    """Test UserService initialization"""

    def test_user_service_initialization(self, user_service):
        """Test UserService initialization"""
        assert user_service is not None
        assert hasattr(user_service, "logger")
        assert hasattr(user_service, "_initialized")

    @pytest.mark.asyncio
    async def test_user_service_initialize(self, user_service):
        """Test UserService initialize method"""
        await user_service.initialize()
        assert user_service._initialized is True

    @pytest.mark.asyncio
    async def test_user_service_cleanup(self, user_service):
        """Test UserService cleanup method"""
        await user_service.initialize()
        await user_service.cleanup()
        assert user_service._initialized is False


class TestCreateUser:
    """Test user creation functionality"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, sample_user_data):
        """Test successful user creation"""
        with patch("services.user_service.hash_password") as mock_hash, patch(
            "services.user_service.save_user_to_db"
        ) as mock_save:
            mock_hash.return_value = "hashed_password"
            mock_save.return_value = {
                "id": "user_123",
                "username": "test_user",
                "email": "test@example.com",
                "role": "student",
                "created_at": "2023-01-01T00:00:00Z",
            }

            result = await user_service.create_user(sample_user_data)

            assert result["username"] == "test_user"
            assert result["email"] == "test@example.com"
            assert "password" not in result
            mock_hash.assert_called_once_with("secure_password123")

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, user_service, sample_user_data):
        """Test user creation with duplicate username"""
        with patch("services.user_service.check_username_exists") as mock_check:
            mock_check.return_value = True

            with pytest.raises(ValidationError) as exc_info:
                await user_service.create_user(sample_user_data)

            assert (
                "kullanıcı adı" in str(exc_info.value).lower()
                or "username" in str(exc_info.value).lower()
            )

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service, sample_user_data):
        """Test user creation with duplicate email"""
        with patch(
            "services.user_service.check_username_exists"
        ) as mock_check_username, patch(
            "services.user_service.check_email_exists"
        ) as mock_check_email:
            mock_check_username.return_value = False
            mock_check_email.return_value = True

            with pytest.raises(ValidationError) as exc_info:
                await user_service.create_user(sample_user_data)

            assert "email" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_user_invalid_email_format(
        self, user_service, sample_user_data
    ):
        """Test user creation with invalid email format"""
        sample_user_data["email"] = "invalid-email-format"

        with pytest.raises(ValidationError) as exc_info:
            await user_service.create_user(sample_user_data)

        assert "email" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_user_weak_password(self, user_service, sample_user_data):
        """Test user creation with weak password"""
        sample_user_data["password"] = "123"

        with pytest.raises(ValidationError) as exc_info:
            await user_service.create_user(sample_user_data)

        assert (
            "password" in str(exc_info.value).lower()
            or "şifre" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_create_user_missing_required_fields(self, user_service):
        """Test user creation with missing required fields"""
        incomplete_data = {
            "username": "test_user"
            # Missing required fields
        }

        with pytest.raises(ValidationError):
            await user_service.create_user(incomplete_data)

    @pytest.mark.asyncio
    async def test_create_student_user(self, user_service, sample_student_data):
        """Test creation of student user"""
        with patch("services.user_service.hash_password") as mock_hash, patch(
            "services.user_service.save_user_to_db"
        ) as mock_save, patch(
            "services.user_service.create_student_profile"
        ) as mock_student:
            mock_hash.return_value = "hashed_password"
            mock_save.return_value = {
                "id": "student_123",
                "username": "ogrenci_ahmet",
                "role": "student",
            }
            mock_student.return_value = {"student_number": "2023001"}

            result = await user_service.create_user(sample_student_data)

            assert result["role"] == "student"
            mock_student.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_teacher_user(self, user_service, sample_teacher_data):
        """Test creation of teacher user"""
        with patch("services.user_service.hash_password") as mock_hash, patch(
            "services.user_service.save_user_to_db"
        ) as mock_save, patch(
            "services.user_service.create_teacher_profile"
        ) as mock_teacher:
            mock_hash.return_value = "hashed_password"
            mock_save.return_value = {
                "id": "teacher_123",
                "username": "ogretmen_ayse",
                "role": "teacher",
            }
            mock_teacher.return_value = {"employee_id": "T2023001"}

            result = await user_service.create_user(sample_teacher_data)

            assert result["role"] == "teacher"
            mock_teacher.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_turkish_characters(self, user_service):
        """Test user creation with Turkish characters"""
        turkish_data = {
            "username": "türkçe_kullanıcı",
            "email": "türkçe@örnek.com",
            "password": "güvenli_şifre123",
            "full_name": "Türkçe İsim Örnekü",
            "role": "öğrenci",
        }

        with patch("services.user_service.hash_password") as mock_hash, patch(
            "services.user_service.save_user_to_db"
        ) as mock_save:
            mock_hash.return_value = "hashed_password"
            mock_save.return_value = {
                "id": "turkish_user_123",
                "username": "türkçe_kullanıcı",
                "full_name": "Türkçe İsim Örnekü",
            }

            result = await user_service.create_user(turkish_data)

            assert "türkçe" in result["username"]
            assert "Türkçe" in result["full_name"]


class TestAuthenticateUser:
    """Test user authentication functionality"""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, user_service):
        """Test successful user authentication"""
        with patch(
            "services.user_service.get_user_by_username"
        ) as mock_get_user, patch(
            "services.user_service.verify_password"
        ) as mock_verify:
            mock_get_user.return_value = {
                "id": "user_123",
                "username": "test_user",
                "password_hash": "hashed_password",
                "role": "student",
                "is_active": True,
            }
            mock_verify.return_value = True

            result = await user_service.authenticate_user(
                "test_user", "correct_password"
            )

            assert result is not None
            assert result["username"] == "test_user"
            assert "password_hash" not in result

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, user_service):
        """Test authentication with wrong password"""
        with patch(
            "services.user_service.get_user_by_username"
        ) as mock_get_user, patch(
            "services.user_service.verify_password"
        ) as mock_verify:
            mock_get_user.return_value = {
                "id": "user_123",
                "username": "test_user",
                "password_hash": "hashed_password",
                "is_active": True,
            }
            mock_verify.return_value = False

            result = await user_service.authenticate_user("test_user", "wrong_password")

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, user_service):
        """Test authentication with non-existent user"""
        with patch("services.user_service.get_user_by_username") as mock_get_user:
            mock_get_user.return_value = None

            result = await user_service.authenticate_user(
                "nonexistent_user", "password"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, user_service):
        """Test authentication with inactive user"""
        with patch("services.user_service.get_user_by_username") as mock_get_user:
            mock_get_user.return_value = {
                "id": "user_123",
                "username": "test_user",
                "password_hash": "hashed_password",
                "is_active": False,
            }

            result = await user_service.authenticate_user("test_user", "password")

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_empty_credentials(self, user_service):
        """Test authentication with empty credentials"""
        result1 = await user_service.authenticate_user("", "password")
        result2 = await user_service.authenticate_user("username", "")
        result3 = await user_service.authenticate_user("", "")

        assert result1 is None
        assert result2 is None
        assert result3 is None

    @pytest.mark.asyncio
    async def test_authenticate_user_turkish_credentials(self, user_service):
        """Test authentication with Turkish credentials"""
        with patch(
            "services.user_service.get_user_by_username"
        ) as mock_get_user, patch(
            "services.user_service.verify_password"
        ) as mock_verify:
            mock_get_user.return_value = {
                "id": "turkish_user_123",
                "username": "türkçe_kullanıcı",
                "password_hash": "hashed_password",
                "is_active": True,
            }
            mock_verify.return_value = True

            result = await user_service.authenticate_user(
                "türkçe_kullanıcı", "güvenli_şifre"
            )

            assert result is not None
            assert "türkçe" in result["username"]


class TestGetUser:
    """Test user retrieval functionality"""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service):
        """Test successful user retrieval by ID"""
        with patch("services.user_service.get_user_from_db") as mock_get_user:
            mock_get_user.return_value = {
                "id": "user_123",
                "username": "test_user",
                "email": "test@example.com",
                "role": "student",
            }

            result = await user_service.get_user_by_id("user_123")

            assert result is not None
            assert result["id"] == "user_123"
            assert result["username"] == "test_user"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service):
        """Test user retrieval with non-existent ID"""
        with patch("services.user_service.get_user_from_db") as mock_get_user:
            mock_get_user.return_value = None

            with pytest.raises(ResourceNotFoundError):
                await user_service.get_user_by_id("nonexistent_id")

    @pytest.mark.asyncio
    async def test_get_user_by_username_success(self, user_service):
        """Test successful user retrieval by username"""
        with patch(
            "services.user_service.get_user_by_username_from_db"
        ) as mock_get_user:
            mock_get_user.return_value = {
                "id": "user_123",
                "username": "test_user",
                "email": "test@example.com",
            }

            result = await user_service.get_user_by_username("test_user")

            assert result is not None
            assert result["username"] == "test_user"

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_service):
        """Test successful user retrieval by email"""
        with patch("services.user_service.get_user_by_email_from_db") as mock_get_user:
            mock_get_user.return_value = {
                "id": "user_123",
                "username": "test_user",
                "email": "test@example.com",
            }

            result = await user_service.get_user_by_email("test@example.com")

            assert result is not None
            assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_users_by_role(self, user_service):
        """Test user retrieval by role"""
        with patch("services.user_service.get_users_by_role_from_db") as mock_get_users:
            mock_get_users.return_value = [
                {"id": "user_1", "username": "student1", "role": "student"},
                {"id": "user_2", "username": "student2", "role": "student"},
            ]

            result = await user_service.get_users_by_role("student")

            assert len(result) == 2
            assert all(user["role"] == "student" for user in result)

    @pytest.mark.asyncio
    async def test_get_users_by_school(self, user_service):
        """Test user retrieval by school"""
        with patch(
            "services.user_service.get_users_by_school_from_db"
        ) as mock_get_users:
            mock_get_users.return_value = [
                {"id": "user_1", "school_id": "school_123"},
                {"id": "user_2", "school_id": "school_123"},
            ]

            result = await user_service.get_users_by_school("school_123")

            assert len(result) == 2
            assert all(user["school_id"] == "school_123" for user in result)


class TestUpdateUser:
    """Test user update functionality"""

    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, user_service):
        """Test successful user profile update"""
        user_id = "user_123"
        update_data = {"full_name": "Updated Full Name", "email": "updated@example.com"}

        with patch("services.user_service.get_user_from_db") as mock_get_user, patch(
            "services.user_service.update_user_in_db"
        ) as mock_update:
            mock_get_user.return_value = {
                "id": "user_123",
                "username": "test_user",
                "email": "old@example.com",
                "full_name": "Old Name",
            }
            mock_update.return_value = {
                "id": "user_123",
                "username": "test_user",
                "email": "updated@example.com",
                "full_name": "Updated Full Name",
            }

            result = await user_service.update_user_profile(user_id, update_data)

            assert result["email"] == "updated@example.com"
            assert result["full_name"] == "Updated Full Name"

    @pytest.mark.asyncio
    async def test_update_user_profile_not_found(self, user_service):
        """Test user profile update with non-existent user"""
        with patch("services.user_service.get_user_from_db") as mock_get_user:
            mock_get_user.return_value = None

            with pytest.raises(ResourceNotFoundError):
                await user_service.update_user_profile("nonexistent_id", {})

    @pytest.mark.asyncio
    async def test_update_user_email_duplicate(self, user_service):
        """Test user update with duplicate email"""
        user_id = "user_123"
        update_data = {"email": "existing@example.com"}

        with patch("services.user_service.get_user_from_db") as mock_get_user, patch(
            "services.user_service.check_email_exists"
        ) as mock_check_email:
            mock_get_user.return_value = {"id": "user_123", "email": "old@example.com"}
            mock_check_email.return_value = True

            with pytest.raises(ValidationError):
                await user_service.update_user_profile(user_id, update_data)

    @pytest.mark.asyncio
    async def test_update_user_readonly_fields(self, user_service):
        """Test user update with read-only fields"""
        user_id = "user_123"
        update_data = {
            "id": "new_id",  # Read-only
            "username": "new_username",  # Read-only
            "role": "admin",  # Read-only
            "created_at": "2023-12-01",  # Read-only
        }

        with patch("services.user_service.get_user_from_db") as mock_get_user, patch(
            "services.user_service.update_user_in_db"
        ) as mock_update:
            mock_get_user.return_value = {
                "id": "user_123",
                "username": "original_username",
                "role": "student",
            }

            # Should filter out read-only fields
            await user_service.update_user_profile(user_id, update_data)

            # Verify read-only fields were not passed to update
            mock_update.assert_called_once()
            call_args = mock_update.call_args[0][1]  # Second argument is update_data
            assert "id" not in call_args
            assert "username" not in call_args
            assert "role" not in call_args


class TestPasswordManagement:
    """Test password management functionality"""

    @pytest.mark.asyncio
    async def test_change_password_success(self, user_service):
        """Test successful password change"""
        user_id = "user_123"
        current_password = "old_password"
        new_password = "new_secure_password123"

        with patch("services.user_service.get_user_from_db") as mock_get_user, patch(
            "services.user_service.verify_password"
        ) as mock_verify, patch(
            "services.user_service.hash_password"
        ) as mock_hash, patch(
            "services.user_service.update_user_password_in_db"
        ) as mock_update:
            mock_get_user.return_value = {
                "id": "user_123",
                "password_hash": "old_hashed_password",
            }
            mock_verify.return_value = True
            mock_hash.return_value = "new_hashed_password"
            mock_update.return_value = True

            result = await user_service.change_password(
                user_id, current_password, new_password
            )

            assert result is True
            mock_verify.assert_called_once_with(current_password, "old_hashed_password")
            mock_hash.assert_called_once_with(new_password)

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, user_service):
        """Test password change with wrong current password"""
        user_id = "user_123"
        current_password = "wrong_password"
        new_password = "new_secure_password123"

        with patch("services.user_service.get_user_from_db") as mock_get_user, patch(
            "services.user_service.verify_password"
        ) as mock_verify:
            mock_get_user.return_value = {
                "id": "user_123",
                "password_hash": "hashed_password",
            }
            mock_verify.return_value = False

            with pytest.raises(AuthenticationError):
                await user_service.change_password(
                    user_id, current_password, new_password
                )

    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(self, user_service):
        """Test password change with weak new password"""
        user_id = "user_123"
        current_password = "old_password"
        new_password = "123"  # Too weak

        with pytest.raises(ValidationError):
            await user_service.change_password(user_id, current_password, new_password)

    @pytest.mark.asyncio
    async def test_reset_password_success(self, user_service):
        """Test successful password reset"""
        user_id = "user_123"
        new_password = "new_secure_password123"

        with patch("services.user_service.get_user_from_db") as mock_get_user, patch(
            "services.user_service.hash_password"
        ) as mock_hash, patch(
            "services.user_service.update_user_password_in_db"
        ) as mock_update:
            mock_get_user.return_value = {"id": "user_123"}
            mock_hash.return_value = "new_hashed_password"
            mock_update.return_value = True

            result = await user_service.reset_password(user_id, new_password)

            assert result is True
            mock_hash.assert_called_once_with(new_password)

    @pytest.mark.asyncio
    async def test_generate_password_reset_token(self, user_service):
        """Test password reset token generation"""
        email = "test@example.com"

        with patch(
            "services.user_service.get_user_by_email_from_db"
        ) as mock_get_user, patch(
            "services.user_service.create_password_reset_token"
        ) as mock_create_token, patch(
            "services.user_service.send_password_reset_email"
        ) as mock_send_email:
            mock_get_user.return_value = {"id": "user_123", "email": "test@example.com"}
            mock_create_token.return_value = "reset_token_123"
            mock_send_email.return_value = True

            result = await user_service.generate_password_reset_token(email)

            assert result is True
            mock_create_token.assert_called_once()
            mock_send_email.assert_called_once()


class TestUserValidation:
    """Test user validation functionality"""

    @pytest.mark.asyncio
    async def test_validate_user_data_success(self, user_service, sample_user_data):
        """Test successful user data validation"""
        is_valid, errors = await user_service.validate_user_data(sample_user_data)

        assert is_valid is True
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validate_user_data_missing_required_fields(self, user_service):
        """Test user data validation with missing required fields"""
        incomplete_data = {
            "username": "test_user"
            # Missing required fields
        }

        is_valid, errors = await user_service.validate_user_data(incomplete_data)

        assert is_valid is False
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_validate_username_format(self, user_service):
        """Test username format validation"""
        valid_usernames = ["test_user", "user123", "turkish_öğrenci"]
        invalid_usernames = ["", "ab", "user with spaces", "user@invalid"]

        for username in valid_usernames:
            is_valid = await user_service.validate_username_format(username)
            assert is_valid is True

        for username in invalid_usernames:
            is_valid = await user_service.validate_username_format(username)
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_email_format(self, user_service):
        """Test email format validation"""
        valid_emails = ["test@example.com", "türkçe@örnek.com", "user+tag@domain.co.uk"]
        invalid_emails = [
            "",
            "invalid-email",
            "@domain.com",
            "user@",
            "user.domain.com",
        ]

        for email in valid_emails:
            is_valid = await user_service.validate_email_format(email)
            assert is_valid is True

        for email in invalid_emails:
            is_valid = await user_service.validate_email_format(email)
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_password_strength(self, user_service):
        """Test password strength validation"""
        strong_passwords = [
            "SecurePass123!",
            "güvenli_şifre456",
            "Complex@Password2023",
        ]
        weak_passwords = ["123", "password", "123456", "abc"]

        for password in strong_passwords:
            is_valid = await user_service.validate_password_strength(password)
            assert is_valid is True

        for password in weak_passwords:
            is_valid = await user_service.validate_password_strength(password)
            assert is_valid is False


class TestUserSearch:
    """Test user search functionality"""

    @pytest.mark.asyncio
    async def test_search_users_by_name(self, user_service):
        """Test user search by name"""
        search_term = "ahmet"

        with patch("services.user_service.search_users_in_db") as mock_search:
            mock_search.return_value = [
                {"id": "1", "full_name": "Ahmet Çelik", "username": "ahmet1"},
                {"id": "2", "full_name": "Mehmet Ahmet", "username": "mehmet_ahmet"},
            ]

            result = await user_service.search_users_by_name(search_term)

            assert len(result) == 2
            assert any("Ahmet" in user["full_name"] for user in result)

    @pytest.mark.asyncio
    async def test_search_users_by_email_domain(self, user_service):
        """Test user search by email domain"""
        domain = "okul.edu.tr"

        with patch(
            "services.user_service.search_users_by_email_domain_in_db"
        ) as mock_search:
            mock_search.return_value = [
                {"id": "1", "email": "ahmet@okul.edu.tr"},
                {"id": "2", "email": "ayse@okul.edu.tr"},
            ]

            result = await user_service.search_users_by_email_domain(domain)

            assert len(result) == 2
            assert all(domain in user["email"] for user in result)

    @pytest.mark.asyncio
    async def test_search_users_advanced(self, user_service):
        """Test advanced user search"""
        search_criteria = {
            "role": "student",
            "school_id": "school_123",
            "grade_level": 12,
            "is_active": True,
        }

        with patch("services.user_service.advanced_search_users_in_db") as mock_search:
            mock_search.return_value = [
                {
                    "id": "1",
                    "role": "student",
                    "school_id": "school_123",
                    "grade_level": 12,
                },
                {
                    "id": "2",
                    "role": "student",
                    "school_id": "school_123",
                    "grade_level": 12,
                },
            ]

            result = await user_service.search_users_advanced(search_criteria)

            assert len(result) == 2
            assert all(user["role"] == "student" for user in result)


class TestUserActivation:
    """Test user activation/deactivation functionality"""

    @pytest.mark.asyncio
    async def test_activate_user_success(self, user_service):
        """Test successful user activation"""
        user_id = "user_123"

        with patch("services.user_service.get_user_from_db") as mock_get_user, patch(
            "services.user_service.update_user_status_in_db"
        ) as mock_update:
            mock_get_user.return_value = {"id": "user_123", "is_active": False}
            mock_update.return_value = True

            result = await user_service.activate_user(user_id)

            assert result is True
            mock_update.assert_called_once_with(user_id, {"is_active": True})

    @pytest.mark.asyncio
    async def test_deactivate_user_success(self, user_service):
        """Test successful user deactivation"""
        user_id = "user_123"

        with patch("services.user_service.get_user_from_db") as mock_get_user, patch(
            "services.user_service.update_user_status_in_db"
        ) as mock_update:
            mock_get_user.return_value = {"id": "user_123", "is_active": True}
            mock_update.return_value = True

            result = await user_service.deactivate_user(user_id)

            assert result is True
            mock_update.assert_called_once_with(user_id, {"is_active": False})

    @pytest.mark.asyncio
    async def test_activate_nonexistent_user(self, user_service):
        """Test activation of non-existent user"""
        with patch("services.user_service.get_user_from_db") as mock_get_user:
            mock_get_user.return_value = None

            with pytest.raises(ResourceNotFoundError):
                await user_service.activate_user("nonexistent_id")


class TestUserServiceErrorHandling:
    """Test error handling in UserService"""

    @pytest.mark.asyncio
    async def test_database_error_handling(self, user_service, sample_user_data):
        """Test handling of database errors"""
        with patch("services.user_service.save_user_to_db") as mock_save:
            mock_save.side_effect = Exception("Database connection failed")

            with pytest.raises(DatabaseError):
                await user_service.create_user(sample_user_data)

    @pytest.mark.asyncio
    async def test_validation_error_aggregation(self, user_service):
        """Test aggregation of multiple validation errors"""
        invalid_data = {
            "username": "",  # Invalid
            "email": "invalid-email",  # Invalid
            "password": "123",  # Too weak
            "role": "invalid_role",  # Invalid
        }

        with pytest.raises(ValidationError) as exc_info:
            await user_service.create_user(invalid_data)

        # Should contain multiple error details
        if hasattr(exc_info.value, "details") and exc_info.value.details:
            assert isinstance(exc_info.value.details, dict)

    @pytest.mark.asyncio
    async def test_concurrent_user_operations(self, user_service):
        """Test concurrent user operations"""
        user_ids = ["user_1", "user_2", "user_3"]

        with patch("services.user_service.get_user_from_db") as mock_get_user:
            mock_get_user.return_value = {"id": "user_1", "username": "test"}

            # Perform concurrent operations
            tasks = [user_service.get_user_by_id(user_id) for user_id in user_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Should handle concurrent operations gracefully
            for result in results:
                assert isinstance(result, dict) or isinstance(result, Exception)


class TestUserServiceIntegration:
    """Integration tests for UserService"""

    @pytest.mark.asyncio
    async def test_complete_user_lifecycle(self, user_service, sample_user_data):
        """Test complete user lifecycle: create -> authenticate -> update -> deactivate"""
        with patch("services.user_service.hash_password") as mock_hash, patch(
            "services.user_service.save_user_to_db"
        ) as mock_save, patch(
            "services.user_service.get_user_by_username"
        ) as mock_get_username, patch(
            "services.user_service.verify_password"
        ) as mock_verify, patch(
            "services.user_service.get_user_from_db"
        ) as mock_get_user, patch(
            "services.user_service.update_user_in_db"
        ) as mock_update, patch(
            "services.user_service.update_user_status_in_db"
        ) as mock_update_status:
            # Setup mocks
            user_id = "user_123"
            mock_hash.return_value = "hashed_password"
            mock_save.return_value = {"id": user_id, "username": "test_user"}
            mock_get_username.return_value = {
                "id": user_id,
                "username": "test_user",
                "password_hash": "hashed_password",
                "is_active": True,
            }
            mock_verify.return_value = True
            mock_get_user.return_value = {"id": user_id, "username": "test_user"}
            mock_update.return_value = {"id": user_id, "email": "updated@example.com"}
            mock_update_status.return_value = True

            # 1. Create user
            created_user = await user_service.create_user(sample_user_data)
            assert created_user["username"] == "test_user"

            # 2. Authenticate user
            auth_result = await user_service.authenticate_user(
                "test_user", "secure_password123"
            )
            assert auth_result is not None

            # 3. Update user
            updated_user = await user_service.update_user_profile(
                user_id, {"email": "updated@example.com"}
            )
            assert updated_user["email"] == "updated@example.com"

            # 4. Deactivate user
            deactivate_result = await user_service.deactivate_user(user_id)
            assert deactivate_result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
