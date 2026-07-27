"""Select.tablesample() SQLAlchemy 2.0'da YOK — kullanan her PostgreSQL yolu çöker.

27 Tem 2026'da ölçüldü: `select(Model).tablesample(func.bernoulli(20))` çağrısı
`AttributeError: 'Select' object has no attribute 'tablesample'` atıyor
(konteyner SQLAlchemy 2.0.51, `hasattr(select(), "tablesample") is False`).
Kod `if dialect == "postgresql"` dalında bunu kullandığı için üretimde HER ZAMAN
patlıyordu; sqlite testlerinde else dalı çalıştığı için testler yeşil kalmıştı.

Belirti dosyaya göre değişiyordu:
  - api/duel_api.py, services/productive_failure_service.py -> 500
  - services/soru_bankasi_service.py -> `except Exception: return []` yutuyor,
    yani sınav üretimi sessizce "soru yok" diyordu (golden-flows.md'nin bir kez
    temizlediği rule-of-eight yutma sınıfının aynısı)

services/offline_sync_service.py:112 bunu zaten keşfetmiş ve tek dosyada
düzeltmişti ("canlı doğrulandı" notuyla); kalan 11 site aynı kalmıştı.

DOĞRU API mevcut: `sqlalchemy.tablesample(Model, func.bernoulli(20))` bir
FROM-clause üretir. Ama ölçüm bunu da eledi — kalite kapısıyla birlikte
TABLESAMPLE planlayıcıyı kilitliyor (13,4 sn). Bu yüzden kanon `func.random()`.
"""

import ast
import os
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

pytestmark = pytest.mark.golden_flow

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = ("services", "api", "app")


def _resolve_dsn() -> str | None:
    dsn = (
        os.environ.get("KVKK_VERIFY_DSN")
        or os.environ.get("DATABASE_URL_SYNC")
        or os.environ.get("DATABASE_URL")
    )
    if not dsn:
        return None
    for prefix in ("postgresql+psycopg2://", "postgresql://"):
        if dsn.startswith(prefix):
            return dsn.replace(prefix, "postgresql+asyncpg://", 1)
    return dsn


@pytest_asyncio.fixture
async def db_session():
    dsn = _resolve_dsn()
    if not dsn:
        pytest.skip("KVKK_VERIFY_DSN / DATABASE_URL ayarlı değil")

    engine = create_async_engine(dsn, poolclass=NullPool)
    try:
        conn = await engine.connect()
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"DB erişilemiyor: {type(exc).__name__}")

    maker = async_sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
    session = maker()
    try:
        yield session
    finally:
        await session.close()
        await conn.close()
        await engine.dispose()


def _contains_select_call(node: ast.AST) -> bool:
    """Bu ifade zincirinde select(...) çağrısı var mı?"""
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name) and func.id == "select":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "select":
                return True
    return False


def _find_select_tablesample(path: Path) -> list[int]:
    """select(...) üzerinde .tablesample(...) çağıran satır numaraları."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        # Ayrıştırılamayan dosya bu testin konusu değil; import edilebilirlik
        # kapısı ayrı bir testte (test_mapped_routers_are_importable).
        return []

    hits: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "tablesample"):
            continue
        # sqlalchemy.tablesample(Model, ...) modül fonksiyonudur — o meşru.
        # Yasak olan, bir select(...) zincirine METOT olarak takılması.
        if _contains_select_call(func.value):
            hits.append(node.lineno)
    return hits


def test_no_select_tablesample_in_backend():
    """Hiçbir üretim dosyası select(...).tablesample(...) kullanmamalı."""
    violations: list[str] = []
    for directory in SCAN_DIRS:
        root = BACKEND_ROOT / directory
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if "_deprecated" in path.parts or "__pycache__" in path.parts:
                continue
            for lineno in _find_select_tablesample(path):
                violations.append(f"{path.relative_to(BACKEND_ROOT)}:{lineno}")

    assert not violations, (
        "select(...).tablesample(...) SQLAlchemy 2.0'da AttributeError atar — "
        "PostgreSQL'de bu yollar çöker veya sessizce boş döner.\n"
        "Kanon: .order_by(func.random()) (bkz services/offline_sync_service.py:112).\n"
        + "\n".join(f"  {v}" for v in violations)
    )


@pytest.mark.asyncio
async def test_pretest_questions_does_not_crash(db_session):
    """get_pretest_questions PostgreSQL'de exception atmadan sonuç dönmeli."""
    from services.productive_failure_service import get_pretest_questions

    rows = await get_pretest_questions(
        db=db_session,
        topic_id="c3261158-b5b3-5b21-aba0-926d0391c800",
        subject="MATEMATIK",
        count=5,
    )
    assert isinstance(rows, list)
