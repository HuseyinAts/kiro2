import logging
import uuid
from typing import Any
from datetime import datetime

from pydantic import ConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from passlib.context import CryptContext

from core.cqrs.base import Command, CommandHandler
from core.kvkk_compliance import is_minor

logger = logging.getLogger(__name__)

# Kopyalanan sabit
_SELF_REGISTERABLE_ROLES = {
    "ogrenci": "STUDENT",
    "student": "STUDENT",
    "veli": "PARENT",
    "parent": "PARENT",
    "ogretmen": "TEACHER",
    "teacher": "TEACHER",
}

def _map_registration_role(rol: Any) -> str:
    rol_key = (rol.value if hasattr(rol, 'value') else str(rol)).strip().lower()
    mapped = _SELF_REGISTERABLE_ROLES.get(rol_key)
    if mapped is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu rol herkese açık kayıt ile oluşturulamaz",
        )
    return mapped

class RegisterUserCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    email: str
    sifre: str
    ad_soyad: str
    rol: Any
    birth_date: Any = None
    veli_email: str | None = None
    sinif: int | None = None
    db: Any  # AsyncSession

class RegisterUserCommandHandler(CommandHandler[RegisterUserCommand, dict[str, Any]]):
    async def handle(self, command: RegisterUserCommand) -> dict[str, Any]:
        db: AsyncSession = command.db
        
        minor = is_minor(command.birth_date)
        if minor and not command.veli_email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="18 yaşından küçük kullanıcılar için veli e-postası zorunludur (KVKK)",
            )

        rol_str = _map_registration_role(command.rol)

        # E-posta benzersizlik kontrolü
        dup = await db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": command.email},
        )
        if dup.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu e-posta adresi zaten kullanımda",
            )

        # Şifre hash
        _pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        pw_hash = _pwd_ctx.hash(command.sifre)

        parts = (command.ad_soyad or "").strip().split(" ", 1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""

        user_id = str(uuid.uuid4())

        await db.execute(
            text("""
            INSERT INTO users
                (id, email, username, password_hash, first_name, last_name,
                 role, is_active, is_verified, total_xp, level,
                 elo_rating, is_premium, is_parent, birth_date, is_2fa_enabled, created_at, updated_at)
            VALUES
                (:id, :email, :username, :pw_hash, :first_name, :last_name,
                 :role, TRUE, FALSE, 0, 1,
                 1200, FALSE, FALSE, :birth_date, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """),
            {
                "id": user_id,
                "email": command.email,
                "username": command.email.split("@")[0],
                "pw_hash": pw_hash,
                "first_name": first_name,
                "last_name": last_name,
                "role": rol_str,
                "birth_date": command.birth_date,
            },
        )

        if rol_str == "STUDENT":
            profile_id = user_id
            grade_level = command.sinif if command.sinif is not None else 11
            if not isinstance(grade_level, int) or grade_level < 9 or grade_level > 12:
                grade_level = 11

            await db.execute(
                text("""
                INSERT INTO student_profiles
                    (id, user_id, grade_level, veli_onay, veli_email, current_level,
                     total_study_hours, total_questions_solved, correct_answers,
                     irt_ability, created_at, updated_at)
                VALUES
                    (:id, :user_id, :grade_level, :veli_onay, :veli_email, 0.0,
                     0, 0, 0,
                     0.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """),
                {
                    "id": profile_id,
                    "user_id": user_id,
                    "grade_level": grade_level,
                    "veli_onay": not minor,
                    "veli_email": command.veli_email if minor else None,
                },
            )

        await db.commit()

        if minor and command.veli_email:
            try:
                from services.veli_onay_service import VeliOnayService
                # Veli onayı e-posta vs işlemleri. (Eski koddaki send email stub olarak duruyor)
                # Buraya direkt taşınabilir veya background task eklenebilir.
                token = await VeliOnayService(db).request_consent(
                    child_user_id=user_id, veli_email=command.veli_email
                )
                from core.email_util import send_email
                send_email(command.veli_email, "Veli Onayı", f"Token: {token}")
            except Exception as e:
                logger.error("veli onay tetikleme hatası: %s", e)

        logger.info(f"Yeni kullanıcı kaydı: {command.email} ({rol_str})")
        return {
            "success": True,
            "message": "Kullanıcı kaydı başarıyla oluşturuldu",
            "id": user_id,
        }

from datetime import UTC
import jwt as pyjwt
from core.dependencies import JWT_ALGORITHM, JWT_SECRET
from core.jwt_auth import get_jwt_manager, UserRole as JWTUserRole
from models.database import User as DBUser
from sqlalchemy import select

class TwoFactorRequired(Exception):
    def __init__(self, user_id: str, email: str):
        self.user_id = user_id
        self.email = email
        super().__init__("2FA verification required")

class LoginCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    email: str
    password: str
    db: Any

class LoginCommandHandler(CommandHandler[LoginCommand, dict[str, Any]]):
    async def handle(self, command: LoginCommand) -> dict[str, Any]:
        db: AsyncSession = command.db
        
        result = await db.execute(select(DBUser).where(DBUser.email == command.email))
        db_user = result.scalar_one_or_none()

        if not db_user:
            raise ValueError("Geçersiz e-posta veya şifre")

        if not db_user.is_active:
            raise ValueError("Hesap aktif değil")

        if not command.password:
            raise ValueError("Şifre alanı boş olamaz")

        import asyncio
        from passlib.context import CryptContext
        import os
        
        _BCRYPT_COST = int(os.environ.get("BCRYPT_COST", "10") or 10)
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=_BCRYPT_COST)
        
        loop = asyncio.get_running_loop()
        is_valid = await loop.run_in_executor(
            None, pwd_context.verify, command.password, db_user.password_hash
        )
        if not is_valid:
            raise ValueError("Geçersiz e-posta veya şifre")

        if getattr(db_user, "is_2fa_enabled", False) and db_user.secret_2fa:
            raise TwoFactorRequired(user_id=str(db_user.id), email=db_user.email)

        jwt_mgr = get_jwt_manager()
        jwt_role = JWTUserRole(db_user.role.value.lower())
        token = jwt_mgr.create_access_token(
            user_id=str(db_user.id),
            email=db_user.email,
            role=jwt_role,
            username=db_user.username,
        )
        refresh_token = jwt_mgr.create_refresh_token(
            user_id=str(db_user.id),
            email=db_user.email,
            role=jwt_role,
        )
        expires_in = jwt_mgr.access_token_expire_minutes * 60

        try:
            import hashlib as _hashlib
            from sqlalchemy import text as _text
            
            _payload = pyjwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            _token_hash = _hashlib.sha256(refresh_token.encode()).hexdigest()
            _jti = _payload.get("jti", "") if _payload else ""
            _exp = datetime.fromtimestamp(_payload.get("exp", 0), tz=UTC) if _payload else datetime.now(UTC)
            
            async with db.begin_nested():
                await db.execute(
                    _text("""
                        INSERT INTO refresh_tokens
                            (id, user_id, token_hash, jti, device_type, expires_at,
                             revoked, usage_count, created_at, updated_at)
                        VALUES
                            (gen_random_uuid(), :uid, :th, :jti, 'desktop', :exp,
                             false, 0, now(), now())
                        ON CONFLICT DO NOTHING
                    """),
                    {"uid": str(db_user.id), "th": _token_hash, "jti": _jti, "exp": _exp},
                )
        except Exception as _rt_err:
            logger.warning(f"Failed to persist refresh token to DB: {_rt_err}")

        db_user.last_login = datetime.now(UTC)
        await db.commit()

        role_mapping = {
            "STUDENT": "ogrenci",
            "TEACHER": "ogretmen",
            "PARENT": "veli",
            "ADMIN": "admin",
            "SUPER_ADMIN": "super_admin",
        }
        frontend_role = role_mapping.get(db_user.role.value, "ogrenci")

        return {
            "success": True,
            "token": token,
            "refreshToken": refresh_token,
            "user": {
                "id": str(db_user.id),
                "email": db_user.email,
                "ad": db_user.first_name,
                "soyad": db_user.last_name,
                "rol": frontend_role,
                "aktif": db_user.is_active,
                "olusturma_tarihi": (db_user.created_at.isoformat() if db_user.created_at else None),
                "son_giris": (db_user.last_login.isoformat() if db_user.last_login else None),
                "telefon": db_user.phone or "",
                "profil_resmi": None,
            },
            "access_token": token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "kullanici": {
                "kullanici_id": str(db_user.id),
                "email": db_user.email,
                "ad_soyad": f"{db_user.first_name} {db_user.last_name}",
                "telefon": db_user.phone or "",
                "aktif": db_user.is_active,
                "rol": frontend_role,
                "olusturma_tarihi": db_user.created_at,
                "son_giris": db_user.last_login,
            }
        }


class RefreshTokenCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    refresh_token: str
    db: Any

class RefreshTokenCommandHandler(CommandHandler[RefreshTokenCommand, dict[str, Any]]):
    async def handle(self, command: RefreshTokenCommand) -> dict[str, Any]:
        jwt_mgr = get_jwt_manager()
        try:
            # We use the async version because we don't have request here easily without leaking HTTP details
            # Wait, jwt_mgr.refresh_access_token handles revocation checks
            new_tokens = await jwt_mgr.refresh_access_token(
                command.refresh_token,
                db=command.db  # Pass async session if refresh_access_token supports it, else we need sync
            )
            return {
                'success': True,
                'token': new_tokens.access_token,
                'refreshToken': new_tokens.refresh_token,
                'access_token': new_tokens.access_token,
                'refresh_token': new_tokens.refresh_token,
                'token_type': new_tokens.token_type,
                'expires_in': new_tokens.expires_in,
            }
        except Exception as e:
            raise ValueError(str(e))



class VeliOnayVerifyCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    token: str
    ip: str | None = None
    ua: str | None = None
    db: Any

class VeliOnayVerifyCommandHandler(CommandHandler[VeliOnayVerifyCommand, dict[str, Any]]):
    async def handle(self, command: VeliOnayVerifyCommand) -> dict[str, Any]:
        from services.veli_onay_service import VeliOnayService
        result = await VeliOnayService(command.db).verify_and_grant(command.token, ip=command.ip, ua=command.ua)
        if not result.success:
            raise ValueError(result.message)
        return {
            'status': result.status or 'granted',
            'message': result.message or ''
        }

class VeliOnayWithdrawCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    token: str
    db: Any

class VeliOnayWithdrawCommandHandler(CommandHandler[VeliOnayWithdrawCommand, dict[str, Any]]):
    async def handle(self, command: VeliOnayWithdrawCommand) -> dict[str, Any]:
        from services.veli_onay_service import VeliOnayService
        ok = await VeliOnayService(command.db).withdraw(command.token)
        if not ok:
            raise ValueError('Geçersiz veya zaten geri çekilmiş bağlantı')
        return {
            'status': 'withdrawn',
            'message': 'Veli onayı geri çekildi'
        }


