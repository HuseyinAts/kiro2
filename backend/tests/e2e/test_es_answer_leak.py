"""Elasticsearch cevap sızıntısı — arama öğrenciye cevap anahtarı vermemeli.

27 Tem 2026 ÖLÇÜMÜ (canlı, seed öğrenci token'ı):

    POST /api/v1/elasticsearch/questions/search  {"query": "üçgen", "size": 2}
    -> HTTP 200, total=4399
    -> source.correct_answer = 'A'      <-- cevap anahtarı
    -> source.explanation   = dolu      <-- çözüm

Yani auth VAR ama işe yaramıyor: `Depends(get_current_user)` herhangi bir
öğrenciyi geçiriyor. Sınırsız arama + her sonuçta cevap = tüm soru bankasının
cevap anahtarı. Bu, S199'da `/cat/next`'te kapatılan "cevap-anahtarı oracle'ı"
sınıfının aynısı, farklı yüzeyde.

Kök neden `core/elasticsearch_client.py`: `{"id": h["_id"], **h["_source"]}`
— `_source` filtresi hiç yok, doküman ne taşıyorsa dışarı çıkıyor.
`api/elasticsearch.py` de `"source": result` diyerek aynen aktarıyor.

İKİNCİ SORUN — KALİTE KAPISI BYPASS'I. ES ayrı bir kopya; PG'deki
`mv_safe_for_beta` kapısı bu yola hiç değmiyor. 500 rastgele ES dokümanı:

    question_bank'ta       500/500   (yetim yok)
    is_active              294/500   = %58.8
    mv_safe_for_beta'da     32/500   = %6.4

Yani öğrenci aramada reddedilmiş/arşivlenmiş soru görüyor. Son-filtreleme
çare değil (%6.4 geçiş oranında 10 sonuç için ~160 doküman çekmek gerekir);
index'in KENDİSİ kapılı kurulmalı — bkz. reindex görevi.

Bu testler filtre REPLİKE ETMEZ; gerçek HTTP ucunu çağırır ve dönen gövdeyi
denetler. Backend/ES/DB yoksa skip — ortam eksikliği başarısızlık değildir.
"""

from __future__ import annotations

import os

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

pytestmark = [pytest.mark.golden_flow, pytest.mark.e2e]

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
TIMEOUT = 30.0
STUDENT = {
    "email": "test@kiro2.com",
    "password": "Kiro2Beta2026@x",  # pragma: allowlist secret
}

SEARCH_PATH = "/api/v1/elasticsearch/questions/search"

# Öğrenciye ASLA gitmeyecek alanlar. `explanation` da cevabı ele verir.
# `is_active` / `quality_score` / `is_calib_pool` iç kalite sinyalleri —
# dışarı sızmaları sızıntının kendisi kadar kritik değil ama sözleşme dışı.
FORBIDDEN_FIELDS = (
    "correct_answer",
    "explanation",
    "is_calib_pool",
    "is_calibrated",
    "quality_score",
)

# Türkçe karakterli sorgu bilinçli: hem sızıntıyı hem de UTF-8 gövde işlemeyi
# aynı anda kapsar (inline curl'de bozulan tam da bu).
QUERIES = ["üçgen", "fonksiyon", "hücre"]


@pytest.fixture(scope="module")
def client() -> httpx.Client:
    c = httpx.Client(base_url=BACKEND_URL, timeout=TIMEOUT)
    try:
        c.get("/health")
    except Exception as exc:
        c.close()
        pytest.skip(f"backend {BACKEND_URL} ulaşılamıyor: {exc}")
    yield c
    c.close()


@pytest.fixture(scope="module")
def student_token(client: httpx.Client) -> str:
    resp = client.post("/api/v1/auth/login", json=STUDENT)
    # 429 is rate-limiting, not a missing environment -- skip'e çevirmek
    # gerçek bir regresyonu (kapı kendini boğuyor) sessizce gizler. Aynı
    # sözleşme test_golden_flows.py::_login() ve GF1wB'de de uygulanıyor.
    if resp.status_code == 429:
        pytest.fail(f"seed öğrenci girişi rate-limited (HTTP 429): {resp.text[:200]}")
    if resp.status_code != 200:
        pytest.skip(
            f"seed öğrenci girişi başarısız: {resp.status_code} {resp.text[:200]}"
        )
    token = resp.json().get("access_token")
    assert token, f"login yanıtında access_token yok: {resp.json()}"
    return token


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


def _search(client: httpx.Client, token: str, query: str, size: int = 5) -> dict:
    resp = client.post(
        SEARCH_PATH,
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query, "size": size},
    )
    if resp.status_code == 404:
        pytest.skip(f"{SEARCH_PATH} yok (router kayıtlı değil?)")
    # Mesaj değişkene alınıyor: uzun assert satırlarını yerel ruff ile
    # pre-commit'in pinlediği ruff 0.7.1 FARKLI biçimlendiriyor (biri
    # `assert x, (\n msg\n)`, diğeri `assert (\n x\n), msg`) — sonsuz salınım.
    # Kısa satır ikisinde de aynı kalıyor.
    detay = f"{resp.status_code} {resp.text[:300]}"
    assert resp.status_code < 500, f"arama çöktü: {detay}"
    assert resp.status_code == 200, f"beklenmeyen durum: {detay}"
    return resp.json()


