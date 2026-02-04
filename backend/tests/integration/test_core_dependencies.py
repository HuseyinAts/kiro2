"""
Comprehensive tests for core.dependencies module
Tests for authentication, authorization and dependency injection
"""
import os
import sys
from unittest.mock import patch

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dependencies import (
    JWT_ALGORITHM,
    JWT_SECRET,
    MOCK_USER,
    create_mock_jwt_token,
    get_current_admin_user,
    get_current_student_user,
    get_current_teacher_user,
    get_current_user,
    get_database_session,
    get_db,
    get_elasticsearch,
    get_mock_current_user,
    get_redis,
)


class TestMockDependencies:
    """Test mock dependency functions"""

    @pytest.mark.asyncio
    async def test_get_db(self):
        """Test get_db function"""
        result = await get_db()
        assert result == {"mock_db": True}
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_redis(self):
        """Test get_redis function"""
        result = await get_redis()
        assert result == {"mock_redis": True}
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_elasticsearch(self):
        """Test get_elasticsearch function"""
        result = await get_elasticsearch()
        assert result == {"mock_elasticsearch": True}
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_database_session(self):
        """Test get_database_session function"""
        result = await get_database_session()
        assert result == {"mock_session": True}
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_mock_current_user(self):
        """Test get_mock_current_user function"""
        result = await get_mock_current_user()

        assert result == MOCK_USER
        assert result["user_id"] == "test_student"
        assert result["username"] == "test_student"
        assert result["role"] == "student"
        assert result["email"] == "test@example.com"


class TestJWTUtils:
    """Test JWT utility functions"""

    def test_create_mock_jwt_token_default(self):
        """Test create_mock_jwt_token with default parameters"""
        token = create_mock_jwt_token()

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == "test_user"
        assert payload["username"] == "test_user"
        assert payload["role"] == "student"
        assert payload["email"] == "test_user@example.com"

    def test_create_mock_jwt_token_custom(self):
        """Test create_mock_jwt_token with custom parameters"""
        token = create_mock_jwt_token(user_id="admin_user", role="admin")

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == "admin_user"
        assert payload["username"] == "admin_user"
        assert payload["role"] == "admin"
        assert payload["email"] == "admin_user@example.com"

    def test_mock_user_constant(self):
        """Test MOCK_USER constant"""
        assert MOCK_USER["user_id"] == "test_student"
        assert MOCK_USER["username"] == "test_student"
        assert MOCK_USER["role"] == "student"
        assert MOCK_USER["email"] == "test@example.com"


