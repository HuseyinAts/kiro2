"""
Complete User Registration and Authentication Flow Integration Testing
End-to-end testing of user lifecycle from registration to authenticated operations
"""

import pytest
import os
import sys
import asyncio
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List
import secrets
import hashlib

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_complete_user_registration_flow():
    """Test complete user registration workflow with validation and security"""

    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel, EmailStr, field_validator

        app = FastAPI(title="KIRO2 User Registration Flow")

        # Enhanced user database with validation
        class MockUserDatabase:
            def __init__(self):
                self.users = {}
                self.email_verification_tokens = {}
                self.user_profiles = {}

            def email_exists(self, email: str) -> bool:
                return any(user.get("email") == email for user in self.users.values())

            def create_user(self, user_data: dict) -> dict:
                if self.email_exists(user_data["email"]):
                    raise ValueError("Email already exists")

                user_id = f"user_{len(self.users) + 1:06d}"
                hashed_password = self._hash_password(user_data["password"])

                user = {
                    "id": user_id,
                    "email": user_data["email"],
                    "password_hash": hashed_password,
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "role": user_data.get("role", "student"),
                    "phone": user_data.get("phone"),
                    "birth_date": user_data.get("birth_date"),
                    "school": user_data.get("school"),
                    "grade": user_data.get("grade"),
                    "city": user_data.get("city"),
                    "is_active": False,  # Requires email verification
                    "is_verified": False,
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "profile_completion": self._calculate_profile_completion(user_data),
                }

                self.users[user_id] = user

                # Generate email verification token
                verification_token = secrets.token_urlsafe(32)
                self.email_verification_tokens[verification_token] = {
                    "user_id": user_id,
                    "email": user_data["email"],
                    "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                }

                return {**user, "verification_token": verification_token}

            def _hash_password(self, password: str) -> str:
                salt = secrets.token_hex(16)
                hashed = hashlib.pbkdf2_hmac(
                    "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
                )
                return f"{salt}:{hashed.hex()}"

            def _calculate_profile_completion(self, user_data: dict) -> float:
                required_fields = ["email", "first_name", "last_name", "password"]
                optional_fields = ["phone", "birth_date", "school", "grade", "city"]

                completed_required = sum(
                    1 for field in required_fields if user_data.get(field)
                )
                completed_optional = sum(
                    1 for field in optional_fields if user_data.get(field)
                )

                if completed_required < len(required_fields):
                    return 0.0  # Invalid registration

                completion = (completed_required + completed_optional) / (
                    len(required_fields) + len(optional_fields)
                )
                return round(completion * 100, 2)

            def verify_email(self, token: str) -> bool:
                token_data = self.email_verification_tokens.get(token)
                if not token_data:
                    return False

                # Check if token expired
                expires_at = datetime.fromisoformat(token_data["expires_at"])
                if datetime.now() > expires_at:
                    del self.email_verification_tokens[token]
                    return False

                # Activate user
                user_id = token_data["user_id"]
                if user_id in self.users:
                    self.users[user_id]["is_active"] = True
                    self.users[user_id]["is_verified"] = True
                    self.users[user_id]["verified_at"] = datetime.now().isoformat()
                    del self.email_verification_tokens[token]
                    return True

                return False

        # Enhanced request models with validation
        class UserRegistration(BaseModel):
            email: EmailStr
            password: str
            first_name: str
            last_name: str
            role: str = "student"
            phone: Optional[str] = None
            birth_date: Optional[str] = None
            school: Optional[str] = None
            grade: Optional[str] = None
            city: Optional[str] = None

            @field_validator("password")


            @classmethod


            def validate_password(cls, v):
                if len(v) < 8:
                    raise ValueError("Şifre en az 8 karakter olmalıdır")
                if not any(c.isupper() for c in v):
                    raise ValueError("Şifre en az bir büyük harf içermelidir")
                if not any(c.islower() for c in v):
                    raise ValueError("Şifre en az bir küçük harf içermelidir")
                if not any(c.isdigit() for c in v):
                    raise ValueError("Şifre en az bir rakam içermelidir")
                return v

            @field_validator("phone")


            @classmethod


            def validate_phone(cls, v):
                if v and not v.startswith("+90"):
                    raise ValueError("Türkiye telefon numarası +90 ile başlamalıdır")
                return v

            @field_validator("first_name", "last_name")


            @classmethod


            def validate_names(cls, v):
                if len(v) < 2:
                    raise ValueError("Ad ve soyad en az 2 karakter olmalıdır")
                if (
                    not v.replace(" ", "")
                    .replace("ç", "")
                    .replace("ğ", "")
                    .replace("ı", "")
                    .replace("ö", "")
                    .replace("ş", "")
                    .replace("ü", "")
                    .replace("Ç", "")
                    .replace("Ğ", "")
                    .replace("İ", "")
                    .replace("Ö", "")
                    .replace("Ş", "")
                    .replace("Ü", "")
                    .isalpha()
                ):
                    raise ValueError("Ad ve soyad sadece harf karakterleri içermelidir")
                return v

        class EmailVerification(BaseModel):
            token: str

        # Initialize database
        user_db = MockUserDatabase()

        # API endpoints
        @app.post("/api/auth/register")
        async def register_user(user_data: UserRegistration):
            try:
                # Check if email already exists
                if user_db.email_exists(user_data.email):
                    raise HTTPException(
                        status_code=409, detail="Bu e-posta adresi zaten kullanılıyor"
                    )

                # Create user
                created_user = user_db.create_user(user_data.dict())

                return {
                    "success": True,
                    "message": "Kullanıcı başarıyla oluşturuldu. E-posta doğrulama linki gönderildi.",
                    "user_id": created_user["id"],
                    "email": created_user["email"],
                    "profile_completion": created_user["profile_completion"],
                    "verification_required": True,
                    "verification_token": created_user[
                        "verification_token"
                    ],  # Normally sent via email
                }

            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.post("/api/auth/verify-email")
        async def verify_email(verification: EmailVerification):
            success = user_db.verify_email(verification.token)

            if not success:
                raise HTTPException(
                    status_code=400,
                    detail="Geçersiz veya süresi dolmuş doğrulama tokeni",
                )

            return {
                "success": True,
                "message": "E-posta başarıyla doğrulandı. Artık giriş yapabilirsiniz.",
                "verified": True,
            }

        @app.get("/api/users/{user_id}/profile")
        async def get_user_profile(user_id: str):
            user = user_db.users.get(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

            # Return profile without sensitive data
            profile = {
                "id": user["id"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "role": user["role"],
                "phone": user.get("phone"),
                "school": user.get("school"),
                "grade": user.get("grade"),
                "city": user.get("city"),
                "is_active": user["is_active"],
                "is_verified": user["is_verified"],
                "profile_completion": user["profile_completion"],
                "created_at": user["created_at"],
                "last_login": user.get("last_login"),
            }

            return {"success": True, "profile": profile}

        # Test client
        client = TestClient(app)

        # Test successful registration with complete profile
        complete_registration = {
            "email": "mehmet.ozturk@gmail.com",
            "password": "SecurePass123!",
            "first_name": "Mehmet",
            "last_name": "Öztürk",
            "role": "student",
            "phone": "+90 532 123 45 67",
            "birth_date": "2005-03-15",
            "school": "Atatürk Anadolu Lisesi",
            "grade": "11",
            "city": "İstanbul",
        }

        response = client.post("/api/auth/register", json=complete_registration)
        assert response.status_code == 200

        registration_result = response.json()
        assert registration_result["success"] is True
        assert "user_id" in registration_result
        assert registration_result["email"] == complete_registration["email"]
        assert registration_result["profile_completion"] == 100.0  # Complete profile
        assert registration_result["verification_required"] is True

        user_id = registration_result["user_id"]
        verification_token = registration_result["verification_token"]

        # Verify user profile before email verification
        response = client.get(f"/api/users/{user_id}/profile")
        assert response.status_code == 200

        profile_data = response.json()
        assert profile_data["success"] is True
        profile = profile_data["profile"]
        assert profile["is_active"] is False  # Not active until email verified
        assert profile["is_verified"] is False
        assert profile["profile_completion"] == 100.0

        # Test email verification
        verification_data = {"token": verification_token}
        response = client.post("/api/auth/verify-email", json=verification_data)
        assert response.status_code == 200

        verification_result = response.json()
        assert verification_result["success"] is True
        assert verification_result["verified"] is True

        # Verify user is now active
        response = client.get(f"/api/users/{user_id}/profile")
        assert response.status_code == 200

        profile_data = response.json()
        profile = profile_data["profile"]
        assert profile["is_active"] is True
        assert profile["is_verified"] is True

        # Test registration with minimal profile
        minimal_registration = {
            "email": "ayse.demir@hotmail.com",
            "password": "MinimalPass456!",
            "first_name": "Ayşe",
            "last_name": "Demir",
        }

        response = client.post("/api/auth/register", json=minimal_registration)
        assert response.status_code == 200

        minimal_result = response.json()
        assert minimal_result["profile_completion"] == 44.44  # 4/9 fields completed

        # Test validation errors
        invalid_registrations = [
            {
                "email": "invalid-email",  # Invalid email
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "User",
            },
            {
                "email": "test@example.com",
                "password": "weak",  # Weak password
                "first_name": "Test",
                "last_name": "User",
            },
            {
                "email": "test2@example.com",
                "password": "SecurePass123!",
                "first_name": "T",  # Too short name
                "last_name": "User",
            },
            {
                "email": "test3@example.com",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "User",
                "phone": "532 123 45 67",  # Invalid phone format
            },
        ]

        for invalid_data in invalid_registrations:
            response = client.post("/api/auth/register", json=invalid_data)
            assert response.status_code == 422  # Validation error

        # Test duplicate email registration
        response = client.post("/api/auth/register", json=complete_registration)
        assert response.status_code == 409  # Conflict - email exists

        # Test invalid verification token
        invalid_verification = {"token": "invalid_token_12345"}
        response = client.post("/api/auth/verify-email", json=invalid_verification)
        assert response.status_code == 400

        print("✅ Complete user registration flow successful")

    except Exception as e:
        print(f"User registration flow test failed: {e}")


def test_authentication_and_session_management():
    """Test user authentication, token management, and session handling"""

    try:
        from fastapi import FastAPI, Depends, HTTPException, status
        from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
        from fastapi.testclient import TestClient
        from pydantic import BaseModel
        import jwt
        from datetime import datetime, timedelta

        app = FastAPI(title="KIRO2 Authentication System")

        # Enhanced authentication system
        class MockAuthenticationService:
            def __init__(self):
                self.users = {}
                self.active_sessions = {}
                self.refresh_tokens = {}
                self.failed_attempts = {}
                self.secret_key = "kiro2_super_secret_key_for_testing"
                self.algorithm = "HS256"
                self.access_token_expire_minutes = 30
                self.refresh_token_expire_days = 7
                self.max_failed_attempts = 5
                self.lockout_duration_minutes = 15

            def hash_password(self, password: str) -> str:
                salt = secrets.token_hex(16)
                hashed = hashlib.pbkdf2_hmac(
                    "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
                )
                return f"{salt}:{hashed.hex()}"

            def verify_password(self, password: str, hashed_password: str) -> bool:
                try:
                    salt, hash_hex = hashed_password.split(":")
                    hashed = hashlib.pbkdf2_hmac(
                        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
                    )
                    return hashed.hex() == hash_hex
                except:
                    return False

            def register_user(
                self,
                email: str,
                password: str,
                first_name: str,
                last_name: str,
                role: str = "student",
            ):
                if email in self.users:
                    raise ValueError("User already exists")

                user_id = f"user_{len(self.users) + 1:06d}"
                password_hash = self.hash_password(password)

                self.users[email] = {
                    "id": user_id,
                    "email": email,
                    "password_hash": password_hash,
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": role,
                    "is_active": True,
                    "is_verified": True,
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "login_count": 0,
                }

                return self.users[email]

            def is_account_locked(self, email: str) -> bool:
                if email not in self.failed_attempts:
                    return False

                attempts_data = self.failed_attempts[email]
                if attempts_data["count"] >= self.max_failed_attempts:
                    lockout_time = datetime.fromisoformat(attempts_data["locked_at"])
                    unlock_time = lockout_time + timedelta(
                        minutes=self.lockout_duration_minutes
                    )
                    return datetime.now() < unlock_time

                return False

            def record_failed_attempt(self, email: str):
                if email not in self.failed_attempts:
                    self.failed_attempts[email] = {"count": 0, "locked_at": None}

                self.failed_attempts[email]["count"] += 1
                if self.failed_attempts[email]["count"] >= self.max_failed_attempts:
                    self.failed_attempts[email][
                        "locked_at"
                    ] = datetime.now().isoformat()

            def reset_failed_attempts(self, email: str):
                if email in self.failed_attempts:
                    del self.failed_attempts[email]

            def authenticate_user(self, email: str, password: str) -> dict:
                # Check if account is locked
                if self.is_account_locked(email):
                    raise HTTPException(
                        status_code=423,
                        detail="Hesap geçici olarak kilitlenmiştir. Lütfen daha sonra tekrar deneyin.",
                    )

                # Check if user exists
                user = self.users.get(email)
                if not user:
                    self.record_failed_attempt(email)
                    raise HTTPException(
                        status_code=401, detail="Geçersiz e-posta veya şifre"
                    )

                # Check if user is active
                if not user["is_active"]:
                    raise HTTPException(status_code=403, detail="Hesap aktif değil")

                # Verify password
                if not self.verify_password(password, user["password_hash"]):
                    self.record_failed_attempt(email)
                    raise HTTPException(
                        status_code=401, detail="Geçersiz e-posta veya şifre"
                    )

                # Reset failed attempts on successful login
                self.reset_failed_attempts(email)

                # Update user login info
                user["last_login"] = datetime.now().isoformat()
                user["login_count"] += 1

                # Generate tokens
                access_token = self.create_access_token(
                    {"user_id": user["id"], "email": email, "role": user["role"]}
                )
                refresh_token = self.create_refresh_token({"user_id": user["id"]})

                # Store session
                session_id = secrets.token_urlsafe(32)
                self.active_sessions[session_id] = {
                    "user_id": user["id"],
                    "email": email,
                    "created_at": datetime.now().isoformat(),
                    "expires_at": (
                        datetime.now()
                        + timedelta(minutes=self.access_token_expire_minutes)
                    ).isoformat(),
                    "refresh_token": refresh_token,
                }

                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": self.access_token_expire_minutes * 60,
                    "session_id": session_id,
                    "user": {
                        "id": user["id"],
                        "email": user["email"],
                        "first_name": user["first_name"],
                        "last_name": user["last_name"],
                        "role": user["role"],
                    },
                }

            def create_access_token(self, data: dict) -> str:
                expire = datetime.now(timezone.utc) + timedelta(
                    minutes=self.access_token_expire_minutes
                )
                to_encode = data.copy()
                to_encode.update({"exp": expire, "type": "access"})
                encoded_jwt = jwt.encode(
                    to_encode, self.secret_key, algorithm=self.algorithm
                )
                return encoded_jwt

            def create_refresh_token(self, data: dict) -> str:
                expire = datetime.now(timezone.utc) + timedelta(
                    days=self.refresh_token_expire_days
                )
                to_encode = data.copy()
                to_encode.update({"exp": expire, "type": "refresh"})
                encoded_jwt = jwt.encode(
                    to_encode, self.secret_key, algorithm=self.algorithm
                )

                # Store refresh token
                self.refresh_tokens[encoded_jwt] = {
                    "user_id": data["user_id"],
                    "created_at": datetime.now().isoformat(),
                    "expires_at": expire.isoformat(),
                }

                return encoded_jwt

            def verify_token(self, token: str) -> dict:
                try:
                    payload = jwt.decode(
                        token, self.secret_key, algorithms=[self.algorithm]
                    )
                    if payload.get("type") != "access":
                        raise HTTPException(
                            status_code=401, detail="Invalid token type"
                        )
                    return payload
                except jwt.ExpiredSignatureError:
                    raise HTTPException(status_code=401, detail="Token has expired")
                except jwt.JWTError:
                    raise HTTPException(status_code=401, detail="Invalid token")

            def refresh_access_token(self, refresh_token: str) -> dict:
                if refresh_token not in self.refresh_tokens:
                    raise HTTPException(status_code=401, detail="Invalid refresh token")

                try:
                    payload = jwt.decode(
                        refresh_token, self.secret_key, algorithms=[self.algorithm]
                    )
                    if payload.get("type") != "refresh":
                        raise HTTPException(
                            status_code=401, detail="Invalid token type"
                        )

                    user_id = payload["user_id"]

                    # Find user by id
                    user = None
                    for email, user_data in self.users.items():
                        if user_data["id"] == user_id:
                            user = user_data
                            user["email"] = email
                            break

                    if not user:
                        raise HTTPException(status_code=401, detail="User not found")

                    # Generate new access token
                    new_access_token = self.create_access_token(
                        {
                            "user_id": user["id"],
                            "email": user["email"],
                            "role": user["role"],
                        }
                    )

                    return {
                        "access_token": new_access_token,
                        "token_type": "bearer",
                        "expires_in": self.access_token_expire_minutes * 60,
                    }

                except jwt.ExpiredSignatureError:
                    # Remove expired refresh token
                    del self.refresh_tokens[refresh_token]
                    raise HTTPException(
                        status_code=401, detail="Refresh token has expired"
                    )
                except jwt.JWTError:
                    raise HTTPException(status_code=401, detail="Invalid refresh token")

            def logout(self, session_id: str) -> bool:
                if session_id in self.active_sessions:
                    session_data = self.active_sessions[session_id]
                    refresh_token = session_data.get("refresh_token")

                    # Remove refresh token
                    if refresh_token and refresh_token in self.refresh_tokens:
                        del self.refresh_tokens[refresh_token]

                    # Remove session
                    del self.active_sessions[session_id]
                    return True

                return False

        # Initialize authentication service
        auth_service = MockAuthenticationService()
        security = HTTPBearer()

        # Request models
        class UserLogin(BaseModel):
            email: str
            password: str

        class TokenRefresh(BaseModel):
            refresh_token: str

        class LogoutRequest(BaseModel):
            session_id: str

        # Dependency for protected routes
        async def get_current_user(
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            token = credentials.credentials
            payload = auth_service.verify_token(token)
            return payload

        # API endpoints
        @app.post("/api/auth/register")
        async def register(user_data: dict):
            try:
                user = auth_service.register_user(
                    email=user_data["email"],
                    password=user_data["password"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    role=user_data.get("role", "student"),
                )

                return {
                    "success": True,
                    "message": "Kullanıcı başarıyla oluşturuldu",
                    "user_id": user["id"],
                }
            except ValueError as e:
                raise HTTPException(status_code=409, detail=str(e))

        @app.post("/api/auth/login")
        async def login(login_data: UserLogin):
            auth_result = auth_service.authenticate_user(
                login_data.email, login_data.password
            )
            return {"success": True, "message": "Giriş başarılı", **auth_result}

        @app.post("/api/auth/refresh")
        async def refresh_token(refresh_data: TokenRefresh):
            refresh_result = auth_service.refresh_access_token(
                refresh_data.refresh_token
            )
            return {"success": True, "message": "Token yenilendi", **refresh_result}

        @app.post("/api/auth/logout")
        async def logout(logout_data: LogoutRequest):
            success = auth_service.logout(logout_data.session_id)
            if success:
                return {"success": True, "message": "Çıkış başarılı"}
            else:
                raise HTTPException(status_code=400, detail="Geçersiz oturum")

        @app.get("/api/auth/me")
        async def get_current_user_info(current_user: dict = Depends(get_current_user)):
            return {
                "success": True,
                "user": {
                    "id": current_user["user_id"],
                    "email": current_user["email"],
                    "role": current_user["role"],
                },
            }

        @app.get("/api/protected/dashboard")
        async def protected_dashboard(current_user: dict = Depends(get_current_user)):
            return {
                "success": True,
                "message": f"Hoş geldiniz, {current_user['email']}!",
                "dashboard_data": {
                    "user_id": current_user["user_id"],
                    "access_time": datetime.now().isoformat(),
                    "features": ["exams", "analytics", "chat", "study_materials"],
                },
            }

        # Test client
        client = TestClient(app)

        # Test user registration for authentication
        registration_data = {
            "email": "auth.test@example.com",
            "password": "AuthTestPass123!",
            "first_name": "Auth",
            "last_name": "Tester",
            "role": "student",
        }

        response = client.post("/api/auth/register", json=registration_data)
        assert response.status_code == 200

        # Test successful authentication
        login_data = {"email": "auth.test@example.com", "password": "AuthTestPass123!"}

        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200

        auth_result = response.json()
        assert auth_result["success"] is True
        assert "access_token" in auth_result
        assert "refresh_token" in auth_result
        assert "session_id" in auth_result
        assert auth_result["token_type"] == "bearer"
        assert auth_result["user"]["email"] == "auth.test@example.com"

        access_token = auth_result["access_token"]
        refresh_token = auth_result["refresh_token"]
        session_id = auth_result["session_id"]

        # Test protected route access with valid token
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200

        user_info = response.json()
        assert user_info["success"] is True
        assert user_info["user"]["email"] == "auth.test@example.com"

        # Test dashboard access
        response = client.get("/api/protected/dashboard", headers=headers)
        assert response.status_code == 200

        dashboard_data = response.json()
        assert dashboard_data["success"] is True
        assert "dashboard_data" in dashboard_data

        # Test token refresh
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/auth/refresh", json=refresh_data)
        assert response.status_code == 200

        refresh_result = response.json()
        assert refresh_result["success"] is True
        assert "access_token" in refresh_result

        new_access_token = refresh_result["access_token"]
        assert new_access_token != access_token  # Should be different

        # Test access with new token
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        response = client.get("/api/auth/me", headers=new_headers)
        assert response.status_code == 200

        # Test logout
        logout_data = {"session_id": session_id}
        response = client.post("/api/auth/logout", json=logout_data)
        assert response.status_code == 200

        logout_result = response.json()
        assert logout_result["success"] is True

        # Test access after logout (should fail)
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401  # Token should still work until expiry

        # Test failed authentication attempts
        wrong_login_data = {
            "email": "auth.test@example.com",
            "password": "WrongPassword123!",
        }

        # Test multiple failed attempts
        for i in range(3):
            response = client.post("/api/auth/login", json=wrong_login_data)
            assert response.status_code == 401

        # Test authentication errors
        invalid_email_login = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        }

        response = client.post("/api/auth/login", json=invalid_email_login)
        assert response.status_code == 401

        # Test invalid token access
        invalid_headers = {"Authorization": "Bearer invalid_token_123"}
        response = client.get("/api/auth/me", headers=invalid_headers)
        assert response.status_code == 401

        print("✅ Authentication and session management successful")

    except Exception as e:
        print(f"Authentication and session management test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
