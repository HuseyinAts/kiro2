import logging
import secrets
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from passlib.context import CryptContext
from pydantic import ConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

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


# `users.username` varchar(100) NOT NULL (information_schema ile ölçüldü).
KULLANICI_ADI_MAX = 100
# Son ek: ayraç + 4 onaltılık karakter -> 65.536 olasılık, 5 denemede çakışma
# olasılığı ihmal edilebilir. Sayılı son ek (`ahmet2`) BİLEREK seçilmedi:
# username'den "bu yerel-adı kaç kişi kullanıyor" okunabilirdi.
_SON_EK_UZUNLUK = 4
_DENEME_SINIRI = 5


class KullaniciAdiUretilemediError(RuntimeError):
    """Sınırlı denemede benzersiz bir `username` bulunamadı.

    Sessizce çakışan bir ad DÖNDÜRÜLMEZ: çağıran yine `UniqueViolationError`
    alır ve bugünkü HTTP 500 gizlenmiş hâlde geri gelirdi.
    """


async def benzersiz_kullanici_adi(
    email: str,
    alinmis_mi: Callable[[str], Awaitable[bool]],
    *,
    deneme_siniri: int = _DENEME_SINIRI,
) -> str:
    """E-postadan çakışmayan bir `username` türet.

    Kararı DB erişiminden ayrı tutuyoruz (`alinmis_mi` geri-çağrı): işleyicinin
    içine gömülü bir döngü mutasyonla çivilenemez, saf fonksiyon çivilenir —
    `core/eposta_dogrulama.py:10-12` ile aynı gerekçe.

    🔴 NEDEN VAR (26 Ağu 2026 canlı ölçümü): `username` e-postanın yerel-adından
    türetiliyor ama benzersizlik ön-kontrolü YALNIZ `email` üzerindeydi. DB'de
    `ix_users_username` UNIQUE olduğu için `ahmet@gmail.com` kayıtlıyken gelen
    `ahmet@hotmail.com` **HTTP 500 "Dahili sunucu hatasi"** alıyordu (users
    47 -> 47, kayıt oluşmuyordu). A1 altın yolunun 1. adımı.

    ⚠️ KALAN YARIŞ PENCERESİ — kapatılmadı, GÖRÜNÜR bırakıldı: kontrol ile
    INSERT arasında başka bir işlem aynı adı alabilir. O durumda bugünkü
    davranışa (500) düşülür, yani daha kötü olmaz; kapatmak SAVEPOINT + yeniden
    deneme gerektirir ve ölçülen kusur bu değil. Aynı pencere `email`
    ön-kontrolünde de zaten var.
    """
    yerel = email.split("@")[0]
    taban = yerel[:KULLANICI_ADI_MAX]
    if not await alinmis_mi(taban):
        return taban

    # Son ek için yer aç: taban + "-" + son_ek <= KULLANICI_ADI_MAX
    kisa_taban = yerel[: KULLANICI_ADI_MAX - _SON_EK_UZUNLUK - 1]
    denenen: set[str] = set()
    for _ in range(deneme_siniri):
        son_ek = secrets.token_hex(_SON_EK_UZUNLUK // 2)
        aday = f"{kisa_taban}-{son_ek}"
        if aday in denenen:
            continue
        denenen.add(aday)
        if not await alinmis_mi(aday):
            return aday

    raise KullaniciAdiUretilemediError(
        f"{deneme_siniri} denemede benzersiz kullanıcı adı üretilemedi (taban={kisa_taban!r})"
    )


def _map_registration_role(rol: Any) -> str:
    rol_key = (rol.value if hasattr(rol, "value") else str(rol)).strip().lower()
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

        # `username` e-postanın yerel-adından türüyor ama `ix_users_username`
        # UNIQUE: `ahmet@gmail.com` kayıtlıyken `ahmet@hotmail.com` eskiden
        # UniqueViolation -> HTTP 500 üretiyordu (26 Ağu 2026 canlı ölçümü).
        async def _kullanici_adi_alinmis_mi(aday: str) -> bool:
            sonuc = await db.execute(
                text("SELECT 1 FROM users WHERE username = :ad LIMIT 1"),
                {"ad": aday},
            )
            return sonuc.fetchone() is not None

        try:
            kullanici_adi = await benzersiz_kullanici_adi(
                command.email, _kullanici_adi_alinmis_mi
            )
        except KullaniciAdiUretilemediError as e:
            # Yeniden denemek GERÇEKTEN işe yarar (son ek rastgele), bu yüzden
            # 500 değil 503: istemciye eyleme dönüştürülebilir bir şey söyle.
            logger.error("kullanıcı adı üretilemedi: %s", e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Kayıt şu anda tamamlanamadı, lütfen tekrar deneyin.",
            ) from e

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
                "username": kullanici_adi,
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

            # CANLI BULGU (30 Ağu 2026, backend/services/profile_sync_service.py
            # yedeğiyle çapraz doğrulandı): bu handler `student_profiles` satırı
            # oluşturuyordu ama `learning_path_student_profiles` HİÇ oluşturmuyordu.
            # Sonuç: her yeni öğrenci kaydı, ilk learning-path isteğinde
            # `verify_student_access`'ten 403/404 alıyordu (profil yok) — sessiz,
            # her kayıtta tekrar eden bir kayıp. Bekçi:
            # tests/integration/test_db_profile_sync.py::test_student_registration_provisions_both_profiles
            # `neuro_inclusive_mode` (NOT NULL, server_default YOK, bkz. S255)
            # burada EXPLICIT veriliyor — raw SQL INSERT, ORM'in Python-tarafi
            # default'undan yararlanamaz.
            student_name = (command.ad_soyad or "").strip() or "Öğrenci"
            await db.execute(
                text("""
                INSERT INTO learning_path_student_profiles
                    (student_id, user_id, name, grade, exam_target, learning_style,
                     knowledge_level, neuro_inclusive_mode, interests, goals,
                     available_time, metadata_json, created_at, updated_at)
                VALUES
                    (:student_id, :user_id, :name, :grade, 'TYT', 'mixed',
                     'beginner', FALSE, '[]', '[]',
                     60, '{}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (student_id) DO NOTHING;
            """),
                {
                    "student_id": profile_id,
                    "user_id": user_id,
                    "name": student_name,
                    "grade": str(grade_level),
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

        # L2: doğrulama e-postası. Kayıt AKIŞINI BLOKLAMAZ — SMTP yoksa
        # kullanıcı yine kayıtlıdır, yalnızca `is_verified` false kalır ve kapı
        # kapalıyken bu hiçbir şeyi engellemez (veli-onay ile aynı desen).
        try:
            from core.eposta_dogrulama import dogrulama_baslat

            await dogrulama_baslat(user_id, command.email)
        except Exception as e:
            logger.error("doğrulama e-postası tetikleme hatası: %s", e)

        logger.info(f"Yeni kullanıcı kaydı: {command.email} ({rol_str})")
        return {
            "success": True,
            "message": "Kullanıcı kaydı başarıyla oluşturuldu",
            "id": user_id,
        }


from datetime import UTC

import jwt as pyjwt
from sqlalchemy import select

from core.dependencies import JWT_ALGORITHM, JWT_SECRET
from core.jwt_auth import UserRole as JWTUserRole
from core.jwt_auth import get_jwt_manager
from models.database import User as DBUser


class TwoFactorRequired(Exception):
    def __init__(self, user_id: str, email: str):
        self.user_id = user_id
        self.email = email
        super().__init__("2FA verification required")


class EpostaDogrulanmamis(Exception):
    """L2 kapısı: hesap var, şifre doğru, ama e-posta doğrulanmamış.

    `ValueError` DEĞİL, ayrı bir tür: `ValueError` uçta jenerik 401 "İşlem
    başarısız" üretiyor ve kullanıcı ne yapacağını bilemiyor. `TwoFactorRequired`
    ile aynı desen — eylem gerektiren durum, kimlik hatası değil.

    N818 (adı "Error" ile bitmeli) kardeş `TwoFactorRequired` ile simetri için
    bilinçli olarak susturuldu.
    """

    def __init__(self, email: str):
        self.email = email
        super().__init__("E-posta doğrulaması gerekli")


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

        # L2 kapısı — `is_active`in kardeşi. Karar burada DEĞİL saf fonksiyonda
        # (`core/eposta_dogrulama.py`): gömülü bir if zinciri mutasyonla
        # çivilenemez. Varsayılan KAPALI; mevcut hesaplar tarih muafiyetiyle
        # korunur.
        # Yerel import KASITLI: bu dosyanın modül-düzeyi import bloğu kodun
        # ALTINDA (7 adet önceden var olan E402). Oraya bir satır daha eklemek
        # mevcut ihlali büyütürdü; dosyadaki diğer işleyiciler de yerel import
        # kullanıyor.
        from core.eposta_dogrulama import giris_engellenmeli_mi

        if giris_engellenmeli_mi(
            bool(getattr(db_user, "is_verified", False)),
            getattr(db_user, "created_at", None),
        ):
            raise EpostaDogrulanmamis(email=db_user.email)

        if not command.password:
            raise ValueError("Şifre alanı boş olamaz")

        import asyncio
        import os

        from passlib.context import CryptContext

        _BCRYPT_COST = int(os.environ.get("BCRYPT_COST", "10") or 10)
        pwd_context = CryptContext(
            schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=_BCRYPT_COST
        )

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

        _jti = None
        try:
            import hashlib as _hashlib

            from sqlalchemy import text as _text

            _payload = pyjwt.decode(
                refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM]
            )
            _token_hash = _hashlib.sha256(refresh_token.encode()).hexdigest()
            _jti = _payload.get("jti", "") if _payload else ""
            _exp = (
                datetime.fromtimestamp(_payload.get("exp", 0), tz=UTC)
                if _payload
                else datetime.now(UTC)
            )

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
                    {
                        "uid": str(db_user.id),
                        "th": _token_hash,
                        "jti": _jti,
                        "exp": _exp,
                    },
                )
        except Exception as _rt_err:
            # SESSIZ DUSURME YASAK (bu dosyadaki role-mapping fix'iyle ayni ilke,
            # api/auth.py:366-369): WARNING'de kalirsa kullanici "basarili" login
            # alir ama refresh_tokens'ta satiri olmaz -- access token suresi
            # dolunca /refresh, gecerli bir JWT'yi aciklamasiz 401 "revoked or
            # does not exist" ile reddeder (core/jwt_auth.py:274-278). Login'i
            # burada BOSA CIKARMIYORUZ -- access_token bu tablodan bagimsiz
            # calisir, bunu engellemek daha buyuk bir kullanilabilirlik
            # regresyonu olurdu -- ama hata artik ERROR + kullanici/jti ile
            # gorunur, tek satirlik sessiz WARNING degil (Faz 2, PR #62 sonrasi
            # backlog).
            logger.error(
                "refresh_token DB'ye yazilamadi (user_id=%s, jti=%s): %s",
                db_user.id,
                _jti,
                _rt_err,
            )

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
                "olusturma_tarihi": (
                    db_user.created_at.isoformat() if db_user.created_at else None
                ),
                "son_giris": (
                    db_user.last_login.isoformat() if db_user.last_login else None
                ),
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
            },
        }


class RefreshTokenCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    refresh_token: str
    db: Any
    # Faz 2 (PR #62 sonrasi backlog, 2 Eylul 2026): opsiyonel FastAPI Request.
    # `core/jwt_auth.py::refresh_access_token` bunu SADECE IP/user-agent
    # yakalamak icin kullaniyordu (`_save_refresh_token_to_db` zaten
    # `request=None` icin guvenli) -- ama persist adiminin KENDISI
    # `if db and request:` ile bu alana bagliydi, ve iki gercek cagiran
    # (api/auth.py: secure_refresh + refresh_token) bunu hic gecirmiyordu.
    # Sonuc: her rotate edilen refresh token DB'ye hic yazilmiyordu (bkz.
    # jwt_auth.py'deki ayrintili not). Burada request'i opsiyonel tutuyoruz
    # ki mevcut/gelecek test cagirilari (db var, request yok) hala calissin
    # -- asil duzeltme jwt_auth.py'de `if db:` olarak genisletildi.
    request: Any = None


class RefreshTokenCommandHandler(CommandHandler[RefreshTokenCommand, dict[str, Any]]):
    async def handle(self, command: RefreshTokenCommand) -> dict[str, Any]:
        jwt_mgr = get_jwt_manager()
        try:
            # We use the async version because we don't have request here easily without leaking HTTP details
            # Wait, jwt_mgr.refresh_access_token handles revocation checks
            new_tokens = await jwt_mgr.refresh_access_token(
                command.refresh_token,
                db=command.db,  # Pass async session if refresh_access_token supports it, else we need sync
                request=command.request,
            )
            return {
                "success": True,
                "token": new_tokens.access_token,
                "refreshToken": new_tokens.refresh_token,
                "access_token": new_tokens.access_token,
                "refresh_token": new_tokens.refresh_token,
                "token_type": new_tokens.token_type,
                "expires_in": new_tokens.expires_in,
            }
        except Exception as e:
            raise ValueError(str(e))


class VeliOnayVerifyCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    token: str
    ip: str | None = None
    ua: str | None = None
    db: Any


class VeliOnayVerifyCommandHandler(
    CommandHandler[VeliOnayVerifyCommand, dict[str, Any]]
):
    async def handle(self, command: VeliOnayVerifyCommand) -> dict[str, Any]:
        from services.veli_onay_service import VeliOnayService

        result = await VeliOnayService(command.db).verify_and_grant(
            command.token, ip=command.ip, ua=command.ua
        )
        if not result.success:
            raise ValueError(result.message)
        return {"status": result.status or "granted", "message": result.message or ""}


class VeliOnayWithdrawCommand(Command):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    token: str
    db: Any


class VeliOnayWithdrawCommandHandler(
    CommandHandler[VeliOnayWithdrawCommand, dict[str, Any]]
):
    async def handle(self, command: VeliOnayWithdrawCommand) -> dict[str, Any]:
        from services.veli_onay_service import VeliOnayService

        ok = await VeliOnayService(command.db).withdraw(command.token)
        if not ok:
            raise ValueError("Geçersiz veya zaten geri çekilmiş bağlantı")
        return {"status": "withdrawn", "message": "Veli onayı geri çekildi"}
