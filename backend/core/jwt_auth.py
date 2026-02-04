"""
JWT Authentication System (Task 48.4: Enhanced with Database Refresh Tokens)
Production-ready JWT implementation with refresh tokens, blacklisting, and security features
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import get_settings


class TokenType(str, Enum):
    """Token türleri"""

    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"


class UserRole(str, Enum):
    """Kullanıcı rolleri"""

    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class TokenPayload(BaseModel):
    """JWT token payload model"""

    sub: str  # user_id
    email: str
    role: UserRole
    exp: datetime
    iat: datetime
    type: TokenType
    jti: str  # JWT ID for blacklisting
    device_id: str | None = None
    permissions: list[str] = []


class JWTTokens(BaseModel):
    """JWT token pair"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class JWTManager:
    """JWT token yönetimi ve güvenlik"""

    def __init__(self):
        self.settings = get_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer(auto_error=False)

        # JWT ayarları
        self.secret_key = self.settings.jwt_secret_key
        self.algorithm = self.settings.jwt_algorithm
        self.access_token_expire_minutes = self.settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = self.settings.jwt_refresh_token_expire_days

        # Token blacklist (production'da Redis kullanılmalı)
        self.blacklisted_tokens: set = set()

        # Device tracking (brute force koruması için)
        self.device_attempts: dict[str, dict] = {}

    def create_access_token(
        self,
        user_id: str,
        email: str,
        role: UserRole,
        permissions: list[str] = None,
        device_id: str = None,
    ) -> str:
        """Access token oluştur"""
        if permissions is None:
            permissions = self._get_default_permissions(role)

        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "email": email,
            "role": role.value,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": TokenType.ACCESS.value,
            "jti": secrets.token_urlsafe(32),
            "device_id": device_id,
            "permissions": permissions,
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self, user_id: str, email: str, role: UserRole, device_id: str = None
    ) -> str:
        """Refresh token oluştur"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": user_id,
            "email": email,
            "role": role.value,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": TokenType.REFRESH.value,
            "jti": secrets.token_urlsafe(32),
            "device_id": device_id,
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_token_pair(
        self,
        user_id: str,
        email: str,
        role: UserRole,
        permissions: list[str] = None,
        device_id: str = None,
    ) -> JWTTokens:
        """Access ve refresh token çifti oluştur"""
        access_token = self.create_access_token(
            user_id, email, role, permissions, device_id
        )
        refresh_token = self.create_refresh_token(user_id, email, role, device_id)

        return JWTTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60,
            refresh_expires_in=self.refresh_token_expire_days * 24 * 60 * 60,
        )

    def verify_token(self, token: str, token_type: TokenType = None) -> TokenPayload:
        """Token doğrula ve payload döndür"""
        try:
            # Token blacklist kontrolü
            if self._is_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                )

            # JWT decode
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Token type kontrolü
            if token_type and payload.get("type") != token_type.value:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected: {token_type.value}",
                )

            # Payload validation
            if not payload.get("sub") or not payload.get("email"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )

            # Expiration check (jwt library handles this automatically)
            # Role validation
            role = payload.get("role")
            if role not in [r.value for r in UserRole]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user role in token",
                )

            return TokenPayload(
                sub=payload["sub"],
                email=payload["email"],
                role=UserRole(role),
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
                type=TokenType(payload["type"]),
                jti=payload.get("jti", ""),
                device_id=payload.get("device_id"),
                permissions=payload.get("permissions", []),
            )

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {e!s}",
            )

    def refresh_access_token(
        self, refresh_token: str, db: Session = None, request: Request = None
    ) -> JWTTokens:
        """
        Refresh token ile yeni access token oluştur (Task 48.4: Database-backed)

        Args:
            refresh_token: Refresh token string
            db: Database session (optional - for persistence)
            request: FastAPI request (optional - for IP/user-agent tracking)

        Returns:
            JWTTokens: Yeni access ve refresh token çifti
        """
        # Refresh token doğrula
        payload = self.verify_token(refresh_token, TokenType.REFRESH)

        # Database persistence varsa, refresh token'ı kontrol et
        if db:
            from models.database import RefreshToken

            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            db_token = (
                db.query(RefreshToken)
                .filter(
                    RefreshToken.jti == payload.jti,
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.revoked == False,
                )
                .first()
            )

            if not db_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has been revoked or does not exist",
                )

            # Token expiration kontrolü
            if db_token.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has expired",
                )

            # Usage tracking
            db_token.last_used_at = datetime.utcnow()
            db_token.usage_count += 1

            # Revoke eski token (rotation policy)
            db_token.revoked = True
            db_token.revoked_at = datetime.utcnow()
            db_token.revoke_reason = "rotated"

        # Yeni token çifti oluştur
        new_tokens = self.create_token_pair(
            user_id=payload.sub,
            email=payload.email,
            role=payload.role,
            permissions=payload.permissions,
            device_id=payload.device_id,
        )

        # Yeni refresh token'ı database'e kaydet
        if db and request:
            self._save_refresh_token_to_db(
                db,
                new_tokens.refresh_token,
                payload.sub,
                payload.device_id,
                request,
            )

        # Eski refresh token'ı blacklist'e ekle (in-memory fallback)
        self.blacklist_token(refresh_token)

        # Database değişikliklerini commit et
        if db:
            db.commit()

        return new_tokens

    def blacklist_token(self, token: str):
        """Token'ı blacklist'e ekle"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            jti = payload.get("jti")
            if jti:
                self.blacklisted_tokens.add(jti)
        except:
            # Token decode edilemese bile güvenlik için ekle
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            self.blacklisted_tokens.add(token_hash)

    def _is_blacklisted(self, token: str) -> bool:
        """Token blacklist kontrolü"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},
            )
            jti = payload.get("jti")
            if jti and jti in self.blacklisted_tokens:
                return True
        except:
            pass

        # Fallback: token hash kontrolü
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token_hash in self.blacklisted_tokens

    def _get_default_permissions(self, role: UserRole) -> list[str]:
        """Role'e göre default permission'ları döndür"""
        permission_map = {
            UserRole.STUDENT: [
                "exam:take",
                "exam:view_results",
                "dashboard:view",
                "content:view",
                "learning_style:view",
                "zpd:view",
            ],
            UserRole.TEACHER: [
                "exam:create",
                "exam:manage",
                "exam:view_all_results",
                "student:view",
                "student:manage",
                "content:create",
                "content:manage",
                "dashboard:teacher",
                "reports:view",
            ],
            UserRole.PARENT: [
                "child:view",
                "child:track",
                "reports:child",
                "dashboard:parent",
            ],
            UserRole.ADMIN: [
                "user:manage",
                "content:admin",
                "system:monitor",
                "reports:admin",
                "dashboard:admin",
            ],
            UserRole.SUPER_ADMIN: ["*"],  # All permissions
        }

        return permission_map.get(role, [])

    def hash_password(self, password: str) -> str:
        """Şifre hash'le"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Şifre doğrula"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def check_rate_limit(
        self, identifier: str, max_attempts: int = 5, window_minutes: int = 15
    ) -> bool:
        """Rate limiting kontrolü"""
        now = datetime.utcnow()

        if identifier not in self.device_attempts:
            self.device_attempts[identifier] = {"attempts": 0, "window_start": now}
            return True

        device_data = self.device_attempts[identifier]

        # Window reset kontrolü
        if now - device_data["window_start"] > timedelta(minutes=window_minutes):
            device_data["attempts"] = 0
            device_data["window_start"] = now

        # Attempt sayısı kontrolü
        if device_data["attempts"] >= max_attempts:
            return False

        device_data["attempts"] += 1
        return True

    def create_password_reset_token(self, user_id: str, email: str) -> str:
        """Şifre sıfırlama token'ı oluştur"""
        expire = datetime.utcnow() + timedelta(hours=1)  # 1 saat geçerli

        payload = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": TokenType.RESET_PASSWORD.value,
            "jti": secrets.token_urlsafe(32),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_email_verification_token(self, user_id: str, email: str) -> str:
        """Email doğrulama token'ı oluştur"""
        expire = datetime.utcnow() + timedelta(hours=24)  # 24 saat geçerli

        payload = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": TokenType.EMAIL_VERIFICATION.value,
            "jti": secrets.token_urlsafe(32),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def _save_refresh_token_to_db(
        self,
        db: Session,
        refresh_token: str,
        user_id: str,
        device_id: Optional[str],
        request: Request,
    ):
        """
        Refresh token'ı database'e kaydet (Task 48.4)

        Args:
            db: Database session
            refresh_token: Refresh token string
            user_id: User ID
            device_id: Device ID
            request: FastAPI request for IP/user-agent
        """
        from models.database import RefreshToken

        # Token payload'ı decode et
        try:
            payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},
            )
        except Exception:
            return  # Silent fail

        # Token hash oluştur
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        # Device bilgilerini çıkar
        user_agent = request.headers.get("user-agent", "") if request else ""
        ip_address = request.client.host if request and request.client else None

        # Device type detection (simple heuristic)
        device_type = "desktop"
        if user_agent:
            ua_lower = user_agent.lower()
            if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
                device_type = "mobile"
            elif "tablet" in ua_lower or "ipad" in ua_lower:
                device_type = "tablet"

        # Database'e kaydet
        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            jti=payload.get("jti", ""),
            device_id=device_id,
            device_name=None,  # Can be set by client
            device_type=device_type,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            expires_at=datetime.fromtimestamp(payload.get("exp", 0)),
            revoked=False,
        )

        db.add(db_token)

    def revoke_refresh_token(
        self, db: Session, refresh_token: str = None, jti: str = None
    ):
        """
        Refresh token'ı revoke et (Task 48.4)

        Args:
            db: Database session
            refresh_token: Refresh token string (optional)
            jti: JWT ID (optional)
        """
        from models.database import RefreshToken

        if refresh_token:
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            db_token = (
                db.query(RefreshToken)
                .filter(RefreshToken.token_hash == token_hash)
                .first()
            )
        elif jti:
            db_token = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        else:
            return

        if db_token and not db_token.revoked:
            db_token.revoked = True
            db_token.revoked_at = datetime.utcnow()
            db_token.revoke_reason = "manual_revoke"
            db.commit()

    def revoke_all_user_tokens(self, db: Session, user_id: str):
        """
        Kullanıcının tüm refresh token'larını revoke et (Task 48.4)
        Logout from all devices

        Args:
            db: Database session
            user_id: User ID
        """
        from models.database import RefreshToken

        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id, RefreshToken.revoked == False
        ).update(
            {
                "revoked": True,
                "revoked_at": datetime.utcnow(),
                "revoke_reason": "logout_all_devices",
            }
        )
        db.commit()

    def revoke_device_tokens(self, db: Session, user_id: str, device_id: str):
        """
        Belirli bir cihazın tüm token'larını revoke et (Task 48.4)

        Args:
            db: Database session
            user_id: User ID
            device_id: Device ID
        """
        from models.database import RefreshToken

        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.device_id == device_id,
            RefreshToken.revoked == False,
        ).update(
            {
                "revoked": True,
                "revoked_at": datetime.utcnow(),
                "revoke_reason": "device_revoke",
            }
        )
        db.commit()

    def cleanup_expired_tokens(self, db: Session):
        """
        Expired refresh token'ları database'den sil (Task 48.4)
        Maintenance task to be run periodically

        Args:
            db: Database session
        """
        from models.database import RefreshToken

        # 30 gün önce expire olmuş token'ları sil
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        db.query(RefreshToken).filter(RefreshToken.expires_at < cutoff_date).delete()
        db.commit()


