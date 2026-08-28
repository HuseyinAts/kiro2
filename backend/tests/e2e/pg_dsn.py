"""Gerçek PostgreSQL DSN çözümleyici — e2e testleri için tek tanım.

NEDEN VAR (27 Tem 2026 ölçümü)
------------------------------
Dört e2e dosyası birbirinin kopyası bir `_resolve_dsn()` taşıyordu:

    dsn = (os.environ.get("KVKK_VERIFY_DSN")
           or os.environ.get("DATABASE_URL_SYNC")
           or os.environ.get("DATABASE_URL"))    # <-- kusur burada
    if not dsn:
        return None

Üçüncü dal ASLA boş dönmez, çünkü `backend/conftest.py:21` modül seviyesinde

    os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL",
                                           "sqlite+aiosqlite:///:memory:")

diyerek dışarıdan gelen gerçek DSN'i EZİYOR. Sonuç: `pytest.skip(...)` ölü kod;
`create_async_engine(sqlite)` başarıyla bağlanıyor (dosyayı yaratıyor) ve test
`question_bank` tablosunu arayıp `no such table` ile patlıyor. Ölçülen etki:

    test_quality_gate_leak.py            -> sızıntı yüzünden DEĞİL, sqlite
                                            yüzünden XFAIL. xfail(strict=True)
                                            ölü-adam anahtarı hiç tetiklenmiyor:
                                            kapı yayıldıktan sonra da sqlite'ta
                                            çökeceği için hâlâ XFAIL kalacaktı.
    test_tablesample_regression.py       -> FAILED (skip değil)
    test_db_schema_parity.py             -> FAILED
    test_student_profile_id_invariant.py -> FAILED (`id::text` sqlite'ta yok)

Yani "yeşil paket" hiçbir şey kanıtlamıyordu. Doğru desen repoda zaten vardı:
`tests/integration/test_curator_verdict_flag_resolve.py:26-37` DATABASE_URL
fallback'i HİÇ kullanmıyor.

KURAL: Gerçek-DB testi, gerçek DB yoksa SKIP olmalı — sahte bir motorla
başarısız OLMAMALI. Başarısızlık "kod bozuk" demektir; ortam eksikliği değil.
"""

from __future__ import annotations

import os

# sqlite/aiosqlite gibi taklit motorlar: bunlarla e2e testi koşmak, testin
# ölçtüğünü sandığı şeyi ölçmediği anlamına gelir.
_FAKE_ENGINE_MARKERS = ("sqlite", ":memory:")


def resolve_pg_dsn() -> str | None:
    """Gerçek PostgreSQL asyncpg DSN'i döndür; yoksa None.

    None dönmesi çağıranın `pytest.skip()` etmesi gerektiği anlamına gelir.
    """
    dsn = os.environ.get("KVKK_VERIFY_DSN") or os.environ.get("DATABASE_URL_SYNC")

    # DATABASE_URL bilinçli olarak SON çare: conftest onu sqlite'a eziyor.
    # Yine de dışarıdan gerçek bir postgres DSN'i geçilmiş olabilir, o yüzden
    # tamamen yok saymak yerine sahte-motor filtresinden geçiriyoruz.
    if not dsn:
        dsn = os.environ.get("DATABASE_URL")

    if not dsn:
        return None

    lowered = dsn.lower()
    if any(marker in lowered for marker in _FAKE_ENGINE_MARKERS):
        return None
    if not lowered.startswith("postgresql"):
        return None

    for prefix in ("postgresql+psycopg2://", "postgresql://"):
        if dsn.startswith(prefix):
            return dsn.replace(prefix, "postgresql+asyncpg://", 1)
    return dsn


SKIP_REASON = (
    "Gerçek PostgreSQL yok. KVKK_VERIFY_DSN (veya DATABASE_URL_SYNC) ile "
    "postgresql:// DSN ver. NOT: conftest.py DATABASE_URL'i sqlite'a ezdiği "
    "için o değişken tek başına yeterli değil."
)
