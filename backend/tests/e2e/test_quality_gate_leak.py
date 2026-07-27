"""Kalite kapısı sızıntısı — öğrenciye servis edilen her soru v_safe_for_beta'da mı?

Convention v3 (12 Haz 2026, soru_bankasi_service.py:32-50): öğrenci-yüzü soru
seçiminin TEK doğruluk kaynağı `v_safe_for_beta` view'idir. View; is_active +
status + pipeline_metadata dışlamalarını (demoted / tier1 tek-sinyal /
fallback-topic / görselsiz-şekil / bozuk-LaTeX) tek yerde kodlar.

Ama bu sözleşme yayılmamıştı (27 Tem 2026 ölçümü):
  v_safe_for_beta                       25.127
  status-only filtre (cat/placement)    34.982   -> +9.855 sızıntı
  sadece is_active (duel/PF/osym)      110.858   -> +85.731 sızıntı

Yani 30 May 2026'da "circular defect / verdict: drop" diye yargılanmış bir soru
27 Tem 2026'da hâlâ öğrenciye servis edilebiliyordu. Bu, .claude/rules/testing.md
Ders #31'in ("status yargısı != servis dışı") aynı sınıfının tekrarı.

Bu test filtreleri REPLİKE ETMEZ — gerçek servis fonksiyonlarını çağırır ve
dönen id'lerin view'in alt kümesi olduğunu doğrular. Filtreyi tekrar yazmak,
düzeltmeye çalıştığımız kod↔view drift'inin ta kendisi olurdu.

ÜRÜN KARARI (27 Tem 2026, Hüseyin): kapı uygulandığında havuzu yetersiz kalan
konuda BOŞ dönülür ve "henüz doğrulanmış soru yok" denir — kalite kapısı
gevşetilmez, komşu konudan doldurulmaz. Bu yüzden testler "en az N soru dönmeli"
diye ısrar etmez; yalnız DÖNENLERİN güvenli olmasını şart koşar.
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

pytestmark = [
    pytest.mark.golden_flow,
    # BEKLENEN KIRMIZI: #7'nin 3. adımı (gate yayılımı) henüz yapılmadı.
    # strict=True → iş bitip testler geçmeye başladığında bu marker'ın
    # KALDIRILMASI zorunlu olur; aksi halde paket "unexpectedly passing" ile
    # kırmızıya döner. Yeşil görünen bir paketin içinde sessizce yaşayan
    # bilinen-kırık test bırakmamak için.
    pytest.mark.xfail(
        reason="#7 adım 3: v_safe_for_beta kapısı cat_session/placement_service/"
        "productive_failure/duel/osym_questions'a henüz yayılmadı",
        strict=True,
    ),
]

# Sızıntıya en açık konu (27 Tem ölçümü: 8.591 aktif / 452 v_safe).
# Kapı yoksa dönen soruların büyük çoğunluğu view dışıdır -> test kırmızı.
LEAKY_TOPIC_ID = "c3261158-b5b3-5b21-aba0-926d0391c800"


@pytest_asyncio.fixture
async def db_session():
    dsn = resolve_pg_dsn()
    if not dsn:
        pytest.skip(SKIP_REASON)

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


async def _unsafe_ids(session: AsyncSession, ids: list[str]) -> list[str]:
    """Verilen id'lerden v_safe_for_beta DIŞINDA kalanlar."""
    if not ids:
        return []
    result = await session.execute(
        text(
            """
            SELECT x.id
            FROM unnest(CAST(:ids AS text[])) AS x(id)
            WHERE NOT EXISTS (
                SELECT 1 FROM v_safe_for_beta v WHERE v.id = x.id
            )
            """
        ),
        {"ids": [str(i) for i in ids]},
    )
    return [r[0] for r in result.fetchall()]


@pytest.mark.asyncio
async def test_productive_failure_pretest_only_safe(db_session):
    """get_pretest_questions yalnız v_safe_for_beta'dan seçmeli."""
    from services.productive_failure_service import get_pretest_questions

    rows = await get_pretest_questions(
        db=db_session, topic_id=LEAKY_TOPIC_ID, subject="MATEMATIK", count=20
    )
    ids = [r["question_id"] for r in rows]
    if not ids:
        pytest.skip(f"{LEAKY_TOPIC_ID} konusunda hiç soru dönmedi — test anlamsız")

    unsafe = await _unsafe_ids(db_session, ids)
    assert not unsafe, (
        f"productive_failure pretest {len(unsafe)}/{len(ids)} soruyu kalite kapısı "
        f"dışından servis etti. Örnek: {unsafe[:3]}"
    )


@pytest.mark.asyncio
async def test_cat_candidate_questions_only_safe(db_session):
    """CAT aday havuzu yalnız v_safe_for_beta'dan gelmeli (ZPD ve warm-up)."""
    from app.services.cat_session import CATSessionService

    service = CATSessionService(redis=None, db=db_session)

    for warm_up in (True, False):
        candidates = await service._get_candidate_questions(
            subject_id="MATEMATIK", theta=0.0, warm_up=warm_up
        )
        ids = [c.question_id for c in candidates]
        if not ids:
            continue

        unsafe = await _unsafe_ids(db_session, ids)
        assert not unsafe, (
            f"CAT (warm_up={warm_up}) {len(unsafe)}/{len(ids)} adayı kalite kapısı "
            f"dışından aldı. Örnek: {unsafe[:3]}"
        )