# Global JWT manager instance
jwt_manager = JWTManager()


def get_jwt_manager() -> JWTManager:
    """JWT manager instance'ını döndür"""
    return jwt_manager


# FastAPI Dependencies
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True)),
    jwt_mgr: JWTManager = Depends(get_jwt_manager),
) -> TokenPayload:
    """
    FastAPI dependency to get current authenticated user from JWT token

    Usage:
        @app.get("/protected")
        async def protected_route(current_user: TokenPayload = Depends(get_current_user)):
            return {"user_id": current_user.sub, "email": current_user.email}

    Args:
        credentials: HTTP Bearer token from request header
        jwt_mgr: JWT manager instance

    Returns:
        TokenPayload: Decoded and validated token payload containing user info

    Raises:
        HTTPException: 401 if token is invalid, expired, or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = jwt_mgr.verify_token(token, TokenType.ACCESS)

    return payload


async def get_current_active_user(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    Get current user and verify they are active (not disabled/banned)

    Usage:
        @app.get("/active-only")
        async def active_route(user: TokenPayload = Depends(get_current_active_user)):
            return {"user_id": user.sub}

    Note: Currently just returns the user, but can be extended to check
    user status in database
    """
    # TODO: Add database check for user active status if needed
    # Example:
    # user_in_db = await get_user_from_db(current_user.sub)
    # if not user_in_db.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


async def require_role(
    required_roles: list[UserRole],
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    Require user to have one of the specified roles

    Usage:
        @app.get("/admin-only")
        async def admin_route(
            user: TokenPayload = Depends(
                lambda: require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])
            )
        ):
            return {"admin_data": "..."}

    Args:
        required_roles: List of allowed roles
        current_user: Current authenticated user

    Returns:
        TokenPayload: Current user if role matches

    Raises:
        HTTPException: 403 if user doesn't have required role
    """
    if current_user.role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required roles: {[r.value for r in required_roles]}",
        )

    return current_user


async def require_permission(
    required_permission: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    Require user to have a specific permission

    Usage:
        @app.post("/create-exam")
        async def create_exam(
            user: TokenPayload = Depends(
                lambda: require_permission("exam:create")
            )
        ):
            return {"status": "created"}

    Args:
        required_permission: Permission string (e.g., "exam:create")
        current_user: Current authenticated user

    Returns:
        TokenPayload: Current user if permission exists

    Raises:
        HTTPException: 403 if user doesn't have required permission
    """
    # Super admin has all permissions
    if current_user.role == UserRole.SUPER_ADMIN or "*" in current_user.permissions:
        return current_user

    if required_permission not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission required: {required_permission}",
        )

    return current_user