class TestAuthentication:
    """Test authentication functions"""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test get_current_user with valid JWT token"""
        # Create valid token
        token = create_mock_jwt_token(user_id="test_user", role="student")

        # Create mock credentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Test get_current_user
        result = await get_current_user(credentials)

        assert result["user_id"] == "test_user"
        assert result["username"] == "test_user"
        assert result["role"] == "student"
        assert result["email"] == "test_user@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid JWT token"""
        # Create invalid token
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_token"
        )

        # Test get_current_user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_missing_sub(self):
        """Test get_current_user with token missing 'sub' claim"""
        # Create token without 'sub' claim
        payload = {
            "username": "test_user",
            "role": "student",
            "email": "test@example.com",
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Test get_current_user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self):
        """Test get_current_user with expired JWT token"""
        import time

        # Create expired token
        payload = {
            "sub": "test_user",
            "username": "test_user",
            "role": "student",
            "email": "test@example.com",
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Test get_current_user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_jwt_decode_exception(self):
        """Test get_current_user with JWT decode exception"""
        # Create malformed token
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="malformed.jwt.token"
        )

        # Test get_current_user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_general_exception(self):
        """Test get_current_user with general exception"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test_token"
        )

        # Mock jwt.decode to raise general exception
        with patch("core.dependencies.jwt.decode") as mock_decode:
            mock_decode.side_effect = Exception("General error")

            # Test get_current_user
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)

            assert exc_info.value.status_code == 401
            assert "Authentication failed" in str(exc_info.value.detail)


class TestAuthorization:
    """Test authorization functions"""

    @pytest.mark.asyncio
    async def test_get_current_admin_user_valid(self):
        """Test get_current_admin_user with admin user"""
        admin_user = {
            "user_id": "admin_user",
            "username": "admin_user",
            "role": "admin",
            "email": "admin@example.com",
        }

        # Test get_current_admin_user
        result = await get_current_admin_user(admin_user)

        assert result == admin_user
        assert result["role"] == "admin"

    @pytest.mark.asyncio
    async def test_get_current_admin_user_invalid(self):
        """Test get_current_admin_user with non-admin user"""
        student_user = {
            "user_id": "student_user",
            "username": "student_user",
            "role": "student",
            "email": "student@example.com",
        }

        # Test get_current_admin_user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(student_user)

        assert exc_info.value.status_code == 403
        assert "Admin access required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_teacher_user_teacher(self):
        """Test get_current_teacher_user with teacher user"""
        teacher_user = {
            "user_id": "teacher_user",
            "username": "teacher_user",
            "role": "teacher",
            "email": "teacher@example.com",
        }

        # Test get_current_teacher_user
        result = await get_current_teacher_user(teacher_user)

        assert result == teacher_user
        assert result["role"] == "teacher"

    @pytest.mark.asyncio
    async def test_get_current_teacher_user_admin(self):
        """Test get_current_teacher_user with admin user"""
        admin_user = {
            "user_id": "admin_user",
            "username": "admin_user",
            "role": "admin",
            "email": "admin@example.com",
        }

        # Test get_current_teacher_user
        result = await get_current_teacher_user(admin_user)

        assert result == admin_user
        assert result["role"] == "admin"

    @pytest.mark.asyncio
    async def test_get_current_teacher_user_invalid(self):
        """Test get_current_teacher_user with student user"""
        student_user = {
            "user_id": "student_user",
            "username": "student_user",
            "role": "student",
            "email": "student@example.com",
        }

        # Test get_current_teacher_user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_teacher_user(student_user)

        assert exc_info.value.status_code == 403
        assert "Teacher access required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_student_user_student(self):
        """Test get_current_student_user with student user"""
        student_user = {
            "user_id": "student_user",
            "username": "student_user",
            "role": "student",
            "email": "student@example.com",
        }

        # Test get_current_student_user
        result = await get_current_student_user(student_user)

        assert result == student_user
        assert result["role"] == "student"

    @pytest.mark.asyncio
    async def test_get_current_student_user_teacher(self):
        """Test get_current_student_user with teacher user"""
        teacher_user = {
            "user_id": "teacher_user",
            "username": "teacher_user",
            "role": "teacher",
            "email": "teacher@example.com",
        }

        # Test get_current_student_user
        result = await get_current_student_user(teacher_user)

        assert result == teacher_user
        assert result["role"] == "teacher"

    @pytest.mark.asyncio
    async def test_get_current_student_user_admin(self):
        """Test get_current_student_user with admin user"""
        admin_user = {
            "user_id": "admin_user",
            "username": "admin_user",
            "role": "admin",
            "email": "admin@example.com",
        }

        # Test get_current_student_user
        result = await get_current_student_user(admin_user)

        assert result == admin_user
        assert result["role"] == "admin"

    @pytest.mark.asyncio
    async def test_get_current_student_user_invalid(self):
        """Test get_current_student_user with invalid role"""
        invalid_user = {
            "user_id": "invalid_user",
            "username": "invalid_user",
            "role": "guest",
            "email": "guest@example.com",
        }

        # Test get_current_student_user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_student_user(invalid_user)

        assert exc_info.value.status_code == 403
        assert "Student access required" in str(exc_info.value.detail)


class TestConstants:
    """Test constants and configuration"""

    def test_jwt_secret_exists(self):
        """Test JWT_SECRET constant exists"""
        assert JWT_SECRET is not None
        assert isinstance(JWT_SECRET, str)
        assert len(JWT_SECRET) > 0

    def test_jwt_algorithm_exists(self):
        """Test JWT_ALGORITHM constant exists"""
        assert JWT_ALGORITHM is not None
        assert JWT_ALGORITHM == "HS256"

    def test_mock_user_structure(self):
        """Test MOCK_USER structure"""
        assert isinstance(MOCK_USER, dict)
        assert "user_id" in MOCK_USER
        assert "username" in MOCK_USER
        assert "role" in MOCK_USER
        assert "email" in MOCK_USER

        assert isinstance(MOCK_USER["user_id"], str)
        assert isinstance(MOCK_USER["username"], str)
        assert isinstance(MOCK_USER["role"], str)
        assert isinstance(MOCK_USER["email"], str)


class TestIntegration:
    """Test integration scenarios"""

    @pytest.mark.asyncio
    async def test_full_auth_flow_student(self):
        """Test full authentication flow for student"""
        # Create token for student
        token = create_mock_jwt_token("student123", "student")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Get current user
        user = await get_current_user(credentials)

        # Test student access
        student_user = await get_current_student_user(user)
        assert student_user["role"] == "student"

        # Test teacher access should fail
        with pytest.raises(HTTPException):
            await get_current_teacher_user(user)

        # Test admin access should fail
        with pytest.raises(HTTPException):
            await get_current_admin_user(user)

    @pytest.mark.asyncio
    async def test_full_auth_flow_teacher(self):
        """Test full authentication flow for teacher"""
        # Create token for teacher
        token = create_mock_jwt_token("teacher123", "teacher")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Get current user
        user = await get_current_user(credentials)

        # Test student access
        student_user = await get_current_student_user(user)
        assert student_user["role"] == "teacher"

        # Test teacher access
        teacher_user = await get_current_teacher_user(user)
        assert teacher_user["role"] == "teacher"

        # Test admin access should fail
        with pytest.raises(HTTPException):
            await get_current_admin_user(user)

    @pytest.mark.asyncio
    async def test_full_auth_flow_admin(self):
        """Test full authentication flow for admin"""
        # Create token for admin
        token = create_mock_jwt_token("admin123", "admin")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Get current user
        user = await get_current_user(credentials)

        # Test all access levels
        student_user = await get_current_student_user(user)
        assert student_user["role"] == "admin"

        teacher_user = await get_current_teacher_user(user)
        assert teacher_user["role"] == "admin"

        admin_user = await get_current_admin_user(user)
        assert admin_user["role"] == "admin"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