def test_es_search_does_not_leak_answer_key(client: httpx.Client, student_token: str):
    """Arama sonucunda cevap anahtarı / çözüm alanı BULUNMAMALI."""
    checked = 0
    leaks: list[str] = []

    for query in QUERIES:
        body = _search(client, student_token, query)
        for result in body.get("results", []):
            source = result.get("source") or {}
            checked += 1
            for field in FORBIDDEN_FIELDS:
                if field in source:
                    leaks.append(
                        f"{query}/{str(source.get('id'))[:8]}: {field}={source[field]!r}"
                    )

    if checked == 0:
        pytest.skip("hiçbir sorgu sonuç dönmedi — test anlamsız")

    ozet = f"{len(leaks)} sızıntı ({checked} sonuç tarandı). İlk 3: {leaks[:3]}"
    assert not leaks, ozet


def test_es_similar_does_not_leak_answer_key(client: httpx.Client, student_token: str):
    """/questions/{id}/similar de cevap anahtarı sızdırmamalı.

    Ayrı test, çünkü ayrı kod yolu: arama `turkish_full_text_search`,
    benzerlik `search()` (more_like_this) kullanıyor. 27 Tem ölçümünde ikisi de
    sızdırıyordu; birini düzeltip diğerini unutmak bu dosyanın var oluş sebebi.
    """
    # Önce aramadan geçerli bir id al — sabit id gömmek veri değişince çürür.
    body = _search(client, student_token, QUERIES[0], size=1)
    results = body.get("results", [])
    if not results:
        pytest.skip("arama sonuç dönmedi — benzerlik testi için id yok")
    qid = (results[0].get("source") or {}).get("id") or results[0].get("id")
    if not qid:
        pytest.skip(f"arama sonucunda id yok: {results[0]!r}")

    resp = client.get(
        f"/api/v1/elasticsearch/questions/{qid}/similar",
        params={"size": 5},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    detay = f"{resp.status_code} {resp.text[:300]}"
    assert resp.status_code < 500, f"/similar çöktü: {detay}"
    if resp.status_code != 200:
        pytest.skip(f"/similar {resp.status_code} döndü")

    leaks: list[str] = []
    checked = 0
    for result in resp.json().get("results", []):
        source = result.get("source") or {}
        checked += 1
        for field in FORBIDDEN_FIELDS:
            if field in source:
                leaks.append(f"{str(source.get('id'))[:8]}: {field}={source[field]!r}")

    if checked == 0:
        pytest.skip("benzer soru dönmedi — test anlamsız")

    assert not leaks, f"{len(leaks)} sızıntı ({checked} sonuç). İlk 3: {leaks[:3]}"


# BEKLENEN KIRMIZI: kapı bypass'ı bilinçli olarak ertelendi (27 Tem kararı).
# Cevap sızıntısı kapatıldı ama ES index'i hâlâ 64.270 dokümanın tamamını
# tutuyor; bunun ~%94'ü mv_safe_for_beta dışında. Kapatılması index'in
# v_safe_for_beta'dan yeniden kurulmasını gerektiriyor (ayrı iş).
#
# strict=True bilinçli: reindex yapıldığı anda bu test geçmeye başlayacak ve
# paket "unexpectedly passing" ile kırmızıya dönecek — marker'ı kaldırmak
# ZORUNLU olacak. Yeşil paketin içinde sessizce yaşayan bilinen-kırık test
# bırakmamak için.
@pytest.mark.xfail(
    reason="ES index'i kalite kapısından geçirilmedi — reindex v_safe_for_beta'dan "
    "yapılana kadar arama kapı dışı soru döndürüyor (ölçüm: 14/15)",
    strict=True,
)
@pytest.mark.asyncio
async def test_es_search_respects_quality_gate(
    client: httpx.Client, student_token: str, db_session: AsyncSession
):
    """Aramadan dönen her soru mv_safe_for_beta içinde olmalı."""
    ids: list[str] = []
    for query in QUERIES:
        body = _search(client, student_token, query)
        for result in body.get("results", []):
            qid = (result.get("source") or {}).get("id") or result.get("id")
            if qid:
                ids.append(str(qid))

    if not ids:
        pytest.skip("hiçbir sorgu sonuç dönmedi — test anlamsız")

    rows = await db_session.execute(
        text(
            """
            SELECT x.id
            FROM unnest(CAST(:ids AS text[])) AS x(id)
            WHERE NOT EXISTS (
                SELECT 1 FROM mv_safe_for_beta m WHERE m.id = x.id
            )
            """
        ),
        {"ids": ids},
    )
    unsafe = [r[0] for r in rows.fetchall()]

    assert not unsafe, (
        f"ES araması {len(unsafe)}/{len(ids)} soruyu kalite kapısı dışından "
        f"servis etti. Örnek: {unsafe[:3]}"
    )
