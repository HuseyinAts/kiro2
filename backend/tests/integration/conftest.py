"""
Integration tests configuration
Use existing Docker PostgreSQL container for faster testing
"""

import os
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

# Set test environment variables before any imports that load config
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

# Fix ALLOWED_ORIGINS JSON parsing error - must be valid JSON array string
# Remove any malformed values and use simple test value
for key in ["ALLOWED_ORIGINS", "SERVER_ALLOWED_ORIGINS"]:
    if key in os.environ:
        # Only keep if it's already valid JSON, otherwise remove it
        try:
            import json

            json.loads(os.environ[key])
        except (json.JSONDecodeError, ValueError):
            del os.environ[key]


def canli_dsn_cozumle() -> str | None:
    """Canli (uretim-semasi) Postgres DSN'ini KAYNAK KODA GOMMEDEN coz.

    NEDEN VAR (S229): DSN'i test dosyasina sabit yazmak parolayi git'e sokuyordu
    ve `detect-secrets` kancasi bunu HAKLI olarak blokladi (Basic Auth
    Credentials). Onceki turda ayni satir formatter tarafindan sarildigi icin
    dedektorun regex'ine takilmamis ve fark edilmeden commit'e girmisti — yani
    "bir kez gecti" guvenlik kaniti DEGIL.

    POSTGRES OLMAYAN DSN REDDEDILIR — bu kural olmadan kusur uretiyordu:
    `DATABASE_URL`'i test kosum ortami `sqlite+aiosqlite:///:memory:` yapiyor
    (bu dosyanin ustundeki `tests/conftest.py` ve bazi test modulleri
    `os.environ.setdefault` ile). Guard'siz surum o SQLite'a baglanip
    `no such table: information_schema.columns` ile 11 test dusurdu. Ayni
    sinifin sessiz hali bu depoda kayitli: "testler sqlite `else` dalini
    kostugu icin yesildi" — orada kirmizi bile vermemisti.

    Sira (`.claude/rules/database.md`: "Config Source: Always read backend/.env"):
      1. `KIRO2_TEST_DSN` — bu amaca ozel, en yuksek oncelik
      2. `KVKK_VERIFY_DSN` — mevcut konvansiyon
         (`scripts/audit_orm_vs_db_parity.py`, `tests/db/test_alembic_from_scratch.py`)
      3. `backend/.env` icindeki `DATABASE_URL` (git-ignore'lu, gercek DSN orada)
      4. `DATABASE_URL` ortam degiskeni — YALNIZCA postgres ise
      5. None -> cagiran `pytest.skip` eder (sessizce sqlite'a DUSMEZ)

    Donen deger daima asyncpg surucusune normalize edilir.
    """

    def _postgres_mu(deger: str | None) -> bool:
        return bool(deger) and deger.strip().startswith(("postgresql", "postgres://"))

    adaylar: list[str | None] = [
        os.environ.get("KIRO2_TEST_DSN"),
        os.environ.get("KVKK_VERIFY_DSN"),
    ]

    env_file = Path(__file__).resolve().parents[2] / ".env"
    if env_file.exists():
        for ham_satir in env_file.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            satir = ham_satir.strip()
            if satir.startswith("DATABASE_URL=") and not satir.startswith("#"):
                adaylar.append(satir.split("=", 1)[1].strip().strip("'\""))
                break

    # En sonda: test kosumunda sqlite'a set edilmis olabilir, o yuzden filtreli
    adaylar.append(os.environ.get("DATABASE_URL"))

    dsn = next((a for a in adaylar if _postgres_mu(a)), None)
    if dsn is None:
        return None

    dsn = dsn.strip()
    if dsn.startswith("postgresql+"):
        return dsn
    if dsn.startswith("postgresql://"):
        return dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
    return dsn.replace("postgres://", "postgresql+asyncpg://", 1)


@pytest_asyncio.fixture
async def live_db():
    """Canli Postgres'e baglı AsyncSession; test sonunda ROLLBACK eder.

    Uretim semasina karsi kosar (mock DB DEGIL): sema kaymasi / ORM-varsayilan
    sinifi kusurlari mock'la yapisal olarak gorulemez (S228/S229 dersi).
    """
    dsn = canli_dsn_cozumle()
    if not dsn:
        pytest.skip(
            "Canli DSN cozulemedi — KIRO2_TEST_DSN / KVKK_VERIFY_DSN / "
            "DATABASE_URL ortam degiskeni ya da backend/.env gerekli"
        )

    engine = create_async_engine(dsn)
    try:
        async with engine.connect():
            pass
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"Canli Postgres ulasilamiyor: {type(exc).__name__}: {exc}")

    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest.fixture(scope="session")
def db_engine():
    """Use existing Docker PostgreSQL container"""
    # Use the test-postgres container running on port 5433
    try:
        engine = create_engine("postgresql://testuser:test123@localhost:5433/testdb")
        # Test connection before proceeding
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("Test PostgreSQL not available on port 5433")

    # Import all models to register with Base
    from models.database import (
        Base,
    )

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup - drop all tables after tests
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def sync_db_session(db_engine):
    """Provide clean database session with auto-rollback"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    yield session

    # Auto-rollback to clean up test data
    session.rollback()
    session.close()
