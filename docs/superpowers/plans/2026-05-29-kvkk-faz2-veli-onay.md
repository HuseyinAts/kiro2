# KVKK Faz 2 — Veli Onay Akışı Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 18 yaşından küçük öğrenci kaydında veliye email ile gönderilen 7 günlük tek-tık token linki üzerinden açık rıza alınması; rıza gelene kadar sosyal/PII özelliklerinin kısıtlanması; veliye geri-çekme hakkı.

**Architecture:** Amaca-özel `veli_consent` tablosu (VARCHAR PK) + `VeliOnayService` (async) + `core/email_util.py` SMTP util + 4 endpoint (`api/auth.py` router'ı altında) + `require_veli_consent` FastAPI dependency + frontend `VeliOnayPage` (public route). Token plaintext sadece email linkinde, DB'de SHA-256 hash.

**Tech Stack:** FastAPI, SQLAlchemy async (AsyncSession), Alembic, PostgreSQL (port 5434), React 18 + TS (Vite), pytest + httpx ASGITransport.

**Spec:** `docs/superpowers/specs/2026-05-29-kvkk-faz2-veli-onay-design.md` (commit 3013f273f)

**Kurallar (CLAUDE.md):**
- models/ relative import ZORUNLU: `from .base import Base` (CI: `check_model_imports.py`)
- Migration: ORM model ÖNCE → `alembic revision --autogenerate` → `information_schema` doğrula
- TDD: fail eden test ÖNCE, sonra fix
- Türkçe: UTF-8 + NFC
- Her endpoint hata → route handler içinde `HTTPException` (middleware değil → 500'e dönüşmez)
- Windows: `python` (python3 değil); psql `"C:/Program Files/PostgreSQL/18/bin/psql.exe"`

---

## File Structure

| Dosya | Sorumluluk | Yeni/Değişiklik |
|---|---|---|
| `backend/models/veli_consent.py` | `VeliConsent` ORM modeli + token helper'ları | YENİ |
| `backend/models/__init__.py` | model registration (alembic autogenerate) | DEĞİŞİKLİK (1 satır) |
| `backend/alembic/versions/*_veli_consent.py` | `veli_consent` tablosu migration | YENİ (autogenerate) |
| `backend/core/email_util.py` | `send_email(to, subject, html)` SMTP util | YENİ |
| `backend/services/veli_onay_service.py` | `VeliOnayService` iş mantığı | YENİ |
| `backend/api/auth.py` | 4 endpoint + register entegrasyonu + schema'lar | DEĞİŞİKLİK |
| `backend/core/dependencies.py` | `require_veli_consent` enforcement dep | DEĞİŞİKLİK |
| `frontend/src/pages/VeliOnayPage.tsx` | veli onay/red sayfası | YENİ |
| `frontend/src/services/authService.ts` | veliOnayVerify/Withdraw/Status metodları | DEĞİŞİKLİK |
| `frontend/src/App.tsx` | `/veli-onay` public route | DEĞİŞİKLİK (1 satır) |
| `backend/tests/unit/test_veli_onay_service.py` | servis testleri | YENİ |
| `backend/tests/integration/test_veli_onay_flow.py` | uçtan uca akış | YENİ |
| `backend/tests/e2e/test_golden_flows.py` | yeni GF testi | DEĞİŞİKLİK |

---

## Task 1: `veli_consent` ORM modeli + token helper'ları

**Files:**
- Create: `backend/models/veli_consent.py`
- Modify: `backend/models/__init__.py` (model import — autogenerate için)
- Test: `backend/tests/unit/test_veli_consent_model.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/unit/test_veli_consent_model.py
"""VeliConsent modeli + token helper unit testleri."""
from models.veli_consent import (
    VeliConsent,
    CONSENT_TOKEN_TTL_DAYS,
    generate_token,
    hash_token,
)


def test_generate_token_is_urlsafe_and_unique():
    t1 = generate_token()
    t2 = generate_token()
    assert isinstance(t1, str) and len(t1) >= 32
    assert t1 != t2  # kriptografik rastgelelik


def test_hash_token_is_sha256_hex_and_stable():
    token = "abc123"
    h = hash_token(token)
    assert len(h) == 64  # sha256 hexdigest
    assert h == hash_token(token)  # deterministik
    assert h != token  # plaintext değil


def test_veli_consent_defaults():
    c = VeliConsent(child_user_id="u1", veli_email="veli@example.com")
    assert c.status == "pending" or c.status is None  # default DB-side/py-side
    assert CONSENT_TOKEN_TTL_DAYS == 7
    assert VeliConsent.__tablename__ == "veli_consent"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_veli_consent_model.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'models.veli_consent'`

- [ ] **Step 3: Create the model**

```python
# backend/models/veli_consent.py
"""KVKK Faz 2: Veli (parental) onay kaydı.

Reşit olmayan öğrenci için veli açık rızası. Token plaintext sadece email
linkinde bulunur; DB'de yalnızca SHA-256 hash saklanır.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text

from .base import Base

CONSENT_TOKEN_TTL_DAYS = 7
CONSENT_VERSION = "kvkk-veli-1.0"


def generate_token() -> str:
    """Kriptografik güvenli, tek-kullanımlık token (passwordless deseni)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Token'ın SHA-256 hex hash'i — DB'de bu saklanır, plaintext değil."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def default_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=CONSENT_TOKEN_TTL_DAYS)


class VeliConsent(Base):
    """Veli onay kaydı (KVKK açık rıza)."""

    __tablename__ = "veli_consent"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    child_user_id = Column(String, index=True, nullable=False)
    veli_email = Column(String(255), nullable=False)
    # pending / granted / withdrawn / expired
    status = Column(String(20), nullable=False, default="pending")
    # sha256(token); granted'da KORUNUR (idempotency + withdraw-by-token), withdrawn/expired'da NULL
    token_hash = Column(String(64), index=True, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    requested_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    granted_at = Column(DateTime(timezone=True), nullable=True)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
    consent_text = Column(Text, nullable=False, default="")
    consent_version = Column(String(20), nullable=False, default=CONSENT_VERSION)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
```

- [ ] **Step 4: Register model for alembic autogenerate**

`backend/models/__init__.py` içinde, diğer model importlarının yanına (örn. `from .birlikte_streak import ...` satırının altına) ekle:

```python
# KVKK Faz 2: veli onay kaydı
from .veli_consent import VeliConsent
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_veli_consent_model.py -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/models/veli_consent.py backend/models/__init__.py backend/tests/unit/test_veli_consent_model.py
git commit -m "feat(kvkk-faz2): veli_consent ORM modeli + token helper (sha256, urlsafe)"
```

---

## Task 2: Alembic migration (`veli_consent` tablosu)

**Files:**
- Create: `backend/alembic/versions/<autogen>_veli_consent.py` (autogenerate)

- [ ] **Step 1: Generate migration from ORM model**

Run: `cd backend && alembic revision --autogenerate -m "veli_consent table (kvkk faz2)"`
Expected: Yeni dosya `alembic/versions/<rev>_veli_consent_table_kvkk_faz2.py`. `down_revision` otomatik mevcut head'e zincirlenir.

- [ ] **Step 2: Review generated migration**

Üretilen dosyayı aç. `upgrade()` içinde `op.create_table("veli_consent", ...)` olmalı ve şu kolonları içermeli: `id` (String(36) PK), `child_user_id` (String, index), `veli_email`, `status`, `token_hash` (index), `token_expires_at`, `requested_at`, `granted_at`, `withdrawn_at`, `consent_text`, `consent_version`, `ip_address`, `user_agent`, `created_at`, `updated_at`. `downgrade()` `op.drop_table("veli_consent")` olmalı. Autogenerate index'leri atlamışsa elle ekle:

```python
op.create_index("ix_veli_consent_child_user_id", "veli_consent", ["child_user_id"])
op.create_index("ix_veli_consent_token_hash", "veli_consent", ["token_hash"])
```

Autogenerate ilgisiz tablo drop'ları üretmişse (mevcut şema drift) ONLARI SİL — sadece `veli_consent` create kalsın.

- [ ] **Step 3: Apply migration**

Run: `cd backend && alembic upgrade head`
Expected: `Running upgrade ... -> <rev>, veli_consent table (kvkk faz2)`

- [ ] **Step 4: Verify schema in DB (CLAUDE.md migration kuralı)**

Run:
```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -p 5434 -U postgres -d kiro2 -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'veli_consent' ORDER BY ordinal_position;"
```
Expected: 15 satır, `id` character varying, `child_user_id` not null, `token_hash` nullable, vb.

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat(kvkk-faz2): veli_consent tablosu migration + DB verify"
```

---

## Task 3: `core/email_util.py` — yeniden kullanılabilir SMTP util

**Files:**
- Create: `backend/core/email_util.py`
- Test: `backend/tests/unit/test_email_util.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/unit/test_email_util.py
"""email_util.send_email unit testleri."""
import core.email_util as email_util


def test_send_email_returns_false_when_smtp_unconfigured(monkeypatch):
    monkeypatch.delenv("SMTP_SERVER", raising=False)
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    ok = email_util.send_email("veli@example.com", "Konu", "<p>merhaba</p>")
    assert ok is False  # config yoksa sessizce False, exception yok


def test_send_email_builds_message_with_html(monkeypatch):
    captured = {}

    class _FakeSMTP:
        def __init__(self, server, port):
            captured["server"] = server
            captured["port"] = port
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def starttls(self):
            captured["starttls"] = True
        def login(self, u, p):
            captured["login"] = (u, p)
        def send_message(self, msg):
            captured["to"] = msg["To"]
            captured["subject"] = msg["Subject"]

    monkeypatch.setenv("SMTP_SERVER", "smtp.test")
    monkeypatch.setenv("SMTP_USERNAME", "user@test")
    monkeypatch.setenv("SMTP_PASSWORD", "pw")
    monkeypatch.setattr(email_util.smtplib, "SMTP", _FakeSMTP)

    ok = email_util.send_email(
        "veli@example.com", "KIRO2 Veli Onayı", "<p>link</p>", blocking=True
    )
    assert ok is True
    assert captured["to"] == "veli@example.com"
    assert captured["subject"] == "KIRO2 Veli Onayı"
    assert captured["starttls"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_email_util.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.email_util'`

- [ ] **Step 3: Create the util**

```python
# backend/core/email_util.py
"""Yeniden kullanılabilir SMTP email gönderim util'i.

kvkk_compliance.py'deki gömülü SMTP mantığının sade, paylaşılan hâli.
Config eksikse exception fırlatmaz — False döner (çağıran akışı bloklamaz).
"""
from __future__ import annotations

import logging
import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def _build_message(to: str, subject: str, html_body: str, from_addr: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    return msg


def send_email(to: str, subject: str, html_body: str, blocking: bool = False) -> bool:
    """Email gönder. Config yoksa False (uyarı loglar). blocking=True testte senkron."""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_addr = os.getenv("EMAIL_FROM") or smtp_username or "noreply@kiro2.edu.tr"

    if not (smtp_server and smtp_username and smtp_password):
        logger.warning("SMTP yapılandırılmamış; %s adresine email atlandı", to)
        return False

    msg = _build_message(to, subject, html_body, from_addr)

    def _send() -> None:
        try:
            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            logger.info("email gönderildi: %s", to)
        except Exception as e:  # noqa: BLE001 — email hatası akışı bozmamalı
            logger.error("email gönderim hatası (%s): %s", to, e)

    if blocking:
        _send()
    else:
        threading.Thread(target=_send, daemon=True).start()
    return True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_email_util.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/core/email_util.py backend/tests/unit/test_email_util.py
git commit -m "feat(kvkk-faz2): core/email_util.send_email — paylaşılan SMTP util"
```

---

## Task 4: `VeliOnayService` — iş mantığı (TDD, integration-style)

**Files:**
- Create: `backend/services/veli_onay_service.py`
- Test: `backend/tests/integration/test_veli_onay_service.py`

> **Not:** Servis `AsyncSession` + gerçek `veli_consent` + `student_profiles` tablosu kullanır. Testler postgres test DB gerektirir. Repo deseni: `USE_POSTGRES_TESTS=true` ile `conftest_postgres.py` async session fixture sağlar. Fixture adı repo'da `async_session` veya `db_session`; testi yazmadan önce `grep -n "async_session\|def db_session" backend/tests/conftest_postgres.py` ile doğrula ve aşağıdaki fixture adını eşleştir.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/integration/test_veli_onay_service.py
"""VeliOnayService akış testleri (postgres test DB)."""
import os

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(
    os.getenv("USE_POSTGRES_TESTS") != "true",
    reason="VeliOnayService gerçek DB gerektirir (USE_POSTGRES_TESTS=true)",
)


async def _seed_minor(db, user_id="vtest-child-1"):
    """Test için minor user + student_profile (veli_onay=False) oluştur."""
    await db.execute(
        text(
            "INSERT INTO users (id, email, username, password_hash, first_name, "
            "last_name, role, is_active, is_verified, total_xp, level, elo_rating, "
            "is_premium, is_parent, created_at, updated_at) VALUES "
            "(:id, :email, :uname, 'x', 'Test', 'Child', CAST('STUDENT' AS userrole), "
            "TRUE, FALSE, 0, 1, 1200, FALSE, FALSE, NOW(), NOW()) "
            "ON CONFLICT (id) DO NOTHING"
        ),
        {"id": user_id, "email": f"{user_id}@t.com", "uname": user_id},
    )
    await db.execute(
        text(
            "INSERT INTO student_profiles (id, user_id, grade_level, veli_onay, "
            "veli_email, current_level, total_study_hours, total_questions_solved, "
            "correct_answers, irt_ability, created_at, updated_at) VALUES "
            "(:id, :uid, 11, FALSE, 'veli@t.com', 0.0, 0, 0, 0, 0.0, NOW(), NOW()) "
            "ON CONFLICT (id) DO NOTHING"
        ),
        {"id": f"prof-{user_id}", "uid": user_id},
    )
    await db.commit()


@pytest.mark.asyncio
async def test_request_then_verify_grants_consent(async_session):
    db = async_session
    await _seed_minor(db, "vtest-child-1")
    from services.veli_onay_service import VeliOnayService

    svc = VeliOnayService(db)
    token = await svc.request_consent("vtest-child-1", "veli@t.com")
    assert token and len(token) >= 32

    result = await svc.verify_and_grant(token, ip="1.2.3.4", ua="pytest")
    assert result.success is True
    assert result.status == "granted"

    row = (
        await db.execute(
            text("SELECT veli_onay FROM student_profiles WHERE user_id = :u"),
            {"u": "vtest-child-1"},
        )
    ).first()
    assert row[0] is True  # veli_onay flip


@pytest.mark.asyncio
async def test_verify_is_idempotent_after_grant(async_session):
    db = async_session
    await _seed_minor(db, "vtest-child-2")
    from services.veli_onay_service import VeliOnayService

    svc = VeliOnayService(db)
    token = await svc.request_consent("vtest-child-2", "veli@t.com")
    await svc.verify_and_grant(token)
    again = await svc.verify_and_grant(token)
    assert again.success is True
    assert again.status == "granted"  # idempotent, hata değil


@pytest.mark.asyncio
async def test_invalid_token_rejected(async_session):
    from services.veli_onay_service import VeliOnayService

    svc = VeliOnayService(async_session)
    result = await svc.verify_and_grant("gecersiz-token-xyz")
    assert result.success is False
    assert result.error_code == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_withdraw_flips_veli_onay_false(async_session):
    db = async_session
    await _seed_minor(db, "vtest-child-3")
    from services.veli_onay_service import VeliOnayService

    svc = VeliOnayService(db)
    token = await svc.request_consent("vtest-child-3", "veli@t.com")
    await svc.verify_and_grant(token)
    ok = await svc.withdraw(token)
    assert ok is True
    row = (
        await db.execute(
            text("SELECT veli_onay FROM student_profiles WHERE user_id = :u"),
            {"u": "vtest-child-3"},
        )
    ).first()
    assert row[0] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && set USE_POSTGRES_TESTS=true && python -m pytest tests/integration/test_veli_onay_service.py -v` (Git Bash: `USE_POSTGRES_TESTS=true python -m pytest ...`)
Expected: FAIL with `ModuleNotFoundError: No module named 'services.veli_onay_service'`

- [ ] **Step 3: Create the service**

```python
# backend/services/veli_onay_service.py
"""KVKK Faz 2: Veli onay (parental consent) iş mantığı."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.veli_consent import (
    CONSENT_VERSION,
    VeliConsent,
    default_expiry,
    generate_token,
    hash_token,
)

logger = logging.getLogger(__name__)

CONSENT_TEXT = (
    "Velisi olduğunuz öğrencinin KIRO2 eğitim platformunu kullanabilmesi için "
    "kişisel verilerinin (kimlik, iletişim, eğitim/performans verileri) eğitim "
    "hizmeti amacıyla işlenmesine açık rıza veriyorsunuz. Bu onayı dilediğiniz "
    "zaman geri çekebilirsiniz (KVKK Madde 11)."
)


@dataclass
class VeliOnayResult:
    success: bool
    status: str | None = None
    error_code: str | None = None
    message: str | None = None


def _as_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


class VeliOnayService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def request_consent(self, child_user_id: str, veli_email: str) -> str:
        """Pending kayıt + token üret. Eski pending'i expire eder. Plaintext token döner."""
        existing = (
            await self.db.execute(
                select(VeliConsent).where(
                    VeliConsent.child_user_id == child_user_id,
                    VeliConsent.status == "pending",
                )
            )
        ).scalars().all()
        for c in existing:
            c.status = "expired"
            c.token_hash = None

        token = generate_token()
        consent = VeliConsent(
            child_user_id=child_user_id,
            veli_email=veli_email,
            status="pending",
            token_hash=hash_token(token),
            token_expires_at=default_expiry(),
            consent_text=CONSENT_TEXT,
            consent_version=CONSENT_VERSION,
        )
        self.db.add(consent)
        await self.db.commit()
        logger.info("veli_onay_requested child=%s", child_user_id)
        return token

    async def verify_and_grant(
        self, token: str, ip: str | None = None, ua: str | None = None
    ) -> VeliOnayResult:
        consent = (
            await self.db.execute(
                select(VeliConsent).where(VeliConsent.token_hash == hash_token(token))
            )
        ).scalar_one_or_none()

        if consent is None:
            return VeliOnayResult(
                False, error_code="INVALID_TOKEN",
                message="Geçersiz veya süresi dolmuş onay bağlantısı",
            )
        if consent.status == "granted":
            return VeliOnayResult(True, status="granted", message="Onay zaten alınmış")
        if consent.status in ("withdrawn", "expired"):
            return VeliOnayResult(
                False, error_code="TOKEN_INVALID",
                message="Bu bağlantı artık geçerli değil",
            )
        if consent.token_expires_at and datetime.now(UTC) > _as_aware(
            consent.token_expires_at
        ):
            consent.status = "expired"
            consent.token_hash = None
            await self.db.commit()
            return VeliOnayResult(
                False, error_code="TOKEN_EXPIRED",
                message="Bağlantı süresi dolmuş. Öğrenci yeniden gönderebilir.",
            )

        consent.status = "granted"
        consent.granted_at = datetime.now(UTC)
        consent.ip_address = ip
        consent.user_agent = ua
        await self.db.execute(
            text(
                "UPDATE student_profiles SET veli_onay = TRUE, updated_at = NOW() "
                "WHERE user_id = :uid"
            ),
            {"uid": consent.child_user_id},
        )
        await self.db.commit()
        logger.info("veli_onay_granted child=%s", consent.child_user_id)
        return VeliOnayResult(True, status="granted", message="Veli onayı alındı")

    async def withdraw(self, token: str) -> bool:
        consent = (
            await self.db.execute(
                select(VeliConsent).where(VeliConsent.token_hash == hash_token(token))
            )
        ).scalar_one_or_none()
        if consent is None or consent.status not in ("granted", "pending"):
            return False
        consent.status = "withdrawn"
        consent.withdrawn_at = datetime.now(UTC)
        consent.token_hash = None
        await self.db.execute(
            text(
                "UPDATE student_profiles SET veli_onay = FALSE, updated_at = NOW() "
                "WHERE user_id = :uid"
            ),
            {"uid": consent.child_user_id},
        )
        await self.db.commit()
        logger.info("veli_onay_withdrawn child=%s", consent.child_user_id)
        return True

    async def get_status(self, child_user_id: str) -> str:
        """En güncel kaydın durumu: pending/granted/withdrawn/expired veya 'none'."""
        consent = (
            await self.db.execute(
                select(VeliConsent)
                .where(VeliConsent.child_user_id == child_user_id)
                .order_by(VeliConsent.requested_at.desc())
            )
        ).scalars().first()
        return consent.status if consent else "none"

    async def resend(self, child_user_id: str, veli_email: str) -> str:
        """Eski pending'i invalidate edip yeni token üretir (request_consent reuse)."""
        return await self.request_consent(child_user_id, veli_email)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && USE_POSTGRES_TESTS=true python -m pytest tests/integration/test_veli_onay_service.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Lint**

Run: `cd backend && ruff check services/veli_onay_service.py --select=E,F,W`
Expected: All checks passed

- [ ] **Step 6: Commit**

```bash
git add backend/services/veli_onay_service.py backend/tests/integration/test_veli_onay_service.py
git commit -m "feat(kvkk-faz2): VeliOnayService — request/verify/withdraw/status (TDD)"
```

---

## Task 5: Endpoint'ler (`api/auth.py`) — verify / withdraw / status / resend

**Files:**
- Modify: `backend/api/auth.py` (router'a 4 endpoint + 3 Pydantic schema)
- Test: `backend/tests/integration/test_veli_onay_endpoints.py`

> Router: `api/auth.py`'deki mevcut `router` (prefix `/api/v1/auth`). `get_db`, `get_current_user`, `_check_rate_limit`, `HTTPException`, `status` zaten import edili.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/integration/test_veli_onay_endpoints.py
"""Veli onay endpoint testleri (public verify/withdraw)."""
import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

pytestmark = pytest.mark.skipif(
    os.getenv("USE_POSTGRES_TESTS") != "true",
    reason="endpoint testleri gerçek DB gerektirir",
)


@pytest.mark.asyncio
async def test_verify_endpoint_grants(async_session):
    db = async_session
    await db.execute(
        text(
            "INSERT INTO users (id, email, username, password_hash, first_name, "
            "last_name, role, is_active, is_verified, total_xp, level, elo_rating, "
            "is_premium, is_parent, created_at, updated_at) VALUES "
            "('vep-1', 'vep1@t.com', 'vep1', 'x', 'T', 'C', CAST('STUDENT' AS userrole), "
            "TRUE, FALSE, 0, 1, 1200, FALSE, FALSE, NOW(), NOW()) "
            "ON CONFLICT (id) DO NOTHING"
        )
    )
    await db.execute(
        text(
            "INSERT INTO student_profiles (id, user_id, grade_level, veli_onay, "
            "veli_email, current_level, total_study_hours, total_questions_solved, "
            "correct_answers, irt_ability, created_at, updated_at) VALUES "
            "('prof-vep-1', 'vep-1', 11, FALSE, 'veli@t.com', 0.0, 0, 0, 0, 0.0, "
            "NOW(), NOW()) ON CONFLICT (id) DO NOTHING"
        )
    )
    await db.commit()

    from services.veli_onay_service import VeliOnayService

    token = await VeliOnayService(db).request_consent("vep-1", "veli@t.com")

    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/veli-onay/verify", json={"token": token}
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "granted"


@pytest.mark.asyncio
async def test_verify_invalid_token_returns_400():
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/veli-onay/verify", json={"token": "yok-boyle-token"}
        )
    assert resp.status_code == 400
    assert resp.status_code < 500  # 500 OLMAMALI (middleware kuralı)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && USE_POSTGRES_TESTS=true python -m pytest tests/integration/test_veli_onay_endpoints.py -v`
Expected: FAIL (404 — endpoint yok)

- [ ] **Step 3: Add schemas + endpoints to `api/auth.py`**

Dosyanın schema bölümüne (diğer `BaseModel` tanımlarının yanına) ekle:

```python
class VeliOnayVerifyRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)


class VeliOnayResponse(BaseModel):
    status: str
    message: str


class VeliOnayStatusResponse(BaseModel):
    status: str
```

`router` tanımının altında, dosyanın endpoint bölümüne ekle (`VeliOnayService` import'unu fonksiyon içinde tut — register'daki lazy-import deseniyle tutarlı):

```python
@router.post("/veli-onay/verify", response_model=VeliOnayResponse)
async def veli_onay_verify(
    request: Request,
    body: VeliOnayVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> VeliOnayResponse:
    """Veli email linkindeki token ile açık rızayı onaylar (public — token=auth)."""
    from services.veli_onay_service import VeliOnayService

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    result = await VeliOnayService(db).verify_and_grant(body.token, ip=ip, ua=ua)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return VeliOnayResponse(status=result.status or "granted", message=result.message or "")


@router.post("/veli-onay/withdraw", response_model=VeliOnayResponse)
async def veli_onay_withdraw(
    body: VeliOnayVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> VeliOnayResponse:
    """Veli onayını geri çeker (public — token=auth, KVKK Madde 11)."""
    from services.veli_onay_service import VeliOnayService

    ok = await VeliOnayService(db).withdraw(body.token)
    if not ok:
        raise HTTPException(status_code=400, detail="Geçersiz veya zaten geri çekilmiş bağlantı")
    return VeliOnayResponse(status="withdrawn", message="Veli onayı geri çekildi")


@router.get("/veli-onay/status", response_model=VeliOnayStatusResponse)
async def veli_onay_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VeliOnayStatusResponse:
    """Öğrencinin kendi veli onay durumu."""
    from services.veli_onay_service import VeliOnayService

    status_str = await VeliOnayService(db).get_status(str(current_user.id))
    return VeliOnayStatusResponse(status=status_str)


@router.post("/veli-onay/resend", response_model=VeliOnayResponse)
async def veli_onay_resend(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VeliOnayResponse:
    """Öğrenci veli onay email'ini tekrar gönderir (rate-limit'li)."""
    from core.email_util import send_email
    from services.veli_onay_service import VeliOnayService

    await _check_rate_limit(request, "register")
    svc = VeliOnayService(db)
    row = (
        await db.execute(
            text("SELECT veli_email FROM student_profiles WHERE user_id = :u"),
            {"u": str(current_user.id)},
        )
    ).first()
    if not row or not row[0]:
        raise HTTPException(status_code=400, detail="Kayıtlı veli e-postası yok")
    veli_email = row[0]
    token = await svc.resend(str(current_user.id), veli_email)
    _send_veli_onay_email(veli_email, token)
    return VeliOnayResponse(status="pending", message="Onay e-postası tekrar gönderildi")
```

`AuthenticatedUser`, `Request`, `text` import edili olduğundan emin ol (değilse dosyanın import bölümüne ekle: `from core.dependencies import AuthenticatedUser` — register'da `get_current_user` zaten kullanılıyorsa import mevcuttur; `from sqlalchemy import text`).

Ayrıca email gövdesi helper'ını dosyaya ekle (Task 6'da register de kullanacak):

```python
def _send_veli_onay_email(veli_email: str, token: str) -> None:
    """Veli onay + geri-çek linkli email gönder (fire-and-forget)."""
    import os

    from core.email_util import send_email

    frontend = os.getenv("FRONTEND_URL", "http://localhost:3001").rstrip("/")
    onay = f"{frontend}/veli-onay?token={token}"
    geri = f"{frontend}/veli-onay?token={token}&action=withdraw"
    html = (
        "<p>Merhaba,</p>"
        "<p>Velisi olduğunuz öğrenci KIRO2'ye kayıt oldu. Eğitim platformunu "
        "kullanabilmesi için açık rızanız gerekmektedir.</p>"
        f'<p><a href="{onay}">Onaylıyorum</a> (bağlantı 7 gün geçerli)</p>'
        f'<p style="font-size:12px;color:#888">Onayı geri çekmek için: '
        f'<a href="{geri}">tıklayın</a></p>'
    )
    send_email(veli_email, "KIRO2 — Veli Onayı Gerekiyor", html)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && USE_POSTGRES_TESTS=true python -m pytest tests/integration/test_veli_onay_endpoints.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Lint**

Run: `cd backend && ruff check api/auth.py --select=E,F,W`
Expected: All checks passed

- [ ] **Step 6: Commit**

```bash
git add backend/api/auth.py backend/tests/integration/test_veli_onay_endpoints.py
git commit -m "feat(kvkk-faz2): veli-onay verify/withdraw/status/resend endpointleri"
```

---

## Task 6: Register entegrasyonu — minor kaydında onay maili tetikle

**Files:**
- Modify: `backend/api/auth.py` (`kullanici_kayit`, minor dalı, ~line 600-625)
- Test: `backend/tests/integration/test_veli_onay_register.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/integration/test_veli_onay_register.py
"""Minor register → veli_consent pending kaydı oluşur."""
import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

pytestmark = pytest.mark.skipif(
    os.getenv("USE_POSTGRES_TESTS") != "true",
    reason="gerçek DB gerektirir",
)


@pytest.mark.asyncio
async def test_minor_register_creates_pending_consent(async_session):
    from main import app

    email = f"minor-{uuid.uuid4().hex[:8]}@t.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "sifre": "Guclu!Parola123",
                "ad_soyad": "Kucuk Ogrenci",
                "rol": "ogrenci",
                "birth_date": "2015-01-01",  # minor
                "veli_email": "veli@t.com",
            },
        )
    assert resp.status_code in (200, 201)

    row = (
        await async_session.execute(
            text(
                "SELECT vc.status FROM veli_consent vc JOIN users u "
                "ON u.id = vc.child_user_id WHERE u.email = :e"
            ),
            {"e": email},
        )
    ).first()
    assert row is not None
    assert row[0] == "pending"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && USE_POSTGRES_TESTS=true python -m pytest tests/integration/test_veli_onay_register.py -v`
Expected: FAIL (`row is None` — consent kaydı oluşmuyor)

- [ ] **Step 3: Inject consent request after minor student_profiles INSERT**

`api/auth.py` `kullanici_kayit` içinde, minor için `student_profiles` INSERT'i ve `await db.commit()`'ten SONRA, `return` ifadesinden ÖNCE ekle. Anchor: student_profiles INSERT param dict'i `"veli_email": kullanici_data.veli_email if minor else None` ile biten blok (~line 618). O bloğun commit'inden sonra:

```python
    # KVKK Faz 2: minor ise veli onay token üret + email (fire-and-forget)
    if minor and kullanici_data.veli_email:
        try:
            from services.veli_onay_service import VeliOnayService

            token = await VeliOnayService(db).request_consent(
                child_user_id=user_id, veli_email=kullanici_data.veli_email
            )
            _send_veli_onay_email(kullanici_data.veli_email, token)
        except Exception as e:  # noqa: BLE001 — email/consent hatası kaydı bozmamalı
            logger.error("veli onay tetikleme hatası: %s", e)
```

> `user_id` register'da kullanıcının id'si (raw INSERT'te `:id` parametresi). `logger` modül başında tanımlı değilse `import logging; logger = logging.getLogger(__name__)` ekle. `request_consent` kendi commit'ini yapar; ana register commit'inden sonra çağrıldığı için user+profile zaten persist.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && USE_POSTGRES_TESTS=true python -m pytest tests/integration/test_veli_onay_register.py -v`
Expected: PASS

- [ ] **Step 5: Regression — adult register hâlâ çalışır**

Run: `cd backend && USE_POSTGRES_TESTS=true python -m pytest tests/integration/test_veli_onay_register.py tests/integration/test_veli_onay_endpoints.py -v`
Expected: hepsi PASS

- [ ] **Step 6: Commit**

```bash
git add backend/api/auth.py backend/tests/integration/test_veli_onay_register.py
git commit -m "feat(kvkk-faz2): minor register → veli onay token + email tetikleme"
```

---

## Task 7: Enforcement dependency `require_veli_consent`

**Files:**
- Modify: `backend/core/dependencies.py` (yeni dependency)
- Test: `backend/tests/integration/test_require_veli_consent.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/integration/test_require_veli_consent.py
"""require_veli_consent: pending minor → 403, granted/adult → geçer."""
import os

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(
    os.getenv("USE_POSTGRES_TESTS") != "true", reason="gerçek DB gerektirir"
)


async def _make_profile(db, uid, veli_onay, birth="2015-01-01"):
    await db.execute(
        text(
            "INSERT INTO users (id, email, username, password_hash, first_name, "
            "last_name, role, is_active, is_verified, total_xp, level, elo_rating, "
            "is_premium, is_parent, birth_date, created_at, updated_at) VALUES "
            "(:id, :e, :u, 'x', 'T', 'C', CAST('STUDENT' AS userrole), TRUE, FALSE, "
            "0, 1, 1200, FALSE, FALSE, :b, NOW(), NOW()) ON CONFLICT (id) DO NOTHING"
        ),
        {"id": uid, "e": f"{uid}@t.com", "u": uid, "b": birth},
    )
    await db.execute(
        text(
            "INSERT INTO student_profiles (id, user_id, grade_level, veli_onay, "
            "veli_email, current_level, total_study_hours, total_questions_solved, "
            "correct_answers, irt_ability, created_at, updated_at) VALUES "
            "(:id, :u, 11, :vo, 'veli@t.com', 0.0, 0, 0, 0, 0.0, NOW(), NOW()) "
            "ON CONFLICT (id) DO NOTHING"
        ),
        {"id": f"prof-{uid}", "u": uid, "vo": veli_onay},
    )
    await db.commit()


@pytest.mark.asyncio
async def test_pending_minor_blocked(async_session):
    from core.dependencies import AuthenticatedUser, UserRole, require_veli_consent
    from fastapi import HTTPException

    await _make_profile(async_session, "rvc-pending", veli_onay=False)
    user = AuthenticatedUser(
        id="rvc-pending", username="x", role=UserRole("ogrenci"), email="x@t.com"
    )
    with pytest.raises(HTTPException) as exc:
        await require_veli_consent(current_user=user, db=async_session)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_granted_minor_allowed(async_session):
    from core.dependencies import AuthenticatedUser, UserRole, require_veli_consent

    await _make_profile(async_session, "rvc-granted", veli_onay=True)
    user = AuthenticatedUser(
        id="rvc-granted", username="x", role=UserRole("ogrenci"), email="x@t.com"
    )
    out = await require_veli_consent(current_user=user, db=async_session)
    assert out is user  # geçer, user döner
```

> **Not:** `UserRole("ogrenci")` doğru enum değerini kullan — testten önce `grep -n "class UserRole" backend/core/dependencies.py` ile değerleri doğrula (ogrenci/student vb.).

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && USE_POSTGRES_TESTS=true python -m pytest tests/integration/test_require_veli_consent.py -v`
Expected: FAIL (`ImportError: cannot import name 'require_veli_consent'`)

- [ ] **Step 3: Add dependency to `core/dependencies.py`**

```python
async def require_veli_consent(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    """Reşit olmayan öğrenci + veli_onay=False ise sosyal/PII erişimini 403'ler.

    Çekirdek öğrenme (soru/sınav/plan) bu dependency'i KULLANMAZ — açık kalır.
    """
    from sqlalchemy import text as _text

    row = (
        await db.execute(
            _text(
                "SELECT veli_onay FROM student_profiles WHERE user_id = :uid"
            ),
            {"uid": str(current_user.id)},
        )
    ).first()
    # Profil yoksa (öğrenci değilse) veya onay True ise geç
    if row is None or row[0] is True:
        return current_user
    raise HTTPException(
        status_code=403,
        detail="Bu özellik için veli onayı gereklidir (KVKK reşit olmayan kullanıcı).",
    )
```

> `Depends`, `HTTPException`, `AsyncSession`, `get_db`, `get_current_user`, `AuthenticatedUser` aynı dosyada zaten tanımlı/import edili.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && USE_POSTGRES_TESTS=true python -m pytest tests/integration/test_require_veli_consent.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/core/dependencies.py backend/tests/integration/test_require_veli_consent.py
git commit -m "feat(kvkk-faz2): require_veli_consent enforcement dependency"
```

---

## Task 8: Enforcement'ı sosyal/PII endpoint'lerine uygula

**Files:**
- Modify: sosyal/leaderboard/study-room/chat router'ları (grep ile tespit)

- [ ] **Step 1: Gated endpoint'leri bul**

Run:
```bash
grep -rln "leaderboard\|study.room\|study_room\|/social\|/friends\|/chat" backend/api --include="*.py"
```
Beklenen: leaderboard, social features, study_rooms, chat router dosyaları.

- [ ] **Step 2: Her gated endpoint'e dependency ekle**

İlgili endpoint'lerin signature'ına ekle (örnek leaderboard endpoint):

```python
from core.dependencies import require_veli_consent

@router.get("/leaderboard")
async def get_leaderboard(
    _consent: AuthenticatedUser = Depends(require_veli_consent),
    db: AsyncSession = Depends(get_db),
):
    ...
```

> Çekirdek öğrenme router'larına (questions, osym-exam, learning-path) **EKLEME**. Sadece sosyal/leaderboard/study-room/chat/public-profil.

- [ ] **Step 3: Smoke — gated endpoint pending minor için 403**

Bir gated endpoint için integration test ekle (Task 7 fixture pattern'i reuse — pending minor JWT ile çağır, 403 bekle). JWT için `.claude/rules/testing.md` `_generate_test_jwt` + `monkeypatch core.dependencies.JWT_SECRET` desenini kullan.

Run: `cd backend && USE_POSTGRES_TESTS=true python -m pytest tests/integration/test_require_veli_consent.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/api/
git commit -m "feat(kvkk-faz2): sosyal/PII endpointlerine veli onay enforcement"
```

---

## Task 9: Frontend — VeliOnayPage + route + authService

**Files:**
- Create: `frontend/src/pages/VeliOnayPage.tsx`
- Modify: `frontend/src/services/authService.ts`
- Modify: `frontend/src/App.tsx` (public route)

- [ ] **Step 1: authService metodları ekle**

`frontend/src/services/authService.ts` içine (mevcut `apiRequest` + `getErrorMessage` deseniyle):

```typescript
async veliOnayVerify(token: string): Promise<{ status: string; message: string }> {
  try {
    return await apiRequest(`${this.baseUrl}/veli-onay/verify`, {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  } catch (error: unknown) {
    throw new Error(getErrorMessage(error) || 'Onay işlemi başarısız');
  }
}

async veliOnayWithdraw(token: string): Promise<{ status: string; message: string }> {
  try {
    return await apiRequest(`${this.baseUrl}/veli-onay/withdraw`, {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  } catch (error: unknown) {
    throw new Error(getErrorMessage(error) || 'Geri çekme başarısız');
  }
}
```

- [ ] **Step 2: VeliOnayPage component oluştur**

```tsx
// frontend/src/pages/VeliOnayPage.tsx
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { authService } from '../services/authService';

export function VeliOnayPage() {
  const [params] = useSearchParams();
  const [message, setMessage] = useState('İşleniyor...');
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    const token = params.get('token');
    const action = params.get('action');
    if (!token) {
      setMessage('Geçersiz bağlantı (token yok).');
      setOk(false);
      return;
    }
    const run = action === 'withdraw'
      ? authService.veliOnayWithdraw(token)
      : authService.veliOnayVerify(token);
    run
      .then((res) => {
        setMessage(res.message || 'İşlem tamamlandı.');
        setOk(true);
      })
      .catch((e: Error) => {
        setMessage(e.message);
        setOk(false);
      });
  }, [params]);

  return (
    <div style={{ maxWidth: 480, margin: '80px auto', textAlign: 'center' }}>
      <h1>Veli Onayı</h1>
      <p role="status" aria-live="polite" style={{ color: ok === false ? '#c00' : '#080' }}>
        {message}
      </p>
    </div>
  );
}

export default VeliOnayPage;
```

- [ ] **Step 3: Route ekle (`App.tsx`)**

Public route'ların (örn. `/login`, `/register`) yanına ekle:

```tsx
<Route path="/veli-onay" element={<VeliOnayPage />} />
```

Ve dosya başına import:
```tsx
import { VeliOnayPage } from './pages/VeliOnayPage';
```

- [ ] **Step 4: Frontend typecheck**

Run: `cd frontend && npm run typecheck`
Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/VeliOnayPage.tsx frontend/src/services/authService.ts frontend/src/App.tsx
git commit -m "feat(kvkk-faz2): frontend VeliOnayPage + authService veli-onay metodları"
```

---

## Task 10: Golden Flow testi + GF list güncelleme

**Files:**
- Modify: `backend/tests/e2e/test_golden_flows.py`
- Modify: `docs/audits/golden-flows-history.md` (wave history satırı)

- [ ] **Step 1: Add Golden Flow test**

`backend/tests/e2e/test_golden_flows.py` içine (mevcut GF deseniyle, `@pytest.mark.golden_flow`):

```python
@pytest.mark.golden_flow
def test_gf_veli_onay_verify_invalid(client):
    """Veli onay verify (geçersiz token) — semantik 4xx, asla 500."""
    resp = client.post(
        "/api/v1/auth/veli-onay/verify", json={"token": "gf-gecersiz-token"}
    )
    assert resp.status_code < 500, (
        f"GF veli-onay crashed: {resp.status_code} {resp.text[:300]}"
    )
    assert resp.status_code in (400, 422)  # geçersiz token semantik hata
```

GF list yorumunu (`test_golden_flows.py` başı) güncelle: yeni satır ekle.

- [ ] **Step 2: Run GF test**

Run: `cd backend && python -m pytest tests/e2e/test_golden_flows.py::test_gf_veli_onay_verify_invalid -m golden_flow -v`
Expected: PASS (veya backend erişilemezse auto-skip — golden-flows.md kuralı)

- [ ] **Step 3: Update wave history doc**

`docs/audits/golden-flows-history.md` sonuna bir satır: KVKK Faz 2 veli-onay GF eklendi.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/e2e/test_golden_flows.py docs/audits/golden-flows-history.md
git commit -m "test(kvkk-faz2): veli-onay golden flow + GF list güncelleme"
```

---

## Task 11: Tam doğrulama + handoff

- [ ] **Step 1: Full quality gate (backend)**

Run:
```bash
cd backend && ruff check api/auth.py core/dependencies.py core/email_util.py services/veli_onay_service.py models/veli_consent.py --select=E,F,W
```
Expected: All checks passed

- [ ] **Step 2: Tüm yeni testler**

Run:
```bash
cd backend && USE_POSTGRES_TESTS=true python -m pytest tests/unit/test_veli_consent_model.py tests/unit/test_email_util.py tests/integration/test_veli_onay_service.py tests/integration/test_veli_onay_endpoints.py tests/integration/test_veli_onay_register.py tests/integration/test_require_veli_consent.py -v
```
Expected: hepsi PASS

- [ ] **Step 3: Docker E2E (CLAUDE.md deploy cycle)**

Backend rebuild + minor register → email log kontrol + verify akışı. (Operatör onayı gerekebilir — İnsan Döngüsünde kuralı.)

- [ ] **Step 4: Session handoff**

`.claude/sessions/latest.md` güncelle + MEMORY.md KVKK Faz 2 satırı.

---

## Self-Review Notları (yazım sonrası)

- **Spec coverage:** §2 model → Task 1/2. §3 servis → Task 4. §4 email → Task 3. §5 endpoint → Task 5. §6 enforcement → Task 7/8. §7 register → Task 6. §8 hata → endpoint 400/idempotent (Task 4/5). §9 test → her task TDD + Task 10 GF. §10 migration → Task 2. Frontend §11 → Task 9. ✓ Tüm spec bölümleri kapsandı.
- **Spec'ten sapma (bilinçli):** Spec "token grant'ta NULL'lanır" diyordu; plan **granted'da token_hash'i KORUR** (idempotency + withdraw-by-token link için), withdrawn/expired'da NULL'lar. Withdraw email linki aynı token'ı kullandığından bu gerekli. Güvenlik etkisi yok (granted token sadece idempotent no-op veya withdraw sağlar).
- **Type tutarlılığı:** `VeliOnayResult(success, status, error_code, message)` tüm task'larda aynı. `child_user_id: str` her yerde. `token_hash` String(64). `veli_onay` UPDATE raw `text()` (register stiliyle tutarlı, StudentProfile ORM bağımlılığı yok).
- **Doğrulanması gereken runtime varsayımlar (her biri ilk kullanımda grep ile):** (a) async test session fixture adı (`async_session` varsayıldı), (b) `UserRole` enum değeri (`ogrenci`), (c) register'da `user_id` değişken adı + final commit/return konumu, (d) `AuthenticatedUser` import yolu auth.py'de mevcut mu.
